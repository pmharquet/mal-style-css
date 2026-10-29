"""Assets originaux du thème BANKAI (encre sumi, pinceau sec, sceau rouge).

Usage : python themes/bankai/src/generate_assets.py
Tout est procédural (numpy + Pillow) : aucune image source n'est utilisée.
"""
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent.parent / "assets"
RED = (178, 14, 32)
INK = (12, 11, 11)
rng = np.random.default_rng(1001)


# ---------- bruit ----------
def periodic_noise_1d(n, octaves=5, seed=0, base_cycles=3):
    """Bruit 1D périodique sur n échantillons (raccord parfait aux bords)."""
    r = np.random.default_rng(seed)
    x = np.arange(n) / n
    out = np.zeros(n)
    for o in range(octaves):
        cycles = base_cycles * 2 ** o
        amp = 0.5 ** o
        for _ in range(3):
            k = cycles + r.integers(0, cycles + 1)
            out += amp * np.sin(2 * math.pi * (k * x + r.random()))
    return out / np.abs(out).max()


def periodic_noise_2d(h, w, beta=2.2, seed=0):
    """Bruit 2D en 1/f^beta via FFT : périodique, donc carrelable."""
    r = np.random.default_rng(seed)
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    f = np.sqrt(fx ** 2 + fy ** 2)
    f[0, 0] = 1
    spectrum = (r.normal(size=(h, w)) + 1j * r.normal(size=(h, w))) / f ** (beta / 2)
    spectrum[0, 0] = 0
    n = np.real(np.fft.ifft2(spectrum))
    return (n - n.min()) / (n.max() - n.min())


def smooth_noise(n, seed, scale=40):
    r = np.random.default_rng(seed)
    pts = r.random(n // scale + 3)
    x = np.arange(n) / scale
    i = x.astype(int)
    f = x - i
    f = f * f * (3 - 2 * f)
    return pts[i] * (1 - f) + pts[i + 1] * f


# ---------- pinceau ----------
def resample(points, n):
    pts = np.array(points, float)
    seg = np.hypot(*np.diff(pts, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    t = np.linspace(0, s[-1], n)
    return np.stack([np.interp(t, s, pts[:, 0]), np.interp(t, s, pts[:, 1])], 1)


def catmull(points, per=40):
    p = np.array(points, float)
    p = np.vstack([p[0], p, p[-1]])
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for t in np.linspace(0, 1, per, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(p[-2])
    return np.array(out)


def brush(size, path, width_fn, bristles=140, dryness=0.5, seed=0, ss=2, steps=700, spread=1.0):
    """Trait de pinceau sec : chaque poil est une polyligne qui se vide d'encre."""
    w, h = size
    r = np.random.default_rng(seed)
    img = Image.new("L", (w * ss, h * ss), 0)
    d = ImageDraw.Draw(img)
    pts = resample(catmull(path), steps)
    tang = np.gradient(pts, axis=0)
    tang /= np.linalg.norm(tang, axis=1, keepdims=True) + 1e-9
    norm = np.stack([-tang[:, 1], tang[:, 0]], 1)
    ts = np.linspace(0, 1, steps)
    widths = np.array([width_fn(t) for t in ts])
    for b in range(bristles):
        o = np.clip(r.normal(0, 0.45), -1, 1) * spread
        load = r.uniform(0.55, 1.0)
        gap = smooth_noise(steps, seed * 1000 + b, scale=r.integers(8, 40))
        # plus le poil est au bord et plus le trait avance, plus il « sèche »
        thresh = dryness * (0.35 + 0.65 * ts ** 1.4) * (0.6 + 0.8 * abs(o)) / load
        on = gap > thresh
        rad = max(1, int(ss * (widths.mean() / bristles) * r.uniform(1.4, 3.2)))
        jitter = r.normal(0, 0.6, size=(steps, 2))
        xy = (pts + norm * (o * widths / 2)[:, None] + jitter) * ss
        run = []
        for i in range(steps):
            if on[i] and widths[i] > 0.5:
                run.append(tuple(xy[i]))
            elif run:
                if len(run) > 1:
                    d.line(run, fill=255, width=rad, joint="curve")
                run = []
        if len(run) > 1:
            d.line(run, fill=255, width=rad, joint="curve")
    img = img.filter(ImageFilter.GaussianBlur(ss * 0.6)).resize((w, h), Image.LANCZOS)
    return img


def colorize(mask, color, alpha_gain=1.0):
    a = np.asarray(mask, float) / 255
    a = np.clip(a * alpha_gain, 0, 1)
    rgba = np.zeros((*a.shape, 4), np.uint8)
    rgba[..., :3] = color
    rgba[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


def roughen(mask, amount=0.25, seed=0):
    """Bords de papier buvard : seuil bruité d'une version floutée."""
    m = np.asarray(mask.filter(ImageFilter.GaussianBlur(1.2)), float) / 255
    n = periodic_noise_2d(*m.shape, beta=1.2, seed=seed)
    m = np.clip((m - 0.5 + (n - 0.5) * amount) * 4 + 0.5, 0, 1)
    return Image.fromarray((m * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(0.6))


def save(img, name, **kw):
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / name
    if name.endswith(".jpg"):
        img.convert("RGB").save(p, quality=86, optimize=True, progressive=True)
    else:
        img.save(p, optimize=True, **kw)
    print(f"{name:22} {img.size[0]}x{img.size[1]}  {p.stat().st_size // 1024} Ko")


# ---------- assets ----------
def paper():
    s = 640
    base = np.array([241, 238, 231], float)
    mott = periodic_noise_2d(s, s, beta=2.6, seed=3) - 0.5
    fine = periodic_noise_2d(s, s, beta=0.6, seed=4) - 0.5
    img = base[None, None, :] + mott[..., None] * 16 + fine[..., None] * 9
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")
    # fibres de washi (dessinées avec raccord sur les bords)
    fib = Image.new("L", (s, s), 0)
    d = ImageDraw.Draw(fib)
    for _ in range(260):
        x, y = rng.random(2) * s
        a = rng.uniform(0, math.pi)
        L = rng.uniform(15, 70)
        pts = [(x + math.cos(a + 0.4 * math.sin(k / 3)) * L * k / 6, y + math.sin(a + 0.4 * math.sin(k / 3)) * L * k / 6) for k in range(7)]
        for dx in (-s, 0, s):
            for dy in (-s, 0, s):
                d.line([(px + dx, py + dy) for px, py in pts], fill=int(rng.uniform(20, 60)), width=1)
    fib = fib.filter(ImageFilter.GaussianBlur(0.5))
    im = ImageChops.subtract(im, Image.merge("RGB", [fib] * 3).point(lambda v: v // 3))
    save(im, "paper.jpg")


def grain():
    s = 256
    n = rng.random((s, s))
    a = np.where(n > 0.6, (n - 0.6) / 0.4, 0) ** 3 * 34
    rgba = np.zeros((s, s, 4), np.uint8)
    rgba[..., :3] = 255
    rgba[..., 3] = a.astype(np.uint8)
    save(Image.fromarray(rgba, "RGBA"), "grain.png")


def ink_edge():
    """Bord supérieur peint de la zone noire : grands coups de pinceau horizontaux.
    Image unique étirée sur la largeur de la page (pas de raccord nécessaire)."""
    w, h = 3000, 300
    base = Image.new("L", (w, h), 0)
    ImageDraw.Draw(base).rectangle([0, 215, w, h], fill=255)
    strokes = [
        (205, 120, 0.35, 61), (170, 95, 0.75, 62), (140, 60, 0.95, 63), (112, 34, 1.15, 64), (190, 80, 0.55, 66),
    ]
    for y, width, dry, seed in strokes:
        r = np.random.default_rng(seed)
        pts = [(-80 + i * (w + 160) / 8, y + r.normal(0, 18)) for i in range(9)]
        wf = lambda t, width=width: width * (0.75 + 0.25 * math.sin(t * 9 + seed))
        m = brush((w, h), pts, wf, bristles=260, dryness=dry, seed=seed, steps=1600, ss=1)
        base = ImageChops.lighter(base, m)
    save(colorize(roughen(base, 0.25, seed=65), INK), "ink-edge.png")


def enso():
    s = 720
    c = s / 2
    R = s * 0.36
    a0 = math.radians(-70)
    pts = []
    for i in range(60):
        t = i / 59
        a = a0 + t * math.radians(332)
        rr = R * (1 + 0.025 * math.sin(t * 7) + 0.03 * t)
        pts.append((c + math.cos(a) * rr, c + math.sin(a) * rr))
    wf = lambda t: 92 * (min(1, t / 0.03) ** 0.4) * (1 - 0.7 * t ** 1.2)
    m = brush((s, s), pts, wf, bristles=230, dryness=0.95, seed=7, steps=1000, spread=1.15)
    save(colorize(roughen(m, 0.3, seed=8), RED), "enso-red.png")
    save(colorize(roughen(m, 0.3, seed=8), (245, 243, 238)), "enso-white.png")


def splatter(name, color, seed):
    s = 900
    r = np.random.default_rng(seed)
    im = Image.new("L", (s * 2, s * 2), 0)
    d = ImageDraw.Draw(im)
    c = s
    for _ in range(26):  # coeur
        rr = r.uniform(40, 150)
        x, y = c + r.normal(0, 70, 2)
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=255)
    for _ in range(140):  # projections
        ang = r.uniform(0, 2 * math.pi)
        dist = r.uniform(180, 820) ** 1.0
        rr = max(3, 60 * (1 - dist / 900) ** 2 * r.uniform(0.2, 1.4))
        x, y = c + math.cos(ang) * dist, c + math.sin(ang) * dist
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=255)
        if r.random() < 0.45:  # filet qui relie au centre
            x2, y2 = c + math.cos(ang) * dist * 0.55, c + math.sin(ang) * dist * 0.55
            d.line([(x2, y2), (x, y)], fill=255, width=int(max(2, rr * 0.7)))
    for _ in range(420):  # bruine
        ang = r.uniform(0, 2 * math.pi)
        dist = abs(r.normal(420, 260))
        rr = r.uniform(1.5, 6)
        x, y = c + math.cos(ang) * dist, c + math.sin(ang) * dist
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=255)
    im = im.filter(ImageFilter.GaussianBlur(3)).resize((s, s), Image.LANCZOS)
    save(colorize(roughen(im, 0.45, seed=seed), color), name)


def slash():
    """Entaille de sabre : fine lentille rouge, cœur clair, éclats."""
    w, h = 2000, 64
    ss = 3
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cy = h * ss / 2
    top, bot = [], []
    for i in range(201):
        t = i / 200
        thick = (math.sin(math.pi * t ** 0.8) ** 1.6) * 7 * ss
        x = t * w * ss
        top.append((x, cy - thick))
        bot.append((x, cy + thick * 0.55))
    d.polygon(top + bot[::-1], fill=RED + (255,))
    core = [(x, cy - (cy - y) * 0.35) for x, y in top] + [(x, cy) for x, _ in bot[::-1]]
    d.polygon(core, fill=(255, 92, 92, 200))
    for _ in range(60):
        x = rng.uniform(0.15, 0.95) * w * ss
        y = cy + rng.normal(0, 9) * ss
        rr = rng.uniform(0.6, 2.4) * ss
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=RED + (int(rng.uniform(120, 255)),))
    im = im.filter(ImageFilter.GaussianBlur(ss * 0.35)).resize((w, h), Image.LANCZOS)
    save(im, "slash-red.png")


def brush_vertical():
    w, h = 380, 1500
    pts = [(200, 30), (185, 400), (205, 800), (190, 1150), (210, 1470)]
    wf = lambda t: 250 * (min(1, t / 0.03) ** 0.4) * (1 - 0.55 * t ** 2.2)
    m = brush((w, h), pts, wf, bristles=200, dryness=0.55, seed=21, steps=1200)
    save(colorize(roughen(m, 0.3, seed=22), RED), "brush-red-v.png")


def brush_underline():
    w, h = 560, 110
    pts = [(20, 66), (180, 52), (380, 58), (540, 44)]
    wf = lambda t: 46 * (min(1, t / 0.06) ** 0.5) * (1 - 0.6 * t ** 1.8)
    m = brush((w, h), pts, wf, bristles=90, dryness=0.5, seed=31, steps=500)
    save(colorize(roughen(m, 0.3, seed=32), RED), "brush-red-h.png")


def hanko():
    """Sceau rouge plein, rongé comme un tampon (le kanji est posé en CSS)."""
    s = 220
    ss = 3
    m = Image.new("L", (s * ss, s * ss), 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([14 * ss, 14 * ss, (s - 14) * ss, (s - 14) * ss], radius=16 * ss, fill=255)
    m = m.resize((s, s), Image.LANCZOS)
    a = np.asarray(m, float) / 255
    n = periodic_noise_2d(s, s, beta=0.9, seed=41)
    holes = (n > 0.72).astype(float) * 0.9
    edge = periodic_noise_2d(s, s, beta=1.6, seed=42)
    a = np.clip(a * (1 - holes) - (a > 0) * (a < 0.98) * np.abs(edge - 0.5) * 1.6, 0, 1)
    mask = Image.fromarray((a * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(0.5))
    save(colorize(mask, (190, 18, 36)), "hanko-red.png")


if __name__ == "__main__":
    paper()
    grain()
    ink_edge()
    enso()
    splatter("splatter-red.png", RED, 51)
    splatter("splatter-ink.png", INK, 52)
    slash()
    brush_vertical()
    brush_underline()
    hanko()
