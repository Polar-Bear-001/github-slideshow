#!/usr/bin/env python3
# 縦と横長の動画を書き出す（第20回 intro_v.py〔縮小なし〕+ enc_v.py + enc_l.py をまとめたもの）。
#   入力: build/（render_v/render_l の出力）, vid/intro_raw.mp4（Kling 5秒）, <tag>_audio.wav, REF/ep11_v.mp4, REF/ep11_l.mp4
#   出力: <ep>/<tag>_v.mp4, <ep>/<tag>_l.mp4
import subprocess, os, shutil, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ep_dir, episode, tag, REF
from lib import review_hl

D = ep_dir(); EP = episode(D); T = tag(EP); B = D + '/build'
ENC = ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', '-g', '30', '-r', '30', '-an']
which = sys.argv[2] if len(sys.argv) > 2 else 'vl'


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: print(r.stderr[-1500:]); raise SystemExit(1)


def seqdir(name, files):
    d = '%s/seq_%s' % (B, name); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    for k, f in enumerate(files): os.symlink(f, '%s/%d.png' % (d, k))
    return d


def intro_v(V):
    """Kling clip scaled to fill 1080x1920, title overlay composited in RGB, encoded once (no bt601/bt709 step at edges)."""
    ov = np.asarray(Image.open(B + '/ov_intro_v.png').convert('RGBA')).astype(np.float32); ov_rgb, ov_a = ov[..., :3], ov[..., 3:4] / 255
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', D + '/vid/intro_raw.mp4', '-vf', 'scale=1080:1920:flags=lanczos,fps=30', '-frames:v', '120',
                          '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1080x1920', '-r', '30', '-i', '-'] + ENC + [V + '/00_intro.mp4'], stdin=subprocess.PIPE)
    n = 0
    while n < 120:
        buf = p.stdout.read(1080 * 1920 * 3)
        if len(buf) < 1080 * 1920 * 3: break
        fr = np.frombuffer(buf, np.uint8).reshape(1920, 1080, 3).astype(np.float32)
        cv = ov_rgb * ov_a + fr * (1 - ov_a); enc.stdin.write(np.clip(cv + 0.5, 0, 255).astype(np.uint8).tobytes()); n += 1
    enc.stdin.close(); enc.wait(); p.wait()
    assert n == 120 and enc.returncode == 0, ('intro frames', n, enc.returncode)


def words_review_closing(V, pre, rvpre, ref_mp4):
    for i in range(1, 11):
        files = ['%s/%s%02d_%s.png' % (B, pre, i, 'AB'[(k // 10) % 2]) for k in range(120)]
        d = seqdir('%sw%02d' % (pre, i), files)
        run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', d + '/%d.png', '-frames:v', '120'] + ENC + ['%s/%02d_word.mp4' % (V, i)])
    files = ['%s/%s_%02d.png' % (B, rvpre, review_hl(k)) for k in range(330)]
    d = seqdir(rvpre, files)
    run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', d + '/%d.png', '-frames:v', '330'] + ENC + [V + '/11_review.mp4'])
    # shared closing cuts from EP11
    run(['ffmpeg', '-v', 'error', '-y', '-i', ref_mp4, '-ss', '56', '-t', '2', '-frames:v', '60'] + ENC + [V + '/12_good.mp4'])
    run(['ffmpeg', '-v', 'error', '-y', '-i', ref_mp4, '-ss', '58', '-t', '3.5', '-frames:v', '105'] + ENC + [V + '/13_bye.mp4'])


def concat(V, out):
    names = sorted(f for f in os.listdir(V) if f.endswith('.mp4') and f[0].isdigit())
    open(V + '/list.txt', 'w').write(''.join("file '%s/%s'\n" % (V, n) for n in names))
    run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', V + '/list.txt', '-c', 'copy', out])


if 'v' in which:
    V = D + '/vseg'; shutil.rmtree(V, ignore_errors=True); os.makedirs(V)
    intro_v(V); print('v intro')
    words_review_closing(V, 'vw', 'vrv', REF + '/ep11_v.mp4'); print('v words/review/closing')
    concat(V, '%s/%s_v_silent.mp4' % (D, T))
    run(['ffmpeg', '-v', 'error', '-y', '-i', '%s/%s_v_silent.mp4' % (D, T), '-i', '%s/%s_audio.wav' % (D, T), '-map', '0:v', '-map', '1:a',
         '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '1', '-shortest', '-movflags', '+faststart', '%s/%s_v.mp4' % (D, T)])
    print('v DONE')

if 'l' in which:
    V = D + '/lseg'; shutil.rmtree(V, ignore_errors=True); os.makedirs(V)
    run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-framerate', '30', '-i', B + '/l_intro_base.png', '-i', D + '/vid/intro_raw.mp4', '-loop', '1', '-framerate', '30', '-i', B + '/l_edge.png',
         '-filter_complex', '[1:v]scale=810:1440:flags=lanczos,fps=30,crop=810:1080:0:288[v];[0:v][v]overlay=0:0:shortest=1[a];[a][2:v]overlay=0:0:format=auto,format=yuv420p',
         '-frames:v', '120'] + ENC + [V + '/00_intro.mp4'])
    print('l intro')
    words_review_closing(V, 'lw', 'lrv', REF + '/ep11_l.mp4'); print('l words/review/closing')
    concat(V, '%s/%s_l_silent.mp4' % (D, T))
    # the landscape version reuses the vertical version's AAC track unchanged (verify_final checks they are identical)
    run(['ffmpeg', '-v', 'error', '-y', '-i', '%s/%s_l_silent.mp4' % (D, T), '-i', '%s/%s_v.mp4' % (D, T), '-map', '0:v', '-map', '1:a',
         '-c', 'copy', '-shortest', '-movflags', '+faststart', '%s/%s_l.mp4' % (D, T)])
    print('l DONE')
