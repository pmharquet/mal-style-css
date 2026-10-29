"""Génère les assets originaux du thème JOURNEY'S END dans ../assets/.

Usage : python themes/journeys-end/src/make_assets.py
Tout est procédural (PIL + numpy), aucune image tierce.
"""
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).resolve().parent.parent / "assets"
OUT.mkdir(exist_ok=True)

GOLD = (196, 160, 82)
GOLD_LIGHT = (240, 218, 160)
INK = (58, 72, 70)


def periodic_noise(size, scale, seed):
    """Bruit lissé et raccordable (convolution FFT = périodique)."""
    rng = np.random.default_rng(seed)
    n = rng.standard_normal((size, size))
    fy = np.fft.fftfreq(size)[:, None]
    fx = np.fft.fftfreq(size)[None, :]
    kernel = np.exp(-(fx ** 2 + fy ** 2) * (scale ** 2) * 2 * math.pi ** 2)
    out = np.real(np.fft.ifft2(np.fft.fft2(n) * kernel))
    out -= out.min()
    return out / out.max()


def fractal(w, h, seed, octaves=5, base=6):
    """Bruit fractal non périodique (bords d'aquarelle)."""
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w))
    amp = 1.0
    for o in range(octaves):
        cells = base * 2 ** o
        small = rng.random((max(2, int(cells * h / w)) + 1, cells + 1))
        img = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        acc += np.asarray(img, dtype=float) / 255 * amp
        amp *= 0.5
    acc -= acc.min()
    return acc / acc.max()


# ---------- Papier vergé (raccordable) ----------
def paper():
    s = 512
    base = np.array([245, 239, 226], dtype=float)
    mottle = periodic_noise(s, 40, 1) - 0.5
    grain = periodic_noise(s, 1.2, 2) - 0.5
    fine = np.random.default_rng(3).standard_normal((s, s)) * 0.5
    lum = mottle * 10 + grain * 9 + fine * 2.2
    img = np.clip(base[None, None, :] + lum[..., None] * np.array([1, 1, 1.15]), 0, 255)
    im = Image.fromarray(img.astype(np.uint8), "RGB")
    # fibres
    d = ImageDraw.Draw(im, "RGBA")
    rng = random.Random(4)
    for _ in range(140):
        x, y = rng.uniform(0, s), rng.uniform(0, s)
        ang = rng.uniform(0, math.pi)
        ln = rng.uniform(6, 22)
        col = (255, 252, 244, 70) if rng.random() < 0.6 else (190, 175, 150, 45)
        pts = []
        for t in range(6):
            k = t / 5
            pts.append((x + math.cos(ang) * ln * k + math.sin(k * 3) * 1.5,
                        y + math.sin(ang) * ln * k))
        for dx in (-s, 0, s):
            for dy in (-s, 0, s):
                d.line([(px + dx, py + dy) for px, py in pts], fill=col, width=1)
    im.save(OUT / "paper.jpg", quality=88)


# ---------- Cercle magique (deux couches qui tournent en sens inverse) ----------
def glyph(draw, cx, cy, size, angle, rng, width, color):
    """Rune procédurale : 3 à 5 traits sur une grille 3x4, orientée vers le centre."""
    grid = [(gx, gy) for gx in (-1, 0, 1) for gy in (-1.5, -0.5, 0.5, 1.5)]
    strokes = []
    p = rng.choice(grid)
    for _ in range(rng.randint(3, 5)):
        q = rng.choice([g for g in grid if g != p and abs(g[0] - p[0]) <= 1 and abs(g[1] - p[1]) <= 1.01])
        strokes.append((p, q))
        p = q if rng.random() < 0.7 else rng.choice(grid)
    ca, sa = math.cos(angle), math.sin(angle)

    def tr(g):
        x, y = g[0] * size * 0.35, g[1] * size * 0.3
        return (cx + x * ca - y * sa, cy + x * sa + y * ca)

    for a, b in strokes:
        draw.line([tr(a), tr(b)], fill=color, width=width)
    if rng.random() < 0.35:
        c = tr(rng.choice(grid))
        r = size * 0.09
        draw.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], outline=color, width=width)


def star(draw, cx, cy, r, n, step, rot, color, width):
    pts = [(cx + r * math.cos(rot + 2 * math.pi * i / n), cy + r * math.sin(rot + 2 * math.pi * i / n)) for i in range(n)]
    for i in range(n):
        draw.line([pts[i], pts[(i + step) % n]], fill=color, width=width)
    return pts


def ring(draw, cx, cy, r, color, width):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=width)


def finish_glow(layer, size):
    alpha = layer.getchannel("A")
    glow = alpha.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.55))
    glow_img = Image.new("RGBA", layer.size, GOLD_LIGHT + (0,))
    glow_img.putalpha(glow)
    out = Image.alpha_composite(glow_img, layer)
    return out.resize((size, size), Image.LANCZOS)


def magic_circle():
    S = 2048
    c = S / 2
    R = 980
    col = GOLD + (255,)
    thin, mid, thick = 3, 5, 9

    outer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(outer)
    ring(d, c, c, R, col, mid)
    ring(d, c, c, R * 0.965, col, thick)
    for i in range(180):
        a = 2 * math.pi * i / 180
        r0 = R * (0.93 if i % 5 == 0 else 0.945)
        d.line([(c + r0 * math.cos(a), c + r0 * math.sin(a)),
                (c + R * 0.958 * math.cos(a), c + R * 0.958 * math.sin(a))], fill=col, width=thin)
    ring(d, c, c, R * 0.925, col, thin)
    ring(d, c, c, R * 0.79, col, mid)
    rng = random.Random(7)
    n = 44
    for i in range(n):
        a = 2 * math.pi * (i + 0.5) / n
        rr = R * 0.857
        glyph(d, c + rr * math.cos(a), c + rr * math.sin(a), R * 0.105, a + math.pi / 2, rng, thin + 1, col)
    for i in range(120):
        a = 2 * math.pi * i / 120
        rr = R * 0.75
        d.ellipse([c + rr * math.cos(a) - 5, c + rr * math.sin(a) - 5, c + rr * math.cos(a) + 5, c + rr * math.sin(a) + 5], fill=col)
    pts = star(d, c, c, R * 0.70, 7, 3, -math.pi / 2, col, mid)
    ring(d, c, c, R * 0.70, col, thin)
    for x, y in pts:
        ring(d, x, y, R * 0.055, col, mid)
        ring(d, x, y, R * 0.03, col, thin)
        d.ellipse([x - 8, y - 8, x + 8, y + 8], fill=col)

    inner = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(inner)
    ring(d, c, c, R * 0.56, col, thick)
    ring(d, c, c, R * 0.535, col, thin)
    star(d, c, c, R * 0.535, 6, 2, -math.pi / 2, col, mid)
    ring(d, c, c, R * 0.40, col, mid)
    for i in range(72):
        a = 2 * math.pi * i / 72
        r0 = R * (0.37 if i % 6 == 0 else 0.385)
        d.line([(c + r0 * math.cos(a), c + r0 * math.sin(a)), (c + R * 0.40 * math.cos(a), c + R * 0.40 * math.sin(a))], fill=col, width=thin)
    rng = random.Random(11)
    for i in range(16):
        a = 2 * math.pi * (i + 0.5) / 16
        rr = R * 0.32
        glyph(d, c + rr * math.cos(a), c + rr * math.sin(a), R * 0.075, a + math.pi / 2, rng, thin, col)
    ring(d, c, c, R * 0.27, col, mid)
    star(d, c, c, R * 0.25, 8, 3, 0, col, thin)
    ring(d, c, c, R * 0.12, col, mid)
    ring(d, c, c, R * 0.06, col, thin)

    for layer, name in ((outer, "outer"), (inner, "inner")):
        img = finish_glow(layer, 760).quantize(colors=96, method=Image.FASTOCTREE)
        img.save(OUT / f"magic-circle-{name}.png", optimize=True)


# ---------- Fleur bleue (jauge de note) ----------
def flower_img(size, petal, petal_light, center, outline=None, scale=8):
    S = size * scale
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = S / 2
    for i in range(5):
        a = -math.pi / 2 + 2 * math.pi * i / 5
        # pétale = ellipse orientée, construite en polygone
        pts, pts2 = [], []
        for t in range(48):
            th = 2 * math.pi * t / 48
            x, y = math.cos(th) * S * 0.17, math.sin(th) * S * 0.25
            y -= S * 0.2
            ca, sa = math.cos(a + math.pi / 2), math.sin(a + math.pi / 2)
            pts.append((c + x * ca - y * sa, c + x * sa + y * ca))
            x2, y2 = x * 0.55, y * 0.75 - S * 0.03
            pts2.append((c + x2 * ca - y2 * sa, c + x2 * sa + y2 * ca))
        d.polygon(pts, fill=petal, outline=outline, width=max(1, scale // 2) if outline else 0)
        d.polygon(pts2, fill=petal_light)
    r = S * 0.1
    d.ellipse([c - r, c - r, c + r, c + r], fill=center)
    return im.resize((size, size), Image.LANCZOS)


def flowers():
    blue = flower_img(28, (84, 129, 203, 255), (146, 184, 236, 255), (236, 205, 112, 255))
    empty = flower_img(28, (222, 214, 196, 255), (233, 227, 213, 255), (214, 204, 182, 255))
    blue.save(OUT / "flower.png")
    empty.save(OUT / "flower-empty.png")


# ---------- Washi tape ----------
def tape(name, color, deco):
    w, h = 132, 34
    S = 4
    im = Image.new("RGBA", (w * S, h * S), color)
    d = ImageDraw.Draw(im)
    if deco == "dots":
        for x in range(0, w * S, 26):
            for y in range(10, h * S, 26):
                off = 13 if (y // 26) % 2 else 0
                d.ellipse([x + off - 4, y - 4, x + off + 4, y + 4], fill=(255, 255, 255, 120))
    else:
        for x in range(-h * S, w * S, 22):
            d.line([(x, h * S), (x + h * S, 0)], fill=(255, 255, 255, 90), width=7)
    im = im.resize((w, h), Image.LANCZOS)
    a = np.asarray(im.getchannel("A"), dtype=float)
    rng = np.random.default_rng(len(name))
    for y in range(h):
        cut_l = int(abs(rng.normal(0, 2.2))) + (1 if y % 3 == 0 else 0)
        cut_r = int(abs(rng.normal(0, 2.2))) + (1 if y % 4 == 0 else 0)
        a[y, :cut_l] = 0
        a[y, w - cut_r:] = 0
    im.putalpha(Image.fromarray(a.astype(np.uint8)))
    im.save(OUT / name)


# ---------- Masque aquarelle de la bannière ----------
def hero_mask():
    w, h = 1600, 620
    n = fractal(w, h, 21, octaves=6, base=4)
    grain = fractal(w, h, 22, octaves=3, base=60)
    y = np.linspace(0, 1, h)[:, None]
    x = np.linspace(0, 1, w)[None, :]
    g = np.minimum(1.0, np.minimum((1 - y) / 0.5, np.minimum(x, 1 - x) / 0.12))
    v = g + (n - 0.5) * 0.42
    t = np.clip((v - 0.12) / 0.6, 0, 1)
    alpha = t * t * (3 - 2 * t)
    # granulation du pigment dans la zone de fondu + « bord mouillé » plus dense
    zone = (alpha > 0.02) & (alpha < 0.98)
    alpha = alpha * np.where(zone, 0.82 + 0.18 * grain, 1)
    alpha = np.clip(alpha + np.exp(-((v - 0.2) / 0.035) ** 2) * 0.18, 0, 1)
    m = Image.fromarray((alpha * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(0.8))
    out = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    out.putalpha(m)
    out.save(OUT / "mask-hero.png", optimize=True)


# ---------- Fleur séchée (coups de cœur 9-10) ----------
def pressed_flower():
    S = 6
    w, h = 110, 150
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    stem = (118, 128, 92, 230)
    leaf = (138, 150, 104, 220)
    pts = [(w * S * (0.55 - 0.18 * t + 0.08 * math.sin(t * 3)), h * S * (0.98 - 0.72 * t)) for t in np.linspace(0, 1, 30)]
    d.line(pts, fill=stem, width=3 * S // 2)
    for t, side in ((0.25, 1), (0.42, -1), (0.6, 1)):
        x, y = pts[int(t * 29)]
        lp = []
        for k in range(40):
            th = 2 * math.pi * k / 40
            lx, ly = math.cos(th) * 20 * S, math.sin(th) * 6 * S
            ang = side * 0.6 - 0.4
            lp.append((x + side * 18 * S + lx * math.cos(ang) - ly * math.sin(ang), y + lx * math.sin(ang) + ly * math.cos(ang)))
        d.polygon(lp, fill=leaf)
    for (fx, fy, fs) in ((0.36, 0.2, 52), (0.62, 0.12, 40), (0.5, 0.36, 34)):
        f = flower_img(fs, (104, 140, 196, 235), (160, 186, 222, 235), (214, 190, 120, 255), scale=8).resize((fs * S, fs * S), Image.LANCZOS)
        im.alpha_composite(f, (int(w * S * fx - fs * S / 2), int(h * S * fy - fs * S / 2)))
    im = im.resize((w, h), Image.LANCZOS)
    im.save(OUT / "pressed-flower.png")


# ---------- Ornement séparateur + rose des vents ----------
def divider():
    S = 4
    w, h = 520, 40
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = w * S / 2
    cy = h * S / 2
    col = GOLD + (255,)
    for side in (-1, 1):
        for i in range(60):
            x0 = c + side * (30 * S + i * 3.5 * S)
            alpha = int(255 * (1 - i / 60) ** 1.3)
            d.line([(x0, cy), (x0 + side * 3.5 * S, cy)], fill=GOLD + (alpha,), width=S)
        sx = c + side * 22 * S
        d.arc([sx - 9 * S, cy - 9 * S, sx + 9 * S, cy + 9 * S], 200 if side < 0 else -20, 340 if side < 0 else 120, fill=col, width=S)
        d.ellipse([c + side * 46 * S - 2.5 * S, cy - 2.5 * S, c + side * 46 * S + 2.5 * S, cy + 2.5 * S], fill=col)
    dia = [(c, cy - 9 * S), (c + 9 * S, cy), (c, cy + 9 * S), (c - 9 * S, cy)]
    d.polygon(dia, outline=col, width=S)
    d.polygon([(c, cy - 4 * S), (c + 4 * S, cy), (c, cy + 4 * S), (c - 4 * S, cy)], fill=col)
    im.resize((w, h), Image.LANCZOS).save(OUT / "divider.png")


def compass():
    S = 4
    s = 220
    im = Image.new("RGBA", (s * S, s * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = s * S / 2
    col = GOLD + (255,)
    soft = GOLD + (150,)
    ring(d, c, c, 96 * S, col, S)
    ring(d, c, c, 90 * S, soft, S)
    for i in range(64):
        a = 2 * math.pi * i / 64
        r0 = (84 if i % 4 == 0 else 87) * S
        d.line([(c + r0 * math.cos(a), c + r0 * math.sin(a)), (c + 90 * S * math.cos(a), c + 90 * S * math.sin(a))], fill=col, width=S)
    for k, (length, width, fill) in enumerate(((80, 13, col), (52, 9, soft))):
        for i in range(4):
            a = -math.pi / 2 + i * math.pi / 2 + (math.pi / 4 if k else 0)
            tip = (c + length * S * math.cos(a), c + length * S * math.sin(a))
            l = (c + width * S * math.cos(a - math.pi / 2), c + width * S * math.sin(a - math.pi / 2))
            r = (c + width * S * math.cos(a + math.pi / 2), c + width * S * math.sin(a + math.pi / 2))
            d.polygon([tip, l, (c, c)], fill=fill)
            d.polygon([tip, r, (c, c)], outline=col, width=S)
    ring(d, c, c, 10 * S, col, S)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/georgiab.ttf", 15 * S)
        for txt, a in (("N", -90), ("E", 0), ("S", 90), ("W", 180)):
            rad = math.radians(a)
            x, y = c + 103 * S * math.cos(rad), c + 103 * S * math.sin(rad)
            d.text((x, y), txt, font=font, fill=col, anchor="mm")
    except OSError:
        pass
    im.resize((s, s), Image.LANCZOS).save(OUT / "compass.png")


if __name__ == "__main__":
    paper()
    magic_circle()
    flowers()
    tape("tape-sage.png", (178, 196, 160, 170), "dots")
    tape("tape-sky.png", (170, 196, 222, 165), "stripes")
    tape("tape-rose.png", (226, 186, 176, 165), "dots")
    hero_mask()
    pressed_flower()
    divider()
    compass()
    for p in sorted(OUT.iterdir()):
        print(p.name, p.stat().st_size)
