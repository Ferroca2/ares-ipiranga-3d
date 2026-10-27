"""Recorta as imagens das opções de jantar para site/opcoes/."""
import os
from PIL import Image
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "site", "opcoes")
os.makedirs(OUT, exist_ok=True)
for d in ["bancada", "rebativel", "rebativel_fechada", "centro"]:
    base = os.path.join(ROOT, "renders_opcoes", d, "terra")
    s = os.path.join(base, "sala.jpg")
    if os.path.exists(s):
        im = Image.open(s)
        im.thumbnail((1600, 1600))
        im.save(os.path.join(OUT, f"{d}_sala.jpg"), quality=82, optimize=True, progressive=True)
    p = os.path.join(base, "planta.jpg")
    if os.path.exists(p):
        # planta ortográfica: 1900 px = 8,3 m, centro (2,1 ; 3,8); recorte da sala x -0,2..4,4, y 5,0..7,75
        Image.open(p).crop((23, 1225, 1076, 1854)).save(os.path.join(OUT, f"{d}_planta.jpg"), quality=85)
print(sorted(os.listdir(OUT)))
