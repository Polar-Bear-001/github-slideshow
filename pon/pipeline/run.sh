#!/bin/bash
# Higgsfield サンドボックスで動かす入口。リポジトリを最新にして、決まった順に処理する。
#   bash run.sh setup                 # 正本・フォント・見本素材・Python の確認（毎回最初に）
#   bash run.sh check  <ep>           # 素材がそろっているか
#   bash run.sh images <ep>           # register -> sheets words
#   bash run.sh voices <ep>           # voice_spec post -> wcheck
#   bash run.sh clip   <ep>           # clip_check（導入動画の崩れ）
#   bash run.sh build  <ep>           # render_v -> render_l -> build_audio -> encode（バックグラウンド推奨）-> verify_final -> sheets final
# <ep> は /home/user/epNN。episode.json はその中に置く。
set -u
H=/home/user; P=$H/pon-repo/pon/pipeline
cmd=$1; EPD=${2:-}

case $cmd in
setup)
  # 正本はサンドボックスの /home/user/pon-repo/pon（GitHub は使わない。RUNBOOK「置き場所」）
  [ -s $H/pon-repo/pon/state.json ] || echo "MISSING $H/pon-repo/pon/state.json"
  ok=1
  for f in fonts/Fredoka.ttf fonts/ZenMaru-Bold.ttf fonts/HachiMaruPop-Regular.ttf ref/ep11_v.mp4 ref/ep11_l.mp4 ref/ref11.wav; do
    [ -s $H/$f ] || { echo "MISSING $H/$f"; ok=0; }
  done
  python3 -c "import cv2, soundfile, librosa, faster_whisper" 2>/dev/null || { echo "installing python deps"; pip install -q opencv-python-headless soundfile librosa faster-whisper >/dev/null 2>&1; }
  [ $ok = 1 ] && echo SETUP_OK || echo "SETUP_MISSING_ASSETS -> RUNBOOK の『素材の復元』を行う"
  ;;
check)
  for f in episode.json img/a01.png img/b10.png img/intro.png vid/intro_raw.mp4 aud/intro.mp3 aud/w10.mp3; do
    [ -s $EPD/$f ] && echo "ok $f" || echo "MISSING $f"
  done
  ;;
images)
  python3 $P/register.py $EPD; rc=$?
  python3 $P/sheets.py $EPD words
  exit $rc
  ;;
voices)
  python3 $P/voice_spec.py $EPD post; a=$?
  python3 $P/wcheck.py $EPD; b=$?
  [ $a = 0 ] && [ $b = 0 ] && echo VOICES_OK || { echo VOICES_NG; exit 1; }
  ;;
clip)
  python3 $P/clip_check.py $EPD/vid/intro_raw.mp4 $EPD/chk/clip
  ;;
build)
  T=$(python3 -c "import json;print('ep%02d'%int(json.load(open('$EPD/episode.json'))['episode']))")
  PREV=$(python3 -c "import json;print('ep%02d'%(int(json.load(open('$EPD/episode.json'))['episode'])-1))")
  cd $EPD && {
    python3 $P/render_v.py $EPD > build_render_v.log 2>&1 &&
    python3 $P/render_l.py $EPD > build_render_l.log 2>&1 &&
    python3 $P/build_audio.py $EPD > build_audio.log 2>&1 &&
    python3 $P/encode.py $EPD > build_encode.log 2>&1 &&
    { if [ -s $H/$PREV/${PREV}_v.mp4 ]; then python3 $P/verify_final.py ${T}_v.mp4 ${T}_l.mp4 $H/$PREV/${PREV}_v.mp4; else python3 $P/verify_final.py ${T}_v.mp4 ${T}_l.mp4; fi; } > build_verify.log 2>&1 &&
    python3 $P/sheets.py $EPD final > build_sheets.log 2>&1 &&
    echo BUILD_OK > build.status; } || echo BUILD_FAIL > build.status
  cat build.status; tail -5 build_verify.log 2>/dev/null
  ;;
*) echo "unknown command $cmd"; exit 2;;
esac
