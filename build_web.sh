#!/bin/zsh
# monta a página e copia tudo para web/ (pasta publicada na Vercel)
cd "$(dirname "$0")"
python3 merge_site.py
mkdir -p web
cp site/index.html web/index.html
rsync -a --delete site/img2/ web/img2/
rsync -a --delete site/models2/ web/models2/
rsync -a --delete site/items/ web/items/
cp Ares_Ipiranga_Atelie_Projeto3D.pdf web/
du -sh web
