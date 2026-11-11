#!/usr/bin/env python3
# 録った声が正しい単語に聞こえるか（faster-whisper で文字起こし）。聞き取れない語があれば終了コード1。
import sys, os, json, re, difflib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ep_dir, episode
from faster_whisper import WhisperModel

D = ep_dir(); EP = episode(D)
m = WhisperModel('small', device='cpu', compute_type='int8')
exp = {'intro': EP['theme_en'].rstrip('!')}   # 導入はテーマ語が聞こえれば OK（「...」や句読点は文字起こしで消える）
for i, w in enumerate(EP['words'], 1): exp['w%02d' % i] = w['en']
bad = []
for k, e in exp.items():
    segs, _ = m.transcribe('%s/aud/%s.mp3' % (D, k), language='en', temperature=0, beam_size=5)
    t = ' '.join(s.text.strip() for s in segs)
    norm = lambda s: re.sub(r'[^a-z ]', '', s.lower().replace('-', ' ')).strip()
    ne, nt = norm(e), norm(t)
    toks = nt.split(); n = len(ne.split())
    grams = [' '.join(toks[i:i + n]) for i in range(max(1, len(toks) - n + 1))]
    ok = ne in nt or ne.replace(' ', '') in nt.replace(' ', '') or any(difflib.SequenceMatcher(None, ne, g).ratio() >= 0.65 for g in grams)
    print('%-6s expected %-32s heard %-34s %s' % (k, e, repr(t), 'OK' if ok else '??'))
    if not ok: bad.append(k)
json.dump(bad, open(D + '/wcheck.json', 'w'))
print('聞き取りチェック:', 'OK' if not bad else 'NG ' + ' '.join(bad))
sys.exit(1 if bad else 0)
