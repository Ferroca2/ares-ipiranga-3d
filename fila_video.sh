#!/bin/zsh
# vídeo em blocos curtos (o Blender acumula memória e é encerrado depois de ~300 quadros), com pausa entre blocos
cd ~/ares-ipiranga-3d
for s in $(seq 697 120 1045); do
  e=$((s + 119)); [ $e -gt 1045 ] && e=1045
  .venv/bin/python video.py terra --frames $s-$e >> logs/video.log 2>&1
  echo "bloco $s-$e: $(ls video/terra | wc -l | tr -d ' ') quadros"
  sleep 60
done
n=$(ls video/terra | wc -l | tr -d ' ')
[ "$n" -ge 1045 ] && ffmpeg -y -loglevel error -framerate 24 -i video/terra/f_%04d.jpg -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart video/ares_ipiranga_tour_terra.mp4 \
  && cp video/ares_ipiranga_tour_terra.mp4 web/video/ && git add web/video video/ares_ipiranga_tour_terra.mp4 && git commit -qm "Vídeo do passeio por todos os cômodos (44 s)" && git push -q && echo "VIDEO PUBLISHED"
echo "FILA DONE" >> fila.log
