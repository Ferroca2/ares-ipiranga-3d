#!/bin/zsh
# Fila única e calma: um Blender por vez, pausa de 2 min entre trabalhos e espera se o Mac reduzir a velocidade por temperatura.
cd ~/ares-ipiranga-3d
PY=.venv/bin/python
calma() {
  sleep 120
  while pmset -g therm 2>/dev/null | grep -qE "CPU_Speed_Limit\s*=\s*([0-8][0-9]|9[0-9])\b"; do echo "  esfriando…"; sleep 120; done
}
publica() {
  $PY deliverables2.py --site > logs/site.log 2>&1 && ./build_web.sh > logs/web.log 2>&1 && git add -A web && git commit -qm "$1" && git push -q && echo "  publicado: $1"
}
# 1. vídeo (retoma do quadro em que parou)
$PY video.py terra >> logs/video.log 2>&1
n=$(ls video/terra | wc -l | tr -d ' ')
echo "video frames $n"
if [ "$n" -ge 1045 ]; then
  ffmpeg -y -loglevel error -framerate 24 -i video/terra/f_%04d.jpg -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart video/ares_ipiranga_tour_terra.mp4 \
    && cp video/ares_ipiranga_tour_terra.mp4 web/video/ && git add web/video video/ares_ipiranga_tour_terra.mp4 && git commit -qm "Vídeo do passeio por todos os cômodos (44 s)" && git push -q && echo "VIDEO PUBLISHED"
fi
# 2. fotos: opção D primeiro, depois o que falta de A e C (pula o que já existe)
for job in parede:terra parede:mata parede:moderno parede:ipe parede:ebano bancada:mata bancada:ipe bancada:ebano centro:terra centro:mata centro:moderno centro:ipe centro:ebano; do
  o=${job%%:*}; p=${job##*:}
  views=()
  for v in sala estar planta; do [ -f renders_j/$o/$p/$v.jpg ] || views+=$v; done
  [ ${#views} -eq 0 ] && continue
  calma
  $PY build2.py --palette $p --dining $o --views ${(j:,:)views} --samples 128 --out renders_j/$o > logs/r_${o}_${p}.log 2>&1
  echo "$o $p: $(ls renders_j/$o/$p | tr '\n' ' ')"
  publica "Fotos da opção $o ($p)"
done
echo "FILA DONE"
