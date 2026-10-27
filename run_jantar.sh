#!/bin/zsh
# fila de GPU: B (padrão) completo nas 5 paletas, vídeo, depois A e C
cd "$(dirname "$0")"
PY=.venv/bin/python
for p in terra mata moderno ipe ebano; do
  $PY build2.py --palette $p --dining rebativel --views sala,estar,isometrica,planta --samples 128 --out renders_j/rebativel 2>&1 | grep -E "^OK|rror"
done
echo "B DONE"
$PY video.py terra 2>&1 | grep -E "VIDEO|rror:"
ffmpeg -y -loglevel error -framerate 24 -i video/terra/f_%04d.jpg -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart video/ares_ipiranga_tour_terra.mp4 && echo "VIDEO DONE"
for o in bancada centro; do
  for p in terra mata moderno ipe ebano; do
    $PY build2.py --palette $p --dining $o --views sala,estar,planta --samples 128 --out renders_j/$o 2>&1 | grep -E "^OK|rror"
  done
  echo "$o DONE"
done
echo ALL DONE
