# 回ごとの設定（episode.json）と作業フォルダの場所。すべてのスクリプトがこれを読む。
#   使い方: python3 <script>.py <回のフォルダ>   例: python3 render_v.py /home/user/ep21
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, '..', 'config')
HOME = os.environ.get('PON_HOME', '/home/user')
REF = os.environ.get('PON_REF', HOME + '/ref')        # ep11_v.mp4, ep11_l.mp4, ref11.wav（締めのカットと音）


def series():
    return json.load(open(os.path.join(CONFIG, 'series.json')))


def ep_dir(argv=None):
    argv = sys.argv if argv is None else argv
    if len(argv) < 2:
        sys.exit('usage: %s <episode dir>' % os.path.basename(argv[0]))
    d = os.path.abspath(argv[1])
    os.makedirs(d + '/build', exist_ok=True)
    return d


def episode(d):
    return json.load(open(os.path.join(d, 'episode.json')))


def words(ep):
    return [(w['en'], w['ja']) for w in ep['words']]


def tag(ep):
    return 'ep%02d' % int(ep['episode'])
