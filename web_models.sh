#!/bin/zsh
# GLBs do visualizador: base sem o jantar + uma peça por opção de jantar, em cada paleta
cd "$(dirname "$0")"
PY=.venv/bin/python
for p in terra mata moderno ipe ebano; do
  cat_flag=(); [[ $p == terra ]] && cat_flag=(--catalog --catalog-out catalog_base.json)
  $PY light_glb.py $p --part base --out modelo2/$p/web/base.glb $cat_flag 2>&1 | grep -E "LIGHT|CATALOG|rror:"
  for o in bancada rebativel rebativel_fechada centro; do
    cf=(); [[ $p == terra && $o != rebativel_fechada ]] && cf=(--catalog --variant $o --catalog-out catalog_$o.json)
    $PY light_glb.py $p --blend modelo2/$p/jantar_$o.blend --part dining --out modelo2/$p/web/$o.glb $cf 2>&1 | grep -E "LIGHT|CATALOG|rror:"
  done
done
echo WEB MODELS DONE
