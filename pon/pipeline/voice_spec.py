#!/usr/bin/env python3
"""声の固定設定（第1回から）と、送信前・録音後のチェック。第20回 vs/voice_spec.py を episode.json で動くようにしたもの。

  python3 voice_spec.py <ep> pre             # 送信前チェック（<ep>/batch_voice.json。prompts.py が作る）。NGなら終了コード1
  python3 voice_spec.py <ep> post            # 録音後チェック（<ep>/aud/intro.mp3, w01.mp3 … w10.mp3）。FAILなら終了コード1
  録り直し1〜2本だけのときは --retake を付ける。

固定設定（変えるときは series.json と RUNBOOK.md を同時に書き換える）
  - モデル elevenlabs_v4。params は prompt と dialogue だけ（stability・similarity_boost・speed などは付けない）。
  - 単語の文字は「Walk!」のように英単語＋「!」1つ。ピリオド・疑問符・「...」は付けない（第13〜15回は「.」で録ってしまい、声が低く暗くなった）。
  - 導入の文字は「Today's theme is... Actions!」。ぽん（Archie）。
  - 単語の担当は ぽん→ホップ→マフィン→スカイ→ベン を2周。
"""
import json, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import series

S = series()
MODEL = S['models']['voice']['model']
VOICE_IDS = {c['ja']: (c['voice']['name'], c['voice']['voice_id']) for c in S['characters'].values()}
CYCLE = [S['characters'][k]['ja'] for k in S['rotation']]
NAME_OF = {vid: (ch, nm) for ch, (nm, vid) in VOICE_IDS.items()}
INTRO_RE = re.compile(r"^Today's theme is\.\.\. [A-Z][A-Za-z ]*!$")
WORD_RE = re.compile(r"^[A-Z][A-Za-z]*(?: [A-Za-z]+)*!$")
ALLOWED_PARAMS = {'prompt', 'dialogue'}
COST_PER_LINE = 0.23

# 基準値＝第2〜12回に「!」で録った単語（声ごとの中央値）。導入は「Today's theme is…」15回分の重心の中央値。
BASE = {
    'Archie': dict(f0=234.1, cent=1275.2, dur=0.49),
    'Bob':    dict(f0=178.4, cent=1402.8, dur=0.59),
    'Grady':  dict(f0=171.4, cent=1273.2, dur=0.51),
    'Bella':  dict(f0=316.7, cent=1653.4, dur=0.69),
    'Annie':  dict(f0=285.4, cent=1574.5, dur=0.53),
}
INTRO_CENT = 1578.0
F0_RANGE = {'Archie': (70, 260), 'Bob': (70, 260), 'Grady': (70, 260), 'Bella': (120, 420), 'Annie': (120, 420)}
F0_FAIL = 0.85     # 10語の平均がこれ未満なら FAIL（低い声）
CENT_WARN = 0.90   # 重心（音の明るさ）の平均がこれ未満なら警告
WORD_LOW = 0.70    # 1語がこれ未満なら「低い」印


def check_pre(batch, retake=False):
    err, warn = [], []
    if batch.get('model') != MODEL:
        err.append('モデルが %r（決まりは %s）' % (batch.get('model'), MODEL))
    items = batch.get('items', [])
    keys = [it.get('key') for it in items]
    if len(set(keys)) != len(keys):
        err.append('同じ key が重複している: %s' % keys)
    if not retake and keys != ['intro'] + ['w%02d' % i for i in range(1, 11)]:
        err.append('key が intro, w01…w10 の順になっていない: %s' % keys)
    for it in items:
        k, p = it.get('key'), it.get('params', {})
        extra = set(p) - ALLOWED_PARAMS
        if extra:
            err.append('%s: 余計なパラメータ %s' % (k, sorted(extra)))
        d = p.get('dialogue', [])
        if len(d) != 1:
            err.append('%s: dialogue は1行だけ（%d行）' % (k, len(d))); continue
        t, vid = d[0].get('text', ''), d[0].get('voice_id')
        if p.get('prompt') != t:
            err.append('%s: prompt と text が違う（%r / %r）' % (k, p.get('prompt'), t))
        if d[0].get('voice_type') != 'preset':
            err.append('%s: voice_type が preset でない' % k)
        if vid not in NAME_OF:
            err.append('%s: 声ID %s が表にない' % (k, vid)); continue
        ch, nm = NAME_OF[vid]
        if k == 'intro':
            if ch != 'ぽん': err.append('intro: 声が %s（ぽん＝Archie の決まり）' % nm)
            if not INTRO_RE.match(t): err.append("intro: 文字が %r" % t)
        else:
            if not WORD_RE.match(t): err.append('%s: 文字が %r（英単語＋「!」1つだけ）' % (k, t))
            m = re.match(r'w(\d\d)$', k or '')
            if m and not retake and CYCLE[(int(m.group(1)) - 1) % 5] != ch:
                warn.append('%s: 担当が %s（ふつうは %s）' % (k, ch, CYCLE[(int(m.group(1)) - 1) % 5]))
    return err, warn, len(items)


def measure(fn, voice):
    import numpy as np, librosa, warnings
    warnings.filterwarnings('ignore')
    SR = 22050
    y, _ = librosa.load(fn, sr=SR)
    lo, hi = F0_RANGE[voice]
    f, vf, vp = librosa.pyin(y, fmin=lo, fmax=hi, sr=SR, frame_length=2048, hop_length=128)
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=128)[0][:len(f)]
    p = f[vf & (rms > rms.max() * 0.2)]
    Sx = np.abs(librosa.stft(y, n_fft=2048, hop_length=256)); r2 = librosa.feature.rms(S=Sx)[0]
    cent = float(np.median(librosa.feature.spectral_centroid(S=Sx, sr=SR)[0][r2 > r2.max() * 0.2]))
    fr = int(0.01 * SR); n = len(y) // fr
    e = np.array([np.sqrt((y[i * fr:(i + 1) * fr] ** 2).mean()) for i in range(n)])
    a = np.where(e > 10 ** (-38 / 20))[0]
    dur = (a[-1] - a[0] + 1) / 100 if len(a) else 0.0
    return dict(f0=float(np.median(p)) if len(p) >= 4 else None, cent=cent, dur=dur)


def check_post(batch, aud_dir, retake=False):
    import numpy as np
    rows, ratios, intro_ratio = [], [], None
    for it in batch['items']:
        k = it['key']; vid = it['params']['dialogue'][0]['voice_id']; ch, nm = NAME_OF[vid]
        fn = os.path.join(aud_dir, k + '.mp3')
        if not os.path.exists(fn):
            rows.append((k, nm, 'ファイルなし')); continue
        m = measure(fn, nm)
        if k == 'intro':
            intro_ratio = m['cent'] / INTRO_CENT; rows.append((k, nm, '重心比 %.2f' % intro_ratio)); continue
        b = BASE[nm]
        r = (m['f0'] / b['f0'] if m['f0'] else None, m['cent'] / b['cent'], m['dur'] / b['dur'])
        ratios.append(r)
        flag = '低い' if (r[0] is not None and r[0] < WORD_LOW) else ''
        rows.append((k, nm, 'F0比 %s 重心比 %.2f 長さ比(参考) %.2f %s' % (('%.2f' % r[0]) if r[0] else '--', r[1], r[2], flag)))
    f0s = [r[0] for r in ratios if r[0] is not None]
    mf = float(np.mean(f0s)) if f0s else None
    mc = float(np.mean([r[1] for r in ratios])) if ratios else None
    verdict, notes = 'PASS', []
    if mf is not None and mf < F0_FAIL:
        verdict = 'WARN' if retake else 'FAIL'; notes.append('声の高さの平均比 %.2f < %.2f' % (mf, F0_FAIL))
    if mc is not None and mc < CENT_WARN:
        verdict = verdict if verdict != 'PASS' else 'WARN'; notes.append('音の明るさの平均比 %.2f < %.2f' % (mc, CENT_WARN))
    if intro_ratio is not None and intro_ratio < 0.85:
        verdict = verdict if verdict != 'PASS' else 'WARN'; notes.append('導入の音の明るさ比 %.2f < 0.85' % intro_ratio)
    return verdict, rows, (mf, mc), notes


def main(argv):
    retake = '--retake' in argv
    argv = [a for a in argv if a != '--retake']
    if len(argv) < 3: print(__doc__); return 2
    d, cmd = argv[1], argv[2]
    batch = json.load(open(os.path.join(d, 'batch_voice.json')))
    if cmd == 'pre':
        err, warn, n = check_pre(batch, retake)
        print('%d本、約 %.1f cr' % (n, n * COST_PER_LINE))
        for w in warn: print('警告:', w)
        for e in err: print('NG  :', e)
        print('送信前チェック:', 'OK' if not err else 'NG（直すまで送らない）')
        return 0 if not err else 1
    if cmd == 'post':
        verdict, rows, (mf, mc), notes = check_post(batch, os.path.join(d, 'aud'), retake)
        for r in rows: print('%-6s %-7s %s' % r)
        print('平均比 F0 %s 重心 %s' % tuple(('%.2f' % x) if x is not None else '--' for x in (mf, mc)))
        for n_ in notes: print('  *', n_)
        print('録音後チェック:', verdict)
        return 1 if verdict == 'FAIL' else 0
    print(__doc__); return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv))
