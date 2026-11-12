#!/usr/bin/env python3
"""投稿用キャプション（YouTube ショート・TikTok・Instagram 共通）を episode.json から作る。第21回の形。
  python3 caption.py <episode.json>        -> 標準出力と、同じフォルダの epNN_caption.txt
episode.json に任意で:
  "caption_emoji": ["🍳", "🥄"]   … 1つ目はタイトル行、2つ目は「きょうの10語」の行（無ければ 🎈 / 📚）
  "caption_lead": "台所にあるもの"  … 「ぽんとなかまたちと、○○を英語で言ってみよう！」の○○（無ければ「<テーマ日本語>のことば」）
"""
import json, os, sys

TAGS = '#ぽんの英単語 #幼児英語 #おうち英語 #こども英語 #英単語 #知育 #2歳 #3歳 #4歳 #5歳 #kidsenglish #englishforkids #learnenglish'


def make(ep):
    em = ep.get('caption_emoji') or ['🎈', '📚']
    lead = ep.get('caption_lead') or '「%s」のことば' % ep['theme_ja']
    lines = ['【ぽんの英単語 #%d】%s / %s %s' % (int(ep['episode']), ep['theme_ja'], ep['theme_en'].rstrip('!'), em[0]), '',
             'ぽんとなかまたちと、%sを英語で言ってみよう！' % lead,
             'ひとつの単語を「ふつう → ゆっくり」の2回ずつ言うよ。',
             '最後はみんなでおさらい✨', '',
             '%s きょうの10語' % (em[1] if len(em) > 1 else '📚')]
    lines += ['%s（%s）' % (w['en'], w['ja']) for w in ep['words']]
    lines += ['', 'いっしょに声に出して言えたかな？', "Let's practice! 👋", '', TAGS]
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    if len(sys.argv) < 2: print(__doc__); sys.exit(2)
    ep = json.load(open(sys.argv[1]))
    txt = make(ep)
    out = os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), 'ep%02d_caption.txt' % int(ep['episode']))
    open(out, 'w').write(txt)
    sys.stdout.write(txt)
