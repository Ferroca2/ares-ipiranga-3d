"""Vídeo de passeio pelo apartamento (Eevee), quadros JPEG em video/<paleta>/ para virar MP4 com ffmpeg.

Um plano contínuo na altura dos olhos: entra pela porta, percorre a sala e a cozinha, segue pelo corredor
e termina no Dormitório 1. A câmera mira um alvo que se move junto, com interpolação suave.

uso: python video.py <paleta> [--fps 24] [--res 1280x720] [--frames a-b]
"""
import bpy, sys, os, math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.abspath(__file__))
a = sys.argv[1:]
PAL = a[0] if a else "terra"
FPS = int(a[a.index("--fps") + 1]) if "--fps" in a else 24
RES = tuple(int(v) for v in (a[a.index("--res") + 1] if "--res" in a else "1280x720").split("x"))
OUT = os.path.join(ROOT, "video", PAL)
os.makedirs(OUT, exist_ok=True)

# (segundo, posição do olho, alvo) em coordenadas de planta (x, y para baixo, z)
KEYS = [
    (0.0, (3.95, 6.40, 1.50), (0.40, 6.20, 1.32)),
    (4.0, (3.10, 6.55, 1.50), (0.30, 6.10, 1.30)),
    (7.5, (2.40, 6.45, 1.50), (0.50, 7.40, 1.25)),
    (10.5, (2.20, 6.35, 1.50), (3.80, 7.35, 1.25)),
    (13.5, (2.52, 5.90, 1.50), (2.52, 3.00, 1.35)),
    (16.5, (2.52, 4.60, 1.50), (0.60, 3.70, 1.20)),
    (19.5, (2.62, 3.85, 1.50), (1.50, 1.20, 1.15)),
    (23.5, (2.55, 2.75, 1.45), (0.80, 0.40, 1.00)),
]

bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "modelo2", PAL, f"ares_ipiranga_final01_{PAL}.blend"))
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE_NEXT"
sc.eevee.taa_render_samples = 32
sc.eevee.use_raytracing = True
sc.eevee.use_shadows = True
sc.render.resolution_x, sc.render.resolution_y = RES
sc.render.resolution_percentage = 100
sc.render.fps = FPS
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Medium High Contrast"
sc.view_settings.exposure = 0.15
sc.render.image_settings.file_format = "JPEG"
sc.render.image_settings.quality = 92
COLL_TETO = bpy.data.collections.get("Teto")
if COLL_TETO:
    COLL_TETO.hide_render = False

cd = bpy.data.cameras.new("CamVideo")
cd.lens = 18
cd.sensor_width = 36
cam = bpy.data.objects.new("CamVideo", cd)
sc.collection.objects.link(cam)
tgt = bpy.data.objects.new("AlvoVideo", None)
sc.collection.objects.link(tgt)
tc = cam.constraints.new("TRACK_TO")
tc.target = tgt
tc.track_axis = "TRACK_NEGATIVE_Z"
tc.up_axis = "UP_Y"
sc.camera = cam

for t, (x, y, z), (tx, ty, tz) in KEYS:
    f = 1 + round(t * FPS)
    cam.location = (x, -y, z)
    cam.keyframe_insert("location", frame=f)
    tgt.location = (tx, -ty, tz)
    tgt.keyframe_insert("location", frame=f)
for ob in (cam, tgt):
    for fc in ob.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "BEZIER"
            kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
sc.frame_start = 1
sc.frame_end = 1 + round(KEYS[-1][0] * FPS)
if "--frames" in a:
    s, e = a[a.index("--frames") + 1].split("-")
    sc.frame_start, sc.frame_end = int(s), int(e)
if "--step" in a:
    sc.frame_step = int(a[a.index("--step") + 1])
sc.render.filepath = os.path.join(OUT, "f_")
bpy.ops.render.render(animation=True)
print("VIDEO FRAMES", PAL, sc.frame_start, sc.frame_end)
