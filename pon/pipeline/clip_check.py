#!/usr/bin/env python3
"""導入動画（Kling）の「作画崩壊」チェック（第19回から。第18回のホップの耳の崩れを受けて追加）。第20回 vs/clip_check.py と同じ。
線のくっきり度（グレー化した画像の Laplacian の分散）を、開始の絵＝最初のフレームを100%として毎フレーム測る。
  ・奥の段(高さ30-55%)／前の段(55-97%) の、0.4〜4秒の平均比と最小比  … 基準は第12〜17回の導入（奥 0.86〜1.02、前 0.70〜0.90）
  ・キャラごとの領域の平均比・最小比・0.60未満のフレーム、キャラごとの横長コンタクトシート（0.4秒おき）
判定：奥の段の平均比が0.75未満、またはキャラ1人の平均比が0.70未満 → 「崩れ疑い」（終了コード1）。
数値だけで決めず、コンタクトシートを目で見る（まばたきの一瞬は崩れではない）。
使い方:  python3 clip_check.py <ep>/vid/intro_raw.mp4 <ep>/chk/clip  [名前:x0,y0,x1,y1 ...]   座標は 716x1280 の動画の画素。
省略時の領域は第18〜20回の構図（奥の段4人＋手前のぽん）。"""
import sys, os, numpy as np, cv2
src, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
cap = cv2.VideoCapture(src); W = int(cap.get(3)); H = int(cap.get(4)); fps = cap.get(5) or 24.0
frames = []
while True:
    ok, f = cap.read()
    if not ok: break
    frames.append(f)
n = len(frames); print('frames %d  fps %.1f  size %dx%d' % (n, fps, W, H))
sx, sy = W / 716.0, H / 1280.0
DEF = {'hop': (0, 360, 270, 720), 'muffin': (190, 360, 380, 720), 'sky': (350, 340, 560, 720), 'ben': (530, 340, 716, 720), 'pon': (60, 700, 650, 1260)}
boxes = {}
for a in sys.argv[3:]:
    k, v = a.split(':'); boxes[k] = tuple(int(float(x)) for x in v.split(','))
if not boxes: boxes = {k: (int(v[0] * sx), int(v[1] * sy), int(v[2] * sx), int(v[3] * sy)) for k, v in DEF.items()}


def sharp(f, b):
    x0, y0, x1, y1 = b; g = cv2.cvtColor(f[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY); return cv2.Laplacian(g, cv2.CV_64F).var()


i0, i1 = int(0.4 * fps), min(n, int(4.0 * fps))


def ratio(b):
    s = np.array([sharp(f, b) for f in frames]); return s / s[0]


flag = []
bands = {'奥の段(30-55%)': (0, int(H * .30), W, int(H * .55)), '前の段(55-97%)': (0, int(H * .55), W, int(H * .97))}
for k, b in bands.items():
    r = ratio(b); m = r[i0:i1].mean(); print('%-14s 平均比 %.2f  最小比 %.2f   (基準 奥0.86-1.02 / 前0.70-0.90)' % (k, m, r[1:].min()))
    if k.startswith('奥') and m < 0.75: flag.append('奥の段の平均比 %.2f < 0.75' % m)
for k, b in boxes.items():
    r = ratio(b); m = r[i0:i1].mean(); bad = [i for i in range(1, n) if r[i] < 0.60]
    print('%-7s 平均比 %.2f  最小比 %.2f  0.60未満: %s' % (k, m, r[1:].min(), ('%d枚 (%s)' % (len(bad), ' '.join('%.1fs' % (i / fps) for i in bad[::max(1, len(bad) // 6)]))) if bad else 'なし'))
    if m < 0.70: flag.append('%s の平均比 %.2f < 0.70' % (k, m))
    idx = [min(n - 1, int(round(t * fps))) for t in np.arange(0, n / fps, 0.4)][:14]; tiles = []
    for i in idx:
        x0, y0, x1, y1 = b; t = cv2.resize(frames[i][y0:y1, x0:x1], (200, int(200 * (y1 - y0) / (x1 - x0))))
        cv2.putText(t, '%.1fs %.2f' % (i / fps, r[i]), (4, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0) if r[i] >= 0.6 else (0, 0, 255), 1); tiles.append(t)
    h = max(t.shape[0] for t in tiles); cols = 7
    rows = [np.hstack([np.pad(t, ((0, h - t.shape[0]), (0, 0), (0, 0))) for t in tiles[j:j + cols]] + [np.zeros((h, 200 * (cols - len(tiles[j:j + cols])), 3), np.uint8)]) for j in range(0, len(tiles), cols)]
    cv2.imwrite('%s/%s_sheet.jpg' % (out, k), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 82])
print('判定:', ('崩れ疑い → ' + '；'.join(flag) + '。コンタクトシート(%s/*_sheet.jpg)を目で確認する' % out) if flag else '基準内（それでもコンタクトシートで耳・しっぽ・顔・手を目で確認）')
sys.exit(1 if flag else 0)
