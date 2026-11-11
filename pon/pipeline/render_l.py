# 横長（1920x1080）の静止画を作る。第20回 make_l.py を回ごとの設定で動くようにしたもの。render_v.py の後に動かす（build/n*.png を使う）。
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from common import ep_dir, episode, words, series

D = ep_dir(); EP = episode(D); WORDS = words(EP); B = D + '/build'
TL = series()['text_layout']
THEME_EN, THEME_JA = EP['theme_en'].rstrip('!') + '!', EP['theme_ja']
base = [Image.open('%s/n%02d.png' % (B, i + 1)).convert('RGB') for i in range(10)]
flip = [Image.open('%s/nf%02d.png' % (B, i + 1)).convert('RGB') for i in range(10)]
bgL = paper_bg(1920, 1080, base[0], 1.0)

# ---- word pages
S_ART = 0.95; ART_BOTTOM = 1020; ART_CX = 520
for i, (en, ja) in enumerate(WORDS):
    t = min(art_top(base[i]), art_top(flip[i]))
    y0 = max(0, int((t - 0.02) * 1344))
    ov = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0))
    paste_c(ov, dots(10, i), 1430, 324)
    paste_c(ov, fit(crayon_text(en, fred(200), RED, stroke=10, seed=10 + i), max_w=800), 1430, 497)
    paste_c(ov, fit(crayon_text(ja, zen(120), INK, stroke=0, seed=40 + i), max_w=760), 1430, 720)
    for tg, im in (('A', base[i]), ('B', flip[i])):
        c = im.crop((0, y0, 752, 1344)); w, h = int(752 * S_ART), int((1344 - y0) * S_ART)
        c = c.resize((w, h), Image.LANCZOS).convert('RGBA')
        al = feather_alpha(w, h, m=40)
        arr = np.asarray(c).copy(); arr[..., 3] = (al * 255).astype(np.uint8)
        pg = bgL.copy(); pg.alpha_composite(Image.fromarray(arr, 'RGBA'), (int(ART_CX - w / 2), ART_BOTTOM - h))
        pg.alpha_composite(ov); pg.convert('RGB').save('%s/lw%02d_%s.png' % (B, i + 1, tg))
print('word pages')

# ---- intro base (the video goes on the left 810 px)
# same geometry as EP11 landscape (measured at 2.5 s): vertical sizes x1.125, centred on the paper panel
pg = bgL.copy()
l1 = rainbow_text("Today's theme is", fred(96), stroke=7, seed=70)
l2 = fit(rainbow_text(THEME_EN, fred(TL['theme_en_font_l_standard']), stroke=12, seed=71), max_w=TL['theme_en_max_w_l'])
l3 = fit(rainbow_text(THEME_JA, hachi(133), stroke=3, seed=72), max_w=1000)
put_ink_top(pg, l1, 1380, 264); put_ink_top(pg, l2, 1381, 376); put_ink_center(pg, l3, 1379, 756)
for nm, l in (('l1', l1), ('l2', l2), ('l3', l3)):
    x0, y0, x1, y1 = ink_box(l); print(nm, 'ink w', x1 - x0 + 1, 'h', y1 - y0 + 1)
pg.convert('RGB').save(B + '/l_intro_base.png')
# crayon edge line between video and paper
ln = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0))
arr = np.zeros((1080, 28, 4), np.float32)
wob = (smooth_noise(1080, 4, 60, 5)[:, 0] - 0.5) * 10
for y in range(1080):
    cx = 14 + wob[y]
    for x in range(28):
        a = np.clip(1 - abs(x - cx) / 4.5, 0, 1)
        arr[y, x] = (88, 96, 40, a * 255)
ln.paste(Image.fromarray(arr.astype(np.uint8), 'RGBA'), (810 - 14, 0))
ln.save(B + '/l_edge.png')
print('intro base saved')

# ---- review
icons = [icon_of(b) for b in base]
CW, CH = 468, 168
cards = [[card(CW, CH, hl, icons[i], WORDS[i][0], 100 + i * 7 + hl, iconbox=(140, 140), fs=96) for hl in (0, 1)] for i in range(10)]
for k in range(11):
    pg = bgL.copy()
    paste_c(pg, fit(rainbow_text("Let's say them all!", fred(80), stroke=6, seed=80), max_w=700), 465, 346)
    paste_c(pg, fit(rainbow_text('Review', fred(240), stroke=12, seed=81), max_w=720), 465, 510)
    paste_c(pg, fit(crayon_text('おさらい', zen(125), rainbow(4), stroke=0, seed=82), max_w=480), 465, 720)
    for i in range(10):
        col, row = i % 2, i // 2
        pg.alpha_composite(cards[i][1 if k == i + 1 else 0], (900 + col * (CW + 18), 72 + row * 192))
    pg.convert('RGB').save('%s/lrv_%02d.png' % (B, k))
print('review done')
