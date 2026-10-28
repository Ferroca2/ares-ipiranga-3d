#!/bin/zsh
# refaz o tom da luz da Terra (base) com o piso mínimo, sem recalcular: reaproveita o .npy
cd ~/ares-ipiranga-3d
until grep -q "LUZ DONE" fila_luz.log 2>/dev/null; do sleep 60; done
sleep 120
cp web_tex/terra/lightmap_base_base.npy web_tex/terra/lm_terra_base.npy
.venv/bin/python light_glb.py terra --part base --out modelo2/terra/web/base.glb --lightmap --lm-size 1024 --lm-from web_tex/terra/lm_terra_base.npy > logs/lm_terra_base_retone.log 2>&1
echo "terra base retone ok=$(grep -c OCCLUSION logs/lm_terra_base_retone.log)"
echo "LUZ2 DONE"
