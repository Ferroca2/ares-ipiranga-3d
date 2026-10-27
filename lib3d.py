"""Biblioteca de modelagem para o projeto v2: materiais PBR, primitivas detalhadas, assets e câmera.

Coordenadas de planta: x para a direita, y para BAIXO, metros. No Blender: X = x, Y = -y.
"""
import math
import os
import random

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.abspath(__file__))
PH = os.path.join(ROOT, "assets", "ph")

MATS = {}
COLL = {}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    MATS.clear()
    COLL.clear()


def srgb2lin(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def rgba(h, a=1.0):
    return (*srgb2lin(h), a)


# ------------------------------------------------------------------ coleções
def collection(name):
    if name not in COLL:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
        COLL[name] = c
    return COLL[name]


def link(ob, coll):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    collection(coll).objects.link(ob)
    return ob


# ------------------------------------------------------------------ materiais
def _bsdf(m):
    m.use_nodes = True
    return m.node_tree.nodes["Principled BSDF"]


def solid(name, color, rough=0.5, metal=0.0, coat=0.0, sheen=0.0, transmission=0.0, ior=1.45,
          emission=None, strength=0.0, alpha=1.0):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    b = _bsdf(m)
    c = rgba(color) if isinstance(color, str) else color
    b.inputs["Base Color"].default_value = c
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Sheen Weight"].default_value = sheen
    b.inputs["Transmission Weight"].default_value = transmission
    b.inputs["IOR"].default_value = ior
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
    if emission:
        b.inputs["Emission Color"].default_value = rgba(emission)
        b.inputs["Emission Strength"].default_value = strength
    m.diffuse_color = c
    m["flat_color"] = list(c)
    MATS[name] = m
    return m


def _tex(nt, path, vec, noncolor=False, proj="BOX"):
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(path, check_existing=True)
    if noncolor:
        t.image.colorspace_settings.name = "Non-Color"
    t.projection = proj
    t.projection_blend = 0.25
    nt.links.new(vec, t.inputs["Vector"])
    return t


def pbr(name, tex, scale=1.0, tint=None, tint_mode="multiply", rough_add=0.0, normal=0.6, sheen=0.0,
        coat=0.0, rotate=0.0, desat=False, bright=1.0, flat=None, rng=(0.86, 1.06)):
    """Material com texturas Poly Haven projetadas em caixa (coordenadas do objeto, em metros).

    tint: cor hex; 'multiply' preserva o desenho da textura, 'replace' usa só a luminância.
    """
    if name in MATS:
        return MATS[name]
    d = os.path.join(PH, "textures", tex)
    m = bpy.data.materials.new(name)
    b = _bsdf(m)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    mp.inputs["Rotation"].default_value = (0, 0, math.radians(rotate))
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    vec = mp.outputs["Vector"]
    col = None
    if os.path.exists(os.path.join(d, "diff.jpg")):
        col = _tex(nt, os.path.join(d, "diff.jpg"), vec).outputs["Color"]
    if col is not None and tint_mode == "replace":
        # só a variação da textura sobrevive (0,86–1,06), multiplicada depois pela cor alvo
        bw = nt.nodes.new("ShaderNodeRGBToBW")
        nt.links.new(col, bw.inputs["Color"])
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = 0.15
        mr.inputs["From Max"].default_value = 0.85
        mr.inputs["To Min"].default_value = rng[0]
        mr.inputs["To Max"].default_value = rng[1]
        nt.links.new(bw.outputs["Val"], mr.inputs["Value"])
        cc = nt.nodes.new("ShaderNodeCombineColor")
        for i in range(3):
            nt.links.new(mr.outputs["Result"], cc.inputs[i])
        col = cc.outputs["Color"]
    elif col is not None and desat:
        hs = nt.nodes.new("ShaderNodeHueSaturation")
        hs.inputs["Saturation"].default_value = 0.0
        hs.inputs["Value"].default_value = bright
        nt.links.new(col, hs.inputs["Color"])
        col = hs.outputs["Color"]
    if tint:
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        if col is None:
            mix.inputs["A"].default_value = (1, 1, 1, 1)
        else:
            nt.links.new(col, mix.inputs["A"])
        mix.inputs["B"].default_value = rgba(tint)
        col = mix.outputs["Result"]
    if col is not None:
        nt.links.new(col, b.inputs["Base Color"])
    if os.path.exists(os.path.join(d, "rough.jpg")):
        r = _tex(nt, os.path.join(d, "rough.jpg"), vec, True).outputs["Color"]
        if rough_add:
            mth = nt.nodes.new("ShaderNodeMath")
            mth.operation = "ADD"
            mth.use_clamp = True
            mth.inputs[1].default_value = rough_add
            nt.links.new(r, mth.inputs[0])
            r = mth.outputs["Value"]
        nt.links.new(r, b.inputs["Roughness"])
    if os.path.exists(os.path.join(d, "nor.jpg")) and normal > 0:
        n = _tex(nt, os.path.join(d, "nor.jpg"), vec, True)
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = normal
        nt.links.new(n.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Sheen Weight"].default_value = sheen
    b.inputs["Coat Weight"].default_value = coat
    fc = rgba(flat or tint or "#B0A898")
    m.diffuse_color = fc
    m["flat_color"] = list(fc)
    MATS[name] = m
    return m


def fabric(name, color, tex="rough_linen", scale=3.0, sheen=0.12):
    return pbr(name, tex, scale=scale, tint=color, tint_mode="replace", sheen=sheen, normal=0.5, flat=color)


# ------------------------------------------------------------------ geometria
def _box_verts(x0, x1, y0, y1, z0, z1):
    X0, X1 = min(x0, x1), max(x0, x1)
    Y0, Y1 = -max(y0, y1), -min(y0, y1)
    return [(X0, Y0, z0), (X1, Y0, z0), (X1, Y1, z0), (X0, Y1, z0),
            (X0, Y0, z1), (X1, Y0, z1), (X1, Y1, z1), (X0, Y1, z1)]


_BOX_F = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]


def mesh_obj(name, verts, faces, material, coll):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    if material is not None:
        ob.data.materials.append(material)
    collection(coll).objects.link(ob)
    return ob


def box(name, x0, x1, y0, y1, z0, z1, material, coll="Moveis", bevel=0.003, segs=2, subsurf=0, smooth=False):
    ob = mesh_obj(name, _box_verts(x0, x1, y0, y1, z0, z1), _BOX_F, material, coll)
    dims = sorted([abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)])
    if bevel > 0 and dims[0] > 0.002:
        md = ob.modifiers.new("Bevel", "BEVEL")
        md.width = min(bevel, dims[0] / 2.05)
        md.segments = segs
        md.limit_method = "NONE"
        md.harden_normals = False
        smooth = True
    if subsurf:
        md = ob.modifiers.new("Subsurf", "SUBSURF")
        md.levels = md.render_levels = subsurf
        smooth = True
    if smooth:
        for p in ob.data.polygons:
            p.use_smooth = True
    return ob


def multi_box(name, boxes, material, coll="Moveis", bevel=0.0):
    """Várias caixas num só objeto (ripados, prateleiras, livros)."""
    v, f = [], []
    for bx in boxes:
        o = len(v)
        v += _box_verts(*bx)
        f += [tuple(i + o for i in face) for face in _BOX_F]
    ob = mesh_obj(name, v, f, material, coll)
    if bevel:
        md = ob.modifiers.new("Bevel", "BEVEL")
        md.width = bevel
        md.segments = 1
        md.limit_method = "NONE"
    return ob


def cyl(name, cx, cy, z0, z1, r, material, coll="Moveis", verts=64, bevel=0.0, r2=None):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=z1 - z0, location=(cx, -cy, (z0 + z1) / 2))
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=z1 - z0, location=(cx, -cy, (z0 + z1) / 2))
    ob = bpy.context.active_object
    ob.name = name
    ob.data.materials.append(material)
    if bevel:
        md = ob.modifiers.new("Bevel", "BEVEL")
        md.width = bevel
        md.segments = 3
        md.limit_method = "ANGLE"
    for p in ob.data.polygons:
        p.use_smooth = True
    return link(ob, coll)


def sphere(name, cx, cy, cz, r, material, coll="Moveis", scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=r, location=(cx, -cy, cz))
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = scale
    ob.data.materials.append(material)
    for p in ob.data.polygons:
        p.use_smooth = True
    return link(ob, coll)


def torus(name, cx, cy, cz, R, r, material, coll="Moveis", rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=(cx, -cy, cz), rotation=rot,
                                     major_segments=64, minor_segments=12)
    ob = bpy.context.active_object
    ob.name = name
    ob.data.materials.append(material)
    for p in ob.data.polygons:
        p.use_smooth = True
    return link(ob, coll)


def soft(name, x0, x1, y0, y1, z0, z1, material, coll="Moveis", round_=0.04, wrinkle=0.0, levels=2):
    """Estofado/almofada: caixa com bevel largo + subdivisão; wrinkle adiciona deformação de tecido."""
    ob = box(name, x0, x1, y0, y1, z0, z1, material, coll, bevel=round_, segs=3, subsurf=levels)
    if wrinkle:
        tx = bpy.data.textures.new(name + "_rug", "CLOUDS")
        tx.noise_scale = 0.12
        md = ob.modifiers.new("Wrinkle", "DISPLACE")
        md.texture = tx
        md.texture_coords = "GLOBAL"
        md.strength = wrinkle
        md.mid_level = 0.5
    return ob


def pillow(name, cx, cy, cz, w, h, d, material, coll="Moveis", tilt=0.0, yaw=0.0, n=24):
    """Almofada estufada paramétrica: bordas finas costuradas, centro cheio, leve assimetria."""
    v, f = [], []
    for side in (1, -1):
        for j in range(n + 1):
            for i in range(n + 1):
                u, t = i / n * 2 - 1, j / n * 2 - 1
                puff = (1 - abs(u) ** 3.5) * (1 - abs(t) ** 3.5)
                x = u * w / 2 * (1 - 0.06 * (1 - t * t))      # cintura nas laterais
                z = t * h / 2 * (1 - 0.06 * (1 - u * u))
                y = side * (0.006 + d / 2 * puff ** 0.6)
                v.append((x, y, z))
    rows = n + 1
    for s_ in range(2):
        o = s_ * rows * rows
        for j in range(n):
            for i in range(n):
                a = o + j * rows + i
                q = (a, a + 1, a + rows + 1, a + rows)
                f.append(q if s_ == 0 else q[::-1])
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], f)
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob.data.materials.append(material)
    ob.location = (cx, -cy, cz)
    ob.rotation_euler = (math.radians(tilt), 0, math.radians(yaw))
    md = ob.modifiers.new("Weld", "WELD")
    md.merge_threshold = 0.013
    md = ob.modifiers.new("Subsurf", "SUBSURF")
    md.levels = md.render_levels = 1
    for p in ob.data.polygons:
        p.use_smooth = True
    collection(coll).objects.link(ob)
    return ob


def curtain(name, x, y0, y1, z0, z1, material, coll="Esquadrias", amp=0.035, period=0.14, along="y"):
    """Cortina com pregas (onda senoidal) ao longo da parede."""
    n = max(8, int(abs(y1 - y0) / period * 10))
    rows = 12
    v, f = [], []
    for j in range(rows + 1):
        z = z0 + (z1 - z0) * j / rows
        for i in range(n + 1):
            t = y0 + (y1 - y0) * i / n
            off = amp * math.sin(2 * math.pi * (t - y0) / period)
            if along == "y":
                v.append((x + off, -t, z))
            else:
                v.append((t, -(x + off), z))
    for j in range(rows):
        for i in range(n):
            a = j * (n + 1) + i
            f.append((a, a + 1, a + n + 2, a + n + 1))
    ob = mesh_obj(name, v, f, material, coll)
    md = ob.modifiers.new("Solid", "SOLIDIFY")
    md.thickness = 0.006
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def plate(name, x, y, z, normal, material, w=0.08, h=0.12, coll="Esquadrias", kind="switch"):
    """Espelho de tomada/interruptor na parede. normal: '+x','-x','+y','-y' (planta)."""
    t = 0.008
    if normal in ("+x", "-x"):
        sgn = 1 if normal == "+x" else -1
        box(name, x, x + sgn * t, y - w / 2, y + w / 2, z - h / 2, z + h / 2, material, coll, bevel=0.002)
    else:
        sgn = 1 if normal == "+y" else -1
        box(name, x - w / 2, x + w / 2, y, y + sgn * t, z - h / 2, z + h / 2, material, coll, bevel=0.002)


def books(name, x0, y0, z0, length, depth, rng, palette, along="x", hmin=0.18, hmax=0.26, lean_end=True):
    """Fileira de livros com alturas e cores variadas; retorna largura ocupada."""
    groups = {}
    pos = 0.0
    while pos < length - 0.02:
        w = rng.uniform(0.015, 0.045)
        h = rng.uniform(hmin, hmax)
        d = depth * rng.uniform(0.75, 1.0)
        c = rng.choice(palette)
        if along == "x":
            bx = (x0 + pos, x0 + pos + w, y0, y0 + d, z0, z0 + h)
        else:
            bx = (x0, x0 + d, y0 + pos, y0 + pos + w, z0, z0 + h)
        groups.setdefault(c, []).append(bx)
        pos += w + 0.002
    for c, bxs in groups.items():
        multi_box(f"{name}_{c[1:]}", bxs, solid(f"Livro {c}", c, 0.55), bevel=0.002)
    return pos


# ------------------------------------------------------------------ assets
def asset(aid, x, y, z=0.0, yaw=0.0, height=None, width=None, coll="Decor"):
    """Importa um modelo glTF da Poly Haven, junta as malhas e posiciona pela base."""
    d = os.path.join(PH, "models", aid)
    path = next(os.path.join(d, f) for f in os.listdir(d) if f.endswith(".gltf"))
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    # aplica transformações da hierarquia e junta
    for o in meshes:
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
    for o in new:
        if o.type != "MESH":
            bpy.data.objects.remove(o)
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = aid
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bb = [Vector(c) for c in ob.bound_box]
    mn = Vector((min(c.x for c in bb), min(c.y for c in bb), min(c.z for c in bb)))
    mx = Vector((max(c.x for c in bb), max(c.y for c in bb), max(c.z for c in bb)))
    s = 1.0
    if height:
        s = height / (mx.z - mn.z)
    elif width:
        s = width / max(mx.x - mn.x, mx.y - mn.y)
    # origem na base, centro
    ctr = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    ob.data.transform(__import__("mathutils").Matrix.Translation(-ctr))
    ob.scale = (s, s, s)
    ob.rotation_euler = (0, 0, math.radians(yaw))
    ob.location = (x, -y, z)
    return link(ob, coll)


# ------------------------------------------------------------------ luz / câmera / render
def world_hdri(strength=1.0, rot=0.0):
    w = bpy.data.worlds.new("Mundo")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(os.path.join(PH, "hdri", "kloofendal_48d_partly_cloudy_puresky.hdr"))
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0, 0, math.radians(rot))
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength
    return w


def area_light(name, x, y, z, sx, sy, power, color=(1.0, 0.88, 0.74), rot=(0, 0, 0), portal=False, coll="Luzes"):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = power
    ld.shape = "RECTANGLE"
    ld.size, ld.size_y = sx, sy
    ld.color = color
    if portal:
        ld.cycles.is_portal = True
    lo = bpy.data.objects.new(name, ld)
    lo.visible_camera = False
    lo.location = (x, -y, z)
    lo.rotation_euler = rot
    collection(coll).objects.link(lo)
    return lo


def point_light(name, x, y, z, power, radius=0.03, color=(1.0, 0.82, 0.62), coll="Luzes"):
    ld = bpy.data.lights.new(name, "POINT")
    ld.energy = power
    ld.shadow_soft_size = radius
    ld.color = color
    lo = bpy.data.objects.new(name, ld)
    lo.location = (x, -y, z)
    collection(coll).objects.link(lo)
    return lo


def sun(energy=3.5, elev=28, azim=-75, color=(1.0, 0.93, 0.84)):
    ld = bpy.data.lights.new("Sol", "SUN")
    ld.energy = energy
    ld.angle = math.radians(1.5)
    ld.color = color
    s = bpy.data.objects.new("Sol", ld)
    s.rotation_euler = (math.radians(90 - elev), 0, math.radians(azim))
    collection("Luzes").objects.link(s)
    return s


def photo_camera(pos, target, lens=20.0, shift_auto=True):
    """Perspectiva de dois pontos: câmera nivelada (verticais retas) e shift vertical para enquadrar."""
    cd = bpy.data.cameras.new("Cam")
    cd.lens = lens
    cd.sensor_width = 36
    cd.clip_start = 0.05
    cam = bpy.data.objects.new("Cam", cd)
    bpy.context.scene.collection.objects.link(cam)
    px, py, pz = pos
    tx, ty, tz = target
    dx, dy = tx - px, -(ty - py)
    yaw = math.atan2(dy, dx) - math.pi / 2
    cam.location = (px, -py, pz)
    cam.rotation_euler = (math.radians(90), 0, yaw)
    if shift_auto:
        dist = math.hypot(dx, dy)
        # shift = deslocamento vertical do alvo no plano do sensor / largura do sensor
        cd.shift_y = max(-0.3, min(0.3, (tz - pz) / dist * lens / 36))
    bpy.context.scene.camera = cam
    return cam


def render_settings(res=(1920, 1280), samples=256, exposure=0.0):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    try:
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        sc.cycles.device = "GPU"
    except Exception:
        sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.015
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.max_bounces = 12
    sc.cycles.diffuse_bounces = 6
    sc.cycles.glossy_bounces = 6
    sc.cycles.transmission_bounces = 8
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.blur_glossy = 1.0
    sc.cycles.light_sampling_threshold = 0.01
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.view_settings.exposure = exposure
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 92


def cushion(name, x0, x1, y0, y1, z0, z1, material, coll="Moveis", puff=0.35):
    """Almofada/assento estofado: bordas arredondadas e centro levemente estufado."""
    t = min(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))
    ob = box(name, x0, x1, y0, y1, z0, z1, material, coll, bevel=t * puff, segs=4, subsurf=2)
    return ob


def surface(name, tex, color, scale=1.0, rng=(0.86, 1.06), grid=None, axes="xy", rough=None,
            rough_add=0.0, normal=0.5, coat=0.0, sheen=0.0, metal=0.0, flat=None, rot=0.0):
    """Material de superfície: a textura vira só variação de luminância (rng) multiplicada pela cor.

    grid = (largura, altura, deslocamento, rejunte_m, cor_rejunte) desenha paginação (réguas, porcelanato,
    azulejo); axes escolhe o plano da paginação ('xy' piso, 'xz' parede ao longo de x, 'yz' parede ao longo de y).
    """
    if name in MATS:
        return MATS[name]
    d = os.path.join(PH, "textures", tex) if tex else None
    m = bpy.data.materials.new(name)
    b = _bsdf(m)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    a, bb = {"xy": ("X", "Y"), "xz": ("X", "Z"), "yz": ("Y", "Z")}[axes]
    nt.links.new(sep.outputs[a], comb.inputs["X"])
    nt.links.new(sep.outputs[bb], comb.inputs["Y"])
    other = ({"X", "Y", "Z"} - {a, bb}).pop()
    nt.links.new(sep.outputs[other], comb.inputs["Z"])
    planar = comb.outputs["Vector"]
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    mp.inputs["Rotation"].default_value = (0, 0, math.radians(rot))
    nt.links.new(planar, mp.inputs["Vector"])
    vec = mp.outputs["Vector"]
    base = rgba(color)
    col = None
    if d and os.path.exists(os.path.join(d, "diff.jpg")):
        t = _tex(nt, os.path.join(d, "diff.jpg"), vec, proj="FLAT")
        bw = nt.nodes.new("ShaderNodeRGBToBW")
        nt.links.new(t.outputs["Color"], bw.inputs["Color"])
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = 0.15
        mr.inputs["From Max"].default_value = 0.85
        mr.inputs["To Min"].default_value = rng[0]
        mr.inputs["To Max"].default_value = rng[1]
        nt.links.new(bw.outputs["Val"], mr.inputs["Value"])
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        cc = nt.nodes.new("ShaderNodeCombineColor")
        for i in range(3):
            nt.links.new(mr.outputs["Result"], cc.inputs[i])
        nt.links.new(cc.outputs["Color"], mix.inputs["A"])
        mix.inputs["B"].default_value = base
        col = mix.outputs["Result"]
    else:
        col = None
    if grid:
        gw, gh, off, mortar, gcol = grid
        br = nt.nodes.new("ShaderNodeTexBrick")
        br.offset = off
        br.offset_frequency = 2
        br.squash = 1.0
        br.inputs["Scale"].default_value = 1.0
        br.inputs["Brick Width"].default_value = gw
        br.inputs["Row Height"].default_value = gh
        br.inputs["Mortar Size"].default_value = mortar
        br.inputs["Mortar Smooth"].default_value = 0.3
        br.inputs["Color1"].default_value = (1, 1, 1, 1)
        br.inputs["Color2"].default_value = (0.94, 0.94, 0.94, 1)
        br.inputs["Mortar"].default_value = (0, 0, 0, 1)
        br.inputs["Bias"].default_value = 0.0
        nt.links.new(planar, br.inputs["Vector"])
        # variação leve por peça
        m2 = nt.nodes.new("ShaderNodeMix")
        m2.data_type = "RGBA"
        m2.blend_type = "MULTIPLY"
        m2.inputs["Factor"].default_value = 0.5
        if col is None:
            m2.inputs["A"].default_value = base
        else:
            nt.links.new(col, m2.inputs["A"])
        nt.links.new(br.outputs["Color"], m2.inputs["B"])
        m3 = nt.nodes.new("ShaderNodeMix")
        m3.data_type = "RGBA"
        nt.links.new(br.outputs["Fac"], m3.inputs["Factor"])
        nt.links.new(m2.outputs["Result"], m3.inputs["A"])
        m3.inputs["B"].default_value = rgba(gcol)
        col = m3.outputs["Result"]
        # rejunte levemente afundado
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.4
        bump.inputs["Distance"].default_value = 0.002
        bump.invert = True
        nt.links.new(br.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    if col is None:
        b.inputs["Base Color"].default_value = base
    else:
        nt.links.new(col, b.inputs["Base Color"])
    if rough is not None:
        b.inputs["Roughness"].default_value = rough
    elif d and os.path.exists(os.path.join(d, "rough.jpg")):
        r = _tex(nt, os.path.join(d, "rough.jpg"), vec, True, proj="FLAT").outputs["Color"]
        if rough_add:
            mth = nt.nodes.new("ShaderNodeMath")
            mth.operation = "ADD"
            mth.use_clamp = True
            mth.inputs[1].default_value = rough_add
            nt.links.new(r, mth.inputs[0])
            r = mth.outputs["Value"]
        nt.links.new(r, b.inputs["Roughness"])
    if not grid and d and normal > 0 and os.path.exists(os.path.join(d, "nor.jpg")):
        n = _tex(nt, os.path.join(d, "nor.jpg"), vec, True, proj="FLAT")
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = normal
        nt.links.new(n.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Sheen Weight"].default_value = sheen
    b.inputs["Metallic"].default_value = metal
    fc = rgba(flat or color)
    m.diffuse_color = fc
    m["flat_color"] = list(fc)
    MATS[name] = m
    return m


def image_mat(name, path, rough=0.6, alpha=False, scale=None):
    """Material de imagem (arte, palhinha). Com scale usa coordenadas de objeto em caixa; sem, usa UV."""
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    b = _bsdf(m)
    nt = m.node_tree
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(path, check_existing=True)
    if scale:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (scale, scale, scale)
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
        t.projection = "BOX"
        t.projection_blend = 0.2
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    if alpha:
        nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
        m.blend_method = "HASHED"
    b.inputs["Roughness"].default_value = rough
    px = list(t.image.pixels[:4]) if t.image.size[0] else [0.7, 0.6, 0.5, 1]
    m.diffuse_color = (0.75, 0.66, 0.52, 1) if alpha else (px[0], px[1], px[2], 1)
    m["flat_color"] = list(m.diffuse_color)
    MATS[name] = m
    return m


def picture(name, x, y, z0, w, h, normal, art_mat, frame_mat, coll="Decor", depth=0.03, border=0.02, mat_border=0.05,
            passe=None):
    """Quadro com moldura e passe-partout. (x, y) = centro na face da parede; normal = direção para a sala."""
    zc = z0 + h / 2
    sgn = 1 if normal in ("+x", "+y") else -1
    ax = normal[1]
    # moldura (caixa) + arte (plano com UV) levemente à frente
    if ax == "x":
        box(name + "_moldura", x, x + sgn * depth, y - w / 2, y + w / 2, z0, z0 + h, frame_mat, coll, bevel=0.002)
        if passe is not None:
            box(name + "_passe", x + sgn * (depth + 0.0005), x + sgn * (depth + 0.0015), y - w / 2 + border,
                y + w / 2 - border, z0 + border, z0 + h - border, passe, coll, bevel=0)
        inset = border + (mat_border if passe is not None else 0)
        bpy.ops.mesh.primitive_plane_add(size=1, location=(x + sgn * (depth + 0.002), -y, zc),
                                         rotation=(math.radians(90), 0, math.radians(90 if sgn > 0 else -90)))
        ob = bpy.context.active_object
        ob.scale = (w - 2 * inset, h - 2 * inset, 1)
    else:
        box(name + "_moldura", x - w / 2, x + w / 2, y, y + sgn * depth, z0, z0 + h, frame_mat, coll, bevel=0.002)
        if passe is not None:
            box(name + "_passe", x - w / 2 + border, x + w / 2 - border, y + sgn * (depth + 0.0005),
                y + sgn * (depth + 0.0015), z0 + border, z0 + h - border, passe, coll, bevel=0)
        inset = border + (mat_border if passe is not None else 0)
        bpy.ops.mesh.primitive_plane_add(size=1, location=(x, -(y + sgn * (depth + 0.002)), zc),
                                         rotation=(math.radians(90), 0, 0 if sgn > 0 else math.pi))
        ob = bpy.context.active_object
        ob.scale = (w - 2 * inset, h - 2 * inset, 1)
    ob.name = name + "_arte"
    ob.data.materials.append(art_mat)
    return link(ob, coll)


def sun_dir(direction, energy=4.0, color=(1.0, 0.92, 0.82), angle=1.2):
    ld = bpy.data.lights.new("Sol", "SUN")
    ld.energy = energy
    ld.angle = math.radians(angle)
    ld.color = color
    s = bpy.data.objects.new("Sol", ld)
    s.rotation_euler = Vector(direction).normalized().to_track_quat("-Z", "Y").to_euler()
    collection("Luzes").objects.link(s)
    return s


def spot(name, x, y, z, target, power, size_deg=40, blend=0.6, color=(1.0, 0.80, 0.60), radius=0.02):
    ld = bpy.data.lights.new(name, "SPOT")
    ld.energy = power
    ld.spot_size = math.radians(size_deg)
    ld.spot_blend = blend
    ld.shadow_soft_size = radius
    ld.color = color
    lo = bpy.data.objects.new(name, ld)
    lo.location = (x, -y, z)
    d = Vector((target[0], -target[1], target[2])) - lo.location
    lo.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    collection("Luzes").objects.link(lo)
    return lo


def wall(name, x0, x1, y0, y1, material, openings=(), coll="Paredes", z0=0.0, z1=2.50):
    """Parede retangular com aberturas (ini, fim, peitoril, verga) ao longo do eixo maior."""
    along_x = (x1 - x0) >= (y1 - y0)
    a0, a1 = (x0, x1) if along_x else (y0, y1)

    def piece(i, b0, b1, za, zb):
        if b1 - b0 < 1e-4 or zb - za < 1e-4:
            return
        if along_x:
            box(f"{name}_{i}", b0, b1, y0, y1, za, zb, material, coll, bevel=0)
        else:
            box(f"{name}_{i}", x0, x1, b0, b1, za, zb, material, coll, bevel=0)

    cur, i = a0, 0
    for (s, e, sill, head) in sorted(openings):
        piece(i, cur, s, z0, z1); i += 1
        piece(i, s, e, z0, sill); i += 1
        piece(i, s, e, head, z1); i += 1
        cur = e
    piece(i, cur, a1, z0, z1)
