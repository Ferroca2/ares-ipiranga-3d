"""GLB leve para o visualizador web, com texturas.

Os materiais do render projetam texturas em caixa pelas coordenadas do objeto, o que o glTF não entende.
Aqui cada um vira imagem: pisos e azulejos são assados (bake de cor) sobre a área inteira que ocupam;
madeiras e tecidos, que repetem, são assados num ladrilho de um período. Depois cada face ganha UV a partir
das coordenadas de mundo, na mesma escala, e o resto do modelo é dizimado.

uso: python light_glb.py <paleta> [--catalog]
"""
import bpy, bmesh, sys, os, re, json, math
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import apply_modifiers
import catalog_items

ROOT = os.path.dirname(os.path.abspath(__file__))
p = [a for a in sys.argv[sys.argv.index("--") + 1:]] if "--" in sys.argv else sys.argv[1:]
PAL = [a for a in p if not a.startswith("--")][-1]
CATALOG = "--catalog" in p
BAKE_DIR = os.path.join(ROOT, "web_tex", PAL)
os.makedirs(BAKE_DIR, exist_ok=True)

# superfícies com paginação procedural: assadas sobre a área real (plano de projeção, px/m, lado máx.)
EXTENT = {
    "Vinilico carvalho": ("xy", 300, 2048),
    "Porcelanato cimento 60": ("xy", 500, 1024),
    "Azulejo box (xz)": ("xz", 700, 1536),
    "Azulejo box (yz)": ("yz", 700, 1536),
    "Azulejo cozinha": ("xz", 700, 1536),
}
AX = {"x": 0, "y": 1, "z": 2}

bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "modelo2", PAL, f"ares_ipiranga_final01_{PAL}.blend"))
sc = bpy.context.scene
for n in ["Ceu_externo", "Exterior"]:
    o = bpy.data.objects.get(n)
    if o:
        bpy.data.objects.remove(o)
for o in list(bpy.data.objects):
    if o.type in ("LIGHT", "CAMERA"):
        bpy.data.objects.remove(o)


def bsdf_of(m):
    return m.node_tree.nodes.get("Principled BSDF") if m and m.use_nodes else None


def classify(m):
    """('extent', ...) | ('period', P) | ('image', P, img, alpha) | ('uv',) | None"""
    if not m or not m.use_nodes:
        return None
    nodes = m.node_tree.nodes
    if m.name in EXTENT:
        return ("extent",)
    imgs = [n for n in nodes if n.type == "TEX_IMAGE" and n.image]
    mp = next((n for n in nodes if n.type == "MAPPING"), None)
    if not imgs or any(n.type == "TEX_BRICK" for n in nodes):
        return None
    if any(n.type == "SEPXYZ" for n in nodes):
        # surface() sem paginação (pintura): textura plana que repete a cada 1/escala metros
        return ("period", 1.0 / mp.inputs["Scale"].default_value[0]) if mp else None
    if not any(n.projection == "BOX" for n in imgs):
        return ("uv",)
    if mp is None:
        return None
    P = 1.0 / mp.inputs["Scale"].default_value[0]
    if any(n.outputs["Alpha"].is_linked for n in imgs):
        return ("image", P, imgs[0].image)
    return ("period", P)


used = {}
for o in bpy.data.objects:
    if o.type == "MESH":
        for s in o.material_slots:
            if s.material:
                used.setdefault(s.material.name, s.material)
kind = {n: classify(m) for n, m in used.items()}

# área (no plano de projeção) ocupada por cada material com paginação
apply_modifiers()
ext_box = {}
for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    mw = o.matrix_world
    for poly in o.data.polygons:
        m = o.material_slots[poly.material_index].material if o.material_slots else None
        if not m or m.name not in EXTENT:
            continue
        a, b = (AX[c] for c in EXTENT[m.name][0])
        bx = ext_box.setdefault(m.name, [1e9, 1e9, -1e9, -1e9])
        for vi in poly.vertices:
            co = mw @ o.data.vertices[vi].co
            bx[0] = min(bx[0], co[a]); bx[1] = min(bx[1], co[b])
            bx[2] = max(bx[2], co[a]); bx[3] = max(bx[3], co[b])

# ------------------------------------------------------------------ bake
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 4
sc.render.bake.use_pass_direct = False
sc.render.bake.use_pass_indirect = False
sc.render.bake.use_pass_color = True
sc.render.bake.margin = 0


def bake(m, a_ax, b_ax, a0, b0, a1, b1, w, h):
    """Assa a cor base de m sobre o retângulo [a0,a1]x[b0,b1] do plano (a_ax, b_ax)."""
    me = bpy.data.meshes.new("bake")
    third = ({0, 1, 2} - {AX[a_ax], AX[b_ax]}).pop()
    vs = []
    for (u, v) in [(a0, b0), (a1, b0), (a1, b1), (a0, b1)]:
        co = [0.0, 0.0, 0.0]
        co[AX[a_ax]] = u; co[AX[b_ax]] = v; co[third] = 0.0
        vs.append(co)
    me.from_pydata(vs, [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new()
    for li, (u, v) in zip(range(4), [(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv.data[li].uv = (u, v)
    ob = bpy.data.objects.new("bake", me)
    sc.collection.objects.link(ob)
    me.materials.append(m)
    img = bpy.data.images.new(f"web_{m.name}", w, h, alpha=False)
    node = m.node_tree.nodes.new("ShaderNodeTexImage")
    node.image = img
    m.node_tree.nodes.active = node
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"COLOR"}, margin=0, use_clear=True)
    m.node_tree.nodes.remove(node)
    bpy.data.objects.remove(ob)
    path = os.path.join(BAKE_DIR, re.sub(r"[^\w]+", "_", m.name) + ".jpg")
    img.filepath_raw = path
    img.file_format = "JPEG"
    sc.render.image_settings.quality = 86
    img.save()
    return img


spec = {}  # nome -> (tipo, dados de UV, imagem)
for n, k in kind.items():
    if not k:
        continue
    m = used[n]
    if k[0] == "extent" and n in ext_box:
        axes, ppm, cap = EXTENT[n]
        a0, b0, a1, b1 = ext_box[n]
        w, h = (a1 - a0) * ppm, (b1 - b0) * ppm
        f = min(1.0, cap / max(w, h))
        img = bake(m, axes[0], axes[1], a0, b0, a1, b1, max(8, int(w * f)), max(8, int(h * f)))
        spec[n] = ("extent", (axes, a0, b0, a1, b1), img)
    elif k[0] == "period":
        img = bake(m, "x", "y", 0, 0, k[1], k[1], 512, 512)
        spec[n] = ("period", k[1], img)
    elif k[0] == "image":
        spec[n] = ("image", k[1], k[2])
    print("BAKED", n, k[0])

# ------------------------------------------------------------------ materiais web
def web_material(m, img, alpha=False):
    b = bsdf_of(m)
    nm = bpy.data.materials.new(m.name + " web")
    nm.use_nodes = True
    nb = nm.node_tree.nodes["Principled BSDF"]
    t = nm.node_tree.nodes.new("ShaderNodeTexImage")
    t.image = img
    nm.node_tree.links.new(t.outputs["Color"], nb.inputs["Base Color"])
    if alpha:
        nm.node_tree.links.new(t.outputs["Alpha"], nb.inputs["Alpha"])
        nm.blend_method = "BLEND"
    if b:
        nb.inputs["Roughness"].default_value = b.inputs["Roughness"].default_value
        nb.inputs["Metallic"].default_value = b.inputs["Metallic"].default_value
    return nm


webmats = {n: web_material(used[n], s[2], alpha=s[0] == "image") for n, s in spec.items()}

# demais materiais: cor sólida (mantém imagem só quando já vem por UV: quadros e objetos importados)
for m in used.values():
    b = bsdf_of(m)
    if not b:
        continue
    k = kind.get(m.name)
    for inp in ("Normal", "Roughness", "Metallic"):
        for l in list(b.inputs[inp].links):
            m.node_tree.links.remove(l)
    if k and k[0] == "uv":
        for n in m.node_tree.nodes:
            if n.type == "TEX_IMAGE" and n.image and max(n.image.size) > 1024:
                n.image.scale(*(int(s * 1024 / max(n.image.size)) for s in n.image.size))
        continue
    for l in list(b.inputs["Base Color"].links):
        m.node_tree.links.remove(l)
    if "flat_color" in m:
        b.inputs["Base Color"].default_value = tuple(m["flat_color"])

# ------------------------------------------------------------------ catálogo: medidas antes de dizimar
def item_objects(pattern, pick):
    obs = [o for o in bpy.data.objects if o.type == "MESH" and re.search(pattern, o.name)]
    if pick and obs:
        cx = [sum((o.matrix_world @ Vector(c)).x for c in o.bound_box) / 8 for o in obs]
        mid = (min(cx) + max(cx)) / 2
        obs = [o for o, x in zip(obs, cx) if (x < mid) == (pick == "west")]
    return obs


def bbox(obs):
    pts = [o.matrix_world @ Vector(c) for o in obs for c in o.bound_box]
    return [min(q[i] for q in pts) for i in range(3)], [max(q[i] for q in pts) for i in range(3)]


catalog = []
if CATALOG:
    for (iid, name, room, typ, pat, face, pick, note) in catalog_items.ITEMS:
        obs = item_objects(pat, pick)
        if not obs:
            print("SEM OBJETOS", iid)
            continue
        mn, mx = bbox(obs)
        dx, dy, dz = (mx[i] - mn[i] for i in range(3))
        # largura = ao longo da parede onde a peça encosta; profundidade = perpendicular
        L, P = (dx, dy) if face in ("n", "s") else (dy, dx)
        catalog.append(dict(id=iid, name=name, room=room, type=typ, note=note, face=face,
                            w=round(L, 3), d=round(P, 3), h=round(dz, 3), z0=round(max(mn[2], 0), 3),
                            objs=[o.name for o in obs]))

# ------------------------------------------------------------------ dizimação e UVs
for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    f = len(o.data.polygons)
    if f > 400 and not any(s.material and s.material.name in EXTENT for s in o.material_slots):
        md = o.modifiers.new("d", "DECIMATE")
        md.ratio = max(0.08, 400 / f) if f > 3000 else 0.5
        with bpy.context.temp_override(object=o, active_object=o):
            bpy.ops.object.modifier_apply(modifier="d")

for o in bpy.data.objects:
    if o.type != "MESH" or not o.material_slots:
        continue
    names = [s.material.name if s.material else None for s in o.material_slots]
    if not any(n in spec for n in names):
        continue
    me = o.data
    if me.users > 1:
        o.data = me = me.copy()
    for l in list(me.uv_layers):
        me.uv_layers.remove(l)
    me.uv_layers.new(name="web")
    uv = me.uv_layers["web"]
    mw, nm3 = o.matrix_world, o.matrix_world.to_3x3()
    for poly in me.polygons:
        s = spec.get(names[poly.material_index])
        if not s:
            continue
        n = nm3 @ poly.normal
        for li in poly.loop_indices:
            co = mw @ me.vertices[me.loops[li].vertex_index].co
            if s[0] == "extent":
                axes, a0, b0, a1, b1 = s[1]
                a, b = co[AX[axes[0]]], co[AX[axes[1]]]
                uv.data[li].uv = ((a - a0) / (a1 - a0), (b - b0) / (b1 - b0))
            else:
                P = s[1]
                ax = max(range(3), key=lambda i: abs(n[i]))
                u, v = {2: (co.x, co.y), 0: (co.y, co.z), 1: (co.x, co.z)}[ax]
                uv.data[li].uv = (u / P, v / P)
    for i, nme in enumerate(names):
        if nme in webmats:
            o.material_slots[i].material = webmats[nme]


def export(path, selection=False):
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", export_image_format="JPEG",
                              export_jpeg_quality=82, export_apply=True, export_normals=True,
                              use_selection=selection, export_texcoords=True)


out = os.path.join(ROOT, "modelo2", PAL, f"ares_ipiranga_final01_{PAL}_web.glb")
export(out)
print("LIGHT", PAL, os.path.getsize(out))

if CATALOG:
    idir = os.path.join(ROOT, "web_items")
    os.makedirs(idir, exist_ok=True)
    for it in catalog:
        for o in bpy.context.view_layer.objects:
            o.select_set(o.name in it["objs"])
        export(os.path.join(idir, f"{it['id']}.glb"), selection=True)
        del it["objs"]
    json.dump(catalog, open(os.path.join(ROOT, "catalog.json"), "w"), ensure_ascii=False, indent=1)
    print("CATALOG", len(catalog))
