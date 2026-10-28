"""Vídeo de passeio pelo apartamento (Eevee), quadros JPEG em video/<paleta>/ para virar MP4 com ffmpeg.

Um plano contínuo na altura dos olhos: entra pela porta, percorre a sala e a cozinha, entra no banheiro
e no Dormitório 2 e termina no Dormitório 1. A câmera mira um alvo que se move junto, com interpolação suave.

uso: python video.py <paleta> [--fps 24] [--res 1280x720] [--frames a-b]
"""
import bpy, sys, os, math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.abspath(__file__))
a = sys.argv[1:]
PAL = a[0] if a else "terra"
FPS = int(a[a.index("--fps") + 1]) if "--fps" in a else 24
RES = tuple(int(v) for v in (a[a.index("--res") + 1] if "--res" in a else "1280x720").split("x"))
OUT = os.path.join(ROOT, "video", a[a.index("--dir") + 1] if "--dir" in a else PAL)
os.makedirs(OUT, exist_ok=True)

# (segundo, posição do olho, alvo) em coordenadas de planta (x, y para baixo, z)
KEYS = [
    (0.0, (3.95, 6.40, 1.50), (0.40, 6.20, 1.32)),
    (4.0, (3.10, 6.55, 1.50), (0.30, 6.10, 1.30)),
    (7.5, (2.40, 6.45, 1.50), (0.50, 7.40, 1.25)),
    (10.5, (2.20, 6.35, 1.50), (3.80, 7.35, 1.25)),
    (13.5, (2.52, 5.80, 1.50), (2.52, 3.00, 1.35)),
    # banheiro
    (16.0, (2.55, 4.72, 1.50), (3.90, 4.40, 1.25)),
    (17.5, (2.85, 4.68, 1.50), (4.00, 4.30, 1.05)),
    (19.5, (3.05, 4.70, 1.50), (4.05, 4.60, 0.95)),
    (22.0, (3.05, 4.70, 1.50), (3.60, 3.30, 1.15)),
    (24.0, (2.85, 4.68, 1.50), (2.00, 4.40, 1.30)),
    # dormitório 2
    (25.5, (2.45, 4.15, 1.50), (0.80, 3.90, 1.20)),
    (26.5, (2.05, 4.13, 1.50), (0.40, 3.40, 1.10)),
    (28.5, (1.85, 4.35, 1.50), (0.25, 3.05, 1.00)),
    (31.0, (1.85, 4.35, 1.50), (0.35, 4.10, 0.95)),
    (32.5, (2.15, 4.12, 1.50), (2.60, 2.60, 1.30)),
    # corredor até o dormitório 1
    (34.0, (2.55, 3.80, 1.50), (2.55, 1.20, 1.25)),
    (35.5, (2.45, 2.75, 1.50), (1.20, 0.80, 1.10)),
    (38.0, (2.10, 2.25, 1.50), (0.70, 0.35, 1.00)),
    (41.0, (2.10, 2.25, 1.50), (1.40, 0.20, 0.90)),
    (43.5, (2.05, 2.30, 1.50), (0.40, 1.20, 1.00)),
]

bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "modelo2", PAL, f"ares_ipiranga_final01_{PAL}.blend"))
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE_NEXT"
sc.eevee.taa_render_samples = int(a[a.index("--samples") + 1]) if "--samples" in a else 16
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
sc.render.use_overwrite = False  # retoma de onde parou
bpy.ops.render.render(animation=True)
print("VIDEO FRAMES", PAL, sc.frame_start, sc.frame_end)
