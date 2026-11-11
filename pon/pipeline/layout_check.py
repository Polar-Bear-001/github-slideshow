#!/usr/bin/env python3
"""導入の絵の「字幕との重なり」チェック（第22回から。第19〜21回で奥の列が上がって日本語の字幕に重なったのを受けて追加）。
導入動画（7.5cr）を作る前に、導入の絵（img/intro.png）に対して動かす。

  python3 layout_check.py <ep> [画像]      画像を省くと <ep>/img/intro.png

縦の導入の字幕（Today's theme is / テーマ英語 / テーマ日本語）を render_v.py と同じ位置・大きさで計算し、
それぞれの文字の箱（少し広げる）の中で、背景（空・草/丘・雲・太陽・紙色）以外の色がどれだけあるかを測る。
キャラの頭や耳、建物などが入ると増える。
  判定: 日本語の箱が JA_MAX、英語の箱が EN_MAX を超える → NG（終了コード1）
基準（日本語の箱の背景以外の色の割合。第22回に測定）: 第13〜18回 0.1〜4.0%（重ならない）、第19回 7.4%（耳がかかり始め）、
第20回 29.4%・第21回 19.9%（重なる）。第1・2・5回は 0%。
chk/layout.jpg に字幕を重ねた画像と箱を描くので、image_paths で必ず目でも見る。
"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from common import ep_dir, episode, series

D = ep_dir(); EP = episode(D); TL = series()['text_layout']
src = sys.argv[2] if len(sys.argv) > 2 else D + '/img/intro.png'
JA_MAX, EN_MAX = 0.05, 0.05
THEME_EN, THEME_JA = EP['theme_en'].rstrip('!') + '!', EP['theme_ja']

# the vertical intro: the Kling clip (made from this picture) is scaled to fill 1080x1920
pic = Image.open(src).convert('RGB').resize((1080, 1920), Image.LANCZOS)
# title layers exactly as render_v.py
l1 = rainbow_text("Today's theme is", fred(85), stroke=6, seed=70)
l2 = fit(rainbow_text(THEME_EN, fred(TL['theme_en_font_v_standard']), stroke=12, seed=71), max_w=TL['theme_en_max_w_v'])
l3 = fit(rainbow_text(THEME_JA, hachi(118), stroke=3, seed=72), max_w=900)
ov = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0))
boxes = {}
for name, layer, how, cx, cy in (('line1', l1, 'top', 539, 84), ('en', l2, 'top', 540, 184), ('ja', l3, 'center', 539, 522)):
    x0, y0, x1, y1 = ink_box(layer)
    ox = int(round(cx - (x0 + x1) / 2)); oy = int(round(cy - y0)) if how == 'top' else int(round(cy - (y0 + y1) / 2))
    ov.alpha_composite(layer, (ox, oy))
    m = 24
    boxes[name] = (max(0, ox + x0 - m), max(0, oy + y0 - m), min(1080, ox + x1 + m), min(1920, oy + y1 + m))

a = np.asarray(pic).astype(np.float32)
r, g, b = a[..., 0], a[..., 1], a[..., 2]
sky = (b > r + 25) & (b >= g - 10)
grass = (g > r + 5) & (g > b + 15)
pale = (a.min(-1) > 205) & (a.max(-1) - a.min(-1) < 40)              # clouds
cream = (r > 200) & (g > 185) & (b > 130) & (r >= g) & (g >= b)      # paper background (EP1/2 style)
sun = (r > 200) & (g > 170) & (b < 140)
foreign = ~(sky | grass | pale | cream | sun)
res = {}
for k, (x0, y0, x1, y1) in boxes.items():
    res[k] = float(foreign[y0:y1, x0:x1].mean())
bad = []
if res['ja'] > JA_MAX: bad.append('日本語の字幕の位置に背景以外の色 %.1f%%（上限 %.1f%%）: 奥のキャラの頭や物が字幕に重なっている' % (res['ja'] * 100, JA_MAX * 100))
if res['en'] > EN_MAX: bad.append('英語の字幕の位置に背景以外の色 %.1f%%（上限 %.1f%%）' % (res['en'] * 100, EN_MAX * 100))
for k, v in res.items(): print('%-6s box %s  背景以外 %.2f%%' % (k, boxes[k], v * 100))

os.makedirs(D + '/chk', exist_ok=True)
vis = pic.convert('RGBA'); vis.alpha_composite(ov); d = ImageDraw.Draw(vis)
for k, b in boxes.items(): d.rectangle(b, outline=(255, 0, 0, 255) if (k == 'ja' and res[k] > JA_MAX) or (k == 'en' and res[k] > EN_MAX) else (0, 160, 0, 255), width=4)
vis = vis.convert('RGB'); vis.thumbnail((540, 960)); vis.save(D + '/chk/layout.jpg', quality=78)
print('chk/layout.jpg を目で確認すること')
print('字幕との重なりチェック:', 'OK' if not bad else 'NG ' + ' / '.join(bad))
sys.exit(1 if bad else 0)
