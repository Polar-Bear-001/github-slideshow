#!/usr/bin/env python3
"""投稿用キャプションを episode.json から作る。第1〜20回のキャプション（「きもち」「はたらくくるま」の回など）と同じ形。
  python3 caption.py <episode.json>        -> 標準出力と、同じフォルダの epNN_caption.txt
形は固定（文言・絵文字・ハッシュタグを変えるときは、ここだけを直す）。テーマ名は theme_ja、単語は「英語 和訳」。
"""
import json, os, sys

TEMPLATE = """🍎1ぷんで「{theme_ja}」のえいご10こ！
ぞうの ぽん といっしょに おぼえよう🐘

{words}

🎶おなじことばを「ふつう」と「ゆっくり」の2かい きかせるよ。さいごの「おさらい」で、おやこでいっしょに いってみてね🎶

📌 つぎのテーマも おたのしみに！ フォローして まっててね

#幼児英語 #おうち英語 #英語あそび #知育動画 #こども英語
"""


def make(ep):
    words = '\n'.join('%s %s' % (w['en'], w['ja']) for w in ep['words'])
    return TEMPLATE.format(theme_ja=ep['theme_ja'], words=words)


if __name__ == '__main__':
    if len(sys.argv) < 2: print(__doc__); sys.exit(2)
    ep = json.load(open(sys.argv[1]))
    txt = make(ep)
    out = os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), 'ep%02d_caption.txt' % int(ep['episode']))
    open(out, 'w').write(txt)
    sys.stdout.write(txt)
