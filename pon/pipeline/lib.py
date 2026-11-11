# 絵本風（クレヨン）文字・紙の背景・カードなどの共通部品。第20回の lib.py をそのまま移したもの（フォントの場所だけ設定化）。
import numpy as np, cv2, os
from PIL import Image, ImageDraw, ImageFont
H = os.environ.get('PON_HOME', '/home/user')
FONTS = os.environ.get('PON_FONTS', H + '/fonts')
FRED = FONTS + '/Fredoka.ttf'; ZEN = FONTS + '/ZenMaru-Bold.ttf'; HACHI = FONTS + '/HachiMaruPop-Regular.ttf'
BROWN = (74, 48, 36); TARGET = (251, 240, 187)
PAL = [(214, 57, 45), (238, 140, 32), (96, 170, 64), (56, 128, 200), (138, 84, 174), (232, 72, 120)]
RED = (206, 48, 42)
INK = (66, 48, 42)


def fred(size, w=700):
    f = ImageFont.truetype(FRED, int(size)); f.set_variation_by_axes([w, 100]); return f
def zen(size): return ImageFont.truetype(ZEN, int(size))
def hachi(size): return ImageFont.truetype(HACHI, int(size))   # intro Japanese theme word (rainbow, per character) of EP1-11


def smooth_noise(h, w, scale, seed):
    rng = np.random.RandomState(seed)
    n = rng.rand(h // scale + 3, w // scale + 3).astype(np.float32)
    return cv2.resize(n, (w, h), interpolation=cv2.INTER_CUBIC)


def streak(h, w, seed, sx=0.7, sy=5.0, ang=35):
    rng = np.random.RandomState(seed)
    n = rng.rand(h, w).astype(np.float32)
    n = cv2.GaussianBlur(n, (0, 0), sigmaX=sx, sigmaY=sy)
    M = cv2.getRotationMatrix2D((w / 2, h / 2), ang, 1.0)
    n = cv2.warpAffine(n, M, (w, h), borderMode=cv2.BORDER_REFLECT)
    return (n - n.mean()) / (n.std() + 1e-6)


def over(rgb, a, rgb2, a2):
    an = a2 + a * (1 - a2)
    out = (rgb2 * a2[..., None] + rgb * (a * (1 - a2))[..., None]) / np.maximum(an[..., None], 1e-6)
    return out, an


def crayon_text(text, font, colors, stroke=0, outline=BROWN, seed=3, wobble=1.8, rough=0.16):
    """colors: one RGB or a list of RGB per character."""
    if isinstance(colors[0], int): colors = [colors] * len(text)
    pad = stroke + 18
    xs = [font.getlength(text[:i]) for i in range(len(text))]
    tw = int(font.getlength(text)); asc, desc = font.getmetrics()
    W = tw + 2 * pad; Hh = asc + desc + 2 * pad
    def mask(chars, st):
        m = Image.new('L', (W, Hh), 0); d = ImageDraw.Draw(m)
        for i in chars:
            if text[i] == ' ': continue
            d.text((pad + xs[i], pad), text[i], font=font, fill=255, stroke_width=st, stroke_fill=255)
        return np.asarray(m).astype(np.float32) / 255
    groups = {}
    for i, ch in enumerate(text):
        if ch != ' ': groups.setdefault(tuple(colors[i]), []).append(i)
    # wobble field (shared)
    dx = (smooth_noise(Hh, W, 28, seed) - 0.5) * 2 * wobble
    dy = (smooth_noise(Hh, W, 28, seed + 1) - 0.5) * 2 * wobble
    gx, gy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(Hh, dtype=np.float32))
    fine = cv2.GaussianBlur(np.random.RandomState(seed + 2).rand(Hh, W).astype(np.float32), (0, 0), 0.8)
    def finish(m):
        m = cv2.remap(m, gx + dx, gy + dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        m = cv2.GaussianBlur(m, (0, 0), 1.1) + (fine - 0.5) * rough * 2 * (m > 0.02)
        return np.clip((m - 0.5) * 5 + 0.5, 0, 1)
    rgb = np.zeros((Hh, W, 3), np.float32); a = np.zeros((Hh, W), np.float32)
    if stroke > 0:
        om = finish(mask(range(len(text)), stroke))
        t = streak(Hh, W, seed + 5, 0.8, 3.0, 20)
        oc = np.array(outline, np.float32)[None, None, :] * (1 + 0.10 * t[..., None])
        rgb, a = over(rgb, a, np.clip(oc, 0, 255), om)
    for k, (col, idx) in enumerate(groups.items()):
        fm = finish(mask(idx, 0))
        t = streak(Hh, W, seed + 11 + k, 0.7, 5.0, 35)
        fc = np.array(col, np.float32)[None, None, :] * (1 + 0.09 * t[..., None])
        sp = (np.random.RandomState(seed + 21 + k).rand(Hh, W) > 0.94).astype(np.float32) * 0.30
        fc = fc * (1 - sp[..., None]) + np.array((250, 240, 200), np.float32)[None, None, :] * sp[..., None]
        rgb, a = over(rgb, a, np.clip(fc, 0, 255), fm)
    ys, xs_ = np.where(a > 0.03)
    y0, y1, x0, x1 = max(ys.min() - 3, 0), min(ys.max() + 4, Hh), max(xs_.min() - 3, 0), min(xs_.max() + 4, W)
    out = np.dstack([rgb, a * 255])[y0:y1, x0:x1].clip(0, 255).astype(np.uint8)
    return Image.fromarray(out, 'RGBA')


def rainbow(n, start=0):
    return [PAL[(start + i) % len(PAL)] for i in range(n)]


def rainbow_text(text, font, stroke=0, start=0, **kw):
    cols, k = [], start
    for ch in text:
        if ch == ' ': cols.append(PAL[0]); continue
        cols.append(PAL[k % len(PAL)]); k += 1
    return crayon_text(text, font, cols, stroke=stroke, **kw)


def fit(img, max_w=None, max_h=None):
    s = 1.0
    if max_w and img.width > max_w: s = min(s, max_w / img.width)
    if max_h and img.height > max_h: s = min(s, max_h / img.height)
    if s < 1: img = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.LANCZOS)
    return img


def paste_c(canvas, layer, cx, cy):
    canvas.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))


def dots(n, cur, d=30, gap=59, lw=3):
    S = 4
    W = (n - 1) * gap + d + 8; Hh = d + 8
    im = Image.new('RGBA', (W * S, Hh * S), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    for i in range(n):
        x0 = (4 + i * gap) * S; y0 = 4 * S
        dr.ellipse([x0, y0, x0 + d * S, y0 + d * S], fill=(RED + (255,)) if i == cur else (252, 246, 215, 255), outline=BROWN + (255,), width=lw * S)
    return im.resize((W, Hh), Image.LANCZOS)


def paper_median(img, y0=0.0, y1=0.25):
    a = np.asarray(img.convert('RGB')); h = a.shape[0]
    return np.median(a[int(h * y0):int(h * y1)].reshape(-1, 3), axis=0)


def normalize_paper(img):
    img = img.convert('RGB'); med = paper_median(img)
    gain = np.array(TARGET, np.float32) / med
    out = np.clip(np.asarray(img).astype(np.float32) * gain[None, None, :], 0, 255).astype(np.uint8)
    res = Image.fromarray(out)
    chk = paper_median(res)
    assert np.all(np.abs(chk - np.array(TARGET)) <= 3), ('paper colour off', chk)
    return res


def mirror_tile(strip, w, h):
    sh, sw = strip.shape[:2]
    cols = int(np.ceil(w / sw)); rows = int(np.ceil(h / sh))
    row = []
    for c in range(cols): row.append(strip if c % 2 == 0 else strip[:, ::-1])
    r0 = np.concatenate(row, axis=1)
    rws = [r0 if r % 2 == 0 else r0[::-1] for r in range(rows)]
    return np.concatenate(rws, axis=0)[:h, :w]


def paper_bg(w, h, src_norm, scale):
    s = src_norm.crop((0, 0, src_norm.width, int(src_norm.height * 0.27)))
    s = s.resize((int(s.width * scale), int(s.height * scale)), Image.LANCZOS)
    return Image.fromarray(mirror_tile(np.asarray(s), w, h)).convert('RGBA')


def feather_alpha(w, h, m=40, top=True, bottom=True, left=True, right=True):
    a = np.ones((h, w), np.float32)
    ramp = lambda n: np.clip(np.arange(n) / m, 0, 1)
    if top: a *= ramp(h)[:, None]
    if bottom: a *= ramp(h)[::-1][:, None]
    if left: a *= ramp(w)[None, :]
    if right: a *= ramp(w)[::-1][None, :]
    return a


# ---- shared helpers (used by render_v / render_l)
def ink_box(im):
    a = np.asarray(im)[..., 3]; ys, xs = np.where(a > 60); return xs.min(), ys.min(), xs.max(), ys.max()


def put_ink_top(canvas, layer, cx, top):
    x0, y0, x1, y1 = ink_box(layer)
    canvas.alpha_composite(layer, (int(round(cx - (x0 + x1) / 2)), int(round(top - y0))))


def put_ink_center(canvas, layer, cx, cy):
    x0, y0, x1, y1 = ink_box(layer)
    canvas.alpha_composite(layer, (int(round(cx - (x0 + x1) / 2)), int(round(cy - (y0 + y1) / 2))))


def art_top(img):
    a = np.asarray(img.convert('RGB')).astype(np.float32)
    d = np.sqrt(((a - np.array(TARGET, np.float32)) ** 2).sum(-1))
    rows = np.where((d > 45).sum(1) > 6)[0]
    return rows.min() / a.shape[0]


def icon_of(img):
    a = np.asarray(img.convert('RGB')).astype(np.float32); h = a.shape[0]
    d = np.sqrt(((a - np.array(TARGET, np.float32)) ** 2).sum(-1)); d[: int(h * 0.30)] = 0
    m = (d > 40).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8)); m = cv2.dilate(m, np.ones((5, 5), np.uint8))
    x, y, w, hh = cv2.boundingRect(m)
    al = np.clip((d - 22) / 26, 0, 1); al = cv2.morphologyEx(al, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)); al = cv2.GaussianBlur(al, (0, 0), 1.0)
    return Image.fromarray(np.dstack([a, al * 255]).clip(0, 255).astype(np.uint8)[y:y + hh, x:x + w], 'RGBA')


def card(w, h, hl, icon, word, seed, iconbox=(150, 150), fs=100):
    S = 2
    im = Image.new('RGBA', (w * S, h * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    border = RED if hl else (134, 102, 66)
    d.rounded_rectangle([3 * S, 3 * S, (w - 3) * S, (h - 3) * S], radius=22 * S, fill=(252, 243, 205, 255), outline=border + (255,), width=(6 if hl else 3) * S)
    im = im.resize((w, h), Image.LANCZOS)
    arr = np.asarray(im).astype(np.float32); t = streak(h, w, seed, 0.6, 2.0, 25)
    arr[..., :3] = np.clip(arr[..., :3] * (1 + 0.022 * t[..., None]), 0, 255); im = Image.fromarray(arr.astype(np.uint8), 'RGBA')
    ic = icon.copy(); ic.thumbnail(iconbox, Image.LANCZOS)
    im.alpha_composite(ic, (int(16 + (iconbox[0] - ic.width) / 2), int((h - ic.height) / 2)))
    tx = fit(crayon_text(word, fred(fs), RED if hl else (77, 52, 38), stroke=0, seed=seed + 3), max_w=int(w * 0.56), max_h=int(h * 0.55))
    paste_c(im, tx, int(w * 0.30 + (w * 0.70 - 16) / 2), h / 2 + 3)
    return im


def review_hl(k):
    """review segment frame k (0..329) -> highlighted card index (0 = none, 1..10)"""
    t = 45 + k / 30.0
    return 0 if t < 46.4 else min(10, int((t - 46.4) / 0.95) + 1)
