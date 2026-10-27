"""Modelagem paramétrica do apto Ares Ipiranga (final 01/08 - 31,22 m²).

Coordenadas de planta: x para a direita, y para BAIXO (como no desenho),
origem na face interna do canto superior esquerdo do Dormitório 1. Metros.
No Blender: X = x, Y = -y, Z para cima.

Uso:
  python build.py --palette terracota --views all --export
"""
import argparse
import math
import os
import sys

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.abspath(__file__))
H = 2.50          # pé-direito
DOOR_H = 2.10
T_EXT = 0.14      # alvenaria estrutural
T_VED = 0.09      # parede de vedação

# ---------------------------------------------------------------- paletas
PALETTES = {
    "terracota": dict(
        label="Terracota", wall="#EEE9E2", accent_sala="#B8613F", accent_d1="#D9CFC3", accent_d2="#C9D3DD",
        floor="#BDB9B3", sofa="#ECE8E1", rug_sala="#A9502F", rug_d1="#6E6A66", wood="#C8A272",
        cabinet="#F2F0EC", throw_d1="#A9502F", throw_d2="#173E73", bedding="#F4F2EF", pillow="#9C9893",
        chair="#3D3B39", accent_obj="#2F6B3A", bath_tile="#E9E6E1", bath_accent="#CFC7BC", counter="#E4E1DC",
    ),
    "nordico": dict(
        label="Nórdico", wall="#F5F3EF", accent_sala="#A9B5A0", accent_d1="#E3DDD2", accent_d2="#B9C4B0",
        floor="#D9D3C8", sofa="#C9C5BE", rug_sala="#E2D6C2", rug_d1="#D8CFC0", wood="#DDC29C",
        cabinet="#FAFAF8", throw_d1="#D2A44B", throw_d2="#8FA084", bedding="#FBFAF7", pillow="#C7C1B6",
        chair="#E8E3DA", accent_obj="#6D8A5C", bath_tile="#F2F1EE", bath_accent="#B9C4B0", counter="#F0EEEA",
    ),
    "grafite": dict(
        label="Grafite & Nogueira", wall="#E4E2DE", accent_sala="#3A3C3F", accent_d1="#4A4C50", accent_d2="#5B6168",
        floor="#8F8C87", sofa="#4B4D52", rug_sala="#2E2F31", rug_d1="#3B3C3E", wood="#6E4B32",
        cabinet="#3B3C3F", throw_d1="#C8932E", throw_d2="#C8932E", bedding="#E8E6E2", pillow="#5A5C60",
        chair="#1F1F20", accent_obj="#C8932E", bath_tile="#D8D6D2", bath_accent="#3F4145", counter="#2B2C2E",
    ),
    "petroleo": dict(
        label="Azul Petróleo", wall="#EFEBE5", accent_sala="#1F4E5A", accent_d1="#2C5B66", accent_d2="#D9B48F",
        floor="#C4B9A9", sofa="#CDBFA8", rug_sala="#B8653E", rug_d1="#C9BBA6", wood="#A87B52",
        cabinet="#E9E4DC", throw_d1="#B8653E", throw_d2="#1F4E5A", bedding="#F3EFE9", pillow="#1F4E5A",
        chair="#7A5A40", accent_obj="#1F4E5A", bath_tile="#ECE8E2", bath_accent="#1F4E5A", counter="#D8D2C8",
    ),
}


def hex2rgba(h, a=1.0):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    # sRGB -> linear
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return (*c, a)


# ---------------------------------------------------------------- materiais
MATS = {}


def mat(name, color, rough=0.6, metal=0.0, transmission=0.0, emission=None, emission_strength=0.0,
        texture=None, alpha=1.0, ior=1.45):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    rgba = hex2rgba(color) if isinstance(color, str) else color
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Transmission Weight"].default_value = transmission
    bsdf.inputs["IOR"].default_value = ior
    if alpha < 1:
        bsdf.inputs["Alpha"].default_value = alpha
    if emission:
        bsdf.inputs["Emission Color"].default_value = hex2rgba(emission)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    m.diffuse_color = rgba
    m["flat_color"] = list(rgba)
    if texture:
        texture(nt, bsdf, rgba)
    MATS[name] = m
    return m


def _darker(rgba, f):
    return (rgba[0] * f, rgba[1] * f, rgba[2] * f, 1)


def tex_tiles(size_x, size_y, grout="#9A968F"):
    def f(nt, bsdf, rgba):
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        br = nt.nodes.new("ShaderNodeTexBrick")
        br.offset = 0.0
        br.squash = 1.0
        br.inputs["Scale"].default_value = 1.0
        br.inputs["Brick Width"].default_value = size_x
        br.inputs["Row Height"].default_value = size_y
        br.inputs["Mortar Size"].default_value = 0.0025
        br.inputs["Mortar Smooth"].default_value = 0.2
        br.inputs["Bias"].default_value = 0.0
        br.inputs["Color1"].default_value = rgba
        br.inputs["Color2"].default_value = _darker(rgba, 0.97)
        br.inputs["Mortar"].default_value = hex2rgba(grout)
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], br.inputs["Vector"])
        nt.links.new(br.outputs["Color"], bsdf.inputs["Base Color"])
    return f


def tex_wood(scale=2.5):
    def f(nt, bsdf, rgba):
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (scale, scale * 18, scale)
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 3.0
        nz.inputs["Detail"].default_value = 6.0
        nz.inputs["Distortion"].default_value = 1.5
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = _darker(rgba, 0.78)
        ramp.color_ramp.elements[1].color = _darker(rgba, 1.08)
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
        nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    return f


def tex_fabric():
    def f(nt, bsdf, rgba):
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 400.0
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.15
        nt.links.new(nz.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        bsdf.inputs["Sheen Weight"].default_value = 0.3
    return f


# ---------------------------------------------------------------- geometria
COLL = {}


def collection(name):
    if name not in COLL:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
        COLL[name] = c
    return COLL[name]


def _link(obj, coll):
    collection(coll).objects.link(obj)
    return obj


def box(name, x0, x1, y0, y1, z0, z1, material, coll="Moveis", bevel=0.0, segs=2):
    """Caixa alinhada em coordenadas de planta (y para baixo)."""
    X0, X1 = min(x0, x1), max(x0, x1)
    Y0, Y1 = -max(y0, y1), -min(y0, y1)
    v = [(X0, Y0, z0), (X1, Y0, z0), (X1, Y1, z0), (X0, Y1, z0),
         (X0, Y0, z1), (X1, Y0, z1), (X1, Y1, z1), (X0, Y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], f)
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob.data.materials.append(material)
    if bevel > 0:
        md = ob.modifiers.new("Bevel", "BEVEL")
        md.width = min(bevel, (X1 - X0) / 2.01, (Y1 - Y0) / 2.01, (z1 - z0) / 2.01)
        md.segments = segs
        md.limit_method = "NONE"
    return _link(ob, coll)


def cyl(name, cx, cy, z0, z1, r, material, coll="Moveis", verts=48, bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=z1 - z0,
                                        location=(cx, -cy, (z0 + z1) / 2))
    ob = bpy.context.active_object
    ob.name = name
    for c in ob.users_collection:
        c.objects.unlink(ob)
    ob.data.materials.append(material)
    if bevel > 0:
        md = ob.modifiers.new("Bevel", "BEVEL")
        md.width = bevel
        md.segments = 3
        md.limit_method = "ANGLE"
    for p in ob.data.polygons:
        p.use_smooth = True
    return _link(ob, coll)


def sphere(name, cx, cy, cz, r, material, coll="Moveis", scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=r, location=(cx, -cy, cz))
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = scale
    for c in ob.users_collection:
        c.objects.unlink(ob)
    ob.data.materials.append(material)
    for p in ob.data.polygons:
        p.use_smooth = True
    return _link(ob, coll)


def wall(name, x0, x1, y0, y1, material, openings=(), coll="Paredes", z0=0.0, z1=H):
    """Parede retangular; aberturas = (ini, fim, peitoril, verga) ao longo do eixo maior."""
    along_x = (x1 - x0) >= (y1 - y0)
    a0, a1 = (x0, x1) if along_x else (y0, y1)

    def piece(i, b0, b1, za, zb):
        if b1 - b0 < 1e-4 or zb - za < 1e-4:
            return
        if along_x:
            box(f"{name}_{i}", b0, b1, y0, y1, za, zb, material, coll)
        else:
            box(f"{name}_{i}", x0, x1, b0, b1, za, zb, material, coll)

    cur = a0
    i = 0
    for (s, e, sill, head) in sorted(openings):
        piece(i, cur, s, z0, z1); i += 1
        piece(i, s, e, z0, sill); i += 1
        piece(i, s, e, head, z1); i += 1
        cur = e
    piece(i, cur, a1, z0, z1)


# ---------------------------------------------------------------- cena
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    MATS.clear()
    COLL.clear()


def build(P):
    reset()
    sc = bpy.context.scene

    # materiais
    m_wall = mat("Parede", P["wall"], 0.85)
    m_acc_sala = mat("Parede destaque sala", P["accent_sala"], 0.85)
    m_acc_d1 = mat("Parede destaque dorm1", P["accent_d1"], 0.85)
    m_acc_d2 = mat("Parede destaque dorm2", P["accent_d2"], 0.85)
    m_ceiling = mat("Teto", "#FAFAF8", 0.9)
    m_floor = mat("Porcelanato 60x60", P["floor"], 0.35, texture=tex_tiles(0.6, 0.6))
    m_bath_floor = mat("Piso banheiro", P["bath_tile"], 0.4, texture=tex_tiles(0.3, 0.3))
    m_bath_wall = mat("Revestimento banheiro", P["bath_tile"], 0.25, texture=tex_tiles(0.3, 0.6, "#B5B1AA"))
    m_bath_acc = mat("Revestimento box", P["bath_accent"], 0.25, texture=tex_tiles(0.1, 0.3, "#A7A39C"))
    m_white = mat("Laca branca", "#F3F2EF", 0.4)
    m_cab = mat("Marcenaria", P["cabinet"], 0.45)
    m_wood = mat("Madeira", P["wood"], 0.5, texture=tex_wood())
    m_counter = mat("Bancada", P["counter"], 0.2)
    m_sofa = mat("Tecido sofa", P["sofa"], 0.9, texture=tex_fabric())
    m_rug_sala = mat("Tapete sala", P["rug_sala"], 0.95, texture=tex_fabric())
    m_rug_d1 = mat("Tapete dorm1", P["rug_d1"], 0.95, texture=tex_fabric())
    m_bed = mat("Roupa de cama", P["bedding"], 0.85, texture=tex_fabric())
    m_throw1 = mat("Manta dorm1", P["throw_d1"], 0.9, texture=tex_fabric())
    m_throw2 = mat("Manta dorm2", P["throw_d2"], 0.9, texture=tex_fabric())
    m_pillow = mat("Almofadas", P["pillow"], 0.9, texture=tex_fabric())
    m_chair = mat("Cadeira", P["chair"], 0.6)
    m_accent = mat("Objeto destaque", P["accent_obj"], 0.5)
    m_black = mat("Preto", "#111111", 0.3)
    m_screen = mat("Tela TV", "#050505", 0.08)
    m_glass_black = mat("Vidro preto", "#0A0A0A", 0.05)
    m_steel = mat("Inox", "#C8C8C8", 0.25, metal=1.0)
    m_chrome = mat("Cromado", "#E0E0E0", 0.08, metal=1.0)
    m_alum = mat("Aluminio", "#2A2A2A", 0.35, metal=0.8)
    m_glass = mat("Vidro", "#FFFFFF", 0.0, transmission=1.0, ior=1.5)
    m_ceramic = mat("Louca", "#F8F8F6", 0.12)
    m_mirror = mat("Espelho", "#FFFFFF", 0.0, metal=1.0)
    m_plant = mat("Folhagem", "#3E6B35", 0.6)
    m_pot = mat("Vaso", "#D8D2C8", 0.7)
    m_lamp = mat("Luminaria", "#FFF4E0", 0.5, emission="#FFE2B8", emission_strength=6.0)
    m_curtain = mat("Cortina", "#F1EEE8", 0.9, transmission=0.0, texture=tex_fabric())

    # ------------------------------------------------ pisos e tetos
    for i, (x0, x1, y0, y1) in enumerate([(0, 2.91, 0, 7.60), (2.91, 4.21, 5.0, 7.60)]):
        box(f"Piso_{i}", x0, x1, y0, y1, -0.02, 0, m_floor, "Piso")
    box("Piso_banho", 3.0, 4.21, 2.95, 5.0, -0.02, 0.0, m_bath_floor, "Piso")
    box("Piso_soleira", 2.91, 3.0, 4.32, 5.0, -0.02, 0, m_floor, "Piso")
    for i, (x0, x1, y0, y1, z) in enumerate([(0, 2.91, 0, 7.60, H), (2.91, 4.21, 5.0, 7.60, H),
                                              (2.91, 4.21, 2.95, 5.0, 2.30)]):
        box(f"Teto_{i}", x0, x1, y0, y1, z, z + 0.05, m_ceiling, "Teto")
    # sanca de gesso ao longo da parede da entrada (cozinha)
    box("Sanca_cozinha", 3.95, 4.21, 5.09, 7.60, 2.30, H, m_ceiling, "Teto")

    # ------------------------------------------------ paredes (cotas do contrato)
    win = 1.00, 2.20
    wall("Fachada", -T_EXT, 0, -T_EXT, 7.60 + T_EXT, m_wall,
         [(0.64, 2.00, *win), (3.20, 4.36, *win), (5.60, 7.20, *win)])
    wall("Parede_topo", 0, 3.05, -T_EXT, 0, m_wall)
    wall("Parede_D1_dir", 2.91, 3.05, 0, 2.81, m_wall)
    wall("Parede_banho_topo", 2.91, 4.21 + T_EXT, 2.81, 2.95, m_wall, [(3.30, 3.85, 1.60, 2.10)])
    wall("Parede_direita", 4.21, 4.21 + T_EXT, 2.95, 7.60 + T_EXT, m_wall, [(5.95, 6.82, 0, DOOR_H)])
    wall("Parede_fundo", 0, 4.21, 7.60, 7.60 + T_EXT, m_wall)
    wall("Parede_banho_esq", 2.91, 3.0, 2.95, 5.09, m_wall, [(4.32, 5.00, 0, DOOR_H)])
    wall("Parede_banho_inf", 3.0, 4.21, 5.0, 5.09, m_wall)
    wall("Parede_D1_D2", 0, 2.13, 2.41, 2.55, m_wall)
    wall("Parede_D2_dir", 2.04, 2.13, 2.55, 5.06, m_wall, [(3.68, 4.48, 0, DOOR_H)])
    wall("Parede_D2_sala", 0, 2.13, 5.06, 5.19, m_wall)
    box("Verga_porta_D1", 2.13, 2.91, 3.56, 3.62, DOOR_H, H, m_wall, "Paredes")

    # pintura de destaque (película de 5 mm sobre a parede)
    e = 0.005
    box("Destaque_sala_TV", 0, 2.04, 5.19, 5.19 + e, 0, H, m_acc_sala, "Paredes")
    box("Destaque_D1_cabeceira", 0, 2.91, 0, e, 0, H, m_acc_d1, "Paredes")
    box("Destaque_D2_cama", 0, 2.04, 2.55, 2.55 + e, 0, H, m_acc_d2, "Paredes")

    # revestimento do banheiro (até o forro)
    bz = 2.30
    box("Rev_banho_dir", 4.21 - e, 4.21, 3.85, 5.0, 0, bz, m_bath_wall, "Paredes")
    box("Rev_banho_inf", 3.0, 4.21, 5.0 - e, 5.0, 0, bz, m_bath_wall, "Paredes")
    box("Rev_banho_esq_a", 3.0, 3.0 + e, 3.85, 4.32, 0, bz, m_bath_wall, "Paredes")
    box("Rev_box_topo_a", 3.0, 3.30, 2.95, 2.95 + e, 0, bz, m_bath_acc, "Paredes")
    box("Rev_box_topo_b", 3.30, 3.85, 2.95, 2.95 + e, 0, 1.60, m_bath_acc, "Paredes")
    box("Rev_box_topo_c", 3.30, 3.85, 2.95, 2.95 + e, 2.10, bz, m_bath_acc, "Paredes")
    box("Rev_box_esq", 3.0, 3.0 + e, 2.95, 3.85, 0, bz, m_bath_acc, "Paredes")
    # shaft (prumada) no canto do box
    box("Shaft_banho", 3.88, 4.21, 2.95, 3.30, 0, bz, m_bath_acc, "Paredes")

    # ------------------------------------------------ esquadrias
    def window(name, y0, y1, sill=1.0, head=2.2, x=-T_EXT / 2):
        box(f"{name}_caixilho_inf", x - 0.04, x + 0.04, y0, y1, sill, sill + 0.04, m_alum, "Esquadrias")
        box(f"{name}_caixilho_sup", x - 0.04, x + 0.04, y0, y1, head - 0.04, head, m_alum, "Esquadrias")
        box(f"{name}_caixilho_a", x - 0.04, x + 0.04, y0, y0 + 0.04, sill, head, m_alum, "Esquadrias")
        box(f"{name}_caixilho_b", x - 0.04, x + 0.04, y1 - 0.04, y1, sill, head, m_alum, "Esquadrias")
        ym = (y0 + y1) / 2
        box(f"{name}_montante", x - 0.03, x + 0.03, ym - 0.02, ym + 0.02, sill, head, m_alum, "Esquadrias")
        box(f"{name}_vidro", x - 0.006, x + 0.006, y0 + 0.04, y1 - 0.04, sill + 0.04, head - 0.04, m_glass, "Esquadrias")
        box(f"{name}_peitoril", -0.02, 0.03, y0, y1, sill - 0.02, sill, m_counter, "Esquadrias")

    window("Janela_D1", 0.64, 2.00)
    window("Janela_D2", 3.20, 4.36)
    window("Janela_sala", 5.60, 7.20)
    # basculante do banheiro
    box("Basculante_vidro", 3.34, 3.81, 2.874, 2.886, 1.62, 2.08, mat("Vidro canelado", "#FFFFFF", 0.35, transmission=1.0), "Esquadrias")
    box("Basculante_quadro", 3.30, 3.85, 2.86, 2.90, 1.60, 1.62, m_alum, "Esquadrias")

    def door_frame(name, axis, a0, a1, c, t):
        if axis == "y":
            box(f"{name}_batente_a", c - t / 2 - 0.01, c + t / 2 + 0.01, a0, a0 + 0.04, 0, DOOR_H, m_white, "Esquadrias")
            box(f"{name}_batente_b", c - t / 2 - 0.01, c + t / 2 + 0.01, a1 - 0.04, a1, 0, DOOR_H, m_white, "Esquadrias")
            box(f"{name}_batente_c", c - t / 2 - 0.01, c + t / 2 + 0.01, a0, a1, DOOR_H - 0.04, DOOR_H, m_white, "Esquadrias")
        else:
            box(f"{name}_batente_a", a0, a0 + 0.04, c - t / 2 - 0.01, c + t / 2 + 0.01, 0, DOOR_H, m_white, "Esquadrias")
            box(f"{name}_batente_b", a1 - 0.04, a1, c - t / 2 - 0.01, c + t / 2 + 0.01, 0, DOOR_H, m_white, "Esquadrias")
            box(f"{name}_batente_c", a0, a1, c - t / 2 - 0.01, c + t / 2 + 0.01, DOOR_H - 0.04, DOOR_H, m_white, "Esquadrias")

    # Dorm 1: porta no corredor, aberta para dentro do quarto
    door_frame("Porta_D1", "x", 2.13, 2.91, 3.59, 0.06)
    box("Porta_D1_folha", 2.17, 2.21, 2.85, 3.57, 0, DOOR_H - 0.04, m_white, "Esquadrias")
    # Dorm 2: aberta para dentro do quarto
    door_frame("Porta_D2", "y", 3.68, 4.48, 2.085, T_VED)
    box("Porta_D2_folha", 1.30, 2.04, 4.40, 4.44, 0, DOOR_H - 0.04, m_white, "Esquadrias")
    # Banho
    door_frame("Porta_banho", "y", 4.32, 5.00, 2.955, T_VED)
    box("Porta_banho_folha", 3.0, 3.62, 4.92, 4.96, 0, DOOR_H - 0.04, m_white, "Esquadrias")
    # Entrada (fechada)
    door_frame("Porta_entrada", "y", 5.95, 6.82, 4.28, T_EXT)
    box("Porta_entrada_folha", 4.23, 4.27, 5.99, 6.78, 0, DOOR_H - 0.04, m_white, "Esquadrias")
    cyl("Macaneta_entrada", 4.20, 6.68, 1.0, 1.02, 0.02, m_chrome, "Esquadrias")

    # rodapé
    for (x0, x1, y0, y1) in [(0, 2.91, 0, 0.012), (0, 0.012, 0, 7.60), (0, 4.21, 7.588, 7.60),
                             (4.198, 4.21, 5.09, 5.95), (4.198, 4.21, 6.82, 7.60)]:
        box(f"Rodape_{x0}_{y0}", x0, x1, y0, y1, 0, 0.07, m_white, "Esquadrias")

    # ------------------------------------------------ DORMITÓRIO 1
    box("D1_tapete", 0.25, 2.25, 0.55, 2.30, 0, 0.012, m_rug_d1)
    bx0, bx1 = 0.56, 1.94           # cama casal 1,38 x 1,88
    box("D1_cabeceira", bx0 - 0.06, bx1 + 0.06, 0.0, 0.06, 0, 1.10, m_wood, bevel=0.01)
    box("D1_cama_base", bx0, bx1, 0.06, 1.96, 0.05, 0.32, m_white, bevel=0.01)
    box("D1_colchao", bx0 + 0.01, bx1 - 0.01, 0.07, 1.95, 0.32, 0.55, m_bed, bevel=0.04, segs=3)
    box("D1_edredom", bx0 - 0.03, bx1 + 0.03, 0.62, 1.99, 0.40, 0.60, m_bed, bevel=0.05, segs=3)
    box("D1_manta", bx0 - 0.04, bx1 + 0.04, 1.42, 1.80, 0.42, 0.615, m_throw1, bevel=0.03, segs=3)
    for i, px in enumerate([bx0 + 0.06, (bx0 + bx1) / 2 + 0.02]):
        box(f"D1_travesseiro_{i}", px, px + 0.62, 0.10, 0.48, 0.55, 0.70, m_bed, bevel=0.06, segs=3)
    box("D1_almofada", (bx0 + bx1) / 2 - 0.25, (bx0 + bx1) / 2 + 0.25, 0.42, 0.58, 0.58, 0.82, m_throw1, bevel=0.05, segs=3)
    box("D1_criado", 0.03, 0.45, 0.02, 0.42, 0, 0.55, m_wood, bevel=0.01)
    cyl("D1_abajur_base", 0.24, 0.22, 0.55, 0.85, 0.03, m_black)
    cyl("D1_abajur_cupula", 0.24, 0.22, 0.80, 1.0, 0.12, m_lamp)
    # guarda-roupa de correr 0,55 de profundidade
    box("D1_guarda_roupa", 2.36, 2.91, 0.02, 1.80, 0, 2.30, m_cab, bevel=0.005)
    for i, ys in enumerate([0.02, 0.61, 1.20]):
        box(f"D1_gr_porta_{i}", 2.345, 2.36, ys + 0.005, ys + 0.585, 0.02, 2.28, m_cab if i != 1 else m_mirror, bevel=0.003)
        box(f"D1_gr_puxador_{i}", 2.335, 2.345, ys + 0.03, ys + 0.05, 0.9, 1.4, m_alum)
    # TV na parede D1/D2
    box("D1_TV", 0.85, 1.83, 2.375, 2.41, 1.05, 1.62, m_screen, bevel=0.003)
    box("D1_painel", 0.60, 2.08, 2.38, 2.41, 0, 0.30, m_wood, bevel=0.005)
    # ar condicionado split
    box("D1_split", 0.55, 1.45, 0.0, 0.22, 2.12, 2.42, m_white, bevel=0.03, segs=3)
    # cortina
    box("D1_cortina", 0.03, 0.08, 0.45, 2.20, 0.05, 2.42, m_curtain, coll="Esquadrias", bevel=0.02)

    # ------------------------------------------------ DORMITÓRIO 2
    y_top = 2.55
    box("D2_cabeceira", 0.0, 0.05, y_top, y_top + 0.95, 0, 0.85, m_wood)
    box("D2_cama_base", 0.05, 1.95, y_top + 0.02, y_top + 0.92, 0.05, 0.30, m_white, bevel=0.01)
    box("D2_colchao", 0.06, 1.94, y_top + 0.03, y_top + 0.91, 0.30, 0.52, m_bed, bevel=0.04, segs=3)
    box("D2_edredom", 0.55, 1.97, y_top + 0.01, y_top + 0.95, 0.38, 0.57, m_bed, bevel=0.05, segs=3)
    box("D2_manta", 1.25, 1.98, y_top + 0.0, y_top + 0.96, 0.40, 0.585, m_throw2, bevel=0.04, segs=3)
    box("D2_travesseiro", 0.10, 0.48, y_top + 0.12, y_top + 0.78, 0.52, 0.66, m_bed, bevel=0.06, segs=3)
    box("D2_almofada", 0.40, 0.56, y_top + 0.30, y_top + 0.62, 0.55, 0.78, m_throw2, bevel=0.05, segs=3)
    # escrivaninha sob a janela
    box("D2_mesa", 0.0, 0.50, 3.62, 4.42, 0.73, 0.76, m_wood, bevel=0.005)
    box("D2_mesa_gaveteiro", 0.02, 0.48, 4.02, 4.40, 0.0, 0.73, m_cab, bevel=0.005)
    box("D2_mesa_perna", 0.02, 0.48, 3.64, 3.67, 0.0, 0.73, m_cab)
    box("D2_notebook", 0.10, 0.40, 3.80, 4.05, 0.76, 0.78, m_alum, bevel=0.004)
    box("D2_notebook_tela", 0.10, 0.12, 3.80, 4.05, 0.78, 0.98, m_alum, bevel=0.003)
    cyl("D2_cadeira_assento", 0.78, 3.95, 0.42, 0.48, 0.22, m_chair, bevel=0.02)
    box("D2_cadeira_encosto", 0.98, 1.03, 3.78, 4.12, 0.48, 0.88, m_chair, bevel=0.02, segs=3)
    cyl("D2_cadeira_pe", 0.78, 3.95, 0.05, 0.42, 0.025, m_black)
    cyl("D2_cadeira_base", 0.78, 3.95, 0.02, 0.06, 0.24, m_black)
    # guarda-roupa ao longo da parede da sala
    box("D2_guarda_roupa", 0.42, 2.04, 4.53, 5.06, 0, 2.30, m_cab, bevel=0.005)
    for i, ys in enumerate([0.42, 0.96, 1.50]):
        box(f"D2_gr_porta_{i}", ys + 0.005, ys + 0.535, 4.515, 4.53, 0.02, 2.28, m_cab, bevel=0.003)
        box(f"D2_gr_puxador_{i}", ys + 0.03, ys + 0.05, 4.505, 4.515, 0.9, 1.4, m_alum)
    box("D2_nicho", 0.0, 0.42, 4.53, 5.06, 0, 2.30, m_wood, bevel=0.005)
    for z in (0.5, 1.0, 1.5):
        box(f"D2_livros_{z}", 0.05, 0.37, 4.60, 4.95, z + 0.02, z + 0.24, m_accent)
    box("D2_cortina", 0.03, 0.08, 3.05, 3.50, 0.9, 2.42, m_curtain, coll="Esquadrias", bevel=0.02)
    box("D2_quadro", 0.6, 1.4, 2.555, 2.575, 1.20, 1.75, m_throw2, bevel=0.004)

    # ------------------------------------------------ BANHEIRO
    box("Banho_box_piso", 3.0, 3.88, 2.95, 3.85, 0, 0.005, m_bath_acc)
    box("Banho_vidro_fixo", 3.0, 3.48, 3.84, 3.86, 0.0, 1.95, m_glass)
    box("Banho_vidro_correr", 3.40, 3.88, 3.865, 3.885, 0.0, 1.95, m_glass)
    box("Banho_trilho", 3.0, 3.88, 3.835, 3.89, 1.95, 1.97, m_chrome)
    cyl("Banho_chuveiro", 3.44, 3.06, 2.05, 2.08, 0.11, m_chrome)
    box("Banho_chuveiro_haste", 3.42, 3.46, 2.955, 3.06, 2.06, 2.08, m_chrome)
    box("Banho_registro", 3.40, 3.48, 2.955, 2.98, 1.05, 1.13, m_chrome)
    # vaso
    box("Banho_caixa", 4.02, 4.20, 3.90, 4.30, 0.40, 0.82, m_ceramic, bevel=0.03, segs=3)
    sphere("Banho_vaso", 3.82, 4.10, 0.30, 0.20, m_ceramic, scale=(1.35, 1.0, 0.75))
    cyl("Banho_vaso_pe", 3.90, 4.10, 0.0, 0.30, 0.13, m_ceramic)
    # cuba e gabinete
    box("Banho_gabinete", 3.75, 4.21, 4.42, 4.98, 0.30, 0.82, m_cab, bevel=0.005)
    box("Banho_bancada", 3.73, 4.21, 4.40, 4.99, 0.82, 0.85, m_counter, bevel=0.003)
    box("Banho_cuba", 3.82, 4.14, 4.52, 4.88, 0.85, 0.97, m_ceramic, bevel=0.03, segs=3)
    box("Banho_torneira", 4.14, 4.18, 4.68, 4.72, 0.85, 1.05, m_chrome)
    box("Banho_espelho", 4.19, 4.205, 4.45, 4.95, 1.05, 1.85, m_mirror)
    box("Banho_toalha", 3.02, 3.05, 4.00, 4.22, 1.05, 1.45, m_throw2, bevel=0.01)

    # ------------------------------------------------ ÁREA DE SERVIÇO (nicho junto ao banho)
    box("Lav_maquina", 2.96, 3.55, 5.12, 5.72, 0, 0.85, m_white, bevel=0.01)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.20, depth=0.02, location=(3.255, -5.73, 0.45),
                                        rotation=(math.pi / 2, 0, 0))
    ob = bpy.context.active_object
    ob.name = "Lav_maquina_porta"
    for c in ob.users_collection:
        c.objects.unlink(ob)
    ob.data.materials.append(m_glass_black)
    _link(ob, "Moveis")
    box("Lav_bancada", 2.93, 3.58, 5.09, 5.76, 0.88, 0.91, m_counter, bevel=0.003)
    box("Lav_shaft", 3.60, 4.21, 5.09, 5.28, 0, H, m_wall, "Paredes")
    box("Lav_tanque_gab", 3.62, 4.19, 5.28, 5.78, 0, 0.85, m_cab, bevel=0.005)
    box("Lav_tanque", 3.62, 4.19, 5.28, 5.80, 0.85, 0.90, m_counter, bevel=0.003)
    box("Lav_tanque_cuba", 3.70, 4.10, 5.34, 5.70, 0.86, 0.905, m_steel)
    box("Lav_torneira", 3.88, 3.92, 5.28, 5.40, 0.90, 1.12, m_chrome)
    box("Lav_armario_sup", 2.93, 3.58, 5.09, 5.44, 1.55, 2.30, m_cab, bevel=0.005)

    # ------------------------------------------------ COZINHA (parede do fundo)
    cy0, cy1 = 7.00, 7.60
    box("Coz_gabinete", 1.62, 3.42, cy0 + 0.03, cy1, 0.10, 0.88, m_cab, bevel=0.004)
    box("Coz_rodape", 1.62, 3.42, cy0 + 0.08, cy1, 0.0, 0.10, m_black)
    box("Coz_bancada", 1.60, 3.44, cy0, cy1, 0.88, 0.92, m_counter, bevel=0.003)
    for i, xs in enumerate([1.62, 2.07, 2.52, 2.97]):
        box(f"Coz_porta_{i}", xs + 0.004, xs + 0.446, cy0 + 0.015, cy0 + 0.03, 0.12, 0.86, m_cab, bevel=0.003)
        box(f"Coz_puxador_{i}", xs + 0.15, xs + 0.30, cy0 + 0.005, cy0 + 0.015, 0.82, 0.84, m_alum)
    box("Coz_cooktop", 1.70, 2.30, cy0 + 0.06, cy1 - 0.04, 0.92, 0.93, m_glass_black, bevel=0.004)
    for i, (dx, dy, r) in enumerate([(0.15, 0.15, 0.08), (0.45, 0.15, 0.06), (0.15, 0.40, 0.06), (0.45, 0.40, 0.08)]):
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.006, location=(1.70 + dx, -(cy0 + 0.06 + dy), 0.935))
        ob = bpy.context.active_object
        ob.name = f"Coz_boca_{i}"
        for c in ob.users_collection:
            c.objects.unlink(ob)
        ob.data.materials.append(m_alum)
        _link(ob, "Moveis")
    box("Coz_cuba", 2.62, 3.12, cy0 + 0.10, cy1 - 0.08, 0.72, 0.921, m_steel)
    box("Coz_torneira", 2.85, 2.89, cy1 - 0.08, cy1 - 0.04, 0.92, 1.25, m_chrome)
    box("Coz_torneira_bico", 2.85, 2.89, cy1 - 0.30, cy1 - 0.04, 1.21, 1.25, m_chrome)
    box("Coz_revest", 1.60, 3.44, cy1 - 0.006, cy1, 0.92, 1.55, m_bath_acc, "Paredes")
    box("Coz_armario_sup", 2.20, 3.44, cy1 - 0.35, cy1, 1.55, 2.25, m_cab, bevel=0.005)
    box("Coz_coifa", 1.72, 2.28, cy1 - 0.40, cy1, 1.60, 1.72, m_steel, bevel=0.005)
    box("Coz_led", 2.22, 3.42, cy1 - 0.33, cy1 - 0.30, 1.545, 1.55, m_lamp)
    # geladeira
    box("Coz_geladeira", 3.52, 4.18, 6.93, 7.58, 0.0, 1.85, m_steel, bevel=0.02, segs=3)
    box("Coz_gel_puxador", 3.56, 3.58, 6.91, 6.93, 1.0, 1.6, m_alum)
    box("Coz_gel_div", 3.52, 4.18, 6.925, 6.935, 1.20, 1.21, m_black)
    box("Coz_microondas", 3.58, 4.10, 7.18, 7.56, 1.85, 2.13, m_black, bevel=0.01)
    # utensílios
    cyl("Coz_fruteira", 3.25, 7.25, 0.92, 0.98, 0.13, m_wood)
    for i, (dx, dy) in enumerate([(-0.05, 0), (0.05, 0.03), (0, -0.05)]):
        sphere(f"Coz_fruta_{i}", 3.25 + dx, 7.25 + dy, 1.0, 0.04, m_accent)

    # ------------------------------------------------ SALA
    # sofá em L (chaise junto à janela)
    sz = 0.0
    box("Sala_sofa_base", 0.02, 1.52, 6.82, 7.58, 0.06, 0.42, m_sofa, bevel=0.03, segs=3)
    box("Sala_chaise_base", 0.02, 0.80, 6.10, 6.82, 0.06, 0.42, m_sofa, bevel=0.03, segs=3)
    box("Sala_sofa_encosto", 0.02, 1.52, 7.36, 7.58, 0.42, 0.85, m_sofa, bevel=0.05, segs=3)
    box("Sala_sofa_braco", 1.36, 1.52, 6.82, 7.36, 0.42, 0.62, m_sofa, bevel=0.05, segs=3)
    box("Sala_chaise_encosto", 0.02, 0.20, 6.10, 7.36, 0.42, 0.78, m_sofa, bevel=0.05, segs=3)
    box("Sala_assento_1", 0.20, 0.80, 6.12, 7.36, 0.42, 0.55, m_sofa, bevel=0.05, segs=3)
    box("Sala_assento_2", 0.80, 1.36, 6.84, 7.36, 0.42, 0.55, m_sofa, bevel=0.05, segs=3)
    box("Sala_almofada_1", 0.25, 0.70, 7.18, 7.35, 0.55, 0.95, m_pillow, bevel=0.06, segs=3)
    box("Sala_almofada_2", 0.85, 1.25, 7.18, 7.35, 0.55, 0.92, m_throw1, bevel=0.06, segs=3)
    for i, (px, py) in enumerate([(0.06, 6.15), (1.46, 6.86), (0.06, 7.52), (1.46, 7.52), (0.76, 6.15)]):
        cyl(f"Sala_sofa_pe_{i}", px, py, 0.0, 0.06, 0.02, m_black)
    # tapete orgânico
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.75, depth=0.012, location=(0.95, -6.25, 0.006))
    ob = bpy.context.active_object
    ob.name = "Sala_tapete"
    ob.scale = (1.0, 0.75, 1)
    for c in ob.users_collection:
        c.objects.unlink(ob)
    ob.data.materials.append(m_rug_sala)
    _link(ob, "Moveis")
    # rack + TV na parede do Dorm 2
    box("Sala_rack", 0.05, 1.40, 5.19, 5.59, 0.10, 0.55, m_wood, bevel=0.006)
    box("Sala_rack_gaveta", 0.75, 1.40, 5.585, 5.595, 0.14, 0.51, m_cab, bevel=0.003)
    for i, px in enumerate([0.15, 1.30]):
        box(f"Sala_rack_pe_{i}", px - 0.02, px + 0.02, 5.25, 5.53, 0, 0.10, m_black)
    box("Sala_TV", 0.40, 1.50, 5.195, 5.23, 1.05, 1.68, m_screen, bevel=0.003)
    cyl("Sala_vaso_planta", 0.22, 5.38, 0.55, 0.75, 0.08, m_pot)
    for i, (dx, dy, dz) in enumerate([(0, 0, 0.88), (0.06, 0.04, 0.82), (-0.05, 0.03, 0.80)]):
        sphere(f"Sala_folhagem_{i}", 0.22 + dx, 5.38 + dy, dz, 0.12, m_plant, scale=(1, 1, 1.4))
    box("Sala_livros", 1.00, 1.25, 5.30, 5.48, 0.55, 0.63, m_accent, bevel=0.004)
    # mesa redonda + banquetas
    tx, ty = 1.75, 6.15
    cyl("Sala_mesa_tampo", tx, ty, 0.73, 0.76, 0.37, m_wood, bevel=0.006)
    cyl("Sala_mesa_coluna", tx, ty, 0.03, 0.73, 0.05, m_black)
    cyl("Sala_mesa_base", tx, ty, 0.0, 0.03, 0.22, m_black)
    for i, ang in enumerate([200, 290, 60]):
        sx = tx + 0.52 * math.cos(math.radians(ang))
        sy = ty + 0.52 * math.sin(math.radians(ang))
        cyl(f"Sala_banqueta_{i}", sx, sy, 0.42, 0.46, 0.17, m_wood, bevel=0.01)
        cyl(f"Sala_banqueta_pe_{i}", sx, sy, 0.0, 0.42, 0.025, m_black)
    # pendente sobre a mesa
    cyl("Sala_pendente_fio", tx, ty, 1.80, H, 0.004, m_black)
    sphere("Sala_pendente", tx, ty, 1.72, 0.14, m_lamp, scale=(1, 1, 0.7))
    # planta de chão no canto da entrada
    cyl("Sala_vaso_chao", 0.15, 5.80, 0, 0.35, 0.13, m_pot)
    sphere("Sala_planta_chao", 0.15, 5.80, 0.75, 0.25, m_plant, scale=(0.9, 0.9, 1.6))
    box("Sala_cortina", 0.03, 0.08, 5.40, 5.70, 0.05, 2.42, m_curtain, coll="Esquadrias", bevel=0.02)
    box("Sala_quadro", 1.55, 1.95, 5.195, 5.215, 1.15, 1.65, m_accent, bevel=0.003)

    # ------------------------------------------------ iluminação
    world = bpy.data.worlds.new("Mundo")
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = hex2rgba("#DCE6F2")
    bg.inputs["Strength"].default_value = 1.2

    sun_d = bpy.data.lights.new("Sol", "SUN")
    sun_d.energy = 3.0
    sun_d.angle = math.radians(3)
    sun_d.color = (1.0, 0.95, 0.88)
    sun = bpy.data.objects.new("Sol", sun_d)
    sun.rotation_euler = (math.radians(55), 0, math.radians(-70))
    _link(sun, "Luzes")

    # plano luminoso do lado de fora das janelas (céu difuso)
    sky = box("Ceu_externo", -3.0, -2.95, -2, 10, -1, 5, mat("Ceu", "#FFFFFF", 1.0, emission="#E8EEF5", emission_strength=1.6), "Luzes")
    sky.visible_shadow = False

    for name, (x, y, sx, sy, w, z) in {
        "D1": (1.35, 1.25, 1.2, 1.2, 70, H - 0.02),
        "D2": (1.0, 3.8, 0.9, 0.9, 50, H - 0.02),
        "Sala": (1.2, 6.4, 1.4, 1.2, 90, H - 0.02),
        "Cozinha": (2.9, 6.6, 1.0, 1.0, 60, H - 0.02),
        "Corredor": (2.5, 4.5, 0.5, 0.8, 25, H - 0.02),
        "Banho": (3.6, 4.0, 0.7, 0.9, 45, 2.28),
    }.items():
        ld = bpy.data.lights.new(f"Luz_{name}", "AREA")
        ld.energy = w
        ld.shape = "RECTANGLE"
        ld.size, ld.size_y = sx, sy
        ld.color = (1.0, 0.90, 0.78)
        lo = bpy.data.objects.new(f"Luz_{name}", ld)
        lo.location = (x, -y, z)
        _link(lo, "Luzes")

    return sc


# ---------------------------------------------------------------- câmeras
VIEWS = {
    # nome: (posição xyz em planta, alvo xyz, lente mm, resolução)
    "sala":     ((3.30, 6.80, 1.55), (0.5, 5.9, 0.80), 15, (1600, 1066)),
    "cozinha":  ((0.55, 5.75, 1.60), (3.3, 7.2, 0.9), 15, (1600, 1066)),
    "dorm1":    ((2.22, 2.28, 1.65), (0.5, 0.5, 0.70), 13, (1600, 1066)),
    "dorm1_b":  ((0.30, 2.25, 1.60), (2.6, 0.7, 1.00), 14, (1600, 1066)),
    "dorm2":    ((1.95, 4.35, 1.55), (0.2, 3.1, 0.70), 14, (1600, 1066)),
    "banho":    ((3.05, 4.85, 1.65), (4.0, 3.3, 0.95), 12, (1066, 1600)),
    "isometrica": ((7.8, 10.6, 9.0), (2.0, 3.7, 0.6), 46, (1600, 1600)),
    "planta":   None,
}


def look_at(cam, target):
    d = Vector(target) - cam.location
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def setup_render(samples):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    try:
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        sc.cycles.device = "GPU"
    except Exception as ex:  # noqa
        print("GPU indisponível, usando CPU:", ex)
        sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 8
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Base Contrast"
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 88


def render_view(view, out_path, samples):
    sc = bpy.context.scene
    setup_render(samples)
    cam_d = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    top = view in ("planta", "isometrica")
    COLL["Teto"].hide_render = top
    if top:
        # abre a vista superior: céu claro e sol por cima
        bpy.data.objects["Ceu_externo"].hide_render = True
        bpy.data.objects["Sol"].rotation_euler = (math.radians(25), math.radians(10), math.radians(-40))
        sc.world.node_tree.nodes["Background"].inputs["Color"].default_value = hex2rgba("#FFFFFF")
        sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
    if view == "planta":
        cam_d.type = "ORTHO"
        cam_d.ortho_scale = 8.3
        cam.location = (2.1, -3.8, 12)
        cam.rotation_euler = (0, 0, 0)
        sc.render.resolution_x, sc.render.resolution_y = 1100, 1900
        sc.render.film_transparent = False
    else:
        pos, tgt, lens, res = VIEWS[view]
        cam_d.lens = lens
        cam_d.clip_start = 0.05
        cam.location = (pos[0], -pos[1], pos[2])
        look_at(cam, (tgt[0], -tgt[1], tgt[2]))
        sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam)


# ---------------------------------------------------------------- exportação
def flatten_materials():
    """Troca texturas procedurais por cor sólida para formatos de troca (glTF/FBX/OBJ)."""
    for m in bpy.data.materials:
        if not m.use_nodes:
            continue
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        if not bsdf:
            continue
        for inp in ("Base Color", "Normal"):
            for l in list(bsdf.inputs[inp].links):
                m.node_tree.links.remove(l)
        if "flat_color" in m:
            bsdf.inputs["Base Color"].default_value = tuple(m["flat_color"])


def apply_modifiers():
    for ob in bpy.data.objects:
        if ob.type != "MESH" or not ob.modifiers:
            continue
        dg = bpy.context.evaluated_depsgraph_get()
        ev = ob.evaluated_get(dg)
        me = bpy.data.meshes.new_from_object(ev)
        ob.modifiers.clear()
        ob.data = me


def export(base, fmts):
    os.makedirs(os.path.dirname(base), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=base + ".blend")
    for o in ("Ceu_externo",):
        if o in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[o])
    apply_modifiers()
    flatten_materials()
    if "glb" in fmts:
        bpy.ops.export_scene.gltf(filepath=base + ".glb", export_format="GLB", export_apply=True,
                                  export_lights=False, export_cameras=False)
    if "fbx" in fmts:
        bpy.ops.export_scene.fbx(filepath=base + ".fbx", apply_unit_scale=True, object_types={"MESH"})
    if "obj" in fmts:
        bpy.ops.wm.obj_export(filepath=base + ".obj", export_materials=True, forward_axis="NEGATIVE_Z", up_axis="Y")
    if "dae" in fmts and hasattr(bpy.ops.wm, "collada_export"):
        try:
            bpy.ops.wm.collada_export(filepath=base + ".dae")
        except Exception as ex:  # noqa
            print("Collada indisponível:", ex)
    if "stl" in fmts:
        bpy.ops.wm.stl_export(filepath=base + ".stl")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--palette", default="terracota")
    ap.add_argument("--views", default="")
    ap.add_argument("--samples", type=int, default=96)
    ap.add_argument("--export", default="")
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])

    P = PALETTES[args.palette]
    views = list(VIEWS) if args.views == "all" else [v for v in args.views.split(",") if v]
    for v in views:
        build(P)
        out = os.path.join(ROOT, "renders", args.palette, f"{v}.jpg")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        render_view(v, out, args.samples)
        print("OK", out)
    if args.export:
        build(P)
        export(os.path.join(ROOT, "modelo", args.palette, f"ares_ipiranga_final01_{args.palette}"),
               args.export.split(","))
        print("EXPORT OK", args.palette)
