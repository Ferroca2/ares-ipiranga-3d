"""Monta site/index.html a partir de index2.html + paletas + visualizador."""
import json, os, re
S = os.path.join(os.path.dirname(os.path.abspath(__file__)), "site")
page = open(os.path.join(S, "index2.html")).read()
pal = json.load(open(os.path.join(S, "palettes2.json")))
viewer = open(os.path.join(S, "viewer.js")).read().replace("`models/${p}.json`", "`models2/${p}.json`")
page = page.replace("__PALETTES__", json.dumps(pal, ensure_ascii=False)).replace("__VIEWER__", viewer)
open(os.path.join(S, "index.html"), "w").write(page)
print("index.html", len(page))
