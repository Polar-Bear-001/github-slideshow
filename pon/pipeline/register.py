#!/usr/bin/env python3
# 2コマ目(B)を1コマ目(A)に位置合わせする（第18〜20回 measure18.py + reg_lib.py）。
#   入力: <ep>/img/a01..a10.png, b01..b10.png   出力: <ep>/img/01..10.png（=A）, f01..f10.png（位置合わせ後のB、または元のB）
#   判定: SIFT の一致点のずれ（中央値）が 2px 以上あり、位置合わせで 30% 以上減るときだけ位置合わせ後を使う
#         （第20回: Beach は中央値 5.0px→改善24% で「使わない」と判断していた）。
#   ずれの中央値が 12px を超える組は「描き直し候補」として表示し、終了コード 3 を返す。
import cv2, numpy as np, sys, os, shutil, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ep_dir, episode

D = ep_dir(); EP = episode(D); I = D + '/img'
names = [w['en'] for w in EP['words']]


def match(A, B):
    ga = cv2.cvtColor(A, cv2.COLOR_BGR2GRAY); gb = cv2.cvtColor(B, cv2.COLOR_BGR2GRAY)
    sift = cv2.SIFT_create(4000)
    ka, da = sift.detectAndCompute(ga, None); kb, db = sift.detectAndCompute(gb, None)
    mt = cv2.BFMatcher().knnMatch(db, da, k=2)
    good = [m for m, n in mt if m.distance < 0.75 * n.distance]
    return ka, kb, good


def disp(A, B):
    ka, kb, good = match(A, B)
    return np.array([np.hypot(kb[m.queryIdx].pt[0] - ka[m.trainIdx].pt[0], kb[m.queryIdx].pt[1] - ka[m.trainIdx].pt[1]) for m in good])


def register(A, B):
    """similarity transform (scale+rot+shift) mapping B onto A, from SIFT matches"""
    ka, kb, good = match(A, B)
    src = np.float32([kb[m.queryIdx].pt for m in good]); dst = np.float32([ka[m.trainIdx].pt for m in good])
    M, inl = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=3.0)
    return M, int(inl.sum()), len(good)


report, redo = [], []
for n in range(1, 11):
    A = cv2.imread('%s/a%02d.png' % (I, n)); B = cv2.imread('%s/b%02d.png' % (I, n))
    assert A is not None and B is not None, ('missing a/b', n)
    d = disp(A, B); M, ni, ng = register(A, B)
    h, w = A.shape[:2]; Bw = cv2.warpAffine(B, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    d2 = disp(A, Bw)
    before, after = float(np.median(d)), float(np.median(d2))
    use = before >= 2.0 and after <= before * 0.7
    shutil.copy('%s/a%02d.png' % (I, n), '%s/%02d.png' % (I, n))
    if use: cv2.imwrite('%s/f%02d.png' % (I, n), Bw)
    else: shutil.copy('%s/b%02d.png' % (I, n), '%s/f%02d.png' % (I, n))
    s = np.hypot(M[0, 0], M[1, 0]); rot = np.degrees(np.arctan2(M[1, 0], M[0, 0]))
    line = '%02d %-12s med %.1f -> %.1f px  scale %.3f rot %.2f  inl %d/%d  %s' % (n, names[n - 1], before, after, s, rot, ni, ng, 'registered' if use else 'not registered')
    print(line); report.append(dict(n=n, word=names[n - 1], before=round(before, 1), after=round(after, 1), registered=use))
    if min(before, after) > 12: redo.append(n)
json.dump(report, open(D + '/register.json', 'w'), indent=1)
if redo:
    print('REDO CANDIDATES (2コマ目が大きくずれている):', redo); sys.exit(3)
