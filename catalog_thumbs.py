"""Miniaturas de estúdio de cada peça do catálogo (Cycles, fundo transparente, sombra no piso).

uso: python catalog_thumbs.py [paleta] [id ...]
"""
import bpy, sys, os, re, math
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib3d
import catalog_items

ROOT = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:]
PAL = args[0] if args else "terra"
ONLY = set(args[1:])
OUT = os.path.join(ROOT, "catalog_png")
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "modelo2", PAL, f"ares_ipiranga_final01_{PAL}.blend"))
sc = bpy.context.scene
for o in list(bpy.data.objects):
    if o.type in ("LIGHT", "CAMERA") or o.name in ("Exterior", "Ceu_externo"):
        bpy.data.objects.remove(o)
lib3d.render_settings((960, 760), samples=48)
sc.cycles.device = "CPU"
sc.render.film_transparent = True
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGBA"

w = bpy.data.worlds.new("estudio")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (1, 1, 1, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.85
sc.world = w
key = bpy.data.lights.new("key", "SUN")
key.energy = 2.6
key.angle = math.radians(12)
key.color = (1.0, 0.95, 0.88)
ko = bpy.data.objects.new("key", key)
sc.collection.objects.link(ko)

cam = bpy.data.cameras.new("cam")
cam.type = "ORTHO"
co = bpy.data.objects.new("cam", cam)
sc.collection.objects.link(co)
sc.camera = co

me = bpy.data.meshes.new("catcher")
me.from_pydata([(-50, -50, 0), (50, -50, 0), (50, 50, 0), (-50, 50, 0)], [], [(0, 1, 2, 3)])
catcher = bpy.data.objects.new("catcher", me)
sc.collection.objects.link(catcher)
catcher.is_shadow_catcher = True

FRONT = {"n": Vector((0, 1, 0)), "s": Vector((0, -1, 0)), "e": Vector((1, 0, 0)), "w": Vector((-1, 0, 0))}
meshes = [o for o in bpy.data.objects if o.type == "MESH" and o not in (catcher,)]

for (iid, name, room, typ, pat, face, pick, note) in catalog_items.ITEMS:
    if ONLY and iid not in ONLY:
        continue
    obs = [o for o in meshes if re.search(pat, o.name)]
    if pick and obs:
        cx = [sum((o.matrix_world @ Vector(c)).x for c in o.bound_box) / 8 for o in obs]
        mid = (min(cx) + max(cx)) / 2
        obs = [o for o, x in zip(obs, cx) if (x < mid) == (pick == "west")]
    if not obs:
        continue
    keep = set(obs)
    for o in meshes:
        o.hide_render = o not in keep
    pts = [o.matrix_world @ Vector(c) for o in obs for c in o.bound_box]
    mn = Vector([min(q[i] for q in pts) for i in range(3)])
    mx = Vector([max(q[i] for q in pts) for i in range(3)])
    ctr = (mn + mx) / 2
    catcher.location.z = mn.z
    catcher.hide_render = mn.z > 0.05

    # 3/4 pela frente, 22° de elevação
    f = FRONT[face]
    yaw = math.atan2(f.y, f.x) + math.radians(32)
    el = math.radians(22)
    dirv = Vector((math.cos(yaw) * math.cos(el), math.sin(yaw) * math.cos(el), math.sin(el)))
    co.location = ctr + dirv * 20
    co.rotation_euler = (-dirv).to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()
    inv = co.matrix_world.inverted()
    loc = [inv @ q for q in pts]
    wx = max(q.x for q in loc) - min(q.x for q in loc)
    wy = max(q.y for q in loc) - min(q.y for q in loc)
    aspect = sc.render.resolution_x / sc.render.resolution_y
    cam.ortho_scale = max(wx, wy * aspect) * 1.18
    cam.shift_x = ((max(q.x for q in loc) + min(q.x for q in loc)) / 2) / cam.ortho_scale
    cam.shift_y = ((max(q.y for q in loc) + min(q.y for q in loc)) / 2) / cam.ortho_scale
    cam.clip_end = 60
    # luz vinda do alto, à esquerda da câmera
    kyaw = yaw + math.radians(55)
    ko.rotation_euler = (-Vector((math.cos(kyaw), math.sin(kyaw), 1.6))).to_track_quat("-Z", "Y").to_euler()

    sc.render.filepath = os.path.join(OUT, f"{iid}.png")
    bpy.ops.render.render(write_still=True)
    print("THUMB", iid)
