"""Vérifie qu'un thème respecte les contraintes du CSS personnalisé de MAL.

Usage : python tools/check_theme.py themes/<nom>/theme.css [...]
- @import doit être écrit @\\import "..." (sinon il n'est servi qu'au propriétaire)
- url() uniquement vers .jpg / .png / .gif
- aucun caractère non-ASCII hors commentaires (MAL le corrompt)
- les assets jsDelivr référencés doivent exister dans le projet
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSET_BASE = "https://cdn.jsdelivr.net/gh/pmharquet/mal-style-css@main/"


def check(path):
    css = Path(path).read_text(encoding="utf-8")
    # Les commentaires sont blanchis en gardant les retours à la ligne (numéros de ligne exacts).
    code = re.sub(r"/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m.group()), css, flags=re.S)
    problems = []
    line = lambda pos: code.count("\n", 0, pos) + 1

    for m in re.finditer(r"@(?<!\\)import", code):
        if code[m.start() - 1] != "\\":
            problems.append(f"l.{line(m.start())} : @import sans échappement (utiliser @\\import)")
    for m in re.finditer(r"url\(\s*['\"]?([^)'\"]+)['\"]?\s*\)", code):
        url = m.group(1).strip()
        if not re.search(r"\.(jpe?g|png|gif)$", url, re.I):
            problems.append(f"l.{line(m.start())} : url() refusée par MAL : {url[:80]}")
        elif url.startswith(ASSET_BASE) and not (ROOT / url[len(ASSET_BASE):]).exists():
            problems.append(f"l.{line(m.start())} : asset absent du projet : {url[len(ASSET_BASE):]}")
    for m in re.finditer(r"[^\x00-\x7f]", code):
        problems.append(f"l.{line(m.start())} : caractère non-ASCII {m.group()!r} (utiliser un échappement CSS)")
        break

    print(f"{path} : {'OK' if not problems else str(len(problems)) + ' problème(s)'}")
    for p in problems[:20]:
        print("  - " + p)
    return not problems


if __name__ == "__main__":
    results = [check(p) for p in sys.argv[1:]]
    sys.exit(0 if all(results) else 1)
