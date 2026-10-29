"""Construit une copie locale des listes MAL publiques pour prévisualiser un thème.

Usage : python tools/preview/build.py [USERNAME]
Puis servir la racine du projet (python -m http.server 8765) et ouvrir :
  http://localhost:8765/tools/preview/cache/anime.html?t=shadow-garden
Le paramètre t est le nom d'un dossier de themes/ (ou un chemin vers un .css).
"""
import re
import sys
import urllib.request
from pathlib import Path

USER = sys.argv[1] if len(sys.argv) > 1 else "Orilo"
OUT = Path(__file__).parent / "cache"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130 Safari/537.36"}
# Le thème est injecté en <style> (comme sur MAL) ; les assets publiés sur jsDelivr
# sont redirigés vers les fichiers locaux du projet.
ASSET_BASE = "https://cdn.jsdelivr.net/gh/pmharquet/mal-style-css@main/"
LOADER = """<style id="theme-css"></style>
<script>
  const t = new URLSearchParams(location.search).get('t') || 'shadow-garden';
  const src = (t.includes('/') ? t : '/themes/' + t + '/theme.css') + '?v=' + Date.now();
  fetch(src).then(r => r.text()).then(css => {
    document.getElementById('theme-css').textContent = css.split('%s').join('/');
  });
</script>""" % ASSET_BASE
ICON = '<svg class="icon icon-{0}" viewBox="0 0 22 20"><circle cx="11" cy="10" r="7"/></svg>'
OWNER_HEADER = ('<div class="header"><div class="header-menu "><div class="btn-menu"> Viewing '
                '<span class="username">Your</span> {kind} List </div></div>'
                '<a class="header-title" href="#">MyAnimeList.net</a></div>')
OWNER_FLOAT = (
    '<div class="list-menu-float"><a class="icon-menu profile" href="#"></a>'
    + "".join(f'<a class="icon-menu {k}" href="#">{ICON.format(k)}<span class="text">{t}</span></a>'
              for k, t in [("quick-add", "Quick Add"), ("anime-list", "Anime List"), ("manga-list", "Manga List"),
                           ("statistics", "Statistics"), ("history", "History"), ("export", "Export")])
    + f'<form><a class="icon-menu logout" href="#">{ICON.format("logout")}<span class="text">Logout</span></a></form>'
    + f'<div class="icon-menu setting">{ICON.format("setting")}<span class="text">'
      '<a class="link-list-setting" href="#">List Settings</a><a class="link-style-setting" href="#">Style Settings</a>'
      '</span></div></div>')
ADS = r"<script[^>]*(btloader|vntsm|quantcast|cmp\.js|googletag|gpt\.js)[^>]*>\s*</script>"

OUT.mkdir(exist_ok=True)
for kind in ("anime", "manga"):
    req = urllib.request.Request(f"https://myanimelist.net/{kind}list/{USER}", headers=UA)
    html = urllib.request.urlopen(req).read().decode("utf-8", "replace")
    styles = list(re.finditer(r"<style[^>]*>.*?</style>", html, re.S))
    # Le 2e <style> de la page est le CSS personnalisé : on le remplace par le thème local.
    custom = styles[1]
    html = html[: custom.start()] + LOADER + html[custom.end():]
    html = re.sub(ADS, "", html)
    # Aperçu local seulement : évite le blocage anti-hotlink de certains hébergeurs d'images.
    html = html.replace("<head>", '<head><meta name="referrer" content="no-referrer">', 1)
    (OUT / f"{kind}.html").write_text(html, encoding="utf-8")
    print(f"{kind}: {len(html)} octets")

    # Variante « propriétaire » : balisage relevé sur la vraie page connectée (icônes simplifiées).
    owner = html.replace('data-owner=""', 'data-owner="1"', 1)
    start, end = owner.find('<div class="header">'), owner.find('<div id="list-container"')
    owner = owner[:start] + OWNER_HEADER.replace("{kind}", kind.capitalize()) + OWNER_FLOAT + owner[end:]
    (OUT / f"owner-{kind}.html").write_text(owner, encoding="utf-8")
    print(f"owner-{kind}: ok")
