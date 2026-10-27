"""Ares Ipiranga · final 01 — v2 "Ateliê Ipiranga: a casa como moldura".

Conceito (research/design_brief.md): marcenaria contínua de freijó como moldura da vida e da arte,
uma cor-assinatura por cômodo, piso único claro, teto branco e luz quente sobreposta (alvenaria estrutural).

Coordenadas de planta: x para a direita, y para BAIXO, metros, origem no canto interno superior
esquerdo do Dormitório 1. Cotas da planta de contrato.

  python build2.py --palette terra --views all --samples 256
"""
import argparse
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402

import art  # noqa: E402
from lib3d import *  # noqa: E402,F403

H = 2.50
DOOR_H = 2.10
T_EXT = 0.14
T_VED = 0.09

PALETTES = {
    "terra": dict(
        label="Terra Paulista", wall="#F2EDE4", wall_d2="#EADBCB", wood="#C39062", accent="#B5583A",
        second="#6E6B4A", dark="#3A3835", metal="black", sofa="#DCD3C4", floor="#D2BC9F",
        bath_floor="#CFCAC2", box_tile="#EEE9E0", backsplash="#F3EFE8", rug="#CDBFA8", duvet="#F1EDE6",
        pillow2="#6E6B4A", art=["#B5583A", "#6E6B4A", "#D9A066", "#3A3835"],
    ),
    "mata": dict(
        label="Mata Atlântica", wall="#F4F1EA", wall_d2="#CDD3C1", wood="#CDAE84", accent="#4F5B3E",
        second="#A3AE94", dark="#2F332B", metal="brass", sofa="#CFCBBE", floor="#D8C7AA",
        bath_floor="#D3D0C8", box_tile="#A9B49B", backsplash="#E8ECE0", rug="#B8B49E", duvet="#F3F1EA",
        pillow2="#A3AE94", art=["#4F5B3E", "#A3AE94", "#C9A97E", "#B08D57"],
    ),
    "moderno": dict(
        label="Modernismo Paulista", wall="#F5F3EE", wall_d2="#DDE3EC", wood="#AC7D52", accent="#1F4E8C",
        second="#BDB8AF", dark="#1E1E1E", metal="black", sofa="#AFAAA1", floor="#CDB596",
        bath_floor="#C4C0B8", box_tile="#F2F1EC", backsplash="#1F4E8C", rug="#D6D1C6", duvet="#F4F3EF",
        pillow2="#E3B23C", art=["#1F4E8C", "#E3B23C", "#1E1E1E", "#BDB8AF"],
    ),
    "ipe": dict(
        label="Ipê", wall="#EFE6D4", wall_d2="#DDB29C", wood="#8A5E3E", accent="#C99A2E",
        second="#D9A68F", dark="#2F4A3A", metal="brass", sofa="#34503F", floor="#CBB08E",
        bath_floor="#D8CDBE", box_tile="#D9A68F", backsplash="#F1E9D8", rug="#E2D2B2", duvet="#F2EBDD",
        pillow2="#D9A68F", art=["#C99A2E", "#2F4A3A", "#D9A68F", "#5A3E2B"],
    ),
    "ebano": dict(
        label="Madeira Preta", wall="#F2EFE9", wall_d2="#D8D1C5", wood="#2A2623", accent="#9C6B43",
        second="#8C8F7E", dark="#141414", metal="brass", sofa="#E2DCD1", floor="#D6C3A5",
        bath_floor="#CBC7C0", box_tile="#ECE8E1", backsplash="#EAE5DC", rug="#C9BBA5", duvet="#F2EFEA",
        pillow2="#8C8F7E", art=["#9C6B43", "#2A2623", "#C9B79A", "#8C8F7E"],
    ),
}


# =====================================================================================
def materials(P):
    M = {}
    M["wall"] = surface("Pintura paredes", "white_plaster_02", P["wall"], scale=0.5, rng=(0.95, 1.02), rough=0.85,
                        normal=0.12)
    M["wall_d2"] = surface("Pintura dorm 2", "white_plaster_02", P["wall_d2"], scale=0.5, rng=(0.95, 1.02),
                           rough=0.85, normal=0.12)
    M["ceiling"] = solid("Teto", "#F7F6F3", 0.9)
    M["floor"] = surface("Vinilico carvalho", "white_oak_veneer", P["floor"], scale=0.9, rng=(0.80, 1.12),
                         grid=(1.22, 0.18, 0.37, 0.0012, "#8E7A63"), axes="xy", rot=90, rough=0.38, coat=0.08)
    M["bath_floor"] = surface("Porcelanato cimento 60", "smooth_concrete_floor", P["bath_floor"], scale=0.5,
                              rng=(0.86, 1.08), grid=(0.6, 0.6, 0.0, 0.0015, "#9E9991"), rough=0.35)
    M["box_y"] = surface("Azulejo box (xz)", None, P["box_tile"], grid=(0.075, 0.30, 0.0, 0.0012, "#CFC9BF"),
                         axes="xz", rough=0.12, coat=0.6)
    M["box_x"] = surface("Azulejo box (yz)", None, P["box_tile"], grid=(0.075, 0.30, 0.0, 0.0012, "#CFC9BF"),
                         axes="yz", rough=0.12, coat=0.6)
    M["splash"] = surface("Azulejo cozinha", None, P["backsplash"], grid=(0.075, 0.30, 0.0, 0.0012, "#CFC9BF"),
                          axes="xz", rough=0.12, coat=0.6)
    M["wood"] = pbr("Freijo", "oak_veneer_01", scale=1.2, tint=P["wood"], tint_mode="replace",
                    rng=(0.70, 1.16), normal=0.25, coat=0.05, flat=P["wood"])
    M["wood_dark"] = pbr("Freijo escuro", "oak_veneer_01", scale=1.2, tint=P["dark"], tint_mode="replace",
                         rng=(0.8, 1.1), normal=0.25, flat=P["dark"])
    M["accent"] = solid("Laca acento", P["accent"], 0.38, coat=0.15)
    M["second"] = solid("Laca secundaria", P["second"], 0.4, coat=0.1)
    M["quartz"] = solid("Quartzo branco", "#F1EFEA", 0.2, coat=0.35)
    M["metal"] = (solid("Metal preto", "#1C1C1C", 0.38, metal=0.7) if P["metal"] == "black"
                  else solid("Latao escovado", "#B89560", 0.28, metal=1.0))
    M["black"] = solid("Preto fosco", "#151515", 0.45)
    M["inox"] = solid("Inox", "#CFCFCF", 0.28, metal=1.0)
    M["glass"] = solid("Vidro", "#FFFFFF", 0.0, transmission=1.0, ior=1.5)
    M["mirror"] = solid("Espelho", "#F2F2F2", 0.02, metal=1.0)
    M["ceramic"] = solid("Louca", "#F6F5F2", 0.06, coat=0.6)
    M["white"] = solid("Laca branca", "#F1F0EC", 0.35, coat=0.1)
    M["alum"] = solid("Aluminio preto", "#222222", 0.35, metal=0.8)
    M["sofa"] = fabric("Linho sofa", P["sofa"])
    M["linen_white"] = fabric("Linho branco", P["duvet"], scale=4.0)
    M["linen_acc"] = fabric("Linho acento", P["accent"], scale=4.0)
    M["velvet"] = fabric("Veludo almofada", P["accent"], tex="velour_velvet", scale=3.0, sheen=0.35)
    M["pillow2"] = fabric("Linho almofada 2", P["pillow2"], scale=4.0)
    M["rug"] = fabric("Tapete la", P["rug"], tex="denim_fabric_03", scale=2.0, sheen=0.25)
    M["curtain"] = fabric("Cortina linho", "#F3EFE8", scale=3.0)
    M["led"] = solid("LED 2700K", "#FFD9A8", 0.5, emission="#FFC98A", strength=12.0)
    M["led_soft"] = solid("LED difuso", "#FFE7C8", 0.5, emission="#FFDDB0", strength=4.0)
    M["switch"] = solid("Espelho tomada", "#F4F3F0", 0.3)
    M["plant_pot"] = solid("Vaso ceramica", "#E7E1D6", 0.6)
    M["paper"] = solid("Passe-partout", "#F6F3EC", 0.8)
    M["palhinha"] = image_mat("Palhinha", os.path.join(art.OUT, "palhinha.png"), rough=0.6, alpha=True, scale=28)
    return M


# =====================================================================================
def shell(P, M):
    """Paredes da planta de contrato, pisos, tetos, esquadrias e portas."""
    w = M["wall"]
    for i, (x0, x1, y0, y1) in enumerate([(0, 2.91, 0, 7.60), (2.91, 4.21, 5.0, 7.60), (2.91, 3.0, 4.32, 5.0)]):
        box(f"Piso_{i}", x0, x1, y0, y1, -0.02, 0, M["floor"], "Piso", bevel=0)
    box("Piso_banho", 3.0, 4.21, 2.95, 5.0, -0.02, 0.0, M["bath_floor"], "Piso", bevel=0)
    for i, (x0, x1, y0, y1, z) in enumerate([(0, 2.91, 0, 7.60, H), (2.91, 4.21, 5.0, 7.60, H),
                                              (3.0, 4.21, 2.95, 5.0, 2.30)]):
        box(f"Teto_{i}", x0, x1, y0, y1, z, z + 0.05, M["ceiling"], "Teto", bevel=0)

    win = (1.00, 2.20)
    wall("Fachada", -T_EXT, 0, -T_EXT, 7.60 + T_EXT, w, [(0.64, 2.00, *win), (3.20, 4.36, *win), (5.60, 7.20, *win)])
    wall("Parede_topo", 0, 3.05, -T_EXT, 0, w)
    wall("Parede_D1_dir", 2.91, 3.05, 0, 2.81, w)
    wall("Parede_banho_topo", 2.91, 4.21 + T_EXT, 2.81, 2.95, w, [(3.30, 3.85, 1.60, 2.10)])
    wall("Parede_direita", 4.21, 4.21 + T_EXT, 2.95, 7.60 + T_EXT, w, [(5.95, 6.82, 0, DOOR_H)])
    wall("Parede_fundo", 0, 4.21, 7.60, 7.60 + T_EXT, w)
    wall("Parede_banho_esq", 2.91, 3.0, 2.95, 5.09, w, [(4.32, 5.00, 0, DOOR_H)])
    wall("Parede_banho_inf", 3.0, 4.21, 5.0, 5.09, w)
    wall("Parede_D1_D2", 0, 2.13, 2.41, 2.55, w)
    wall("Parede_D2_dir", 2.04, 2.13, 2.55, 5.06, w, [(3.68, 4.48, 0, DOOR_H)])
    wall("Parede_D2_sala", 0, 2.13, 5.06, 5.19, w)
    box("Verga_porta_D1", 2.13, 2.91, 3.56, 3.62, DOOR_H, H, w, "Paredes", bevel=0)

    # pintura do Dormitório 2 (parede média) — película sobre as 4 faces internas
    e = 0.003
    d2 = M["wall_d2"]
    wall("D2_pint_esq", 0, e, 2.55, 5.06, d2, [(3.20, 4.36, 1.0, 2.2)], coll="Paredes")
    wall("D2_pint_dir", 2.04 - e, 2.04, 2.55, 5.06, d2, [(3.68, 4.48, 0, DOOR_H)], coll="Paredes")
    box("D2_pint_topo", 0, 2.04, 2.55, 2.55 + e, 0, H, d2, "Paredes", bevel=0)
    box("D2_pint_inf", 0, 2.04, 5.06 - e, 5.06, 0, H, d2, "Paredes", bevel=0)

    # esquadrias de alumínio preto com peitoril de quartzo
    def window(name, y0, y1, sill=1.0, head=2.2, x=-T_EXT / 2):
        a = M["alum"]
        box(f"{name}_inf", x - 0.035, x + 0.035, y0, y1, sill, sill + 0.035, a, "Esquadrias")
        box(f"{name}_sup", x - 0.035, x + 0.035, y0, y1, head - 0.035, head, a, "Esquadrias")
        box(f"{name}_a", x - 0.035, x + 0.035, y0, y0 + 0.035, sill, head, a, "Esquadrias")
        box(f"{name}_b", x - 0.035, x + 0.035, y1 - 0.035, y1, sill, head, a, "Esquadrias")
        ym = (y0 + y1) / 2
        for k, (xa, xb, ya, yb) in enumerate([(x - 0.03, x - 0.005, y0 + 0.03, ym + 0.02), (x + 0.005, x + 0.03, ym - 0.02, y1 - 0.03)]):
            f = 0.03
            box(f"{name}_folha{k}_a", xa, xb, ya, ya + f, sill + 0.03, head - 0.03, a, "Esquadrias")
            box(f"{name}_folha{k}_b", xa, xb, yb - f, yb, sill + 0.03, head - 0.03, a, "Esquadrias")
            box(f"{name}_folha{k}_c", xa, xb, ya, yb, sill + 0.03, sill + 0.03 + f, a, "Esquadrias")
            box(f"{name}_folha{k}_d", xa, xb, ya, yb, head - 0.03 - f, head - 0.03, a, "Esquadrias")
        box(f"{name}_vidro1", x - 0.02, x - 0.014, y0 + 0.055, ym - 0.005, sill + 0.055, head - 0.055, M["glass"], "Esquadrias", bevel=0)
        box(f"{name}_vidro2", x + 0.014, x + 0.02, ym + 0.005, y1 - 0.055, sill + 0.055, head - 0.055, M["glass"], "Esquadrias", bevel=0)
        box(f"{name}_peitoril", -0.03, 0.025, y0 - 0.02, y1 + 0.02, sill - 0.02, sill, M["quartz"], "Esquadrias")
        area_light(f"Portal_{name}", -0.10, (y0 + y1) / 2, (sill + head) / 2, head - sill, y1 - y0, 0,
                   rot=(0, math.radians(-90), 0), portal=True)

    window("Janela_D1", 0.64, 2.00)
    window("Janela_D2", 3.20, 4.36)
    window("Janela_sala", 5.60, 7.20)
    box("Basculante_vidro", 3.34, 3.81, 2.874, 2.886, 1.62, 2.08, solid("Vidro canelado", "#FFFFFF", 0.3, transmission=1.0), "Esquadrias", bevel=0)
    box("Basculante_quadro", 3.30, 3.85, 2.86, 2.90, 1.60, 1.63, M["alum"], "Esquadrias")

    # portas: batente + guarnição 5 cm + folha + maçaneta
    def door(name, axis, a0, a1, c, t, leaf, handle):
        g = M["white"]
        for s in (-1, 1):
            if axis == "y":
                cx = c + s * (t / 2 + 0.006)
                box(f"{name}_guarn_a{s}", cx - 0.006, cx + 0.006, a0 - 0.05, a0, 0, DOOR_H + 0.05, g, "Esquadrias")
                box(f"{name}_guarn_b{s}", cx - 0.006, cx + 0.006, a1, a1 + 0.05, 0, DOOR_H + 0.05, g, "Esquadrias")
                box(f"{name}_guarn_c{s}", cx - 0.006, cx + 0.006, a0 - 0.05, a1 + 0.05, DOOR_H, DOOR_H + 0.05, g, "Esquadrias")
            else:
                cy = c + s * (t / 2 + 0.006)
                box(f"{name}_guarn_a{s}", a0 - 0.05, a0, cy - 0.006, cy + 0.006, 0, DOOR_H + 0.05, g, "Esquadrias")
                box(f"{name}_guarn_b{s}", a1, a1 + 0.05, cy - 0.006, cy + 0.006, 0, DOOR_H + 0.05, g, "Esquadrias")
                box(f"{name}_guarn_c{s}", a0 - 0.05, a1 + 0.05, cy - 0.006, cy + 0.006, DOOR_H, DOOR_H + 0.05, g, "Esquadrias")
        if axis == "y":
            box(f"{name}_bat_a", c - t / 2, c + t / 2, a0, a0 + 0.02, 0, DOOR_H, g, "Esquadrias")
            box(f"{name}_bat_b", c - t / 2, c + t / 2, a1 - 0.02, a1, 0, DOOR_H, g, "Esquadrias")
            box(f"{name}_bat_c", c - t / 2, c + t / 2, a0, a1, DOOR_H - 0.02, DOOR_H, g, "Esquadrias")
        else:
            box(f"{name}_bat_a", a0, a0 + 0.02, c - t / 2, c + t / 2, 0, DOOR_H, g, "Esquadrias")
            box(f"{name}_bat_b", a1 - 0.02, a1, c - t / 2, c + t / 2, 0, DOOR_H, g, "Esquadrias")
            box(f"{name}_bat_c", a0, a1, c - t / 2, c + t / 2, DOOR_H - 0.02, DOOR_H, g, "Esquadrias")
        box(f"{name}_folha", *leaf, 0.008, DOOR_H - 0.025, g, "Esquadrias", bevel=0.003)
        hx, hy = handle
        cyl(f"{name}_roseta", hx, hy, 1.0, 1.06, 0.025, M["metal"], "Esquadrias")
        box(f"{name}_alavanca", hx - 0.012, hx + 0.012, hy - 0.012, hy + 0.012, 1.02, 1.04, M["metal"], "Esquadrias")

    door("Porta_D1", "x", 2.13, 2.91, 3.59, 0.10, (2.16, 2.20, 2.82, 3.57), (2.21, 2.88))
    door("Porta_D2", "y", 3.68, 4.48, 2.085, T_VED, (1.30, 2.03, 4.41, 4.45), (1.36, 4.46))
    door("Porta_banho", "y", 4.32, 5.00, 2.955, T_VED, (3.01, 3.63, 4.93, 4.97), (3.56, 4.98))
    door("Porta_entrada", "y", 5.95, 6.82, 4.28, T_EXT, (4.215, 4.255, 5.97, 6.80), (4.205, 6.70))
    # soleiras de granito
    box("Soleira_banho", 2.91, 3.0, 4.32, 5.00, -0.002, 0.004, M["quartz"], "Esquadrias")

    # rodapé 7 cm na cor da parede (marcenaria recebe rodapé recuado próprio)
    rp = solid("Rodape", P["wall"], 0.5, coat=0.1)
    for (x0, x1, y0, y1) in [(0, 0.015, 0, 5.60), (0.015, 2.36, 0, 0.015), (0, 2.13, 2.395, 2.41),
                             (0, 2.04, 2.55, 2.565), (0, 2.04, 5.045, 5.06), (0.015, 2.04, 5.19, 5.205),
                             (2.13, 2.145, 3.62, 3.68), (2.13, 2.145, 4.48, 5.06), (2.895, 2.91, 3.62, 4.32),
                             (4.195, 4.21, 5.09, 5.95), (4.195, 4.21, 6.82, 6.95), (0, 0.015, 7.20, 7.60)]:
        box(f"Rodape_{x0:.2f}_{y0:.2f}", x0, x1, y0, y1, 0, 0.07, rp, "Esquadrias", bevel=0.002)


# =====================================================================================
def sala(P, M, rnd):
    wood, acc = M["wood"], M["accent"]
    # ---- Parede A (y = 7,60): ripado + rack + TV | cozinha 1,84 m | torre da geladeira
    slats = [(x, x + 0.02, 7.56, 7.60, 0.0, H) for x in [0.02 + i * 0.035 for i in range(47)] if x + 0.02 <= 1.665]
    multi_box("Sala_ripado", slats, wood, bevel=0.0015)
    box("Sala_ripado_fundo", 0.0, 1.665, 7.595, 7.60, 0, H, M["wood_dark"], bevel=0)
    box("Sala_ripado_led", 0.02, 1.64, 7.55, 7.555, H - 0.02, H - 0.012, M["led"], bevel=0)
    # rack suspenso em laca (fundo a 0,25 m do piso)
    rz0, rz1 = 0.25, 0.60
    box("Rack_caixa", 0.50, 1.665, 7.17, 7.555, rz0, rz1, acc, bevel=0.004)
    for i, (a, b) in enumerate([(0.50, 0.89), (0.89, 1.28), (1.28, 1.665)]):
        box(f"Rack_porta_{i}", a + 0.0015, b - 0.0015, 7.165, 7.17, rz0 + 0.003, rz1 - 0.04, acc, bevel=0.0015)
        box(f"Rack_cava_{i}", a + 0.0015, b - 0.0015, 7.17, 7.20, rz1 - 0.037, rz1 - 0.004, M["black"], bevel=0)
    box("Rack_led_sob", 0.52, 1.64, 7.30, 7.32, rz0 - 0.004, rz0 - 0.001, M["led_soft"], bevel=0)
    # TV 43"
    box("TV", 0.60, 1.56, 7.525, 7.555, 0.97, 1.53, M["black"], bevel=0.004)
    box("TV_tela", 0.61, 1.55, 7.522, 7.525, 0.98, 1.52, solid("Tela", "#060708", 0.06, coat=1.0), bevel=0)
    # prateleira de freijó com livros e objetos (1/3 vazio)
    box("Sala_prateleira", 0.50, 1.665, 7.30, 7.555, 1.75, 1.78, wood, bevel=0.002)
    books("Sala_livros", 0.55, 7.33, 1.78, 0.42, 0.20, rnd, [P["accent"], "#E9E2D3", P["dark"], P["second"], "#C9B79A"],
          hmin=0.17, hmax=0.25)
    multi_box("Sala_livros_deitados", [(1.05, 1.30, 7.33, 7.52, 1.78, 1.81), (1.07, 1.27, 7.34, 7.50, 1.81, 1.835)],
              solid("Livro deitado", "#E4DCCB", 0.6), bevel=0.002)
    asset("ceramic_vase_01", 1.18, 7.43, 1.835, height=0.16)
    asset("standing_picture_frame_01", 1.48, 7.45, 1.78, yaw=180, height=0.22)
    asset("ceramic_vase_02", 1.45, 7.36, rz1, height=0.14)
    # tomadas e ponto de TV
    plate("Sala_tomada_tv", 1.08, 7.555, 0.75, "-y", M["switch"])

    # cozinha: inferiores com rodapé recuado, tampo de quartzo 0,90, aéreos até o teto
    k0, k1 = 1.665, 3.51
    cy0 = 7.00
    box("Coz_rodape", k0, k1, cy0 + 0.05, 7.60, 0, 0.10, M["black"], bevel=0)
    box("Coz_caixa", k0, k1, cy0 + 0.02, 7.60, 0.10, 0.86, wood, bevel=0.002)
    mods = [(k0, 2.125), (2.125, 2.585), (2.585, 3.05), (3.05, k1)]
    for i, (a, b) in enumerate(mods):
        if i == 0:  # gaveteiro sob o cooktop
            for j, (z0, z1) in enumerate([(0.10, 0.36), (0.36, 0.62), (0.62, 0.86)]):
                box(f"Coz_gaveta_{j}", a + 0.0015, b - 0.0015, cy0, cy0 + 0.02, z0 + 0.0015, z1 - 0.035, wood, bevel=0.0015)
                box(f"Coz_gaveta_cava_{j}", a + 0.0015, b - 0.0015, cy0 + 0.005, cy0 + 0.03, z1 - 0.033, z1 - 0.003, M["black"], bevel=0)
        else:
            box(f"Coz_porta_{i}", a + 0.0015, b - 0.0015, cy0, cy0 + 0.02, 0.1015, 0.825, wood, bevel=0.0015)
            box(f"Coz_cava_{i}", a + 0.0015, b - 0.0015, cy0 + 0.005, cy0 + 0.03, 0.828, 0.858, M["black"], bevel=0)
    box("Coz_tampo", k0, k1 + 0.0, cy0 - 0.02, 7.60, 0.86, 0.90, M["quartz"], bevel=0.003)
    # cooktop de 2 bocas (indução) e cuba de embutir
    box("Coz_cooktop", 1.75, 2.05, 7.08, 7.50, 0.90, 0.906, solid("Vitroceramica", "#0B0B0C", 0.05, coat=1.0), bevel=0.003)
    for i, yy in enumerate([7.19, 7.39]):
        torus(f"Coz_boca_{i}", 1.90, yy, 0.9065, 0.075, 0.002, solid("Serigrafia", "#5A5A5A", 0.4))
    box("Coz_cuba", 2.62, 3.12, 7.10, 7.50, 0.70, 0.901, M["inox"], bevel=0.01)
    box("Coz_cuba_fundo", 2.635, 3.105, 7.115, 7.485, 0.70, 0.71, solid("Inox escuro", "#8D8D8D", 0.35, metal=1.0), bevel=0)
    # torneira gourmet (bica alta)
    cyl("Coz_torneira_base", 2.87, 7.54, 0.90, 0.96, 0.025, M["metal"])
    cyl("Coz_torneira_col", 2.87, 7.54, 0.96, 1.30, 0.012, M["metal"])
    torus("Coz_torneira_arco", 2.87, 7.43, 1.30, 0.11, 0.012, M["metal"], rot=(math.radians(90), 0, math.radians(90)))
    cyl("Coz_torneira_bico", 2.87, 7.32, 1.22, 1.30, 0.013, M["metal"])
    # azulejo 7,5 × 30 entre 0,90 e 1,55
    box("Coz_backsplash", k0, k1, 7.594, 7.60, 0.90, 1.55, M["splash"], "Paredes", bevel=0)
    # aéreos do 1,55 ao teto; 2 módulos em laca
    box("Coz_aereo_caixa", k0, k1, 7.27, 7.60, 1.55, H, wood, bevel=0.002)
    for i, (a, b) in enumerate(mods):
        mat_ = acc if i in (1, 2) else wood
        box(f"Coz_aereo_porta_{i}", a + 0.0015, b - 0.0015, 7.25, 7.27, 1.585, H - 0.003, mat_, bevel=0.0015)
        box(f"Coz_aereo_cava_{i}", a + 0.0015, b - 0.0015, 7.255, 7.28, 1.552, 1.582, M["black"], bevel=0)
    box("Coz_perfil_led", k0 + 0.02, k1 - 0.02, 7.33, 7.35, 1.545, 1.55, M["led"], bevel=0)
    box("Coz_depurador", 1.70, 2.10, 7.27, 7.55, 1.53, 1.55, M["inox"], bevel=0.002)
    # objetos de vida
    box("Coz_tabua", 3.20, 3.48, 7.53, 7.555, 0.90, 1.28, M["wood"], bevel=0.008)
    cyl("Coz_fruteira", 2.35, 7.30, 0.90, 0.97, 0.14, M["wood"], r2=0.11)
    for i, (dx, dy, c) in enumerate([(-0.04, 0.0, "#E0A53A"), (0.04, 0.02, "#C9502E"), (0.0, -0.05, "#9AB04A")]):
        sphere(f"Coz_fruta_{i}", 2.35 + dx, 7.30 + dy, 0.99, 0.038, solid(f"Fruta {i}", c, 0.4))
    for i, x in enumerate([3.30, 3.40]):
        cyl(f"Coz_pote_{i}", x, 7.42, 0.90, 1.08 + i * 0.04, 0.045, M["glass"])
        cyl(f"Coz_pote_cont_{i}", x, 7.42, 0.905, 1.0 + i * 0.03, 0.04, solid(f"Graos {i}", ["#D9C38F", "#6B4A2E"][i], 0.8))
        cyl(f"Coz_pote_tampa_{i}", x, 7.42, 1.08 + i * 0.04, 1.095 + i * 0.04, 0.047, M["wood"])
    # cafeteira italiana
    cyl("Coz_moka_base", 2.20, 7.45, 0.90, 1.00, 0.045, M["inox"], verts=8)
    cyl("Coz_moka_topo", 2.20, 7.45, 1.00, 1.10, 0.04, M["inox"], verts=8, r2=0.035)
    asset("potted_plant_04", 3.38, 7.25, 0.90, height=0.20)
    plate("Coz_tomada_1", 2.30, 7.594, 1.10, "-y", M["switch"], w=0.12, h=0.08)
    plate("Coz_tomada_2", 3.30, 7.594, 1.10, "-y", M["switch"], w=0.12, h=0.08)

    # torre da geladeira com armário até o teto
    for i, x in enumerate([3.51, 4.192]):
        box(f"Torre_lateral_{i}", x, x + 0.018, 6.93, 7.60, 0, H, wood, bevel=0.002)
    box("Torre_aereo", 3.528, 4.192, 6.95, 7.60, 1.90, H, wood, bevel=0.002)
    box("Torre_aereo_porta", 3.53, 4.19, 6.93, 6.95, 1.93, H - 0.003, wood, bevel=0.0015)
    box("Torre_aereo_cava", 3.53, 4.19, 6.935, 6.96, 1.90, 1.928, M["black"], bevel=0)
    box("Geladeira", 3.55, 4.17, 6.97, 7.57, 0.0, 1.86, M["inox"], bevel=0.015, segs=3)
    box("Geladeira_div", 3.55, 4.17, 6.965, 6.975, 1.18, 1.19, M["black"], bevel=0)
    box("Geladeira_puxador", 3.58, 3.60, 6.94, 6.965, 0.80, 1.60, M["metal"], bevel=0.005)

    # ---- Parede B (y = 5,19): sofá de 2 lugares, arte grande
    sx0, sx1, sy0, sy1 = 0.15, 1.85, 5.21, 6.06
    for i, (px, py) in enumerate([(sx0 + 0.06, sy0 + 0.06), (sx1 - 0.06, sy0 + 0.06), (sx0 + 0.06, sy1 - 0.06), (sx1 - 0.06, sy1 - 0.06)]):
        cyl(f"Sofa_pe_{i}", px, py, 0.0, 0.15, 0.012, M["metal"])
    box("Sofa_base", sx0, sx1, sy0, sy1, 0.15, 0.30, M["sofa"], bevel=0.02, segs=3)
    soft("Sofa_encosto_base", sx0, sx1, sy0, sy0 + 0.18, 0.30, 0.66, M["sofa"], round_=0.04)
    soft("Sofa_braco_e", sx0, sx0 + 0.13, sy0, sy1, 0.30, 0.60, M["sofa"], round_=0.045)
    soft("Sofa_braco_d", sx1 - 0.13, sx1, sy0, sy1, 0.30, 0.60, M["sofa"], round_=0.045)
    mid = (sx0 + sx1) / 2
    for i, (a, b) in enumerate([(sx0 + 0.135, mid - 0.003), (mid + 0.003, sx1 - 0.135)]):
        cushion(f"Sofa_assento_{i}", a, b, sy0 + 0.17, sy1 - 0.005, 0.30, 0.44, M["sofa"], puff=0.4)
        cushion(f"Sofa_encosto_{i}", a + 0.01, b - 0.01, sy0 + 0.02, sy0 + 0.22, 0.44, 0.82, M["sofa"], puff=0.45)
    # almofadas com vinco, levemente giradas
    pillow("Sofa_almofada_1", sx0 + 0.33, sy0 + 0.30, 0.63, 0.44, 0.42, 0.12, M["velvet"], tilt=-14, yaw=8)
    pillow("Sofa_almofada_2", sx0 + 0.70, sy0 + 0.29, 0.62, 0.42, 0.40, 0.12, M["pillow2"], tilt=-12, yaw=-6)
    pillow("Sofa_almofada_3", sx1 - 0.35, sy0 + 0.30, 0.60, 0.50, 0.30, 0.12, M["linen_white"], tilt=-12, yaw=4)
    # manta jogada no braço
    soft("Sofa_manta_topo", sx1 - 0.16, sx1 + 0.015, sy0 + 0.25, sy0 + 0.70, 0.60, 0.625, M["linen_acc"], round_=0.008, wrinkle=0.012)
    soft("Sofa_manta_lado", sx1 + 0.005, sx1 + 0.022, sy0 + 0.25, sy0 + 0.70, 0.18, 0.62, M["linen_acc"], round_=0.006, wrinkle=0.012)
    # tapete
    soft("Sala_tapete", 0.48, 1.72, 5.78, 6.98, 0.0, 0.012, M["rug"], round_=0.004, levels=1)
    # arte grande sobre o sofá (0,70 × 1,00)
    am = image_mat(f"Arte sala {P['label']}", os.path.join(art.OUT, f"{P['key']}_art_sala.jpg"), rough=0.7)
    picture("Sala_arte", 1.00, 5.19, 1.10, 1.00, 0.70, "+y", am, M["wood_dark"], passe=M["paper"], depth=0.03)

    # ---- Canto alemão sob a janela: banco-baú + mesa 0,60 × 0,80 + cadeira de palhinha
    bx0, bx1, by0, by1 = 0.0, 0.42, 6.12, 7.14
    box("Banco_bau", bx0 + 0.005, bx1, by0, by1, 0.06, 0.42, wood, bevel=0.002)
    box("Banco_rodape", bx0 + 0.02, bx1 - 0.04, by0 + 0.02, by1 - 0.02, 0, 0.06, M["black"], bevel=0)
    box("Banco_tampo", bx0 + 0.005, bx1, by0, by1, 0.42, 0.45, wood, bevel=0.003)
    cushion("Banco_assento", bx0 + 0.02, bx1 - 0.01, by0 + 0.01, by1 - 0.01, 0.45, 0.53, M["linen_acc"], puff=0.35)
    pillow("Banco_encosto_1", 0.09, by0 + 0.27, 0.74, 0.46, 0.42, 0.14, M["pillow2"], tilt=0, yaw=90)
    pillow("Banco_encosto_2", 0.09, by1 - 0.27, 0.73, 0.46, 0.40, 0.14, M["linen_white"], tilt=0, yaw=90)
    tx0, tx1, ty0, ty1 = 0.47, 1.07, 6.24, 7.04
    box("Mesa_tampo", tx0, tx1, ty0, ty1, 0.72, 0.75, wood, bevel=0.012, segs=4)
    box("Mesa_coluna", (tx0 + tx1) / 2 - 0.04, (tx0 + tx1) / 2 + 0.04, (ty0 + ty1) / 2 - 0.20, (ty0 + ty1) / 2 + 0.20, 0.03, 0.72, M["metal"], bevel=0.004)
    box("Mesa_base", (tx0 + tx1) / 2 - 0.20, (tx0 + tx1) / 2 + 0.20, (ty0 + ty1) / 2 - 0.30, (ty0 + ty1) / 2 + 0.30, 0.0, 0.03, M["metal"], bevel=0.004)
    chair("Cadeira_1", 1.33, 6.60, -95, M)
    # mesa posta: caneca, livro aberto, vaso com galho
    cyl("Mesa_caneca", 0.72, 6.50, 0.75, 0.84, 0.04, M["ceramic"])
    torus("Mesa_caneca_alca", 0.765, 6.50, 0.795, 0.025, 0.006, M["ceramic"], rot=(math.radians(90), 0, 0))
    box("Mesa_livro_a", 0.78, 0.98, 6.70, 6.84, 0.75, 0.765, M["paper"], bevel=0.002)
    box("Mesa_livro_b", 0.80, 0.97, 6.84, 6.98, 0.75, 0.763, M["paper"], bevel=0.002)
    asset("ceramic_vase_04", 0.62, 6.88, 0.75, height=0.22)
    # pendente sobre a mesa (base a 1,50 m)
    pend = asset("modern_ceiling_lamp_01", (tx0 + tx1) / 2, (ty0 + ty1) / 2, 1.50, width=0.38, coll="Decor")
    bpy.context.view_layer.update()
    pend.location.z = max(1.50, H - pend.dimensions.z)
    point_light("Luz_pendente", (tx0 + tx1) / 2, (ty0 + ty1) / 2, 1.55, 18, radius=0.08)
    asset("potted_plant_02", 0.20, 7.38, 0.0, height=0.85)

    # cortina de linho até o teto, recolhida na lateral
    box("Sala_trilho", 0.03, 0.08, 5.22, 7.30, H - 0.03, H - 0.005, M["black"], "Esquadrias", bevel=0.002)
    curtain("Sala_cortina", 0.06, 5.22, 5.58, 0.01, H - 0.03, M["curtain"], amp=0.04, period=0.10)

    # nicho de serviço: lava e seca + tanque, portas de correr em palhinha
    box("Lav_maquina", 2.95, 3.55, 5.12, 5.72, 0, 0.85, M["white"], bevel=0.012, segs=3)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.17, minor_radius=0.018, location=(3.25, -5.725, 0.43),
                                     rotation=(math.radians(90), 0, 0))
    ob = bpy.context.active_object
    ob.name = "Lav_porta_aro"
    ob.data.materials.append(solid("Cromo escuro", "#6B6E72", 0.2, metal=1.0))
    link(ob, "Moveis")
    cyl_ = cyl("Lav_porta_vidro", 3.25, 5.725, 0.42, 0.44, 0.16, solid("Vidro fume", "#2A2D31", 0.05, transmission=0.6))
    cyl_.rotation_euler = (math.radians(90), 0, 0)
    cyl_.location = (3.25, -5.73, 0.43)
    box("Lav_bancada", 2.93, 3.58, 5.09, 5.76, 0.87, 0.90, M["quartz"], bevel=0.003)
    box("Lav_shaft", 3.60, 4.21, 5.09, 5.28, 0, H, M["wall"], "Paredes", bevel=0)
    box("Lav_tanque_gab", 3.62, 4.19, 5.28, 5.76, 0.10, 0.85, wood, bevel=0.002)
    box("Lav_tanque", 3.60, 4.21, 5.28, 5.78, 0.85, 0.90, M["quartz"], bevel=0.003)
    box("Lav_tanque_cuba", 3.70, 4.10, 5.33, 5.70, 0.70, 0.901, M["inox"], bevel=0.01)
    box("Lav_prateleira", 2.93, 3.58, 5.09, 5.40, 1.80, 1.83, wood, bevel=0.002)
    for i, x in enumerate([3.05, 3.17, 3.29]):
        cyl(f"Lav_frasco_{i}", x, 5.25, 1.83, 1.83 + 0.14 + 0.03 * i, 0.04, solid(f"Frasco {i}", ["#E8E3D8", P["second"], "#D9CBB4"][i], 0.4))
    # portas de correr em palhinha com quadro de freijó (uma recolhida sobre a outra)
    def palhinha_door(name, x0, x1, y):
        f = 0.045
        box(f"{name}_q_e", x0, x0 + f, y, y + 0.03, 0.0, DOOR_H, wood, bevel=0.002)
        box(f"{name}_q_d", x1 - f, x1, y, y + 0.03, 0.0, DOOR_H, wood, bevel=0.002)
        box(f"{name}_q_s", x0, x1, y, y + 0.03, DOOR_H - f, DOOR_H, wood, bevel=0.002)
        box(f"{name}_q_i", x0, x1, y, y + 0.03, 0.0, 0.12, wood, bevel=0.002)
        box(f"{name}_q_m", x0, x1, y, y + 0.03, 1.00, 1.04, wood, bevel=0.002)
        box(f"{name}_tela", x0 + f, x1 - f, y + 0.013, y + 0.017, 0.12, DOOR_H - f, M["palhinha"], bevel=0)
    palhinha_door("Lav_porta_a", 3.56, 4.21, 5.80)
    palhinha_door("Lav_porta_b", 3.53, 4.18, 5.835)
    box("Lav_trilho", 2.91, 4.21, 5.79, 5.87, DOOR_H, DOOR_H + 0.04, wood, bevel=0.002)
    box("Lav_bandeira", 2.91, 4.21, 5.80, 5.83, DOOR_H + 0.04, H, wood, bevel=0.002)

    # interruptores, interfone, quadro de luz
    plate("Sala_interruptor", 4.205, 5.88, 1.10, "-x", M["switch"])
    box("Interfone", 4.19, 4.205, 5.84, 5.92, 1.35, 1.55, M["white"], "Esquadrias", bevel=0.006)
    plate("Sala_tomada_sofa", 1.95, 5.205, 0.30, "+y", M["switch"])

    # trilho eletrificado com spots (luz sobreposta)
    box("Sala_trilho_luz", 0.55, 2.55, 6.38, 6.42, H - 0.035, H - 0.003, M["black"], "Luzes", bevel=0.003)
    for i, (x, tgt) in enumerate([(0.75, (1.0, 5.20, 1.4)), (1.30, (1.08, 7.55, 1.6)), (1.95, (2.6, 7.3, 0.9)), (2.40, (3.0, 7.4, 0.9))]):
        cyl(f"Spot_corpo_{i}", x, 6.40, H - 0.17, H - 0.04, 0.03, M["black"])
        spot(f"Spot_{i}", x, 6.40, H - 0.18, tgt, 35, size_deg=38, blend=0.8)


def chair(name, cx, cy, yaw_deg, M):
    """Cadeira de freijó com assento e encosto de palhinha (0,44 × 0,46, assento a 0,45)."""
    w, d = 0.44, 0.46
    coll = "Moveis"
    lx, ly = w / 2 - 0.025, d / 2 - 0.025
    objs = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            top = 0.86 if sy < 0 else 0.43
            objs.append(cyl(f"{name}_perna_{sx}{sy}", sx * lx, sy * ly, 0.0, top, 0.016, M["wood"], r2=0.019))
    objs.append(box(f"{name}_quadro", -w / 2, w / 2, -d / 2, d / 2, 0.40, 0.44, M["wood"], coll, bevel=0.004))
    objs.append(box(f"{name}_assento", -w / 2 + 0.03, w / 2 - 0.03, -d / 2 + 0.03, d / 2 - 0.03, 0.437, 0.441, M["palhinha"], coll, bevel=0))
    objs.append(box(f"{name}_encosto", -w / 2 + 0.01, w / 2 - 0.01, -d / 2 + 0.005, -d / 2 + 0.03, 0.62, 0.84, M["wood"], coll, bevel=0.006))
    objs.append(box(f"{name}_encosto_tela", -w / 2 + 0.04, w / 2 - 0.04, -d / 2 + 0.016, -d / 2 + 0.019, 0.65, 0.81, M["palhinha"], coll, bevel=0))
    pivot = bpy.data.objects.new(name, None)
    collection(coll).objects.link(pivot)
    for o in objs:
        o.parent = pivot
    pivot.location = (cx, -cy, 0)
    pivot.rotation_euler = (0, 0, math.radians(yaw_deg))
    return pivot


# =====================================================================================
def corredor(P, M):
    """Barrado na cor-assinatura até 1,10 m com filete de freijó e galeria de quadros."""
    e = 0.003
    acc = solid("Barrado", P["accent"], 0.6)
    for name, x0, x1, segs in [("W", 2.13, 2.13 + e, [(3.62, 3.68), (4.48, 5.19)]),
                               ("E", 2.91 - e, 2.91, [(3.62, 4.32)])]:
        for i, (a, b) in enumerate(segs):
            box(f"Barrado_{name}{i}", x0, x1, a, b, 0.07, 1.10, acc, "Paredes", bevel=0)
            xf = (x1 + 0.01) if name == "W" else (x0 - 0.01)
            box(f"Filete_{name}{i}", min(x0, xf), max(x1, xf), a, b, 1.10, 1.12, M["wood"], "Paredes", bevel=0.002)
    for i, (x, y, w, h, z0, nrm, img) in enumerate([
            (2.133, 4.83, 0.40, 0.50, 1.30, "+x", "art_mod"),
            (2.907, 3.97, 0.36, 0.46, 1.32, "-x", "art_line")]):
        am = image_mat(f"Arte corredor {i} {P['label']}", os.path.join(art.OUT, f"{P['key']}_{img}.jpg"), rough=0.7)
        picture(f"Galeria_{i}", x, y, z0, w, h, nrm, am, M["wood_dark"], passe=M["paper"], depth=0.025)
    for i, y in enumerate([4.0, 4.85]):
        cyl(f"Corredor_spot_{i}", 2.52, y, H - 0.10, H - 0.002, 0.04, M["black"])
        spot(f"Spot_corredor_{i}", 2.52, y, H - 0.11, (2.52, y, 0), 20, size_deg=70, blend=0.9)
    plate("Corredor_interruptor", 2.145, 3.62 + 0.10, 1.10, "+x", M["switch"])


# =====================================================================================
def dorm1(P, M, rnd):
    wood, acc = M["wood"], M["accent"]
    # composição da cabeceira: painel de freijó + cabeceira estofada em gomos verticais
    box("D1_painel", 0.0, 2.34, 0.0, 0.02, 0.0, 1.30, wood, bevel=0.002)
    gx0, gx1 = 0.45, 1.93
    n = 6
    gw = (gx1 - gx0) / n
    for i in range(n):
        cushion(f"D1_cabeceira_gomo_{i}", gx0 + i * gw + 0.003, gx0 + (i + 1) * gw - 0.003, 0.02, 0.08, 0.40, 1.22,
                M["linen_acc"], puff=0.45)
    # criados suspensos com gaveta e LED embaixo
    for side, (a, b) in (("e", (0.04, 0.44)), ("d", (1.96, 2.33))):
        box(f"D1_criado_{side}", a, b, 0.02, 0.38, 0.42, 0.58, wood, bevel=0.002)
        box(f"D1_criado_cava_{side}", a + 0.002, b - 0.002, 0.375, 0.39, 0.545, 0.575, M["black"], bevel=0)
        box(f"D1_criado_led_{side}", a + 0.02, b - 0.02, 0.10, 0.30, 0.416, 0.42, M["led_soft"], bevel=0)
        # arandela articulada a 1,10 m
        ax = (a + b) / 2
        cyl(f"D1_arandela_base_{side}", ax, 0.025, 1.08, 1.16, 0.035, M["metal"])
        box(f"D1_arandela_braco_{side}", ax - 0.006, ax + 0.006, 0.025, 0.24, 1.115, 1.127, M["metal"], bevel=0.003)
        cyl(f"D1_arandela_cupula_{side}", ax, 0.27, 1.02, 1.13, 0.06, M["metal"], r2=0.035)
        point_light(f"Luz_arandela_{side}", ax, 0.27, 1.01, 6, radius=0.03)
    # cama box baú 1,38 × 1,88 com roupa de cama em linho
    bx0, bx1, by0, by1 = 0.50, 1.88, 0.09, 1.97
    box("D1_box", bx0, bx1, by0, by1, 0.05, 0.32, M["linen_white"], bevel=0.02, segs=3)
    box("D1_box_rodape", bx0 + 0.03, bx1 - 0.03, by0 + 0.03, by1 - 0.03, 0.0, 0.05, M["black"], bevel=0)
    soft("D1_colchao", bx0 + 0.005, bx1 - 0.005, by0 + 0.005, by1 - 0.005, 0.32, 0.55, M["linen_white"], round_=0.05)
    soft("D1_edredom", bx0 - 0.04, bx1 + 0.04, by0 + 0.62, by1 + 0.035, 0.30, 0.60, M["linen_white"], round_=0.07, wrinkle=0.018)
    soft("D1_dobra", bx0 - 0.035, bx1 + 0.035, by0 + 0.55, by0 + 0.75, 0.56, 0.635, M["linen_white"], round_=0.04, wrinkle=0.01)
    soft("D1_peseira", bx0 - 0.05, bx1 + 0.05, by1 - 0.55, by1 + 0.045, 0.32, 0.625, M["pillow2"], round_=0.03, wrinkle=0.012)
    for i, x in enumerate([bx0 + 0.36, bx1 - 0.36]):
        pillow(f"D1_travesseiro_{i}", x, by0 + 0.22, 0.62, 0.62, 0.40, 0.14, M["linen_white"], tilt=-65)
        pillow(f"D1_almofada_euro_{i}", x, by0 + 0.12, 0.80, 0.58, 0.50, 0.15, M["linen_white"], tilt=-12)
    pillow("D1_almofada_lombar", (bx0 + bx1) / 2, by0 + 0.38, 0.69, 0.48, 0.26, 0.12, M["velvet"], tilt=-20)
    # guarda-roupa de correr até o teto, freijó com puxador cava vertical
    wx0, wx1, wy0, wy1 = 2.36, 2.91, 0.0, 1.80
    box("D1_gr_caixa", wx0, wx1, wy0, wy1, 0.0, H, wood, bevel=0.002)
    box("D1_gr_rodape", wx0 - 0.002, wx0 + 0.04, wy0, wy1, 0.0, 0.08, M["black"], bevel=0)
    for i, (a, b, xo) in enumerate([(wy0 + 0.002, 0.92, wx0 - 0.02), (0.88, wy1 - 0.002, wx0 - 0.045)]):
        box(f"D1_gr_porta_{i}", xo, xo + 0.022, a, b, 0.08, H - 0.01, wood, bevel=0.0015)
        yv = b - 0.04 if i == 0 else a + 0.012
        box(f"D1_gr_cava_{i}", xo - 0.002, xo + 0.012, yv, yv + 0.028, 0.80, 1.40, M["black"], bevel=0.002)
    box("D1_gr_trilho", wx0 - 0.05, wx0, wy0, wy1, H - 0.03, H, wood, bevel=0)
    # TV na parede oposta (D1/D2)
    box("D1_TV", 0.72, 1.62, 2.38, 2.41, 1.05, 1.56, M["black"], bevel=0.004)
    # split na parede da cabeceira, acima de 2,15
    box("D1_split", 0.78, 1.60, 0.0, 0.21, 2.15, 2.44, M["white"], bevel=0.03, segs=4)
    box("D1_split_aleta", 0.80, 1.58, 0.205, 0.215, 2.17, 2.20, solid("Cinza aleta", "#D8D8D6", 0.4), bevel=0.002)
    # cortina e trilho
    box("D1_trilho", 0.03, 0.08, 0.05, 2.38, H - 0.03, H - 0.005, M["black"], "Esquadrias", bevel=0.002)
    curtain("D1_cortina", 0.06, 2.02, 2.38, 0.01, H - 0.03, M["curtain"], amp=0.035, period=0.09)
    # tapete, livros, vaso, tomadas
    soft("D1_tapete", 0.20, 2.25, 0.95, 2.36, 0.0, 0.012, M["rug"], round_=0.004, levels=1)
    multi_box("D1_livros", [(2.00, 2.24, 0.10, 0.30, 0.58, 0.605), (2.01, 2.22, 0.11, 0.28, 0.605, 0.63),
                           (2.03, 2.21, 0.12, 0.27, 0.63, 0.648)], solid("Livros criado", "#E4DCCB", 0.6), bevel=0.002)
    asset("ceramic_vase_04", 0.18, 0.20, 0.58, height=0.20)
    cyl("D1_copo", 0.33, 0.28, 0.58, 0.68, 0.032, M["glass"])
    for i, x in enumerate([0.24, 2.15]):
        plate(f"D1_tomada_{i}", x, 0.021, 0.75, "+y", M["switch"])
    plate("D1_interruptor", 2.145, 2.62, 1.10, "+x", M["switch"])


# =====================================================================================
def dorm2(P, M, rnd):
    wood = M["wood"]
    y0 = 2.55
    # daybed com 2 gavetas e 3 almofadas de encosto
    box("D2_daybed_base", 0.03, 1.95, y0 + 0.02, y0 + 0.92, 0.06, 0.32, wood, bevel=0.002)
    box("D2_daybed_rodape", 0.06, 1.92, y0 + 0.05, y0 + 0.86, 0.0, 0.06, M["black"], bevel=0)
    for i, (a, b) in enumerate([(0.03, 0.99), (0.99, 1.95)]):
        box(f"D2_gaveta_{i}", a + 0.002, b - 0.002, y0 + 0.92, y0 + 0.935, 0.07, 0.29, wood, bevel=0.0015)
        box(f"D2_gaveta_cava_{i}", a + 0.002, b - 0.002, y0 + 0.915, y0 + 0.94, 0.29, 0.315, M["black"], bevel=0)
    soft("D2_colchao", 0.04, 1.94, y0 + 0.03, y0 + 0.91, 0.32, 0.50, M["pillow2"], round_=0.04)
    soft("D2_manta", 1.20, 1.96, y0 + 0.02, y0 + 0.95, 0.30, 0.515, M["linen_acc"], round_=0.03, wrinkle=0.012)
    for i, x in enumerate([0.38, 0.95, 1.52]):
        pillow(f"D2_encosto_{i}", x, y0 + 0.13, 0.74, 0.52, 0.48, 0.16, [M["linen_white"], M["velvet"], M["linen_white"]][i], tilt=-10)
    pillow("D2_rolo", 0.12, y0 + 0.48, 0.60, 0.20, 0.20, 0.70, M["pillow2"], tilt=0)
    am = image_mat(f"Arte d2 {P['label']}", os.path.join(art.OUT, f"{P['key']}_art_mod.jpg"), rough=0.7)
    picture("D2_arte", 0.98, y0 + 0.003, 1.20, 0.55, 0.55, "+y", am, M["wood_dark"], passe=M["paper"], depth=0.025)
    # escrivaninha suspensa 1,00 × 0,55 a 0,75 m sob a janela + persiana rolô
    box("D2_mesa", 0.0, 0.55, 3.45, 4.45, 0.72, 0.75, wood, bevel=0.003)
    box("D2_mesa_gaveta", 0.03, 0.50, 3.60, 4.30, 0.62, 0.72, wood, bevel=0.002)
    box("D2_mesa_gaveta_cava", 0.50, 0.515, 3.60, 4.30, 0.69, 0.715, M["black"], bevel=0)
    asset("desk_lamp_arm_01", 0.18, 3.62, 0.75, yaw=90, height=0.55)
    box("D2_notebook", 0.12, 0.40, 3.88, 4.20, 0.75, 0.765, M["alum"], bevel=0.004)
    books("D2_livros_mesa", 0.05, 4.25, 0.75, 0.16, 0.22, rnd, ["#E9E2D3", P["accent"], P["second"]], along="y")
    chair("D2_cadeira", 0.78, 3.95, 75, M)
    box("D2_persiana_caixa", -0.02, 0.10, 3.18, 4.38, 2.22, 2.32, M["white"], "Esquadrias", bevel=0.004)
    box("D2_persiana_tela", 0.05, 0.055, 3.20, 4.36, 1.85, 2.22, solid("Tela solar", "#EDE8DE", 0.8, transmission=0.3), "Esquadrias", bevel=0)
    box("D2_persiana_barra", 0.04, 0.065, 3.20, 4.36, 1.83, 1.85, M["metal"], "Esquadrias", bevel=0.003)
    # guarda-roupa 1,00 × 0,55 em laca de acento, até o teto
    gx0, gx1, gy0, gy1 = 1.04, 2.04, 4.51, 5.06
    box("D2_gr_caixa", gx0, gx1, gy0, gy1, 0.0, H, wood, bevel=0.002)
    for i, (a, b) in enumerate([(gx0, (gx0 + gx1) / 2), ((gx0 + gx1) / 2, gx1)]):
        box(f"D2_gr_porta_{i}", a + 0.0015, b - 0.0015, gy0 - 0.02, gy0, 0.08, H - 0.005, M["accent"], bevel=0.0015)
        xc = b - 0.035 if i == 0 else a + 0.008
        box(f"D2_gr_cava_{i}", xc, xc + 0.028, gy0 - 0.025, gy0 - 0.012, 0.85, 1.35, M["black"], bevel=0.002)
    box("D2_gr_rodape", gx0, gx1, gy0 - 0.02, gy0 + 0.04, 0.0, 0.08, M["black"], bevel=0)
    # estante aberta de freijó entre a mesa e o guarda-roupa
    ex0, ex1, ey0, ey1 = 0.02, 1.02, 4.76, 5.06
    for x in (ex0, ex1 - 0.02):
        box(f"D2_estante_lat_{x:.2f}", x, x + 0.02, ey0, ey1, 0.0, 2.0, wood, bevel=0.002)
    for z in (0.0, 0.40, 0.80, 1.20, 1.60, 1.98):
        box(f"D2_estante_prat_{z}", ex0, ex1, ey0, ey1, z, z + 0.022, wood, bevel=0.002)
    for z, L in ((0.422, 0.60), (0.822, 0.38), (1.222, 0.70), (1.622, 0.45)):
        books(f"D2_estante_livros_{z}", ex0 + 0.03, ey0 + 0.04, z, L, 0.22, rnd,
              [P["accent"], "#E9E2D3", P["dark"], P["second"], "#C9B79A", "#8C5A3C"], hmin=0.20, hmax=0.30)
    asset("ceramic_vase_02", 0.85, 4.92, 0.822, height=0.17)
    asset("potted_plant_01", 0.80, 4.92, 1.222, height=0.26)
    asset("ceramic_vase_01", 0.70, 4.92, 1.622, height=0.20)
    asset("potted_plant_04", 0.80, 4.62, 0.0, height=0.45)
    # plafon
    cyl("D2_plafon", 1.0, 3.80, H - 0.06, H - 0.005, 0.15, M["white"])
    cyl("D2_plafon_difusor", 1.0, 3.80, H - 0.065, H - 0.06, 0.14, M["led_soft"])
    plate("D2_interruptor", 2.035, 4.58, 1.10, "-x", M["switch"])
    plate("D2_tomada_mesa", 0.005, 4.40, 0.30, "+x", M["switch"])


# =====================================================================================
def banho(P, M):
    # revestimento só na área molhada (box) até o forro; o resto pintado
    bz = 2.30
    e = 0.004
    box("Box_parede_fundo", 3.0, 3.88, 2.95, 2.95 + e, 0, 1.60, M["box_y"], "Paredes", bevel=0)
    box("Box_parede_fundo_b", 3.0, 3.30, 2.95, 2.95 + e, 1.60, bz, M["box_y"], "Paredes", bevel=0)
    box("Box_parede_fundo_c", 3.85, 3.88, 2.95, 2.95 + e, 1.60, bz, M["box_y"], "Paredes", bevel=0)
    box("Box_parede_fundo_d", 3.30, 3.85, 2.95, 2.95 + e, 2.10, bz, M["box_y"], "Paredes", bevel=0)
    box("Box_parede_esq", 3.0, 3.0 + e, 2.95, 3.85, 0, bz, M["box_x"], "Paredes", bevel=0)
    box("Box_shaft", 3.88, 4.21, 2.95, 3.30, 0, bz, M["box_x"], "Paredes", bevel=0)
    box("Box_shaft_frente", 3.88, 4.21, 3.30 - e, 3.30, 0, bz, M["box_y"], "Paredes", bevel=0)
    box("Box_piso", 3.0, 3.88, 2.95, 3.85, 0.0, 0.004, M["bath_floor"], bevel=0)
    box("Box_ralo", 3.10, 3.78, 3.70, 3.76, 0.004, 0.006, M["inox"], bevel=0)
    # vidro incolor do piso ao forro, perfil fino
    box("Box_vidro_fixo", 3.0, 3.47, 3.845, 3.853, 0.0, bz, M["glass"], bevel=0)
    box("Box_vidro_correr", 3.42, 3.88, 3.862, 3.870, 0.0, bz - 0.04, M["glass"], bevel=0)
    box("Box_perfil", 3.0, 3.88, 3.84, 3.875, bz - 0.03, bz, M["metal"], bevel=0.002)
    box("Box_puxador", 3.45, 3.47, 3.873, 3.89, 0.9, 1.3, M["metal"], bevel=0.004)
    # chuveiro de teto quadrado e misturador
    box("Box_chuveiro", 3.32, 3.56, 3.28, 3.52, bz - 0.012, bz, M["metal"], bevel=0.003)
    cyl("Box_misturador", 3.44, 2.955, 1.05, 1.07, 0.035, M["metal"])
    cyl("Box_misturador_alav", 3.44, 2.975, 1.06, 1.065, 0.006, M["metal"])
    # prateleira de quartzo + frascos
    box("Box_prateleira", 3.004, 3.12, 3.10, 3.70, 1.15, 1.17, M["quartz"], bevel=0.002)
    for i, (y, h, c) in enumerate([(3.20, 0.20, "#EDE9E2"), (3.30, 0.17, P["second"]), (3.42, 0.14, "#3B3836")]):
        cyl(f"Box_frasco_{i}", 3.06, y, 1.17, 1.17 + h, 0.032, solid(f"Frasco box {i}", c, 0.3))
    # vaso sanitário com caixa acoplada (linhas retas suaves)
    vx, vy = 3.92, 4.08
    soft("Vaso_base", vx - 0.20, 4.20, vy - 0.18, vy + 0.18, 0.0, 0.40, M["ceramic"], round_=0.06, levels=2)
    soft("Vaso_assento", vx - 0.28, 4.05, vy - 0.18, vy + 0.18, 0.40, 0.43, M["ceramic"], round_=0.012, levels=1)
    soft("Vaso_caixa", 4.04, 4.20, vy - 0.18, vy + 0.18, 0.43, 0.80, M["ceramic"], round_=0.03, levels=1)
    box("Vaso_botao", 4.10, 4.14, vy - 0.03, vy + 0.03, 0.80, 0.806, M["metal"], bevel=0.003)
    # bancada suspensa 0,60 × 0,45 de freijó + cuba de apoio + espelho com LED traseiro
    by0, by1 = 4.38, 4.98
    box("Gabinete", 3.76, 4.21, by0, by1, 0.65, 0.87, M["wood"], bevel=0.002)
    box("Gabinete_cava", 3.745, 3.765, by0 + 0.003, by1 - 0.003, 0.84, 0.865, M["black"], bevel=0)
    box("Bancada_banho", 3.74, 4.21, by0 - 0.01, by1 + 0.01, 0.87, 0.89, M["quartz"], bevel=0.002)
    soft("Cuba_apoio", 3.86, 4.12, by0 + 0.12, by1 - 0.12, 0.89, 1.02, M["ceramic"], round_=0.06, levels=2)
    box("Cuba_interior", 3.88, 4.10, by0 + 0.14, by1 - 0.14, 0.95, 1.021, solid("Louca interior", "#E9E8E4", 0.05, coat=0.6), bevel=0.04, segs=4)
    cyl("Torneira_parede", 4.19, (by0 + by1) / 2, 1.12, 1.15, 0.022, M["metal"])
    box("Torneira_bica", 4.03, 4.20, (by0 + by1) / 2 - 0.009, (by0 + by1) / 2 + 0.009, 1.125, 1.142, M["metal"], bevel=0.004)
    box("Espelho", 4.185, 4.205, by0 + 0.0, by1 - 0.0, 1.20, 2.05, M["mirror"], bevel=0.02, segs=4)
    box("Espelho_led", 4.205, 4.209, by0 + 0.03, by1 - 0.03, 1.23, 2.02, M["led_soft"], bevel=0)
    point_light("Luz_espelho", 4.17, (by0 + by1) / 2, 1.62, 8, radius=0.25)
    # toalhas, papel, planta
    cyl("Toalheiro", 3.02, 4.08, 1.38, 1.41, 0.012, M["metal"])
    soft("Toalha_rosto", 3.012, 3.045, 3.96, 4.20, 0.98, 1.40, M["pillow2"], round_=0.01, wrinkle=0.006)
    cyl("Papeleira", 4.19, 3.86, 0.70, 0.71, 0.02, M["metal"])
    cyl("Papel", 4.13, 3.86, 0.65, 0.75, 0.055, M["paper"]).rotation_euler = (math.radians(90), 0, 0)
    asset("potted_plant_04", 4.12, by0 + 0.06, 0.89, height=0.16)
    box("Saboneteira", 3.80, 3.86, by1 - 0.10, by1 - 0.04, 0.89, 1.02, solid("Vidro ambar", "#7A4A23", 0.1, transmission=0.6), bevel=0.01)
    plate("Banho_interruptor", 2.905, 4.25, 1.10, "-x", M["switch"])
    # luz: plafon embutido no forro
    cyl("Banho_spot", 3.55, 4.20, 2.295, 2.30, 0.05, M["led_soft"])


# =====================================================================================
def lights(P):
    world_hdri(0.9, rot=200)
    # paisagem luminosa do lado de fora: só a câmera e reflexos a veem (não ilumina a cena)
    ext = box("Exterior", -6.0, -5.95, -4, 12, -2, 6, solid("Exterior", "#FFFFFF", 1.0, emission="#E9EEF2", strength=2.2), "Luzes", bevel=0)
    for attr in ("visible_diffuse", "visible_shadow", "visible_volume_scatter"):
        setattr(ext, attr, False)
    # sol de fim de tarde entrando pela fachada (luz viajando para +x)
    sun_dir((1.0, -0.35, -0.42), energy=3.2, color=(1.0, 0.86, 0.70))
    for name, (x, y, z, sx, sy, w) in {
        "Sala": (1.2, 6.40, H - 0.01, 1.8, 1.2, 18),
        "Cozinha": (2.6, 7.0, H - 0.01, 1.4, 0.5, 10),
        "D1": (1.2, 1.2, H - 0.01, 1.6, 1.6, 12),
        "D2": (1.0, 3.8, H - 0.07, 1.0, 1.0, 10),
        "Corredor": (2.52, 4.4, H - 0.01, 0.5, 1.2, 6),
        "Banho": (3.55, 4.1, 2.29, 0.8, 1.0, 14),
        "Servico": (3.55, 5.45, H - 0.01, 1.0, 0.5, 6),
    }.items():
        area_light(f"Luz_{name}", x, y, z, sx, sy, w).visible_camera = False


# =====================================================================================
VIEWS = {
    # nome: (posição, alvo, lente, resolução)
    "sala":      ((3.95, 6.62, 1.22), (0.40, 5.95, 1.05), 20, (1920, 1280)),
    "estar":     ((2.08, 5.42, 1.18), (2.08, 7.60, 1.15), 18, (1920, 1280)),
    "cozinha":   ((0.62, 5.80, 1.25), (3.70, 7.25, 1.20), 20, (1920, 1280)),
    "corredor":  ((2.50, 6.75, 1.25), (2.50, 2.60, 1.20), 22, (1280, 1600)),
    "dorm1":     ((2.25, 2.32, 1.22), (0.55, 0.30, 0.95), 20, (1920, 1280)),
    "dorm1_b":   ((0.28, 2.28, 1.22), (2.30, 0.60, 1.15), 20, (1920, 1280)),
    "dorm2":     ((1.92, 4.38, 1.22), (0.25, 3.05, 1.00), 18, (1920, 1280)),
    "banho":     ((3.05, 4.88, 1.30), (3.95, 3.30, 1.20), 16, (1280, 1600)),
    "isometrica": None,
    "planta": None,
}


def render_view(view, out, samples, P):
    sc = bpy.context.scene
    top = view in ("planta", "isometrica")
    COLL["Teto"].hide_render = top
    if "Luzes" in COLL:
        for o in COLL["Luzes"].objects:
            if o.type == "LIGHT" and o.data.type == "AREA" and o.name.startswith("Luz_"):
                o.hide_render = top
    if top:
        bg = sc.world.node_tree.nodes["Background"]
        for l in list(bg.inputs["Color"].links):
            sc.world.node_tree.links.remove(l)
        bg.inputs["Color"].default_value = rgba("#F3F1EC")
        bg.inputs["Strength"].default_value = 1.0
        bpy.data.objects["Exterior"].hide_render = True
    if view == "planta":
        render_settings((1100, 1900), samples)
        cd = bpy.data.cameras.new("Cam")
        cd.type = "ORTHO"
        cd.ortho_scale = 8.3
        cam = bpy.data.objects.new("Cam", cd)
        sc.collection.objects.link(cam)
        cam.location = (2.1, -3.8, 12)
        sc.camera = cam
    elif view == "isometrica":
        render_settings((1800, 1800), samples)
        cd = bpy.data.cameras.new("Cam")
        cd.lens = 46
        cam = bpy.data.objects.new("Cam", cd)
        sc.collection.objects.link(cam)
        cam.location = (7.8, -10.6, 9.0)
        from mathutils import Vector as V
        cam.rotation_euler = (V((2.0, -3.7, 0.6)) - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.camera = cam
    else:
        pos, tgt, lens, res = VIEWS[view]
        render_settings(res, samples, exposure=0.15)
        photo_camera(pos, tgt, lens)
        cam = sc.camera
        cam.data.dof.use_dof = False
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)


def build(key):
    reset()
    P = dict(PALETTES[key], key=key)
    art.make_all({key: P}) if not os.path.exists(os.path.join(art.OUT, f"{key}_art_sala.jpg")) else None
    if not os.path.exists(os.path.join(art.OUT, "palhinha.png")):
        art.palhinha()
    M = materials(P)
    rnd = random.Random(7)
    shell(P, M)
    sala(P, M, rnd)
    corredor(P, M)
    dorm1(P, M, rnd)
    dorm2(P, M, rnd)
    banho(P, M)
    lights(P)
    return P


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--palette", default="terra")
    ap.add_argument("--views", default="")
    ap.add_argument("--samples", type=int, default=256)
    ap.add_argument("--export", default="")
    ap.add_argument("--out", default="renders2")
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    views = list(VIEWS) if args.views == "all" else [v for v in args.views.split(",") if v]
    for v in views:
        P = build(args.palette)
        out = os.path.join(ROOT, args.out, args.palette, f"{v}.jpg")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        render_view(v, out, args.samples, P)
        print("OK", out, flush=True)
    if args.export:
        import build as v1
        build(args.palette)
        v1.export(os.path.join(ROOT, "modelo2", args.palette, f"ares_ipiranga_final01_{args.palette}"),
                  args.export.split(","))
        print("EXPORT OK", args.palette, flush=True)
