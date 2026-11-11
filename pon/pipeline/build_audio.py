#!/usr/bin/env python3
# 60.5秒の音声を組み立てる（第20回 build_audio.py と同じ配置）。入力: <ep>/aud/intro.mp3, w01..w10.mp3 と REF/ref11.wav（締めの音）。
import numpy as np, soundfile as sf, subprocess, sys, os, io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ep_dir, episode, tag, REF

D = ep_dir(); EP = episode(D)
SR = 44100
TOTAL = 60.5   # 導入4秒の標準（第14回から）
SHIFT = 1.0    # 第11回の見本（導入5秒）より導入が1秒短いので、見本から取る区間は1秒早く置く
STAT_TARGET = {'intro': -17.9, 'word': -18.3}


def decode(path, extra=None):
    cmd = ['ffmpeg', '-v', 'error', '-y', '-i', path, '-ac', '1', '-ar', str(SR)]
    if extra: cmd += ['-af', extra]
    cmd += ['-f', 'wav', 'pipe:1']
    raw = subprocess.check_output(cmd)
    x, sr = sf.read(io.BytesIO(raw)); assert sr == SR
    return x.astype(np.float64)


def stat(seg):
    a = seg[np.abs(seg) > 0.01]
    return 20 * np.log10(np.sqrt((a ** 2).mean()) + 1e-12)


def clean(x, target):
    fr = int(0.01 * SR); n = len(x) // fr
    rms = np.array([np.sqrt((x[i * fr:(i + 1) * fr] ** 2).mean()) for i in range(n)])
    act = np.where(rms > 10 ** (-38 / 20))[0]
    a, b = act[0] * fr, (act[-1] + 1) * fr
    y = x[a:b].copy()
    f = int(0.012 * SR)
    y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    for _ in range(6):
        g = 10 ** ((target - stat(y)) / 20)
        y = y * g
    pk = np.abs(y).max()
    if pk > 0.9:
        print('  peak %.3f > 0.9 -> scaled' % pk)
        y *= 0.9 / pk
    return y


def slow(y):
    tmp = D + '/build/_slow_in.wav'; sf.write(tmp, y, SR)
    return decode(tmp, 'atempo=0.6')


def place(buf, y, t):
    i = int(round(t * SR)); buf[i:i + len(y)] += y[:len(buf) - i]


voices = {'intro': D + '/aud/intro.mp3'}
for i in range(1, 11):
    voices[i] = D + '/aud/w%02d.mp3' % i

buf = np.zeros(int(TOTAL * SR))
report = []
ref, _ = sf.read(REF + '/ref11.wav'); assert _ == SR
iv = clean(decode(voices['intro']), STAT_TARGET['intro']); place(buf, iv, 0.45)
assert 0.45 + len(iv) / SR < 3.9, ('intro voice too long for a 4 s intro', len(iv) / SR)
report.append(('intro', 0.45, len(iv) / SR, stat(iv)))
for i in range(1, 11):
    nv = clean(decode(voices[i]), STAT_TARGET['word'])
    sv = slow(nv)
    t0 = 4 + 4 * (i - 1)
    place(buf, nv, t0 + 0.35); place(buf, sv, t0 + 1.85)
    place(buf, nv, 45.4 + 0.95 * (i - 1) + 0.05)
    report.append((i, t0 + 0.35, len(nv) / SR, stat(nv)))
    report.append(('%d slow' % i, t0 + 1.85, len(sv) / SR, stat(sv)))
    assert t0 + 1.85 + len(sv) / SR < t0 + 4.0, ('slow word overruns slot', i, len(sv) / SR)
for name, a, b in [('say', 45.10, 46.30), ('good', 56.10, 57.60), ('bye', 58.15, 60.50)]:
    seg = ref[int(a * SR):int(b * SR)].copy()
    place(buf, seg, a - SHIFT)
    report.append((name, a - SHIFT, b - a, stat(seg)))
f = int(0.3 * SR); buf[-f:] *= np.linspace(1, 0, f)
pk = np.abs(buf).max(); print('mix peak', pk)
if pk > 0.95: buf *= 0.95 / pk
sf.write('%s/%s_audio.wav' % (D, tag(EP)), buf, SR)
for r in report: print(r[0], 'start %.2f dur %.2f stat %.2f' % r[1:])
