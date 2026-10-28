"""Junta a pesquisa de compras (um JSON por grupo) em compras.json, que o site lê.

Cada peça: {"variantes": {chave: [opções]}, "paletas": {paleta: chave}, "dica": "…"}. Chaves "<id>:<parte>"
dividem uma peça em partes (cuba e torneira, box e colchão…). Links que o checador marcou como quebrados saem.

uso: python compras_merge.py <pasta com os JSONs> [--check checagem.json]
"""
import json, os, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PALS = ["terra", "mata", "moderno", "ipe", "ebano"]

# acabamentos que não são peças do modelo: cor de cada paleta (hex do build2.PALETTES) e onde vão
ACABAMENTOS = [
    ("tinta_parede", "Tinta das paredes", "Apartamento todo", "wall"),
    ("tinta_d2", "Tinta do Dormitório 2", "Dormitório 2", "wall_d2"),
    ("tinta_acento", "Cor de acento", "Barrado e lacas da marcenaria", "accent"),
    ("piso_vinilico", "Piso vinílico carvalho", "Sala e dormitórios", "floor"),
    ("porcelanato_banho", "Porcelanato 60 × 60 efeito cimento", "Banho", "bath_floor"),
    ("azulejo_box", "Azulejo 7,5 × 30 do box", "Banho", "box_tile"),
    ("azulejo_cozinha", "Azulejo 7,5 × 30 da cozinha", "Cozinha", "backsplash"),
    ("tapete_sala", "Tapete da sala", "Sala", "rug"),
    ("tapete_quarto", "Tapete do quarto", "Dormitório 1", "rug"),
    ("cortina", "Cortina de linho", "Sala e Dormitório 1", None),
]
HEX = {
    "wall": ["#F2EDE4", "#F4F1EA", "#F5F3EE", "#EFE6D4", "#F2EFE9"],
    "wall_d2": ["#EADBCB", "#CDD3C1", "#DDE3EC", "#DDB29C", "#D8D1C5"],
    "accent": ["#B5583A", "#4F5B3E", "#1F4E8C", "#C99A2E", "#9C6B43"],
    "floor": ["#D2BC9F", "#D8C7AA", "#CDB596", "#CBB08E", "#D6C3A5"],
    "bath_floor": ["#CFCAC2", "#D3D0C8", "#C4C0B8", "#D8CDBE", "#CBC7C0"],
    "box_tile": ["#EEE9E0", "#A9B49B", "#F2F1EC", "#D9A68F", "#ECE8E1"],
    "backsplash": ["#F3EFE8", "#E8ECE0", "#1F4E8C", "#F1E9D8", "#EAE5DC"],
    "rug": ["#CDBFA8", "#B8B49E", "#D6D1C6", "#E2D2B2", "#C9BBA5"],
}
# prestadores que valem para toda peça de marcenaria, e os específicos de algumas
EXTRA = {"cabeceira": ["estofador"], "portas_lav": ["palhinha"]}

FIELDS = ["loja", "produto", "marca", "cor", "medidas", "preco", "nota", "avaliacoes", "url", "verificado", "obs"]


def merge(src, check=None):
    bad = set()
    if check and os.path.exists(check):
        bad = {u for u, r in json.load(open(check)).items() if r.get("ok") is False}
    out, dropped = {}, []
    for f in sorted(os.listdir(src), key=lambda f: (f == "lacunas.json", f)):
        if not f.endswith(".json") or f.startswith("_"):
            continue
        for key, it in json.load(open(os.path.join(src, f))).items():
            var = {}
            for k, ops in (it.get("variantes") or {}).items():
                keep = []
                for o in ops:
                    if not o.get("url") or o["url"] in bad:
                        dropped.append((key, k, o.get("url")))
                        continue
                    keep.append({x: o.get(x) for x in FIELDS if o.get(x) not in (None, "")})
                if keep:
                    var[k] = keep
            if not var:
                continue
            pals = it.get("paletas") or {}
            if "*" in var:
                pals = {p: pals.get(p, "*") for p in PALS}
            # a segunda rodada (lacunas) acrescenta opções às variantes que já existem
            prev = out.setdefault(key, {"variantes": {}, "paletas": {}, "dica": ""})
            for k, ops in var.items():
                have = {o["url"] for o in prev["variantes"].get(k, [])}
                prev["variantes"].setdefault(k, []).extend(o for o in ops if o["url"] not in have)
                if f == "lacunas.json":
                    prev["variantes"][k].sort(key=lambda o: (o.get("preco") is None, o.get("preco") or 0))
            prev["paletas"].update({p: v for p, v in pals.items() if v in prev["variantes"]})
            prev["dica"] = prev["dica"] or it.get("dica") or ""
    fin = [dict(id=i, nome=n, onde=w, hex=dict(zip(PALS, HEX[h])) if h else None) for i, n, w, h in ACABAMENTOS]
    data = {"itens": out, "acabamentos": fin, "extra": EXTRA}
    json.dump(data, open(os.path.join(ROOT, "compras.json"), "w"), ensure_ascii=False, indent=1)
    return data, dropped


if __name__ == "__main__":
    a = sys.argv[1:]
    data, dropped = merge(a[0], a[a.index("--check") + 1] if "--check" in a else None)
    n = sum(len(o) for it in data["itens"].values() for o in it["variantes"].values())
    print(f"compras.json: {len(data['itens'])} peças, {n} links; {len(dropped)} removidos")
    for d in dropped:
        print("  fora:", *d)
