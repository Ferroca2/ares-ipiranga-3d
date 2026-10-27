"""Gera a planta cotada, o caderno PDF e as imagens otimizadas para a página web."""
import json
import os
import shutil

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from build import PALETTES

ROOT = os.path.dirname(os.path.abspath(__file__))
REN = os.path.join(ROOT, "renders")
SITE = os.path.join(ROOT, "site")
PAL_ORDER = ["terracota", "nordico", "grafite", "petroleo"]

ROOMS = [
    # chave, título, vistas, medidas (cotas do contrato), área aproximada
    ("sala", "Sala de estar e jantar", ["sala"], "4,21 × 2,41 m, integrada à cozinha", "≈ 10,1 m²"),
    ("cozinha", "Cozinha e área de serviço", ["cozinha"], "bancada 1,84 m · nicho de serviço 1,30 × 0,70 m", "na sala"),
    ("dorm1", "Dormitório 1", ["dorm1", "dorm1_b"], "2,91 × 2,41 m", "≈ 7,0 m²"),
    ("dorm2", "Dormitório 2", ["dorm2"], "2,01 × 2,51 m", "≈ 5,0 m²"),
    ("banho", "Banheiro", ["banho"], "1,21 × 2,11 m", "≈ 2,6 m²"),
]

# rótulos na planta: (texto, x, y em metros de planta)
LABELS = [
    ("DORMITÓRIO 1", "2,91 × 2,41", 1.25, 2.15),
    ("DORMITÓRIO 2", "2,01 × 2,51", 1.30, 3.90),
    ("BANHO", "1,21 × 2,11", 3.60, 4.05),
    ("SALA", "4,21 × 2,41", 0.95, 6.55),
    ("COZINHA", "", 2.70, 6.75),
    ("SERVIÇO", "", 3.55, 5.95),
]


def plan_px(x, y):
    s = 1900 / 8.3
    return 550 + (x - 2.1) * s, 950 + (y - 3.8) * s


def font(size, bold=False):
    for p in (["/System/Library/Fonts/Supplemental/Arial Bold.ttf"] if bold else []) + [
            "/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def labeled_plan(palette):
    im = Image.open(os.path.join(REN, palette, "planta.jpg")).convert("RGBA")
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    f1, f2 = font(30, True), font(24)
    for title, dims, x, y in LABELS:
        px, py = plan_px(x, y)
        w1 = d.textlength(title, font=f1)
        w2 = d.textlength(dims, font=f2) if dims else 0
        w = max(w1, w2) + 28
        h = 46 + (30 if dims else 0)
        d.rounded_rectangle([px - w / 2, py - h / 2, px + w / 2, py + h / 2], 10, fill=(255, 255, 255, 215))
        d.text((px - w1 / 2, py - h / 2 + 8), title, font=f1, fill=(30, 30, 30, 255))
        if dims:
            d.text((px - w2 / 2, py - h / 2 + 44), dims, font=f2, fill=(90, 90, 90, 255))
    # norte/escala
    sx, sy = plan_px(0.0, 7.95)
    s = 1900 / 8.3
    d.rectangle([sx, sy, sx + s, sy + 8], fill=(30, 30, 30, 255))
    d.text((sx + s + 14, sy - 10), "1 m", font=f2, fill=(30, 30, 30, 255))
    out = Image.alpha_composite(im, ov).convert("RGB")
    path = os.path.join(REN, palette, "planta_cotada.jpg")
    out.save(path, quality=90)
    return path


def swatches(P):
    return [P[k] for k in ("wall", "accent_sala", "floor", "wood", "sofa", "throw_d1", "throw_d2", "cabinet")]


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def pdf():
    W, Hh = landscape(A3)
    path = os.path.join(ROOT, "Ares_Ipiranga_Final01_Projeto3D.pdf")
    c = canvas.Canvas(path, pagesize=(W, Hh))
    c.setTitle("Ares Ipiranga · Final 01 · Projeto de interiores 3D")
    M = 40
    ink = (0.12, 0.12, 0.13)
    grey = (0.45, 0.45, 0.47)

    def header(title, sub=""):
        c.setFillColorRGB(*ink)
        c.setFont("Helvetica-Bold", 26)
        c.drawString(M, Hh - M - 20, title)
        if sub:
            c.setFont("Helvetica", 13)
            c.setFillColorRGB(*grey)
            c.drawString(M, Hh - M - 42, sub)
        c.setFont("Helvetica", 9)
        c.setFillColorRGB(*grey)
        c.drawRightString(W - M, M - 18, "Ares Ipiranga (Brio) · Unidade final 01/08 · 31,22 m² · estudo de interiores, medidas internas aproximadas")

    def img(path, x, y, w, h):
        ir = ImageReader(path)
        iw, ih = ir.getSize()
        r = min(w / iw, h / ih)
        dw, dh = iw * r, ih * r
        c.drawImage(ir, x + (w - dw) / 2, y + (h - dh) / 2, dw, dh)
        return x + (w - dw) / 2, y + (h - dh) / 2, dw, dh

    # capa
    img(os.path.join(REN, "terracota", "isometrica.jpg"), W * 0.40, M, W * 0.60 - M, Hh - 2 * M)
    c.setFillColorRGB(*ink)
    c.setFont("Helvetica-Bold", 44)
    c.drawString(M, Hh * 0.62, "Ares Ipiranga")
    c.setFont("Helvetica", 22)
    c.drawString(M, Hh * 0.62 - 36, "Unidade final 01 / 08 · 31,22 m²")
    c.setFont("Helvetica", 14)
    c.setFillColorRGB(*grey)
    for i, t in enumerate(["Projeto de interiores em 3D", "2 dormitórios · sala · cozinha · banho · serviço",
                           "4 opções de paleta: " + ", ".join(PALETTES[p]["label"] for p in PAL_ORDER)]):
        c.drawString(M, Hh * 0.62 - 80 - i * 22, t)
    c.showPage()

    # planta cotada + quadro de áreas
    header("Planta humanizada 3D", "Medidas internas do contrato (osso); móveis conforme a planta decorada")
    _, _, pw, _ = img(os.path.join(REN, "terracota", "planta_cotada.jpg"), M, M, W * 0.42, Hh - 2 * M - 60)
    tx = M + W * 0.46
    ty = Hh - M - 110
    c.setFont("Helvetica-Bold", 15)
    c.setFillColorRGB(*ink)
    c.drawString(tx, ty, "Quadro de áreas")
    ty -= 28
    c.setFont("Helvetica", 12)
    for _, title, _, dims, area in ROOMS:
        c.setFillColorRGB(*ink)
        c.drawString(tx, ty, title)
        c.setFillColorRGB(*grey)
        c.drawString(tx + 230, ty, dims)
        c.drawRightString(tx + 520, ty, area)
        ty -= 22
    c.setFillColorRGB(*ink)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(tx, ty - 6, "Área privativa total")
    c.drawRightString(tx + 520, ty - 6, "31,22 m²")
    ty -= 60
    c.setFont("Helvetica-Bold", 15)
    c.drawString(tx, ty, "Premissas do modelo")
    c.setFont("Helvetica", 11.5)
    c.setFillColorRGB(*grey)
    notes = [
        "Pé-direito 2,50 m; forro de gesso a 2,30 m no banho e sanca na entrada.",
        "Alvenaria estrutural 14 cm (não removível); vedações de 9 cm.",
        "Janelas com peitoril 1,00 m e verga 2,20 m; basculante no banho.",
        "Dormitório 1: cama casal 1,38 × 1,88 m e guarda-roupa de correr 0,55 m.",
        "Dormitório 2: cama de solteiro 0,88 × 1,88 m, escrivaninha e guarda-roupa.",
        "Serviço: lava e seca sob bancada + tanque, junto à parede do banho.",
        "Cozinha: bancada linear com cooktop 4 bocas, cuba e geladeira no canto.",
        "Medidas sujeitas ao projeto executivo; confirme in loco antes da marcenaria.",
    ]
    for n in notes:
        ty -= 19
        c.drawString(tx, ty, "• " + n)
    c.showPage()

    # paletas
    header("Paletas de cor", "Cada cômodo foi renderizado nas quatro opções")
    colw = (W - 2 * M) / 4
    names = ["Paredes", "Destaque", "Piso", "Madeira", "Estofado", "Têxtil 1", "Têxtil 2", "Marcenaria"]
    for i, p in enumerate(PAL_ORDER):
        P = PALETTES[p]
        x = M + i * colw
        img(os.path.join(REN, p, "isometrica.jpg"), x + 6, Hh * 0.38, colw - 12, Hh * 0.46)
        c.setFillColorRGB(*ink)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(x + 10, Hh * 0.36, P["label"])
        for j, (hx, nm) in enumerate(zip(swatches(P), names)):
            yy = Hh * 0.33 - j * 24
            c.setFillColorRGB(*hexrgb(hx))
            c.setStrokeColorRGB(0.8, 0.8, 0.8)
            c.rect(x + 10, yy - 4, 30, 18, fill=1, stroke=1)
            c.setFillColorRGB(*grey)
            c.setFont("Helvetica", 10.5)
            c.drawString(x + 48, yy + 1, f"{nm}  {hx.upper()}")
    c.showPage()

    # cômodos: 4 opções lado a lado
    for key, title, views, dims, area in ROOMS:
        for v in views:
            header(title + (" · vista 2" if v.endswith("_b") else ""), f"{dims} · {area} · quatro opções de cor")
            gw, gh = (W - 2 * M - 16) / 2, (Hh - 2 * M - 80) / 2
            for i, p in enumerate(PAL_ORDER):
                gx = M + (i % 2) * (gw + 16)
                gy = M + (1 - i // 2) * (gh + 10)
                x, y, dw, dh = img(os.path.join(REN, p, f"{v}.jpg"), gx, gy + 16, gw, gh - 16)
                c.setFillColorRGB(*ink)
                c.setFont("Helvetica-Bold", 11)
                c.drawString(x, y - 13, PALETTES[p]["label"])
            c.showPage()
    c.save()
    return path


def site():
    os.makedirs(os.path.join(SITE, "img"), exist_ok=True)
    os.makedirs(os.path.join(SITE, "models"), exist_ok=True)
    views = ["planta_cotada", "isometrica", "sala", "cozinha", "dorm1", "dorm1_b", "dorm2", "banho"]
    for p in PAL_ORDER:
        for v in views:
            im = Image.open(os.path.join(REN, p, f"{v}.jpg"))
            im.thumbnail((1400, 1400))
            im.save(os.path.join(SITE, "img", f"{p}_{v}.jpg"), quality=80, optimize=True, progressive=True)
        glb = os.path.join(ROOT, "modelo", p, f"ares_ipiranga_final01_{p}.glb")
        if os.path.exists(glb):
            shutil.copy(glb, os.path.join(SITE, "models", f"{p}.glb"))
    meta = {p: dict(label=PALETTES[p]["label"], swatches=swatches(PALETTES[p])) for p in PAL_ORDER}
    print(json.dumps(meta, ensure_ascii=False))


if __name__ == "__main__":
    for p in PAL_ORDER:
        labeled_plan(p)
    print("PDF", pdf())
    site()
