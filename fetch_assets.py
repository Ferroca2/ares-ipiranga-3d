"""Baixa assets CC0 da Poly Haven (modelos glTF 1k, texturas 2k, HDRI 2k)."""
import json, os, sys, urllib.request
UA = {"User-Agent": "ares-ipiranga-3d/1.0 (interior study)"}
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "ph")
MODELS = ["potted_plant_02", "potted_plant_04", "potted_plant_01", "ceramic_vase_01", "ceramic_vase_02",
          "ceramic_vase_04", "decorative_book_set_01", "standing_picture_frame_01", "modern_ceiling_lamp_01",
          "desk_lamp_arm_01", "jug_01"]
TEXTURES = ["oak_veneer_01", "natural_walnut_veneer", "white_plaster_02", "rough_linen", "velour_velvet",
            "marble_01", "terrazzo_tiles", "long_white_tiles", "smooth_concrete_floor", "fabric_pattern_07",
            "plank_flooring_04", "large_grey_tiles", "white_oak_veneer", "denim_fabric_03"]
HDRIS = ["kloofendal_48d_partly_cloudy_puresky"]

def get(url, path):
    if os.path.exists(path):
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA)) as r, open(path, "wb") as f:
        f.write(r.read())

def files(aid):
    return json.load(urllib.request.urlopen(urllib.request.Request(f"https://api.polyhaven.com/files/{aid}", headers=UA)))

for m in MODELS:
    fm = files(m)
    if "gltf" not in fm:
        print("skip (sem glTF)", m); continue
    g = fm["gltf"]["1k"]["gltf"]
    d = os.path.join(OUT, "models", m)
    get(g["url"], os.path.join(d, os.path.basename(g["url"])))
    for rel, inc in g.get("include", {}).items():
        get(inc["url"], os.path.join(d, rel))
    print("model", m)
for t in TEXTURES:
    f = files(t)
    for k, key in [("diff", "Diffuse"), ("rough", "Rough"), ("nor", "nor_gl"), ("disp", "Displacement")]:
        if key in f and "2k" in f[key]:
            u = f[key]["2k"]["jpg"]["url"]
            get(u, os.path.join(OUT, "textures", t, f"{k}.jpg"))
    print("texture", t, [k for k in f if k in ("Diffuse", "Rough", "nor_gl")])
for h in HDRIS:
    u = files(h)["hdri"]["2k"]["hdr"]["url"]
    get(u, os.path.join(OUT, "hdri", h + ".hdr"))
    print("hdri", h)
