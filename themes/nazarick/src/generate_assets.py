"""Génère les assets originaux du thème NAZARICK (or ciselé, gemmes, étendards...).

Usage : python themes/nazarick/src/generate_assets.py
Sortie : themes/nazarick/assets/*.png / *.jpg

Principe : chaque forme est dessinée en masque haute résolution (x4), puis
« métallisée » : le masque flouté sert de carte de hauteur, sa normale éclaire
une rampe de couleurs (or, pierre...). Rien n'est repris d'une œuvre existante.
"""
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent.parent / "assets"
OUT.mkdir(exist_ok=True)
S = 4  # suréchantillonnage

GOLD = [(0.00, (52, 32, 8)), (0.30, (122, 86, 28)), (0.55, (201, 161, 74)),
        (0.78, (243, 220, 155)), (1.00, (255, 248, 222))]
SILVER = [(0.00, (30, 30, 36)), (0.40, (110, 112, 124)), (0.75, (205, 208, 220)), (1.00, (255, 255, 255))]


def ramp(values, stops):
    """Applique une rampe de couleurs à un tableau de valeurs 0..1."""
    v = np.clip(values, 0, 1)
    out = np.zeros(v.shape + (3,), np.float32)
    for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
        m = (v >= p0) & (v <= p1)
        t = ((v - p0) / max(p1 - p0, 1e-6))[m][:, None]
        out[m] = np.array(c0) * (1 - t) + np.array(c1) * t
    return out


def metal(mask, stops=GOLD, blur=3.0, light=(-0.55, -0.75, 0.6), base=0.06, gloss=0.8):
    """Transforme un masque L en métal biseauté RGBA."""
    m = np.asarray(mask, np.float32) / 255
    h = np.asarray(mask.filter(ImageFilter.GaussianBlur(blur * S)), np.float32) / 255
    gy, gx = np.gradient(h * 6)
    n = np.dstack([-gx, -gy, np.ones_like(h)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    lx, ly, lz = light
    ln = math.sqrt(lx * lx + ly * ly + lz * lz)
    d = (n[..., 0] * lx + n[..., 1] * ly + n[..., 2] * lz) / ln
    yy = np.linspace(0, 1, m.shape[0])[:, None] * np.ones_like(m)
    val = base + gloss * d + 0.10 * np.sin(yy * math.pi * 3) - 0.08 * (1 - h)
    rgb = ramp(val, stops)
    a = (m * 255).astype(np.uint8)
    return Image.fromarray(np.dstack([rgb.astype(np.uint8), a]), "RGBA")


def canvas(w, h):
    return Image.new("L", (w * S, h * S), 0)


def down(img, w, h):
    return img.resize((w, h), Image.LANCZOS)


def spiral_points(cx, cy, r0, turns, direction=1, start=0.0, shrink=0.82):
    pts = []
    steps = int(60 * turns)
    for i in range(steps + 1):
        t = i / steps
        ang = start + direction * t * turns * 2 * math.pi
        r = r0 * (shrink ** (t * turns * 4))
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return pts


def stroke(draw, pts, width):
    draw.line(pts, fill=255, width=width, joint="curve")
    r = width / 2
    for x, y in (pts[0], pts[-1]):
        draw.ellipse((x - r, y - r, x + r, y + r), fill=255)


def diamond(draw, cx, cy, rx, ry, fill=255):
    draw.polygon([(cx, cy - ry), (cx + rx, cy), (cx, cy + ry), (cx - rx, cy)], fill=fill)


# ---------------------------------------------------------------------------
# Cadre 9-slice (border-image) : double filet perlé + rinceaux d'angle
def frame():
    W = 240
    C = 80  # taille d'un coin (border-image-slice)
    mask = canvas(W, W)
    d = ImageDraw.Draw(mask)
    k = S
    # filets extérieur et intérieur
    for inset, wd in ((6, 3), (18, 2)):
        d.rectangle((inset * k, inset * k, (W - inset) * k, (W - inset) * k), outline=255, width=wd * k)
    # perles entre les filets
    for i in range(0, W, 10):
        for (x, y) in ((i, 12), (i, W - 12), (12, i), (W - 12, i)):
            if C - 10 < i < W - C + 10 or True:
                d.ellipse(((x - 1.6) * k, (y - 1.6) * k, (x + 1.6) * k, (y + 1.6) * k), fill=255)
    # coins : rinceaux symétriques
    for cx, cy, sx, sy in ((0, 0, 1, 1), (W, 0, -1, 1), (0, W, 1, -1), (W, W, -1, -1)):
        def P(x, y):
            return ((cx + sx * x) * k, (cy + sy * y) * k)
        # plaque d'angle
        rx0, ry0 = P(21, 21)
        d.ellipse((rx0 - 10 * k, ry0 - 10 * k, rx0 + 10 * k, ry0 + 10 * k), fill=255)
        d.ellipse((rx0 - 16 * k, ry0 - 16 * k, rx0 + 16 * k, ry0 + 16 * k), outline=255, width=int(2 * k))
        for ang in range(0, 360, 45):
            a = math.radians(ang)
            lx, ly = rx0 + 20 * k * math.cos(a), ry0 + 20 * k * math.sin(a)
            d.ellipse((lx - 3 * k, ly - 3 * k, lx + 3 * k, ly + 3 * k), fill=255)
        for (ax, ay) in ((40, 10), (10, 40)):
            qx, qy = P(ax, ay)
            d.ellipse((qx - 7 * k, qy - 3.4 * k, qx + 7 * k, qy + 3.4 * k) if ax > ay else (qx - 3.4 * k, qy - 7 * k, qx + 3.4 * k, qy + 7 * k), fill=255)
        # volutes
        for (ox, oy, dirn, st) in ((52, 14, 1, math.pi), (14, 52, -1, -math.pi / 2)):
            pts = spiral_points(ox, oy, 13, 1.25, direction=dirn, start=st)
            stroke(d, [P(x, y) for x, y in pts], int(2.6 * k))
        stroke(d, [P(22, 46), P(30, 58), P(26, 72)], int(2.2 * k))
        stroke(d, [P(46, 22), P(58, 30), P(72, 26)], int(2.2 * k))
        for x, y, r in ((26, 74, 3), (74, 26, 3), (40, 40, 3.5)):
            d.ellipse(((cx + sx * x - r) * k, (cy + sy * y - r) * k, (cx + sx * x + r) * k, (cy + sy * y + r) * k), fill=255)
    # vide central (le contenu du cadre reste transparent)
    img = down(metal(mask, blur=1.2), W, W)
    img.save(OUT / "frame.png", optimize=True)


# ---------------------------------------------------------------------------
# Gemmes de statut (taille de rose, sertie d'or)
GEMS = {
    "watching": (155, 70, 230),    # améthyste — Salle du trône
    "completed": (225, 40, 30),    # rubis — Lave
    "onhold": (90, 190, 255),      # saphir glacé — Glacier
    "dropped": (150, 10, 30),      # grenat — Catacombes
    "planned": (40, 200, 120),     # émeraude — Jungle
    "all": (240, 190, 70),         # topaze — Tombeau
}


def gem(name, color):
    W = 64
    k = S
    c = W * k / 2
    img = Image.new("RGBA", (W * k, W * k), (0, 0, 0, 0))
    # serti doré
    bez = canvas(W, W)
    d = ImageDraw.Draw(bez)
    d.ellipse((4 * k, 4 * k, (W - 4) * k, (W - 4) * k), fill=255)
    for i in range(8):
        a = i * math.pi / 4
        x, y = c + 28 * k * math.cos(a), c + 28 * k * math.sin(a)
        d.ellipse((x - 3.2 * k, y - 3.2 * k, x + 3.2 * k, y + 3.2 * k), fill=255)
    img.alpha_composite(metal(bez, blur=1.4))
    # pierre : facettes triangulaires autour d'une table octogonale
    stone = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(stone)
    R, r = 21 * k, 10 * k
    col = np.array(color, np.float32)
    for i in range(16):
        a0, a1 = i * math.pi / 8, (i + 1) * math.pi / 8
        am = (a0 + a1) / 2
        light = 0.55 + 0.55 * math.cos(am + 2.3)
        shade = tuple(int(v) for v in np.clip(col * light + (40 if i % 2 else 0), 0, 255))
        pts = [(c + R * math.cos(a0), c + R * math.sin(a0)), (c + R * math.cos(a1), c + R * math.sin(a1)),
               (c + r * math.cos(am), c + r * math.sin(am))]
        sd.polygon(pts, fill=shade + (255,))
    table = [(c + r * math.cos(i * math.pi / 4 + math.pi / 8), c + r * math.sin(i * math.pi / 4 + math.pi / 8)) for i in range(8)]
    sd.polygon(table, fill=tuple(int(v) for v in np.clip(col * 1.15 + 30, 0, 255)) + (255,))
    # reflets
    sd.ellipse((c - 12 * k, c - 15 * k, c - 4 * k, c - 9 * k), fill=(255, 255, 255, 200))
    sd.ellipse((c + 6 * k, c + 8 * k, c + 9 * k, c + 11 * k), fill=(255, 255, 255, 120))
    img.alpha_composite(stone)
    # halo interne
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((c - 16 * k, c - 16 * k, c + 16 * k, c + 16 * k), fill=tuple(color) + (90,))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(6 * k)))
    down(img, W, W).save(OUT / f"gem-{name}.png", optimize=True)


# ---------------------------------------------------------------------------
# Médaillon de note (pièce d'or de YGGDRASIL, centre lisse pour le chiffre romain)
def coin():
    W = 120
    k = S
    c = W * k / 2
    m = canvas(W, W)
    d = ImageDraw.Draw(m)
    d.ellipse((4 * k, 4 * k, (W - 4) * k, (W - 4) * k), fill=255)
    rim = metal(m, blur=4)
    inner = canvas(W, W)
    di = ImageDraw.Draw(inner)
    di.ellipse((16 * k, 16 * k, (W - 16) * k, (W - 16) * k), fill=255)
    beads = canvas(W, W)
    db = ImageDraw.Draw(beads)
    for i in range(36):
        a = i * 2 * math.pi / 36
        x, y = c + 49 * k * math.cos(a), c + 49 * k * math.sin(a)
        db.ellipse((x - 2.2 * k, y - 2.2 * k, x + 2.2 * k, y + 2.2 * k), fill=255)
    img = rim.copy()
    # champ central légèrement creusé et assombri
    field = metal(inner, blur=6, light=(0.55, 0.75, 0.6), base=0.28, gloss=0.35)
    img.alpha_composite(field)
    img.alpha_composite(metal(beads, blur=0.8))
    ring = canvas(W, W)
    ImageDraw.Draw(ring).ellipse((22 * k, 22 * k, (W - 22) * k, (W - 22) * k), outline=255, width=int(1.6 * k))
    img.alpha_composite(metal(ring, blur=0.6))
    down(img, W, W).save(OUT / "coin.png", optimize=True)


# ---------------------------------------------------------------------------
# Médaillon d'avatar : anneau couronné
def avatar_frame():
    W = 260
    k = S
    c = W * k / 2
    m = canvas(W, W)
    d = ImageDraw.Draw(m)
    d.ellipse((22 * k, 22 * k, (W - 22) * k, (W - 22) * k), fill=255)
    d.ellipse((38 * k, 38 * k, (W - 38) * k, (W - 38) * k), fill=0)
    # pointes de couronne
    for i in range(24):
        a = i * 2 * math.pi / 24 - math.pi / 2
        long = 1.0 if i % 2 == 0 else 0.55
        r0, r1 = 108 * k, (108 + 14 * long) * k
        w = 0.07 if i % 2 == 0 else 0.05
        pts = [(c + r0 * math.cos(a - w), c + r0 * math.sin(a - w)), (c + r1 * math.cos(a), c + r1 * math.sin(a)),
               (c + r0 * math.cos(a + w), c + r0 * math.sin(a + w))]
        d.polygon(pts, fill=255)
    for i in range(4):
        a = i * math.pi / 2 - math.pi / 2
        x, y = c + 115 * k * math.cos(a), c + 115 * k * math.sin(a)
        diamond(d, x, y, 9 * k, 13 * k)
    img = metal(m, blur=2.2)
    beads = canvas(W, W)
    db = ImageDraw.Draw(beads)
    for i in range(48):
        a = i * 2 * math.pi / 48
        x, y = c + 99 * k * math.cos(a), c + 99 * k * math.sin(a)
        db.ellipse((x - 2.4 * k, y - 2.4 * k, x + 2.4 * k, y + 2.4 * k), fill=255)
    img.alpha_composite(metal(beads, blur=0.7, base=0.5))
    down(img, W, W).save(OUT / "avatar-frame.png", optimize=True)


# ---------------------------------------------------------------------------
# Séparateur ornemental
def divider():
    W, H = 640, 48
    k = S
    m = canvas(W, H)
    d = ImageDraw.Draw(m)
    cx, cy = W / 2, H / 2
    diamond(d, cx * k, cy * k, 14 * k, 18 * k)
    for sx in (-1, 1):
        # filet effilé
        pts = [((cx + sx * 26) * k, (cy - 1.6) * k), ((cx + sx * 300) * k, cy * k), ((cx + sx * 26) * k, (cy + 1.6) * k)]
        d.polygon(pts, fill=255)
        diamond(d, (cx + sx * 34) * k, cy * k, 5 * k, 7 * k)
        for ox in (60, 110):
            pts = spiral_points(cx + sx * ox, cy - 8, 7, 1.0, direction=sx, start=math.pi / 2)
            stroke(d, [(x * k, y * k) for x, y in pts], int(1.8 * k))
            pts = spiral_points(cx + sx * ox, cy + 8, 7, 1.0, direction=-sx, start=-math.pi / 2)
            stroke(d, [(x * k, y * k) for x, y in pts], int(1.8 * k))
        d.ellipse(((cx + sx * 150 - 2.5) * k, (cy - 2.5) * k, (cx + sx * 150 + 2.5) * k, (cy + 2.5) * k), fill=255)
    down(metal(m, blur=1.0), W, H).save(OUT / "divider.png", optimize=True)


# ---------------------------------------------------------------------------
# Étendard de guilde suspendu (velours pourpre, galon d'or, sceau original)
def banner(name, cloth=(58, 22, 92)):
    W, H = 220, 760
    k = S
    w, h = W * k, H * k
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # silhouette : rectangle + queue d'aronde
    shape = Image.new("L", (w, h), 0)
    sd = ImageDraw.Draw(shape)
    top, bot, notch = 34 * k, (H - 40) * k, 90 * k
    left, right = 22 * k, (W - 22) * k
    sd.polygon([(left, top), (right, top), (right, bot), (w / 2, bot - notch), (left, bot)], fill=255)
    # plis du velours
    xs = np.linspace(0, 1, w)
    folds = 0.62 + 0.22 * np.sin(xs * math.pi * 5.2 + 0.6) + 0.1 * np.sin(xs * math.pi * 11)
    ys = np.linspace(0, 1, h)[:, None]
    shade = folds[None, :] * (0.85 + 0.25 * (1 - ys))
    rng = np.random.default_rng(7)
    noise = rng.normal(0, 0.035, (h // 8, w // 8))
    noise = np.asarray(Image.fromarray(((noise + 0.5) * 255).clip(0, 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255 - 0.5
    rgb = np.clip(np.array(cloth, np.float32)[None, None, :] * (shade[..., None] + noise[..., None] * 0.6), 0, 255)
    cl = Image.fromarray(np.dstack([rgb.astype(np.uint8), np.asarray(shape)]), "RGBA")
    img.alpha_composite(cl)
    # galon d'or
    trim = Image.new("L", (w, h), 0)
    td = ImageDraw.Draw(trim)
    inset = 12 * k
    td.line([(left + inset, top), (left + inset, bot - 6 * k), (w / 2, bot - notch - 2 * k), (right - inset, bot - 6 * k), (right - inset, top)],
            fill=255, width=int(3.5 * k), joint="curve")
    td.line([(left + inset + 8 * k, top), (left + inset + 8 * k, bot - 22 * k), (w / 2, bot - notch - 18 * k),
             (right - inset - 8 * k, bot - 22 * k), (right - inset - 8 * k, top)], fill=255, width=int(1.4 * k), joint="curve")
    # glands
    for x in np.linspace(left + 4 * k, right - 4 * k, 9):
        if abs(x - w / 2) < 6 * k:
            continue
        yb = bot - notch * (1 - abs(x - w / 2) / (w / 2 - left)) if abs(x - w / 2) < (w / 2 - left) else bot
        td.line([(x, yb), (x, yb + 26 * k)], fill=255, width=int(2 * k))
        td.ellipse((x - 4 * k, yb + 22 * k, x + 4 * k, yb + 34 * k), fill=255)
    # hampe
    td.rounded_rectangle((6 * k, 18 * k, w - 6 * k, 34 * k), radius=8 * k, fill=255)
    for x in (6 * k, w - 6 * k):
        td.ellipse((x - 11 * k, 15 * k, x + 11 * k, 37 * k), fill=255)
    for x in (60 * k, w - 60 * k):
        td.line([(x, 34 * k), (x, 46 * k)], fill=255, width=int(3 * k))
    img.alpha_composite(metal(trim, blur=1.2))
    # sceau : bâton couronné de sept serpents (création originale)
    seal = Image.new("L", (w, h), 0)
    ed = ImageDraw.Draw(seal)
    cx, cy = w / 2, 300 * k
    ed.ellipse((cx - 62 * k, cy - 62 * k, cx + 62 * k, cy + 62 * k), outline=255, width=int(4 * k))
    ed.ellipse((cx - 52 * k, cy - 52 * k, cx + 52 * k, cy + 52 * k), outline=255, width=int(1.5 * k))
    ed.line([(cx, cy - 40 * k), (cx, cy + 150 * k)], fill=255, width=int(7 * k))
    diamond(ed, cx, cy + 156 * k, 9 * k, 14 * k)
    for i in range(7):
        a = -math.pi / 2 + (i - 3) * 0.42
        x1, y1 = cx + 40 * k * math.cos(a), cy - 2 * k + 40 * k * math.sin(a)
        mx, my = cx + 18 * k * math.cos(a + 0.35), cy + 18 * k * math.sin(a + 0.35)
        ed.line([(cx, cy + 6 * k), (mx, my), (x1, y1)], fill=255, width=int(3.2 * k), joint="curve")
        ed.ellipse((x1 - 6 * k, y1 - 6 * k, x1 + 6 * k, y1 + 6 * k), fill=255)
    diamond(ed, cx, cy + 6 * k, 10 * k, 12 * k)
    for sx in (-1, 1):
        pts = spiral_points(cx / k + sx * 30, cy / k + 92, 14, 1.15, direction=-sx, start=0 if sx > 0 else math.pi)
        stroke(ed, [(x * k, y * k) for x, y in pts], int(3 * k))
    img.alpha_composite(metal(seal, blur=1.6))
    # ombre portée douce
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sh = Image.fromarray((np.asarray(shape, np.float32) * 0.55).astype(np.uint8))
    shadow.putalpha(sh.filter(ImageFilter.GaussianBlur(10 * k)))
    final = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    final.alpha_composite(shadow, (10 * k, 14 * k))
    final.alpha_composite(img)
    down(final, W, H).save(OUT / f"{name}.png", optimize=True)


# ---------------------------------------------------------------------------
# Texture de pierre d'obsidienne (raccordable)
def stone():
    N = 512
    rng = np.random.default_rng(41)

    def octave(cells, amp):
        base = rng.random((cells, cells)).astype(np.float32)
        tile = np.tile(base, (3, 3))
        im = Image.fromarray((tile * 255).astype(np.uint8)).resize((N * 3, N * 3), Image.BICUBIC)
        return np.asarray(im, np.float32)[N:2 * N, N:2 * N] / 255 * amp

    n = octave(4, 0.5) + octave(8, 0.3) + octave(16, 0.15) + octave(48, 0.05)
    n = (n - n.min()) / (n.max() - n.min())
    veins = np.clip(1 - np.abs(n - 0.5) * 40, 0, 1) ** 4 * 0.35
    v = 0.10 + 0.22 * n
    rgb = np.dstack([v * 64 + veins * 70, v * 48 + veins * 50, v * 84 + veins * 80])
    Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(OUT / "stone.jpg", quality=88)


if __name__ == "__main__":
    frame()
    for name, color in GEMS.items():
        gem(name, color)
    coin()
    avatar_frame()
    divider()
    for name, cloth in {"all": (44, 16, 66), "watching": (78, 30, 124), "completed": (112, 14, 22),
                        "onhold": (20, 44, 98), "dropped": (58, 8, 16), "planned": (14, 72, 46)}.items():
        banner(f"banner-{name}", cloth)
    stone()
    print(sorted(p.name for p in OUT.iterdir()))
