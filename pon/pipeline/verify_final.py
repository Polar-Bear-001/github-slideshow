#!/usr/bin/env python3
"""完成動画の数値チェック（60.5秒の標準）。第20回 vs/verify_final.py と同じ。アップロードする前に必ず通す。

  python3 verify_final.py <ep>_v.mp4 <ep>_l.mp4 [前回の縦 .mp4]

見るもの：縦と横長の大きさ・コーデック・30fps・1815フレーム・60.5秒／音声(AAC 48kHz モノ)の長さ／縦と横長の音声が完全に同じか
／音が割れていない・最後の0.3秒でフェードアウトしている／導入と単語10語の音量が標準(−17.9／−18.3dB)の±1.5dB以内か
／前回の動画を付けたときは、単語ごとの音量の差が1dB以内か。最後に FP 行（この回の指紋）を出す。
"""
import subprocess, json, sys, hashlib
import numpy as np

SPEC = dict(total=60.5, fps='30/1', frames=1815, vsize={'v': (1080, 1920), 'l': (1920, 1080)}, sr=48000,
            intro_db=-17.9, word_db=-18.3, tol_db=1.5, prev_tol_db=1.0, w0=4.0)
SR = 44100


def probe(fn):
    out = subprocess.check_output(['ffprobe', '-v', 'error', '-count_packets', '-show_entries',
                                   'stream=codec_type,codec_name,width,height,r_frame_rate,nb_read_packets,sample_rate,channels,duration',
                                   '-of', 'json', fn])
    return {s['codec_type']: s for s in json.loads(out)['streams']}


def decode(fn):
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', fn, '-vn', '-ac', '1', '-ar', str(SR), '-f', 'f32le', 'pipe:1'])
    return np.frombuffer(raw, np.float32).astype(np.float64)


def stat(seg):
    a = seg[np.abs(seg) > 0.01]
    return float(20 * np.log10(np.sqrt((a ** 2).mean()) + 1e-12)) if len(a) else -99.0


def slots(x):
    d = {'intro': stat(x[int(0.4 * SR):int(3.9 * SR)])}
    for i in range(1, 11):
        t0 = SPEC['w0'] + 4 * (i - 1)
        d['w%02d' % i] = stat(x[int((t0 + 0.2) * SR):int((t0 + 1.8) * SR)])
    return d


def main(argv):
    if len(argv) < 3:
        print(__doc__); return 2
    fv, fl = argv[1], argv[2]
    prev = argv[3] if len(argv) > 3 else None
    bad, notes, aud = [], [], {}
    for tg, fn in (('v', fv), ('l', fl)):
        s = probe(fn); v, a = s['video'], s['audio']
        if v['codec_name'] != 'h264': bad.append('%s: 映像が %s' % (tg, v['codec_name']))
        if (v['width'], v['height']) != SPEC['vsize'][tg]: bad.append('%s: 大きさ %dx%d' % (tg, v['width'], v['height']))
        if v['r_frame_rate'] != SPEC['fps']: bad.append('%s: フレームレート %s' % (tg, v['r_frame_rate']))
        if int(v['nb_read_packets']) != SPEC['frames']: bad.append('%s: フレーム数 %s（標準 %d）' % (tg, v['nb_read_packets'], SPEC['frames']))
        if abs(float(v['duration']) - SPEC['total']) > 0.03: bad.append('%s: 映像の長さ %s 秒' % (tg, v['duration']))
        if a['codec_name'] != 'aac' or int(a['sample_rate']) != SPEC['sr'] or int(a['channels']) != 1:
            bad.append('%s: 音声が %s %s Hz %dch（標準 aac 48000Hz モノ）' % (tg, a['codec_name'], a['sample_rate'], int(a['channels'])))
        if abs(float(a['duration']) - SPEC['total']) > 0.05: bad.append('%s: 音声の長さ %s 秒' % (tg, a['duration']))
        x = decode(fn); aud[tg] = x
        pk = float(np.abs(x).max())
        if pk > 0.97: bad.append('%s: 音のピーク %.3f（割れる）' % (tg, pk))
        if np.abs(x[-int(0.02 * SR):]).max() > 0.02: bad.append('%s: 最後がフェードアウトしていない' % tg)
        print('%s: %dx%d %s %s枚 %.2f秒 / 音声 %s %sHz 最大 %.3f' % (tg, v['width'], v['height'], v['r_frame_rate'], v['nb_read_packets'], float(v['duration']), a['codec_name'], a['sample_rate'], pk))
    md = {t: hashlib.md5(aud[t].astype(np.float32).tobytes()).hexdigest() for t in aud}
    if md['v'] != md['l']: bad.append('縦と横長の音声が同じでない（%s / %s）' % (md['v'][:8], md['l'][:8]))
    d = slots(aud['v'])
    dp = slots(decode(prev)) if prev else None
    print('音量(dB)  標準  ' + ('前回  差' if dp else ''))
    for k, val in d.items():
        std = SPEC['intro_db'] if k == 'intro' else SPEC['word_db']
        flag = ''
        if abs(val - std) > SPEC['tol_db']: flag = ' ←標準から外れている'; bad.append('%s の音量 %.1fdB（標準 %.1f±%.1f）' % (k, val, std, SPEC['tol_db']))
        line = '%-6s %6.1f %6.1f' % (k, val, std)
        if dp:
            df = val - dp[k]; line += ' %6.1f %5.1f' % (dp[k], df)
            if abs(df) > SPEC['prev_tol_db']: flag += ' ←前回と1dB以上違う'; notes.append('%s: 前回との音量差 %.1fdB' % (k, df))
        print(line + flag)
    fp = dict(total=SPEC['total'], frames=SPEC['frames'], audio_md5=md['v'][:12], intro_db=round(d['intro'], 1),
              word_db=round(float(np.mean([d['w%02d' % i] for i in range(1, 11)])), 1))
    print('FP', json.dumps(fp))
    for n in notes: print('注意:', n)
    for b in bad: print('NG  :', b)
    print('完成動画チェック:', 'OK（アップロードしてよい）' if not bad else 'NG（直すまでアップロードしない）')
    return 0 if not bad else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
