#!/bin/zsh
# Luz pré-calculada no 3D, depois da fila de fotos. Um cálculo por vez, com pausa e checagem de temperatura.
# Não publica: o resultado é conferido antes de ir para o site.
cd ~/ares-ipiranga-3d
PY=.venv/bin/python
until grep -q "VIDEO PUBLISHED" fila_video.log 2>/dev/null; do sleep 60; done
calma() {
  sleep 120
  while pmset -g therm 2>/dev/null | grep -qE "CPU_Speed_Limit\s*=\s*([0-8][0-9]|9[0-9])\b"; do echo "  esfriando…"; sleep 120; done
}
run() {  # paleta parte saída blend tamanho [npy]
  local p=$1 part=$2 out=$3 blend=$4 size=$5 from=$6
  local args=(light_glb.py $p --part $part --out $out --lightmap --lm-size $size --lm-samples 128)
  [[ -n $blend ]] && args+=(--blend $blend)
  [[ -n $from ]] && args+=(--lm-from $from)
  calma
  local log=logs/lm_${p}_${part}_$(basename $out .glb).log
  $PY $args > $log 2>&1
  echo "[$p $part $(basename $out)] exit=$? $(grep -hE 'UVHASH|OCCLUSION|rror' $log | tr '\n' ' ' | cut -c1-200)"
}
DIN=(bancada rebativel rebativel_fechada centro parede parede_fechada)
for p in terra mata moderno ipe ebano; do
  run $p base modelo2/$p/web/base.glb "" 2048
  for o in $DIN; do
    if [[ $p == terra ]]; then run terra dining modelo2/terra/web/$o.glb modelo2/terra/jantar_$o.blend 1024
    else run $p dining modelo2/$p/web/$o.glb modelo2/$p/jantar_$o.blend 1024 web_tex/terra/lightmap_dining_$o.npy; fi
  done
done
echo "LUZ DONE"
