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
def opt(name, default=None):
    return p[p.index(name) + 1] if name in p else default


PAL = p[0]
CATALOG = "--catalog" in p
BLEND = opt("--blend", os.path.join(ROOT, "modelo2", PAL, f"ares_ipiranga_final01_{PAL}.blend"))
OUT = opt("--out", os.path.join(ROOT, "modelo2", PAL, f"ares_ipiranga_final01_{PAL}_web.glb"))
PART = opt("--part", "all")          # all | base (sem o jantar) | dining (só o jantar)
VARIANT = opt("--variant")           # opção de jantar do .blend, para o catálogo
CAT_OUT = opt("--catalog-out", os.path.join(ROOT, "catalog.json"))
LIGHTMAP = "--lightmap" in p          # pré-calcula a luz (Cycles) num atlas que vai como occlusionTexture
LM_SIZE = int(opt("--lm-size", "2048"))
LM_SAMPLES = int(opt("--lm-samples", "256"))
LM_DEVICE = opt("--lm-device", "GPU")
LM_FROM = opt("--lm-from")             # reaproveita a luz já calculada (.npy) de outra paleta: mesma geometria, mesmos UVs
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

bpy.ops.wm.open_mainfile(filepath=BLEND)
sc = bpy.context.scene
for n in ["Ceu_externo", "Exterior"]:
    o = bpy.data.objects.get(n)
    if o:
        bpy.data.objects.remove(o)
for o in list(bpy.data.objects):
    # com lightmap as luzes ficam até o bake
    if o.type == "CAMERA" or (o.type == "LIGHT" and not LIGHTMAP):
        bpy.data.objects.remove(o)


def is_dining(o):
    return "dining" in o or (o.parent is not None and "dining" in o.parent)


# o jantar da sala sai em arquivo próprio para o visualizador trocar as opções; no bake do jantar
# o resto do apartamento fica na cena até o fim, para iluminar e sombrear as peças
for o in list(bpy.data.objects):
    d = is_dining(o)
    if (PART == "base" and d) or (PART == "dining" and not LIGHTMAP and not d and o.type in ("MESH", "EMPTY")):
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
    for (iid, name, room, typ, pat, face, pick, note, *extra) in catalog_items.ITEMS:
        src, opts = (extra + [None, None])[:2]
        if src != VARIANT:
            continue
        obs = item_objects(pat, pick)
        if not obs:
            print("SEM OBJETOS", iid)
            continue
        mn, mx = bbox(obs)
        dx, dy, dz = (mx[i] - mn[i] for i in range(3))
        # largura = ao longo da parede onde a peça encosta; profundidade = perpendicular
        L, P = (dx, dy) if face in ("n", "s") else (dy, dx)
        catalog.append(dict(id=iid, name=name, room=room, type=typ, note=note, face=face, opts=opts or "",
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


# ------------------------------------------------------------------ lightmap
def bake_lightmap():
    import numpy as np
    from PIL import Image, ImageFilter
    targets = [o for o in bpy.data.objects if o.type == "MESH" and o.data.polygons
               and (PART != "dining" or is_dining(o))]
    for o in targets:
        if o.data.users > 1:
            o.data = o.data.copy()
        me = o.data
        # malhas fechadas com faces para dentro (almofadas, frutas) assariam preto
        bm = bmesh.new()
        bm.from_mesh(me)
        if bm.edges and all(e.is_manifold for e in bm.edges):
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            bm.to_mesh(me)
        bm.free()
        # TEXCOORD_0 = textura (vazio quando o material é cor sólida), TEXCOORD_1 = lightmap
        if not me.uv_layers:
            me.uv_layers.new(name="web")
        while len(me.uv_layers) > 1:
            me.uv_layers.remove(me.uv_layers[-1])
        lm = me.uv_layers.new(name="lm")
        me.uv_layers.active = lm
    for o in bpy.context.view_layer.objects:
        o.select_set(o in targets)
    bpy.context.view_layer.objects.active = targets[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.002, correct_aspect=True,
                             scale_to_bounds=False)
    bpy.ops.uv.pack_islands(margin=0.003, rotate=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    # impressão digital do layout UV: tem de bater entre paletas para reaproveitar a luz
    import hashlib
    hsh = hashlib.md5()
    for o in sorted(targets, key=lambda o: o.name):
        uv = o.data.uv_layers["lm"].data
        arr = [0.0] * (len(uv) * 2)
        uv.foreach_get("uv", arr)
        hsh.update(o.name.encode()); hsh.update(bytes(str([round(x, 4) for x in arr[:64]]), "ascii"))
    print("UVHASH", hsh.hexdigest())

    import numpy as np
    stem = f"lightmap_{PART}_{os.path.splitext(os.path.basename(OUT))[0]}"
    if LM_FROM:
        return tone_lightmap(np.load(LM_FROM).astype(np.float32), stem)
    img = bpy.data.images.new("lightmap", LM_SIZE, LM_SIZE, float_buffer=True)
    added = []
    for m in {s.material for o in targets for s in o.material_slots if s.material}:
        n = m.node_tree.nodes.new("ShaderNodeTexImage")
        n.image = img
        m.node_tree.nodes.active = n
        added.append((m, n))
    sc.render.engine = "CYCLES"
    if LM_DEVICE == "GPU":
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
    sc.cycles.device = LM_DEVICE
    sc.cycles.samples = LM_SAMPLES
    sc.cycles.use_denoising = False
    sc.render.bake.use_pass_direct = True
    sc.render.bake.use_pass_indirect = True
    sc.render.bake.use_pass_color = False
    sc.render.bake.margin = 6
    for o in bpy.context.view_layer.objects:
        o.select_set(o in targets)
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, margin=6, use_clear=True)
    for m, n in added:
        m.node_tree.nodes.remove(n)

    a = np.array(img.pixels[:], dtype=np.float32).reshape(LM_SIZE, LM_SIZE, 4)[::-1, :, :3]
    lum = a @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    np.save(os.path.join(BAKE_DIR, stem + ".npy"), lum.astype(np.float16))
    return tone_lightmap(lum, stem)


def tone_lightmap(lum, stem):
    """Luz (irradiância) -> luminância normalizada em 8 bits; o visualizador multiplica pela luz ambiente."""
    import numpy as np
    from PIL import Image, ImageFilter
    used = lum[lum > 1e-4]
    ref = float(np.percentile(used, 98)) if used.size else 1.0
    v = np.clip(lum / ref, 0, 1) ** (1 / 1.6)       # curva suave: mais níveis nas sombras
    im = Image.fromarray((v * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(1.0))
    path = os.path.join(BAKE_DIR, stem + ".jpg")
    im.convert("RGB").save(path, quality=88)
    print("LIGHTMAP", path, "ref", round(ref, 3))
    return path, ref


def add_occlusion(glb, jpg):
    """Embute o atlas como occlusionTexture (texCoord 1) em todos os materiais do GLB."""
    import struct
    b = open(glb, "rb").read()
    off, js, bn = 12, None, b""
    while off < len(b):
        ln, typ = struct.unpack("<I4s", b[off:off + 8])
        if typ == b"JSON":
            js = json.loads(b[off + 8:off + 8 + ln])
        elif typ == b"BIN\x00":
            bn = b[off + 8:off + 8 + ln]
        off += 8 + ln
    data = open(jpg, "rb").read()
    pad = (4 - len(bn) % 4) % 4
    bn = bn + b"\x00" * pad
    js.setdefault("bufferViews", []).append({"buffer": 0, "byteOffset": len(bn), "byteLength": len(data)})
    bn = bn + data
    bn += b"\x00" * ((4 - len(bn) % 4) % 4)
    js["buffers"][0]["byteLength"] = len(bn)
    js.setdefault("images", []).append({"bufferView": len(js["bufferViews"]) - 1, "mimeType": "image/jpeg", "name": "lightmap"})
    js.setdefault("samplers", []).append({"magFilter": 9729, "minFilter": 9987, "wrapS": 33071, "wrapT": 33071})
    js.setdefault("textures", []).append({"source": len(js["images"]) - 1, "sampler": len(js["samplers"]) - 1})
    t = len(js["textures"]) - 1
    has_uv1 = set()
    for mesh in js.get("meshes", []):
        for prim in mesh["primitives"]:
            if "TEXCOORD_1" in prim["attributes"] and "material" in prim:
                has_uv1.add(prim["material"])
    for i, m in enumerate(js.get("materials", [])):
        if i in has_uv1:
            m["occlusionTexture"] = {"index": t, "texCoord": 1}
    jb = json.dumps(js, separators=(",", ":")).encode()
    jb += b" " * ((4 - len(jb) % 4) % 4)
    out = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(jb) + 8 + len(bn))
    out += struct.pack("<I4s", len(jb), b"JSON") + jb + struct.pack("<I4s", len(bn), b"BIN\x00") + bn
    open(glb, "wb").write(out)
    print("OCCLUSION", len(has_uv1), "materiais")


lm_path = None
if LIGHTMAP:
    lm_path, lm_ref = bake_lightmap()
    for o in list(bpy.data.objects):
        if o.type == "LIGHT" or (PART == "dining" and o.type in ("MESH", "EMPTY") and not is_dining(o)):
            bpy.data.objects.remove(o)


def export(path, selection=False):
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", export_image_format="JPEG",
                              export_jpeg_quality=82, export_apply=True, export_normals=True,
                              use_selection=selection, export_texcoords=True)


out = OUT
os.makedirs(os.path.dirname(out), exist_ok=True)
export(out)
if lm_path:
    add_occlusion(out, lm_path)
print("LIGHT", PAL, os.path.getsize(out))

if CATALOG:
    idir = os.path.join(ROOT, "web_items")
    os.makedirs(idir, exist_ok=True)
    for it in catalog:
        for o in bpy.context.view_layer.objects:
            o.select_set(o.name in it["objs"])
        export(os.path.join(idir, f"{it['id']}.glb"), selection=True)
        del it["objs"]
    json.dump(catalog, open(CAT_OUT, "w"), ensure_ascii=False, indent=1)
    print("CATALOG", len(catalog))
