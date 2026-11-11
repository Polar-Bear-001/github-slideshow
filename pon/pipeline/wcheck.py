#!/usr/bin/env python3
# 録った声が正しい単語に聞こえるか（faster-whisper で文字起こし）。聞き取れない語があれば終了コード1。
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ep_dir, episode
from faster_whisper import WhisperModel

D = ep_dir(); EP = episode(D)
m = WhisperModel('small', device='cpu', compute_type='int8')
exp = {'intro': "Today's theme is... %s!" % EP['theme_en'].rstrip('!')}
for i, w in enumerate(EP['words'], 1): exp['w%02d' % i] = w['en']
bad = []
for k, e in exp.items():
    segs, _ = m.transcribe('%s/aud/%s.mp3' % (D, k), language='en', temperature=0, beam_size=5)
    t = ' '.join(s.text.strip() for s in segs)
    norm = lambda s: s.lower().replace("'", '').replace('-', ' ').strip('!. ')
    ok = norm(e) in norm(t) or norm(e).replace(' ', '') in norm(t).replace(' ', '')
    print('%-6s expected %-32s heard %-34s %s' % (k, e, repr(t), 'OK' if ok else '??'))
    if not ok: bad.append(k)
json.dump(bad, open(D + '/wcheck.json', 'w'))
print('聞き取りチェック:', 'OK' if not bad else 'NG ' + ' '.join(bad))
sys.exit(1 if bad else 0)
