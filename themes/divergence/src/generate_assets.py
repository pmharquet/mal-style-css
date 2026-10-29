"""Génère les assets originaux du thème DIVERGENCE (tubes nixie, compteur, textures).

Usage : python themes/divergence/src/generate_assets.py
Sorties dans themes/divergence/assets/ :
  meter-<ligne>.gif   compteur de divergence (8 tubes) : brouillage puis valeur, joué une fois
  nixie-score.png     sprite des notes (off, 1 à 10) en tubes nixie, 2x
  grain.png           grain photo/CRT en tuile
Les polices (Oswald, OFL) sont téléchargées depuis le dépôt Google Fonts au premier lancement.
"""
import random
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
OUT = HERE.parent / "assets"
FONTS = HERE / "fonts"
OSWALD = FONTS / "Oswald.ttf"
OSWALD_URL = "https://github.com/google/fonts/raw/main/ofl/oswald/Oswald%5Bwght%5D.ttf"

WORLDLINES = {
    "1048596": "1.048596",  # All : Steins;Gate
    "0571024": "0.571024",  # En cours : alpha
    "1130205": "1.130205",  # Terminés : beta
    "0337187": "0.337187",  # En pause
    "0000000": "0.000000",  # Abandonnés
    "1382733": "1.382733",  # Prévus
}

CORE = (255, 214, 160)
GLOW_NEAR = (255, 128, 32)
GLOW_FAR = (255, 84, 0)
GHOST = (92, 62, 44)


def font(size, weight=200):
    if not OSWALD.exists():
        FONTS.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(OSWALD_URL, OSWALD)
    f = ImageFont.truetype(str(OSWALD), size)
    f.set_variation_by_axes([weight])
    return f


def centered(draw, box, text, fnt, fill):
    x0, y0, x1, y1 = box
    l, t, r, b = draw.textbbox((0, 0), text, font=fnt)
    draw.text(((x0 + x1 - (r - l)) / 2 - l, (y0 + y1 - (b - t)) / 2 - t), text, font=fnt, fill=fill)


def tube(w, h, lit, s=1):
    """Un tube nixie : verre, cathodes fantômes, grille d'anode, chiffre allumé."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    r = w // 2
    body = (int(3 * s), int(2 * s), w - int(3 * s), h - int(2 * s))

    # Enveloppe de verre (dôme en haut)
    glass = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    g = ImageDraw.Draw(glass)
    g.rounded_rectangle(body, radius=r - int(3 * s), fill=(24, 15, 11, 235))
    g.rounded_rectangle(body, radius=r - int(3 * s), outline=(120, 96, 80, 150), width=max(1, int(1.5 * s)))
    img.alpha_composite(glass)

    digit_box = (int(8 * s), int(h * .16), w - int(8 * s), int(h * .86))
    size = int((digit_box[3] - digit_box[1]) * 1.08)
    f = font(size)

    # Cathodes éteintes empilées (visibles à travers le verre)
    ghost = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(ghost)
    for d in "0123456789":
        centered(gd, digit_box, d, f, GHOST + (70,))
    img.alpha_composite(ghost)

    # Grille d'anode en nid d'abeille
    mesh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    md = ImageDraw.Draw(mesh)
    step = max(4, int(6 * s))
    for y in range(digit_box[1] - step, digit_box[3] + step, step):
        for x in range(digit_box[0] - step, digit_box[2] + step, step):
            ox = step // 2 if (y // step) % 2 else 0
            md.ellipse((x + ox, y, x + ox + step * .55, y + step * .55), outline=(150, 120, 100, 34))
    img.alpha_composite(mesh)

    # Chiffre allumé + halo
    if lit:
        core = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        cd = ImageDraw.Draw(core)
        if lit == ".":
            cx, cy, rr = w * .5, digit_box[3] - 4 * s, 4.2 * s
            cd.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=CORE + (255,))
        elif lit == "10":
            f2 = font(int(size * .62), 250)
            centered(cd, digit_box, "10", f2, CORE + (255,))
        else:
            centered(cd, digit_box, lit, f, CORE + (255,))
        a = core.getchannel("A")
        far = Image.new("RGBA", (w, h), GLOW_FAR + (0,))
        far.putalpha(a.filter(ImageFilter.GaussianBlur(9 * s)).point(lambda v: min(255, v * 2.4)))
        near = Image.new("RGBA", (w, h), GLOW_NEAR + (0,))
        near.putalpha(a.filter(ImageFilter.GaussianBlur(2.2 * s)).point(lambda v: min(255, v * 2)))
        img.alpha_composite(far)
        img.alpha_composite(near)
        img.alpha_composite(core)

    # Reflets du verre
    hl = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hl)
    hd.rounded_rectangle((int(w * .18), int(h * .08), int(w * .26), int(h * .82)), radius=int(3 * s), fill=(255, 240, 225, 46))
    hd.ellipse((int(w * .3), int(h * .03), int(w * .7), int(h * .09)), fill=(255, 240, 225, 30))
    img.alpha_composite(hl.filter(ImageFilter.GaussianBlur(1.6 * s)))
    return img


def meter_frame(digits, tw=68, th=172, gap=8, pad=20):
    """Compteur complet sur son socle ; digits = liste de 8 valeurs ('', '.', '0'-'9')."""
    w = pad * 2 + 8 * tw + 7 * gap
    h = pad + th + 38
    img = Image.new("RGBA", (w, h), (9, 7, 6, 255))
    d = ImageDraw.Draw(img)
    # Lueur ambiante derrière les tubes
    amb = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(amb).ellipse((w * .1, pad + th * .2, w * .9, pad + th * 1.05), fill=(255, 90, 10, 40))
    img.alpha_composite(amb.filter(ImageFilter.GaussianBlur(40)))
    # Socle métallique
    base_y = pad + th - 15
    d.rounded_rectangle((pad - 12, base_y, w - pad + 12, h - 10), radius=6, fill=(30, 26, 24, 255))
    d.line((pad - 10, base_y + 1, w - pad + 10, base_y + 1), fill=(96, 84, 76, 255), width=1)
    for sx in (pad + 2, w - pad - 10):
        d.ellipse((sx, base_y + 13, sx + 7, base_y + 20), fill=(70, 62, 58, 255), outline=(20, 18, 16, 255))
        d.line((sx + 1, base_y + 16, sx + 6, base_y + 16), fill=(20, 18, 16, 255))
    for i, dg in enumerate(digits):
        x = pad + i * (tw + gap)
        img.alpha_composite(tube(tw, th, dg), (x, pad))
        # Pied du tube dans le socle
        d.rounded_rectangle((x + 8, base_y + 3, x + tw - 8, base_y + 10), radius=3, fill=(16, 13, 12, 255))
    return img


def meter_gif(value, name):
    target = [value[0], "."] + list(value[2:])
    rnd = random.Random(value)
    frames, durations = [], []
    for _ in range(11):  # brouillage
        frames.append(meter_frame([("." if i == 1 else rnd.choice("0123456789" + "  ").strip()) for i in range(8)]))
        durations.append(60)
    for k in range(1, 9):  # stabilisation tube par tube
        frames.append(meter_frame([target[i] if i < k else ("." if i == 1 else rnd.choice("0123456789")) for i in range(8)]))
        durations.append(70)
    frames.append(meter_frame(target))
    durations.append(60000)
    pal = frames[-1].convert("RGB").quantize(colors=192, method=Image.Quantize.MEDIANCUT)
    q = [f.convert("RGB").quantize(palette=pal, dither=Image.Dither.FLOYDSTEINBERG) for f in frames]
    # Sans paramètre loop, le GIF n'est joué qu'une fois : la valeur finale reste affichée.
    q[0].save(OUT / f"meter-{name}.gif", save_all=True, append_images=q[1:], duration=durations, optimize=True, disposal=1)


def score_sprite(cw=72, ch=132):
    states = [""] + [str(i) for i in range(1, 10)] + ["10"]
    sprite = Image.new("RGBA", (cw * len(states), ch), (0, 0, 0, 0))
    for i, st in enumerate(states):
        sprite.alpha_composite(tube(cw, ch, st, s=1.5), (i * cw, 0))
    sprite.save(OUT / "nixie-score.png", optimize=True)


def grain(size=180):
    rnd = random.Random(7)
    img = Image.new("LA", (size, size))
    img.putdata([(rnd.randint(0, 255), rnd.randint(0, 34)) for _ in range(size * size)])
    img.save(OUT / "grain.png", optimize=True)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, value in WORLDLINES.items():
        meter_gif(value, name)
    score_sprite()
    grain()
    for p in sorted(OUT.iterdir()):
        print(f"{p.name:24} {p.stat().st_size // 1024:5} Ko")
