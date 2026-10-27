"""v2: planta cotada, caderno PDF (A3) e assets da página para o conceito "Ateliê Ipiranga"."""
import base64
import json
import os
import struct

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

ROOT = os.path.dirname(os.path.abspath(__file__))
REN = os.path.join(ROOT, "renders2")
SITE = os.path.join(ROOT, "site")
ORDER = ["terra", "mata", "moderno", "ipe"]

# paletas (espelha build2.PALETTES sem importar bpy)
PAL = {
    "terra": ("Terra Paulista", ["#F2EDE4", "#C39062", "#B5583A", "#6E6B4A", "#3A3835"],
              "Base mineral quente: tijolo e terra roxa. A terracota costura rack, cabeceira, barrado e guarda-roupa."),
    "mata": ("Mata Atlântica", ["#F4F1EA", "#CDAE84", "#4F5B3E", "#A3AE94", "#B08D57"],
             "Calma e biofílica. Sálvia como parede média no quarto 2, musgo nas lacas, metais em latão."),
    "moderno": ("Modernismo Paulista", ["#F5F3EE", "#AC7D52", "#1F4E8C", "#BDB8AF", "#1E1E1E"],
                "Referência aos azulejos da arquitetura moderna brasileira: cobalto no backsplash e no barrado."),
    "ipe": ("Ipê", ["#EFE6D4", "#8A5E3E", "#C99A2E", "#D9A68F", "#2F4A3A"],
            "A mais ousada: ocre nas lacas, argila no quarto 2 e sofá verde-garrafa."),
}

ROOMS = [
    ("estar", "Sala · parede única", "4,21 m de marcenaria contínua: ripado com TV, cozinha e torre da geladeira"),
    ("sala", "Sala de estar e jantar", "4,21 × 2,41 m · sofá 1,70 m, canto alemão sob a janela"),
    ("cozinha", "Cozinha e serviço", "bancada 1,84 m, aéreos até o teto, nicho com portas de palhinha"),
    ("corredor", "Corredor-galeria", "0,78 m · barrado até 1,10 m com filete de freijó"),
    ("dorm1", "Dormitório 1", "2,91 × 2,41 m · cabeceira estofada, criados suspensos, arandelas"),
    ("dorm1_b", "Dormitório 1 · armário", "guarda-roupa de correr até o teto com puxador cava"),
    ("dorm2", "Dormitório 2 · estúdio", "2,01 × 2,51 m · daybed, escrivaninha, estante e armário em laca"),
    ("banho", "Banheiro", "1,21 × 2,11 m · box até o forro, bancada suspensa, espelho com LED"),
]

LABELS = [("DORMITÓRIO 1", "2,91 × 2,41", 1.20, 2.15), ("DORMITÓRIO 2", "2,01 × 2,51", 1.30, 3.95),
          ("BANHO", "1,21 × 2,11", 3.60, 4.45), ("ESTAR / JANTAR", "4,21 × 2,41", 1.25, 6.35),
          ("COZINHA", "", 2.60, 6.80), ("SERVIÇO", "", 3.55, 6.05), ("GALERIA", "", 2.52, 4.75)]


def font(size, bold=False):
    for p in (["/System/Library/Fonts/Supplemental/Arial Bold.ttf"] if bold else []) + [
            "/System/Library/Fonts/Supplemental/Arial.ttf"]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def labeled_plan(p):
    im = Image.open(os.path.join(REN, p, "planta.jpg")).convert("RGBA")
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    f1, f2 = font(26, True), font(22)
    s = 1900 / 8.3
    for title, dims, x, y in LABELS:
        px, py = 550 + (x - 2.1) * s, 950 + (y - 3.8) * s
        w1 = d.textlength(title, font=f1)
        w2 = d.textlength(dims, font=f2) if dims else 0
        w, h = max(w1, w2) + 26, 40 + (28 if dims else 0)
        d.rounded_rectangle([px - w / 2, py - h / 2, px + w / 2, py + h / 2], 8, fill=(255, 255, 255, 222))
        d.text((px - w1 / 2, py - h / 2 + 7), title, font=f1, fill=(28, 28, 28, 255))
        if dims:
            d.text((px - w2 / 2, py - h / 2 + 38), dims, font=f2, fill=(95, 95, 95, 255))
    sx, sy = 550 + (0 - 2.1) * s, 950 + (7.95 - 3.8) * s
    d.rectangle([sx, sy, sx + s, sy + 7], fill=(28, 28, 28, 255))
    d.text((sx + s + 12, sy - 9), "1 m", font=f2, fill=(28, 28, 28, 255))
    out = os.path.join(REN, p, "planta_cotada.jpg")
    Image.alpha_composite(im, ov).convert("RGB").save(out, quality=92)


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def pdf():
    W, Hh = landscape(A3)
    path = os.path.join(ROOT, "Ares_Ipiranga_Atelie_Projeto3D.pdf")
    c = canvas.Canvas(path, pagesize=(W, Hh))
    c.setTitle("Ateliê Ipiranga · Ares Ipiranga final 01 · Projeto de interiores")
    M = 40
    ink, grey = (0.12, 0.12, 0.13), (0.45, 0.45, 0.47)

    def header(t, sub=""):
        c.setFillColorRGB(*ink)
        c.setFont("Helvetica-Bold", 24)
        c.drawString(M, Hh - M - 20, t)
        if sub:
            c.setFont("Helvetica", 12.5)
            c.setFillColorRGB(*grey)
            c.drawString(M, Hh - M - 40, sub)
        c.setFont("Helvetica", 8.5)
        c.setFillColorRGB(*grey)
        c.drawRightString(W - M, M - 20, "Ateliê Ipiranga · Ares Ipiranga (Brio) · final 01/08 · 31,22 m² · estudo de interiores; medidas internas do contrato")

    def img(p, x, y, w, h):
        ir = ImageReader(p)
        iw, ih = ir.getSize()
        r = min(w / iw, h / ih)
        dw, dh = iw * r, ih * r
        c.drawImage(ir, x + (w - dw) / 2, y + (h - dh) / 2, dw, dh)
        return x + (w - dw) / 2, y + (h - dh) / 2, dw, dh

    def para(text, x, y, width, size=11, lead=15, color=grey, fontname="Helvetica"):
        c.setFont(fontname, size)
        c.setFillColorRGB(*color)
        words, line = text.split(), ""
        for wd in words:
            t = (line + " " + wd).strip()
            if c.stringWidth(t, fontname, size) > width:
                c.drawString(x, y, line)
                y -= lead
                line = wd
            else:
                line = t
        if line:
            c.drawString(x, y, line)
            y -= lead
        return y

    # capa
    img(os.path.join(REN, "terra", "sala.jpg"), W * 0.36, M, W * 0.64 - M, Hh - 2 * M)
    c.setFillColorRGB(*ink)
    c.setFont("Helvetica-Bold", 46)
    c.drawString(M, Hh * 0.66, "Ateliê Ipiranga")
    c.setFont("Helvetica", 19)
    c.drawString(M, Hh * 0.66 - 34, "a casa como moldura")
    y = para("Projeto de interiores para o apartamento final 01 do Ares Ipiranga (Brio), 31,22 m², 2 dormitórios. "
             "Marcenaria contínua de freijó emoldura a vida e a arte; uma cor-assinatura por cômodo; piso único "
             "claro, teto branco e luz quente sobreposta, porque a alvenaria é estrutural.", M, Hh * 0.66 - 80, W * 0.30, 12.5, 18)
    c.showPage()

    # conceito + pesquisa
    header("Conceito e fundamentos", "Do briefing de pesquisa (research/design_brief.md)")
    col = (W - 2 * M - 40) / 2
    y = Hh - M - 90
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(*ink)
    c.drawString(M, y, "Princípios aplicados")
    y -= 24
    for t, d in [
        ("Mostrar piso", "A área de piso visível é o fator mais forte de amplitude percebida (Stamps, 2011). Rack, criados e escrivaninha suspensos; sofá com pés de 15 cm; nenhum móvel no centro."),
        ("Volumes altos só nas paredes", "Enclausuramento acompanha a altura dos limites próximos (Stamps, 2012): armários vão até o teto, encostados; perto da circulação, nada acima de 0,90 m."),
        ("Teto branco, sem rebaixo na sala", "Teto claro é percebido mais alto (Oberfeld, Hecht & Gamer, 2010). Forro só no banho."),
        ("Janela livre e parede do fundo iluminada", "Vista e iluminância na parede oposta ampliam (Tural & Tural, 2024): cortina recolhida na lateral, wall-wash no ripado."),
        ("Uma peça de marcenaria por cômodo", "Método MKCA / Soek: um único volume contínuo em vez de móveis soltos; paleta de 2–3 materiais."),
        ("Flexibilidade soft", "Schneider & Till (2005): daybed que vira quarto de hóspedes, banco-baú no jantar."),
        ("Ergonomia", "Circulação ≥ 0,75 m, frente da bancada ≥ 0,90 m, lateral de cama ≈ 0,50 m (Panero & Zelnik; Neufert)."),
    ]:
        c.setFont("Helvetica-Bold", 11.5)
        c.setFillColorRGB(*ink)
        c.drawString(M, y, t)
        y = para(d, M, y - 15, col, 10.5, 14) - 8
    x2 = M + col + 40
    y = Hh - M - 90
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(*ink)
    c.drawString(x2, y, "Referências de projeto")
    y -= 24
    for t, d in [
        ("Casa 100 Arquitetura · Compact fit, 24 m² (SP)", "Lógica de quarto de hotel; cozinha e armário num nicho só."),
        ("Pro.a Arquitetos · Apto Nébias, 32 m² (SP)", "Madeira e vidro, marcenaria autoral."),
        ("Soek · Apto 33, 33 m² (SP)", "Uma marcenaria envolve o espaço e concentra eletros e acessos."),
        ("Estúdio BRA · Apto Cazo, 38 m² (SP)", "Paleta curta de madeira e cinza sobre branco."),
        ("MKCA · Unfolding Apartment, 37 m² (NY)", "Um único armário gigante libera o resto do espaço."),
        ("Gary Chang · Domestic Transformer, 32 m² (HK)", "Painéis em trilho: o mesmo espaço em vários usos."),
        ("Elii · Didomestic (Madri)", "Um gesto de cor como identidade."),
        ("Linguagem: SuperLimão, Memola, Alan Chu, Triplex", "Cor pontual, materiais crus, fundo neutro para arte."),
    ]:
        c.setFont("Helvetica-Bold", 11)
        c.setFillColorRGB(*ink)
        c.drawString(x2, y, t)
        y = para(d, x2, y - 14, col, 10.5, 14) - 8
    c.showPage()

    # planta
    header("Planta humanizada", "Medidas internas do contrato; layout Ateliê Ipiranga")
    img(os.path.join(REN, "terra", "planta_cotada.jpg"), M, M, W * 0.40, Hh - 2 * M - 60)
    img(os.path.join(REN, "terra", "isometrica.jpg"), M + W * 0.42, M, W * 0.58 - 2 * M, Hh - 2 * M - 60)
    c.showPage()

    # paletas
    header("Quatro paletas", "Mesma marcenaria e layout; muda a cor-assinatura, a madeira e os têxteis")
    cw = (W - 2 * M) / 4
    for i, p in enumerate(ORDER):
        lab, sw, why = PAL[p]
        x = M + i * cw
        img(os.path.join(REN, p, "estar.jpg"), x + 6, Hh * 0.42, cw - 12, Hh * 0.42)
        c.setFillColorRGB(*ink)
        c.setFont("Helvetica-Bold", 15)
        c.drawString(x + 8, Hh * 0.39, lab)
        for j, hx in enumerate(sw):
            c.setFillColorRGB(*hexrgb(hx))
            c.setStrokeColorRGB(0.8, 0.8, 0.8)
            c.rect(x + 8 + j * 44, Hh * 0.33, 38, 26, fill=1, stroke=1)
            c.setFillColorRGB(*grey)
            c.setFont("Helvetica", 7.5)
            c.drawString(x + 8 + j * 44, Hh * 0.33 - 11, hx.upper())
        para(why, x + 8, Hh * 0.27, cw - 24, 10.5, 14)
    c.showPage()

    # páginas grandes da paleta recomendada
    for v, t, d in ROOMS:
        header(t, d + " · paleta Terra Paulista")
        img(os.path.join(REN, "terra", f"{v}.jpg"), M, M, W - 2 * M, Hh - 2 * M - 60)
        c.showPage()

    # comparação por cômodo
    for v, t, d in ROOMS:
        header(t + " · opções de cor", d)
        gw, gh = (W - 2 * M - 16) / 2, (Hh - 2 * M - 80) / 2
        for i, p in enumerate(ORDER):
            gx = M + (i % 2) * (gw + 16)
            gy = M + (1 - i // 2) * (gh + 10)
            x, y, dw, dh = img(os.path.join(REN, p, f"{v}.jpg"), gx, gy + 16, gw, gh - 16)
            c.setFillColorRGB(*ink)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(x, y - 13, PAL[p][0])
        c.showPage()
    c.save()
    return path


def glb_to_json(src, dst):
    b = open(src, "rb").read()
    off, js, bin_ = 12, None, None
    while off < len(b):
        ln, typ = struct.unpack("<I4s", b[off:off + 8])
        data = b[off + 8:off + 8 + ln]
        off += 8 + ln
        if typ == b"JSON":
            js = json.loads(data)
        elif typ == b"BIN\x00":
            bin_ = data
    js["buffers"][0]["uri"] = "data:application/octet-stream;base64," + base64.b64encode(bin_).decode()
    json.dump(js, open(dst, "w"), separators=(",", ":"))


def site():
    img_dir = os.path.join(SITE, "img2")
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(os.path.join(SITE, "models2"), exist_ok=True)
    for p in ORDER:
        for v in ["planta_cotada", "isometrica"] + [r[0] for r in ROOMS]:
            im = Image.open(os.path.join(REN, p, f"{v}.jpg"))
            im.thumbnail((1600, 1600))
            im.save(os.path.join(img_dir, f"{p}_{v}.jpg"), quality=80, optimize=True, progressive=True)
        g = os.path.join(ROOT, "modelo2", p, f"ares_ipiranga_final01_{p}_web.glb")
        if os.path.exists(g):
            glb_to_json(g, os.path.join(SITE, "models2", f"{p}.json"))
    meta = {p: dict(label=PAL[p][0], swatches=PAL[p][1], why=PAL[p][2]) for p in ORDER}
    json.dump(meta, open(os.path.join(SITE, "palettes2.json"), "w"), ensure_ascii=False)


if __name__ == "__main__":
    for p in ORDER:
        labeled_plan(p)
    print("PDF", pdf())
    site()
    print("site ok")
