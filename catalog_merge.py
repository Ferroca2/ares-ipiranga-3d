"""Junta os catálogos da base e de cada opção de jantar em catalog.json, na ordem de catalog_items."""
import json, os
import catalog_items

R = os.path.dirname(os.path.abspath(__file__))


def merge():
    cat = []
    for f in ["catalog_base.json", "catalog_rebativel.json", "catalog_bancada.json", "catalog_centro.json"]:
        if os.path.exists(os.path.join(R, f)):
            ids = {x["id"] for x in cat}
            cat += [c for c in json.load(open(os.path.join(R, f))) if c["id"] not in ids]
    order = [i[0] for i in catalog_items.ITEMS]
    cat.sort(key=lambda c: order.index(c["id"]) if c["id"] in order else 999)
    json.dump(cat, open(os.path.join(R, "catalog.json"), "w"), ensure_ascii=False, indent=1)
    return cat
