import bpy, sys, os
p = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=f"modelo2/{p}/ares_ipiranga_final01_{p}.blend")
from build import apply_modifiers, flatten_materials
for n in ["Ceu_externo", "Exterior"]:
    o = bpy.data.objects.get(n)
    if o: bpy.data.objects.remove(o)
apply_modifiers(); flatten_materials()
for o in bpy.data.objects:
    if o.type == 'MESH':
        f = len(o.data.polygons)
        if f > 400:
            m = o.modifiers.new("d", 'DECIMATE'); m.ratio = max(0.08, 400 / f) if f > 3000 else 0.5
            bpy.context.view_layer.objects.active = o
            with bpy.context.temp_override(object=o, active_object=o):
                bpy.ops.object.modifier_apply(modifier="d")
for o in list(bpy.data.objects):
    if o.type in ('LIGHT', 'CAMERA'): bpy.data.objects.remove(o)
out = os.path.abspath(f"modelo2/{p}/ares_ipiranga_final01_{p}_web.glb")
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_image_format='NONE', export_apply=True, export_normals=True)
print("LIGHT", p, os.path.getsize(out))
