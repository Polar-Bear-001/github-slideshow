# 縦（1080x1920）の静止画を作る：単語ページ（A/B 2コマ）、導入の文字、おさらい11枚。第20回 make_v.py を回ごとの設定で動くようにしたもの。
#   入力: <ep>/img/01..10.png（1コマ目）, <ep>/img/f01..f10.png（2コマ目、位置合わせ済み）
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from common import ep_dir, episode, words, series

D = ep_dir(); EP = episode(D); WORDS = words(EP); B = D + '/build'
S = series(); TL = S['text_layout']
THEME_EN, THEME_JA = EP['theme_en'].rstrip('!') + '!', EP['theme_ja']
assert len(WORDS) == 10, 'need exactly 10 words'


def fit_vert(img):
    im = img.resize((1080, 1930), Image.LANCZOS); return im.crop((0, 5, 1080, 1925))


base = [normalize_paper(Image.open('%s/img/%02d.png' % (D, i + 1))) for i in range(10)]
flip = [normalize_paper(Image.open('%s/img/f%02d.png' % (D, i + 1))) for i in range(10)]
for i in range(10): base[i].save('%s/n%02d.png' % (B, i + 1)); flip[i].save('%s/nf%02d.png' % (B, i + 1))
print('normalized, paper', [tuple(paper_median(b).astype(int)) for b in base[:3]])

# ---- word pages
TOP_MIN = 672 / 1920.0
bg_w = paper_bg(1080, 1920, base[0], 1.436)
scales = []
for i in range(10):
    t = min(art_top(base[i]), art_top(flip[i]))
    scales.append(min(1.0, (1 - TOP_MIN) / (1 - t)))
print('art scales', [round(x, 3) for x in scales])


def page_img(im, sc):
    f = fit_vert(im).convert('RGBA')
    if sc >= 0.999: return f
    w, h = int(1080 * sc), int(1920 * sc)
    g = f.resize((w, h), Image.LANCZOS)
    al = feather_alpha(w, h, m=28, top=True, bottom=False, left=True, right=True)
    arr = np.asarray(g).copy(); arr[..., 3] = (al * 255).astype(np.uint8)
    pg = bg_w.copy(); pg.alpha_composite(Image.fromarray(arr, 'RGBA'), ((1080 - w) // 2, 1920 - h)); return pg


for i, (en, ja) in enumerate(WORDS):
    ov = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0))
    paste_c(ov, dots(10, i), 540, 210)
    paste_c(ov, fit(crayon_text(en, fred(TL['word_en_font_v']), RED, stroke=11, seed=10 + i), max_w=864), 540, 372)
    paste_c(ov, fit(crayon_text(ja, zen(TL['word_ja_font_v']), INK, stroke=0, seed=40 + i), max_w=864), 540, 590)
    for tg, im in (('A', base[i]), ('B', flip[i])):
        f = page_img(im, scales[i]); f.alpha_composite(ov); f.convert('RGB').save('%s/vw%02d_%s.png' % (B, i + 1, tg))
print('word pages done')

# ---- intro title block (same geometry as EP7-20, measured on the finished videos at 2.5 s)
#   line1 "Today's theme is": Fredoka 85, stroke 6, ink top y=84, ink-centre x=539
#   word: Fredoka 240, stroke 12 (natural size; shrunk only if wider than theme_en_max_w_v), ink top y=184, centre x=540
#   ja  : Hachi Maru Pop 118, RAINBOW per character, outline stroke 3, ink centre (539, 522)
ov = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0))
l1 = rainbow_text("Today's theme is", fred(85), stroke=6, seed=70)
l2 = fit(rainbow_text(THEME_EN, fred(TL['theme_en_font_v_standard']), stroke=12, seed=71), max_w=TL['theme_en_max_w_v'])
l3 = fit(rainbow_text(THEME_JA, hachi(118), stroke=3, seed=72), max_w=900)
put_ink_top(ov, l1, 539, 84); put_ink_top(ov, l2, 540, 184); put_ink_center(ov, l3, 539, 522)
print('intro ink boxes l1/l2/l3', ink_box(l1), ink_box(l2), ink_box(l3))
ov.save(B + '/ov_intro_v.png')

# ---- review
bg0 = paper_bg(1080, 1920, base[0], 1.436)
icons = [icon_of(b) for b in base]
CW, CH = 495, 174
cards = [[card(CW, CH, hl, icons[i], WORDS[i][0], 100 + i * 7 + hl) for hl in (0, 1)] for i in range(10)]


def review_page(hl_idx):
    pg = bg0.copy()
    paste_c(pg, fit(rainbow_text("Let's say them all!", fred(80), stroke=6, seed=80), max_w=690), 540, 0.106 * 1920)
    paste_c(pg, fit(rainbow_text('Review', fred(240), stroke=12, seed=81), max_w=800), 540, 0.195 * 1920)
    paste_c(pg, fit(crayon_text('おさらい', zen(125), rainbow(4), stroke=0, seed=82), max_w=500), 540, 0.305 * 1920)
    for i in range(10):
        col, row = i % 2, i // 2
        x = 33 + col * (CW + 24); y = 768 + row * (CH + 26)
        pg.alpha_composite(cards[i][1 if hl_idx == i + 1 else 0], (x, y))
    return pg.convert('RGB')


for k in range(0, 11): review_page(k).save('%s/vrv_%02d.png' % (B, k))
print('review done')
