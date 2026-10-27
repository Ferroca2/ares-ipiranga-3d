#!/bin/zsh
# monta a página e copia tudo para web/ (pasta publicada na Vercel)
cd "$(dirname "$0")"
python3 merge_site.py
mkdir -p web
cp site/index.html web/index.html
rsync -a --delete site/img2/ web/img2/
rsync -a --delete site/models3/ web/models3/
rm -rf web/models2
rsync -a --delete site/items/ web/items/
cp Ares_Ipiranga_Atelie_Projeto3D.pdf web/
cp site/opcoes-jantar.html web/ 2>/dev/null; [ -d site/opcoes ] && rsync -a site/opcoes/ web/opcoes/
mkdir -p web/video && [ -f video/ares_ipiranga_tour_terra.mp4 ] && cp video/ares_ipiranga_tour_terra.mp4 web/video/
du -sh web
