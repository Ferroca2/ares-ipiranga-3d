#!/bin/zsh
# luz pré-calculada para o visualizador: assa na Terra e reaproveita nas outras paletas (mesma geometria)
cd "$(dirname "$0")"
PY=.venv/bin/python
until grep -q "WATCH DONE" publish_watch.log 2>/dev/null; do sleep 30; done
run() {  # paleta parte saída blend tamanho [npy]
  local p=$1 part=$2 out=$3 blend=$4 size=$5 from=$6
  local args=(light_glb.py $p --part $part --out $out --lightmap --lm-size $size --lm-samples 128)
  [[ -n $blend ]] && args+=(--blend $blend)
  [[ -n $from ]] && args+=(--lm-from $from)
  $PY $args 2>&1 | grep -E "UVHASH|LIGHTMAP|OCCLUSION|LIGHT |rror:" | sed "s/^/[$p $part $(basename $out)] /"
}
T=web_tex/terra
run terra base modelo2/terra/web/base.glb "" 2048
for o in bancada rebativel rebativel_fechada centro; do
  run terra dining modelo2/terra/web/$o.glb modelo2/terra/jantar_$o.blend 1024
done
for p in mata moderno ipe ebano; do
  run $p base modelo2/$p/web/base.glb "" 2048 $T/lightmap_base_base.npy
  for o in bancada rebativel rebativel_fechada centro; do
    run $p dining modelo2/$p/web/$o.glb modelo2/$p/jantar_$o.blend 1024 $T/lightmap_dining_$o.npy
  done
done
echo "LIGHTMAP BAKED"
