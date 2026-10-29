"""Génère les assets originaux du thème ZERO REQUIEM (PNG avec transparence).

Usage : python themes/zero-requiem/src/generate_assets.py
Sortie : themes/zero-requiem/assets/
"""
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent.parent / "assets"
OUT.mkdir(exist_ok=True)
SS = 2  # suréchantillonnage pour des bords propres


def bezier(p0, p1, p2, n=60):
    """Points d'une courbe de Bézier quadratique."""
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        pts.append((x, y))
    return pts


def scaled(pts, k=SS):
    return [(x * k, y * k) for x, y in pts]


def gold_fill(mask, top=(250, 232, 170), mid=(205, 165, 78), bottom=(120, 86, 30)):
    """Remplit un masque avec un dégradé vertical or."""
    w, h = mask.size
    grad = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(h - 1, 1)
        a, b, u = (top, mid, t * 2) if t < .5 else (mid, bottom, (t - .5) * 2)
        grad.putpixel((0, y), tuple(int(a[i] + (b[i] - a[i]) * u) for i in range(3)))
    grad = grad.resize((w, h))
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(grad, (0, 0), mask)
    return out


def tint(mask, rgb, alpha=1.0):
    layer = Image.new("RGBA", mask.size, rgb + (0,))
    layer.putalpha(mask.point(lambda v: int(v * alpha)))
    return layer


# ---------- Sigil du Geass (rouge lumineux) ----------
def geass_sigil():
    W, H = 1000, 640
    m = Image.new("L", (W * SS, H * SS), 0)
    d = ImageDraw.Draw(m)
    # Chevron central : large, bord supérieur entaillé, pointe en bas
    d.polygon(scaled([(372, 360), (428, 326), (500, 404), (572, 326), (628, 360), (500, 512)]), fill=255)
    # Ailes : lames épaisses qui partent des épaules du chevron, avec un coude marqué
    for side in (-1, 1):
        cx = 500
        upper = bezier((cx + side * 60, 318), (cx + side * 240, 222), (cx + side * 448, 70))
        lower = bezier((cx + side * 116, 352), (cx + side * 280, 268), (cx + side * 448, 70))
        d.polygon(scaled(upper + lower[::-1]), fill=255)
        # coude : petite marche entre l'aile et le chevron
        d.polygon(scaled([(cx + side * 60, 318), (cx + side * 92, 300), (cx + side * 128, 346), (cx + side * 116, 352)]), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(1.5 * SS)).point(lambda v: 255 if v > 120 else 0)
    m = m.resize((W, H), Image.LANCZOS)

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for radius, alpha, col in ((70, .5, (220, 0, 30)), (28, .8, (255, 10, 45)), (9, 1, (255, 30, 60))):
        img = Image.alpha_composite(img, tint(m.filter(ImageFilter.GaussianBlur(radius)), col, alpha))
    img = Image.alpha_composite(img, tint(m, (255, 52, 78)))
    core = m.filter(ImageFilter.MinFilter(11)).filter(ImageFilter.GaussianBlur(7))
    img = Image.alpha_composite(img, tint(core, (255, 150, 165), .75))
    img.save(OUT / "geass-sigil.png", optimize=True)
    img.resize((W // 4, H // 4), Image.LANCZOS).save(OUT / "geass-sigil-small.png", optimize=True)


# ---------- Médaillon doré (cadre de l'avatar) ----------
def medallion():
    S = 400
    m = Image.new("L", (S * SS, S * SS), 0)
    d = ImageDraw.Draw(m)
    c = S * SS / 2

    def ring(r, w):
        d.ellipse((c - r * SS, c - r * SS, c + r * SS, c + r * SS), outline=255, width=int(w * SS))

    ring(190, 7)
    ring(172, 2)
    ring(160, 3)
    # Crans comme les cases d'un échiquier autour du cercle
    import math
    for i in range(32):
        a = i * math.pi * 2 / 32
        r1, r2 = 175, 186 if i % 2 else 181
        d.line([(c + math.cos(a) * r1 * SS, c + math.sin(a) * r1 * SS),
                (c + math.cos(a) * r2 * SS, c + math.sin(a) * r2 * SS)], fill=255, width=2 * SS)
    # Losanges cardinaux
    for i in range(4):
        a = i * math.pi / 2 - math.pi / 2
        x, y = c + math.cos(a) * 190 * SS, c + math.sin(a) * 190 * SS
        k = 13 * SS
        d.polygon([(x, y - k), (x + k * .7, y), (x, y + k), (x - k * .7, y)], fill=255)
    m = m.resize((S, S), Image.LANCZOS)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    img = Image.alpha_composite(img, tint(m.filter(ImageFilter.GaussianBlur(6)), (201, 162, 74), .35))
    img = Image.alpha_composite(img, gold_fill(m))
    img.save(OUT / "medallion.png", optimize=True)


# ---------- Ornement doré (séparateur de section) ----------
def ornament():
    W, H = 1000, 44
    m = Image.new("L", (W * SS, H * SS), 0)
    d = ImageDraw.Draw(m)
    cy = H / 2
    for side in (-1, 1):
        x0 = 500 + side * 30
        x1 = 500 + side * 470
        d.polygon(scaled([(x0, cy - 1.6), (x1, cy - .2), (x1, cy + .2), (x0, cy + 1.6)]), fill=255)
        for off, k in ((52, 5), (78, 3)):
            x = 500 + side * off
            d.polygon(scaled([(x, cy - k), (x + k * .8, cy), (x, cy + k), (x - k * .8, cy)]), fill=255)
    k = 14
    d.polygon(scaled([(500, cy - k), (500 + k * .75, cy), (500, cy + k), (500 - k * .75, cy)]), fill=255)
    d.polygon(scaled([(500, cy - 8), (504.5, cy), (500, cy + 8), (495.5, cy)]), fill=0)
    m = m.resize((W, H), Image.LANCZOS)
    gold_fill(m).save(OUT / "ornament.png", optimize=True)


# ---------- Grain (texture de fond) ----------
def grain():
    S = 256
    rnd = random.Random(7)
    a = Image.new("L", (S, S))
    a.putdata([rnd.choice((0, 0, 0, 6, 10, 16)) for _ in range(S * S)])
    img = Image.new("RGBA", (S, S), (255, 255, 255, 0))
    img.putalpha(a)
    img.save(OUT / "grain.png", optimize=True)


if __name__ == "__main__":
    geass_sigil()
    medallion()
    ornament()
    grain()
    print(sorted(p.name for p in OUT.iterdir()))
