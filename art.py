"""Gera texturas 2D do projeto: palhinha (tela de cana) e obras de arte abstratas por paleta.

A arte segue a linguagem do modernismo brasileiro (curvas de Tomie Ohtake, módulos de Athos Bulcão):
formas planas em 3–4 cores da paleta sobre papel de algodão.
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "assets", "gen")
os.makedirs(OUT, exist_ok=True)


def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def paper(w, h, base="#F1ECE2", seed=0):
    rnd = random.Random(seed)
    im = Image.new("RGB", (w, h), hexc(base))
    px = im.load()
    for _ in range(w * h // 6):
        x, y = rnd.randrange(w), rnd.randrange(h)
        r, g, b = px[x, y]
        d = rnd.randint(-7, 5)
        px[x, y] = (r + d, g + d, b + d)
    return im.filter(ImageFilter.GaussianBlur(0.6))


def palhinha(size=512):
    """Tela de palhinha (trama octogonal clássica) com furos transparentes."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cane = (206, 176, 128, 255)
    dark = (150, 118, 74, 255)
    n = 4
    step = size / n
    wd = int(step * 0.16)
    for i in range(n + 1):
        p = i * step
        d.line([(p, 0), (p, size)], fill=cane, width=wd)
        d.line([(0, p), (size, p)], fill=cane, width=wd)
    for i in range(-n, 2 * n):
        p = i * step
        d.line([(p, 0), (p + size, size)], fill=dark, width=int(wd * 0.8))
        d.line([(p, size), (p + size, 0)], fill=dark, width=int(wd * 0.8))
    im = im.filter(ImageFilter.GaussianBlur(1.2))
    path = os.path.join(OUT, "palhinha.png")
    im.save(path)
    return path


def art_curves(cols, w=1400, h=1000, seed=1, base="#F1ECE2"):
    """Composição de faixas curvas sobrepostas (à maneira de Tomie Ohtake)."""
    rnd = random.Random(seed)
    im = paper(w, h, base, seed)
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    cx, cy = w * rnd.uniform(0.35, 0.6), h * rnd.uniform(0.45, 0.6)
    for i, c in enumerate(cols):
        r = h * (0.62 - i * 0.12)
        t0 = rnd.uniform(150, 220)
        d.arc([cx - r, cy - r, cx + r, cy + r], t0, t0 + rnd.uniform(150, 230), fill=hexc(c) + (255,),
              width=int(h * 0.075))
    d.ellipse([w * 0.70, h * 0.16, w * 0.70 + h * 0.18, h * 0.34], fill=hexc(cols[-1]) + (255,))
    im.paste(lay, (0, 0), lay)
    return im


def art_modules(cols, w=1000, h=1000, seed=2, base="#F1ECE2", n=4):
    """Módulos quadrados com semicírculos girados (à maneira dos azulejos de Athos Bulcão)."""
    rnd = random.Random(seed)
    im = paper(w, h, base, seed)
    d = ImageDraw.Draw(im)
    s = w / n
    for i in range(n):
        for j in range(n):
            x, y = i * s, j * s
            c = hexc(rnd.choice(cols))
            rot = rnd.choice([0, 90, 180, 270])
            d.pieslice([x - s / 2 + (s if rot in (90, 180) else 0), y - s / 2 + (s if rot in (180, 270) else 0),
                        x + s / 2 + (s if rot in (90, 180) else 0), y + s / 2 + (s if rot in (180, 270) else 0)],
                       rot, rot + 90, fill=c)
            if rnd.random() < 0.35:
                d.rectangle([x + s * 0.42, y + s * 0.42, x + s * 0.58, y + s * 0.58], fill=hexc(rnd.choice(cols)))
    return im


def art_line(cols, w=800, h=1000, seed=3, base="#F3EFE6"):
    """Desenho de linha contínua (figura abstrata) em tinta escura com uma mancha de cor."""
    rnd = random.Random(seed)
    im = paper(w, h, base, seed)
    d = ImageDraw.Draw(im)
    d.ellipse([w * 0.18, h * 0.42, w * 0.18 + w * 0.42, h * 0.42 + w * 0.42], fill=hexc(cols[0]))
    pts = []
    x, y = w * 0.5, h * 0.15
    for k in range(260):
        t = k / 260
        x = w * (0.5 + 0.28 * math.sin(t * 9.0 + rnd.uniform(-0.1, 0.1)) * math.cos(t * 2.3))
        y = h * (0.12 + 0.78 * t + 0.03 * math.sin(t * 17))
        pts.append((x, y))
    d.line(pts, fill=(40, 36, 32), width=6, joint="curve")
    return im


def make_all(palettes):
    paths = {"palhinha": palhinha()}
    for key, P in palettes.items():
        art = P["art"]
        a = art_curves(art, seed=sum(map(ord, key)) % 97)
        a.save(os.path.join(OUT, f"{key}_art_sala.jpg"), quality=92)
        b = art_modules(art, seed=sum(map(ord, key)) % 89 + 3)
        b.save(os.path.join(OUT, f"{key}_art_mod.jpg"), quality=92)
        c = art_line(art[1:], seed=sum(map(ord, key)) % 83 + 5)
        c.save(os.path.join(OUT, f"{key}_art_line.jpg"), quality=92)
    return paths
