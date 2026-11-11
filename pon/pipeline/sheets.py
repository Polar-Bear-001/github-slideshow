#!/usr/bin/env python3
# 目で見るための縮小シート（解剖チェック用）。sandbox_exec の image_paths で開ける大きさ（1枚 < 120KB）にする。
#   python3 sheets.py <ep> words   -> chk/words_1.jpg, words_2.jpg（A/B を並べた5語ずつ、幅500px以上/語）
#   python3 sheets.py <ep> intro   -> chk/intro.jpg（導入の絵）
#   python3 sheets.py <ep> final   -> chk/final_v.jpg, final_l.jpg（完成動画の 2,6,10,30,48,56,59 秒）
import sys, os, subprocess
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ep_dir, episode, tag

D = ep_dir(); EP = episode(D); what = sys.argv[2]; C = D + '/chk'; os.makedirs(C, exist_ok=True)


def save(im, fn, maxkb=120):
    q = 80
    while True:
        im.save(fn, quality=q)
        if os.path.getsize(fn) < maxkb * 1024 or q <= 40: break
        q -= 8
    print(fn, os.path.getsize(fn) // 1024, 'KB')


if what == 'words':
    for part, rng in ((1, range(1, 6)), (2, range(6, 11))):
        tiles = []
        for n in rng:
            a = Image.open('%s/img/a%02d.png' % (D, n)).convert('RGB'); b = Image.open('%s/img/f%02d.png' % (D, n)).convert('RGB')
            for im in (a, b):
                im = im.crop((0, int(im.height * 0.30), im.width, im.height)); im.thumbnail((260, 520)); tiles.append(im)
        W = sum(t.width for t in tiles[:2]) + 10; Hh = max(t.height for t in tiles)
        sheet = Image.new('RGB', (W * 5, Hh + 24), 'white'); dr = ImageDraw.Draw(sheet)
        for i in range(5):
            x = i * W; sheet.paste(tiles[2 * i], (x, 24)); sheet.paste(tiles[2 * i + 1], (x + tiles[2 * i].width + 4, 24))
            dr.text((x + 4, 4), '%d %s (A | B)' % (rng[i], EP['words'][rng[i] - 1]['en']), fill='black')
        save(sheet, '%s/words_%d.jpg' % (C, part))
elif what == 'intro':
    im = Image.open(D + '/img/intro.png').convert('RGB'); im.thumbnail((540, 960)); save(im, C + '/intro.jpg')
elif what == 'final':
    for k in 'vl':
        fn = '%s/%s_%s.mp4' % (D, tag(EP), k); tiles = []
        for t in (2, 6, 10, 30, 48, 56, 59):
            out = '%s/_f%s_%d.png' % (C, k, t)
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', fn, '-frames:v', '1', out], check=True)
            im = Image.open(out).convert('RGB'); im.thumbnail((240, 240) if k == 'l' else (180, 320)); tiles.append(im)
        sheet = Image.new('RGB', (sum(t.width for t in tiles), max(t.height for t in tiles)), 'white'); x = 0
        for t in tiles: sheet.paste(t, (x, 0)); x += t.width
        save(sheet, '%s/final_%s.jpg' % (C, k))
