#!/bin/sh
# Régénère les aperçus d'un thème : themes/<thème>/preview-{top,list,completed,manga}.jpg
# Usage : sh tools/preview/make_previews.sh <thème> [scroll_liste]
set -e
t="$1"; scroll="${2:-800}"; d="tools/preview/shots/previews"
mkdir -p "$d"
node tools/preview/shot.mjs "$t" --out "$d/$t-top.png" >/dev/null
node tools/preview/shot.mjs "$t" --scroll "$scroll" --hover 2 --out "$d/$t-list.png" >/dev/null
node tools/preview/shot.mjs "$t" --status 2 --out "$d/$t-completed.png" >/dev/null
node tools/preview/shot.mjs "$t" --list manga --out "$d/$t-manga.png" >/dev/null
for k in top list completed manga; do
  python -c "from PIL import Image; Image.open('$d/$t-$k.png').convert('RGB').save('themes/$t/preview-$k.jpg', quality=84, optimize=True)"
done
echo "$t ok"
