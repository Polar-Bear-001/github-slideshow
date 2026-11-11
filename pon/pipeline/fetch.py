#!/usr/bin/env python3
# 生成結果をサンドボックスに取り込む。episode.json の jobs.<key>.url を読んでダウンロードする。
#   python3 fetch.py <ep> [keys...]     keys 省略時は全部。置き場所:
#     aNN/bNN -> img/aNN.png, img/bNN.png   intro -> img/intro.png   video -> vid/intro_raw.mp4   vNN / vintro -> aud/wNN.mp3, aud/intro.mp3
import json, os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ep_dir, episode

D = ep_dir(); EP = episode(D); jobs = EP.get('jobs', {})
for sub in ('img', 'vid', 'aud'): os.makedirs(D + '/' + sub, exist_ok=True)


def dest(k):
    if k[0] in 'ab' and k[1:].isdigit(): return '%s/img/%s.png' % (D, k)
    if k == 'intro': return D + '/img/intro.png'
    if k == 'video': return D + '/vid/intro_raw.mp4'
    if k == 'vintro': return D + '/aud/intro.mp3'
    if k[0] == 'v' and k[1:].isdigit(): return '%s/aud/w%s.mp3' % (D, k[1:])
    return None


keys = sys.argv[2:] or list(jobs)
bad = []
for k in keys:
    j = jobs.get(k); p = dest(k)
    if not j or not p or not j.get('url'): print('skip', k); continue
    r = subprocess.run(['curl', '-fsSL', '--retry', '3', '-o', p, j['url']])
    if r.returncode or not os.path.getsize(p): bad.append(k)
    else: print('ok', k, '->', os.path.relpath(p, D), os.path.getsize(p) // 1024, 'KB')
if bad: print('FAILED', bad); sys.exit(1)
