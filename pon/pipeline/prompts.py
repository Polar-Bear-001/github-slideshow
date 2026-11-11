#!/usr/bin/env python3
"""回の設定（episode.json）から、Higgsfield に送る生成リクエストを作る。手で打たずに、出力をそのまま batch ツールに渡す。

  python3 prompts.py <episode.json> check   # 10語・担当の巡回・使用済み語との重複・必須項目を確かめる（NGなら終了コード1）
  python3 prompts.py <episode.json> a       # 単語の1コマ目10枚  -> generate_image_batch の requests（index 1..10）
  python3 prompts.py <episode.json> b       # 2コマ目10枚（jobs.aNN が必要）
  python3 prompts.py <episode.json> intro   # 導入の絵1枚       -> generate_image の params
  python3 prompts.py <episode.json> video   # 導入動画1本（jobs.intro が必要） -> generate_video の params
  python3 prompts.py <episode.json> voice   # 声11本 -> generate_audio_batch の requests（index 0=intro, 1..10）。batch_voice.json も書く
  python3 prompts.py <episode.json> redo N  # N語目の1コマ目だけ作り直す（a と同じ形で1件）
各コマンドは JSON を標準出力に出し、episode.json と同じフォルダの req_<stage>.json にも保存する。
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(os.path.join(HERE, '..', 'config', 'series.json')))
USED = json.load(open(os.path.join(HERE, '..', 'config', 'used_words.json')))
PB = S['prompt_blocks']; CH = S['characters']; IMG = S['models']['image']


def norm(w):
    w = w.lower().strip().rstrip('!.')
    w = re.sub(r'[^a-z ]', '', w).strip()
    if len(w) > 3 and w.endswith('ies'): return w[:-3] + 'y'
    if len(w) > 3 and w.endswith('es') and w[:-2].endswith(('s', 'x', 'ch', 'sh')): return w[:-2]
    if len(w) > 3 and w.endswith('s') and not w.endswith('ss'): return w[:-1]
    return w


def used_set(exclude_ep=None):
    out = {}
    for k, e in USED['episodes'].items():
        if exclude_ep is not None and int(k) == int(exclude_ep): continue
        for w in e['words']: out[norm(w)] = int(k)
    for w in USED.get('also_avoid', []): out.setdefault(norm(w), 0)
    return out


def char_of(ep, i):
    w = ep['words'][i]
    return w.get('char') or S['rotation'][i % 5]


def img_params(prompt, medias):
    return {'model': IMG['model'], 'prompt': prompt, 'aspect_ratio': IMG['aspect_ratio'], 'quality': IMG['quality'],
            'resolution': IMG['resolution'], 'medias': [{'role': 'image', 'value': m} for m in medias]}


def first_prompt(ep, i):
    w = ep['words'][i]; c = CH[char_of(ep, i)]
    scene = w['scene'].strip()
    eyes = PB['eyes_open']
    if c.get('sleepy_eyes'):
        scene = scene.rstrip('.') + ', ' + PB['muffin_eyes_scene']; eyes = ''
    if c.get('pose_rule') and c['pose_rule'] not in scene:
        scene = scene.rstrip('.') + '; ' + c['pose_rule'] + '.'
    p = PB['word_first']
    for k, v in (('{HERO}', w['hero'].strip().rstrip('.')), ('{SCENE}', scene), ('{CHAR}', c['en']), ('{DESIGN}', c['design']),
                 ('{ANATOMY_COMMON}', PB['anatomy_common']), ('{ANATOMY}', c['anatomy'] + ' ' + w.get('extra_anatomy', '')), ('{EYES}', eyes)):
        p = p.replace(k, v)
    return re.sub(r'\s+', ' ', p).strip()


def check(ep):
    err = []
    for k in ('episode', 'theme_en', 'theme_ja', 'words', 'intro'):
        if k not in ep: err.append('missing ' + k)
    if err: return err
    ws = ep['words']
    if len(ws) != 10: err.append('words は10語（%d語）' % len(ws))
    used = used_set(exclude_ep=ep['episode'])
    seen = set()
    for i, w in enumerate(ws):
        for k in ('en', 'ja', 'hero', 'scene', 'changes'):
            if not w.get(k): err.append('%d語目: %s がない' % (i + 1, k))
        n = norm(w.get('en', ''))
        if n in used: err.append('%d語目 %s は使用済み（第%s回）' % (i + 1, w.get('en'), used[n] or 'avoid'))
        if n in seen: err.append('%d語目 %s が回の中で重複' % (i + 1, w.get('en')))
        seen.add(n)
        if not re.match(r"^[A-Z][A-Za-z]*(?: [A-Za-z]+)*$", w.get('en', '')): err.append('%d語目 英語の形 %r（先頭大文字、記号なし）' % (i + 1, w.get('en')))
        if char_of(ep, i) != S['rotation'][i % 5]: err.append('%d語目 担当 %s（決まりは %s）' % (i + 1, char_of(ep, i), S['rotation'][i % 5]))
        if len(w.get('en', '')) > 11: err.append('%d語目 %s は長い（11文字まで。字幕が小さくなる）' % (i + 1, w.get('en')))
    if not re.match(r'^[A-Z][A-Za-z ]*$', ep['theme_en'].rstrip('!')): err.append('theme_en の形 %r' % ep['theme_en'])
    it = ep['intro']
    for k in ('front_scene', 'prop', 'front_motion', 'prop_rule'):
        if not it.get(k): err.append('intro.%s がない' % k)
    return err


def main(argv):
    if len(argv) < 3: print(__doc__); return 2
    path, stage = argv[1], argv[2]
    ep = json.load(open(path)); jobs = ep.get('jobs', {})
    out = None
    if stage == 'check':
        err = check(ep)
        for e in err: print('NG:', e)
        print('episode check:', 'OK' if not err else 'NG'); return 1 if err else 0
    if stage in ('a', 'redo'):
        idx = range(10) if stage == 'a' else [int(argv[3]) - 1]
        out = [{'index': i + 1, 'params': img_params(first_prompt(ep, i), [S['references']['style'], CH[char_of(ep, i)]['ref']])} for i in idx]
    elif stage == 'b':
        out = []
        for i in range(10):
            a = jobs.get('a%02d' % (i + 1), {}).get('id')
            if not a: sys.exit('jobs.a%02d.id がない' % (i + 1))
            c = CH[char_of(ep, i)]
            p = PB['word_second_prefix'].replace('{CHANGES}', ep['words'][i]['changes'].strip().rstrip('.')) + first_prompt(ep, i)
            out.append({'index': i + 1, 'params': img_params(p, [a, S['references']['style'], c['ref']])})
    elif stage == 'intro':
        it = ep['intro']
        back = '; '.join(CH[k]['short'] for k in ('hop', 'muffin', 'sky', 'ben'))
        anat = ' '.join(CH[k]['anatomy'] for k in S['rotation'])
        p = PB['intro_image']
        for k, v in (('{FRONT_SCENE}', it['front_scene'].strip()), ('{BACK_ROW}', back), ('{ANATOMY_COMMON}', PB['anatomy_common']), ('{ANATOMY_ALL}', anat)):
            p = p.replace(k, v)
        layout = ep.get('layout_sample') or S['references']['intro_layout_sample_latest']
        out = img_params(re.sub(r'\s+', ' ', p).strip(), [S['references']['style']] + [CH[k]['ref'] for k in S['rotation']] + [layout])
    elif stage == 'video':
        it = ep['intro']; j = jobs.get('intro', {}).get('id')
        if not j: sys.exit('jobs.intro.id がない')
        p = PB['intro_video']
        for k, v in (('{PROP}', it['prop']), ('{FRONT_MOTION}', it['front_motion'].strip().rstrip('.')), ('{PROP_RULE}', it['prop_rule'].strip())):
            p = p.replace(k, v)
        V = S['models']['intro_video']
        out = {'model': V['model'], 'prompt': re.sub(r'\s+', ' ', p).strip(), 'duration': V['duration'], 'resolution': V['resolution'],
               'aspect_ratio': '9:16', 'medias': [{'role': 'start_image', 'value': j}]}
    elif stage == 'voice':
        def line(key, ck, text):
            v = CH[ck]['voice']
            return {'key': key, 'params': {'prompt': text, 'dialogue': [{'text': text, 'voice_id': v['voice_id'], 'voice_type': 'preset'}]}}
        items = [line('intro', 'pon', "Today's theme is... %s!" % ep['theme_en'].rstrip('!'))]
        for i, w in enumerate(ep['words']):
            items.append(line('w%02d' % (i + 1), char_of(ep, i), w['en'] + '!'))
        batch = {'model': S['models']['voice']['model'], 'items': items}
        json.dump(batch, open(os.path.join(os.path.dirname(os.path.abspath(path)), 'batch_voice.json'), 'w'), ensure_ascii=False, indent=1)
        out = [{'index': k, 'params': dict(model=batch['model'], **it['params'])} for k, it in enumerate(items)]
    else:
        print(__doc__); return 2
    s = json.dumps(out, ensure_ascii=False, indent=1)
    open(os.path.join(os.path.dirname(os.path.abspath(path)), 'req_%s.json' % stage), 'w').write(s)
    print(s); return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
