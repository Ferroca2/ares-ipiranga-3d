#!/bin/zsh
# publica o site a cada etapa da fila de renderização (B pronto, vídeo, A e C)
cd "$(dirname "$0")"
pub() {
  .venv/bin/python deliverables2.py ${1:---site} > /dev/null 2>&1
  ./build_web.sh > /dev/null 2>&1
  git add -A && git commit -qm "$2

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && git push -q && echo "PUBLISHED $2"
}
for step in "B DONE" "VIDEO DONE" "bancada DONE" "ALL DONE"; do
  until grep -q "$step" run_jantar.log; do sleep 30; done
  if [[ $step == "ALL DONE" ]]; then pub " " "Renders das 3 opções de jantar nas 5 paletas e caderno PDF atualizado"
  else pub --site "Site: $step"; fi
done
echo WATCH DONE
