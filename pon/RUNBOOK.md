# ぽんの英単語 — 自動制作の手順書（スケジュール実行用）

この手順書は、スケジュールで起動した Claude のセッションが **1回の実行で1話（縦＋横長の2本）** を作るためのもの。
1日2回起動するので、1日2話になる。人の確認を待たずに最後まで進めるが、下の「止める条件」に当たったら作らずに止めて報告する。

## 置き場所（大事）

- **正本は Higgsfield のサンドボックス `/home/user/pon-repo/pon/`**（この手順書・設定・使用済み単語・回の記録・state・スクリプト）。
  会話のコンテナではなく、必ず `sandbox_exec` で読み書きする（`cat`、`python3 - <<'EOF'` で JSON を書き換える、など）。
- 各回の作業フォルダはサンドボックスの `/home/user/epNN`。フォント `/home/user/fonts`、締めの素材 `/home/user/ref`（ep11_v.mp4, ep11_l.mp4, ref11.wav）。
- サンドボックスは最後に使ってから24時間で消えることがある。だから **毎回の最後に `pon/` を tgz にして Higgsfield のプロジェクトに保存**する（6.）。
  消えていたら「復元」（最後の節）で戻す。
- GitHub（Polar-Bear-001/github-slideshow の `pon/`）は同じ内容の写し。push できる設定になっていれば最後に写してよいが、できなくても制作は止めない。

道具：Higgsfield コネクタ（`balance`, `generate_image_batch`, `generate_image`, `generate_video`, `generate_audio_batch`, `generate_audio`, `jobs_wait`,
`sandbox_exec`, `media_upload`, `media_confirm`, `attach_project_asset`, `list_project_assets`, `create_project`）。

以下 `P=/home/user/pon-repo/pon`、`PL=$P/pipeline`。

---

## 第22回で決まった作り方（ユーザー確認済み・この形を守る）

- **単語の絵**：2コマ目は「同じ場面の次の瞬間」。モノとキャラの両方がはっきり動く（`obj_change`/`char_change`/`b_hero`/`b_scene`、見本は `episodes/ep22.json`）。
  `images` は2コマ目を基本そのまま使い、地面の高さ・大きさがずれたときだけ自動で補正。A/B は0.5秒ごとに切り替え。
- **導入動画**：`series.json` の `intro_video` の指示（第23回から：ぽんの全身をぬいぐるみのようにゆっくり左右に揺らし、塗りを「体に付いた布の柄」として一緒に動かす。前の指示は `intro_video_old_v1`）で Kling 3.0 Turbo を1回生成し、**出力をそのまま使う**。
  `ponfix.py` / `ponwarp.py` などの後からの補正は**しない**（動画がガタガタになるため）。
  塗りが体と一緒に動いていない・透けているときは、作り直さず納品して、報告と通知のいちばん最初で知らせる（直すかは人が決める）。
- 完成版の見本：第22回 v7（縦 2a902382…, 横 e92ed090…）。

## 0. 始める前の確認（毎回）

1. `sandbox_exec`：`ls /home/user/pon-repo/pon/state.json /home/user/fonts/Fredoka.ttf /home/user/ref/ep11_v.mp4` — どれかが無ければ最後の節「復元」を先に行う。
2. `cat $P/state.json`。
   - `paused: true` なら何もせず、「一時停止中（理由: …）」とだけ報告して終わる。
   - `in_progress` に回の番号が入っていたら、前回の実行が途中で止まっている。**新しい回を始めずに、その回を再開する**（`$P/episodes/epNN.json` の `jobs` にある ID は生成済み。もう一度生成しない）。
3. `balance` でクレジットを確かめる。`$P/config/series.json` の `budget.min_balance_to_start`（60）未満なら作らない。`state.json` を `paused: true, pause_reason: "クレジット不足"` にして6.の保存だけ行い、報告して終わる。
4. `bash $PL/run.sh setup` で `SETUP_OK` を確かめる。

## 1. 回の企画（テーマと10語）

`state.json` の `next_episode` を回の番号 N とする（2桁表記 `epNN`）。

1. `$P/config/used_words.json` と `$P/config/theme_ideas.md` を読み、まだ使っていないテーマを1つ選ぶ。
   - 幼児（2〜5歳）が日常で見聞きする、**絵1枚で迷わず分かる具体物・動作**のテーマ。直前の2回と同じジャンルは避ける。
   - 英語は先頭大文字で11文字以内、記号なし（`Fire truck` のような2語は可）。和訳はひらがな中心（カタカナ語はカタカナ）。
   - 10語すべて、使用済み語（単数・複数も同じとみなす）と `also_avoid` に重ならないこと。
   - 担当は1語目から ぽん→ホップ→マフィン→スカイ→ベン を2周（`char`: `pon, hop, muffin, sky, ben, pon, …`）。
2. `$P/episodes/epNN.json` を `$P/episodes/ep20.json` と同じ形で書く（`jobs` は空 `{}` から）。各語の英文：
   - `hero`: 主役の物を英語で、形と色が分かるように（例 `The bakery (yellow walls, a brown roof with a chimney, …)`）。**文字・数字・看板は入れない**。過去の単語と同じ物は主役にしない。
   - `scene`: 担当キャラがその物のそばで何をしているか1文（例 `Ben stands in front smiling with both hands at the chest.`）。
     速く振る・振り回すなどの大きな動きは書かない。ホップの耳、マフィンの目としっぽの決まりは `prompts.py` が自動で足す。
   - **2コマ目（第23回から）**：2コマ目は「同じ場面の次の瞬間」。モノとキャラの両方がはっきり動くように、次の4つを書く。
     - `obj_change`：モノの動き（例 `the scissors are now open wide, the two round blunt blades apart in a big V shape, lying in the same spot`）。
       開く・閉じる・傾く・引き出す・ふたが開く・湯気が出る など**形がはっきり変わる動き**にする。透明・細い物の小さな変化（テープの引き出しなど）は見えにくいので避ける。モノの大きさと置き場所は変えない。
     - `char_change`：キャラのポーズの変化（例 `Muffin raises one paw high in a cheerful wave and tilts the head a little`）。立ち位置と大きさは変えず、ポーズだけ変える。速く振る・振り回すは書かない。
     - `b_hero`：2コマ目のモノの説明（`hero` に `obj_change` の状態を入れたもの。例 `A big pair of child safety scissors …, opened wide in a V shape and lying flat on a wooden desk`）。
     - `b_scene`：2コマ目のキャラの1文（例 `Muffin stands beside the open scissors raising one paw high in a cheerful wave, head tilted a little, smiling.`）。
     - 書き方の見本は `episodes/ep22.json` の1・3・8語目（Pencil, Scissors, Tape）。Tape は透明で動きが見えにくかった悪い例。
     - 動きはモノ1つ・キャラ1つまで。1コマ目の `scene` は「動きの始まり」のポーズとして、2コマ目と対で考える。
     - （第22回までの `changes` は古い形。`prompts.py` は古い回も読めるが、新しい回は上の4つを書く）
   - `intro`: 導入の絵で手前のぽんが持つ/示す物（`front_scene`、「large Pon the gray-blue baby elephant stands smiling and …」で始める）、その物の名前（`prop`）、ぽんの動き（`front_motion`、とても小さい動き）、物が崩れない決まり（`prop_rule`）。`ep20.json` の地図の例にならう。
     **第28回から（導入の絵をテーマの場面にする）**：さらに `setting`（背景の場面。丘にこだわらない。例：農場なら「左端に一部だけ見える赤い納屋（屋根は40%の線より下）、低い木の柵、干し草」。背の高い建物・木は端で切るか低く描くと書く）、`theme_items`（ぽんのまわりに描くテーマの物を3〜4個。10語の中から選ぶ）、`back_action`（奥の4人がテーマに参加する動き。例：うさぎがひよこを持つ）も書く。ぽんが持つ物（`front_scene` / `prop`）もテーマがひと目で分かる物にする（例：農場なら納屋のおもちゃより子ひつじを抱く）。上の40%は字幕のための空きで、空など、あっさりした背景だけにする（指示文に書いてある）。
   - 動物そのものなど、追加の解剖の決まりが要る語は `extra_anatomy` に書く（例 Zoo のキリン）。
   - `caption_emoji`：テーマに合う絵文字を2つほど（例 Beach Day なら `["🏖️", "🐚"]`）。1つ目がキャプション冒頭の絵文字になる（第25回から。無いと 🍎）。
3. `python3 $PL/prompts.py $P/episodes/epNN.json check` が `OK` になるまで直す。
4. `state.json` の `in_progress` を N にする。`mkdir -p /home/user/epNN && cp $P/episodes/epNN.json /home/user/epNN/episode.json`。

## 2. 生成（クレジットを使う。上限は1話30cr）

生成リクエストは `python3 $PL/prompts.py $P/episodes/epNN.json <stage>` の出力（JSON）を**そのまま**ツールに渡す。手で書き換えない。
返ってきた job ID と、`jobs_wait` で完了したときの `result_url` を、`$P/episodes/epNN.json` の `jobs` に `{"id": …, "url": …}` で書き、
`/home/user/epNN/episode.json` にもコピーする（書き換えは `python3 - <<'EOF'` で JSON を読み書きする）。キーは `a01..a10`, `b01..b10`, `intro`, `video`, `vintro`, `v01..v10`。

1. **1コマ目10枚**：stage `a` → `generate_image_batch` の `requests`。`jobs_wait`（12件まで、15秒ずつ）で完了を待つ。
2. **導入の絵**：stage `intro` → `generate_image` の `params`。
3. **声11本**：stage `voice`（`batch_voice.json` も書かれる。`cp $P/episodes/batch_voice.json /home/user/epNN/`）。
   `python3 $PL/voice_spec.py /home/user/epNN pre` が OK なら、出力を `generate_audio_batch` へ（index 0 → `vintro`, 1..10 → `v01..v10`）。
4. **2コマ目10枚**：`jobs.aNN` が全部そろってから stage `b` → `generate_image_batch`。
5. **導入の絵の字幕チェック（導入動画の前に必ず）**：`mkdir -p /home/user/epNN && cp $P/episodes/epNN.json /home/user/epNN/episode.json && python3 $PL/fetch.py /home/user/epNN intro`
   → `python3 $PL/layout_check.py /home/user/epNN` と `chk/layout.jpg` の目視（`image_paths`）。
   - 字幕（英語・日本語）の箱に奥のキャラの頭・耳・帽子や物が入っていたら NG（終了コード1）。stage `intro` をもう一度送って描き直す（1枚0.5cr、**2回まで**）。
   - 2回描き直しても NG なら、いちばん数値の小さい絵を使い `notes` に書く。
   - 構図の見本は第1・2・5・12回の導入の絵で固定（`series.json` の `references.intro_layout_samples`）。前の回の絵は見本にしない。
     参照が多すぎて生成が拒否されたら、`epNN.json` に `"layout_samples": ["3b9c474d-fd42-4d47-9445-f4466df532c9", "72708e06-932d-4e87-b3a4-2386baa955e0"]` を書いて送り直す。
6. **導入動画**：5. が OK の絵（`jobs.intro`）で stage `video` → `generate_video`（Kling 3.0 Turbo、5秒、約7.5cr）。
   - モデル名などが変わって拒否されたら `models_explore` で同等のもの（Kling 3.0 系、5秒、720p、start_image）を探し、`epNN.json` の `notes` に書く。
   - 画像モデル `gpt_image_2_5` が拒否されたときも同様（`gpt_image_2_6` など）。

## 3. 取り込みとチェック

1. `python3 $PL/fetch.py /home/user/epNN` で全部ダウンロード（`bash $PL/run.sh check /home/user/epNN` で確認）。
2. **声**：`bash $PL/run.sh voices /home/user/epNN`。`VOICES_NG` の語は、その1本だけ `generate_audio`（同じ params）で録り直す。1語につき1回まで。
3. **絵**：`bash $PL/run.sh images /home/user/epNN` → 2コマ目の位置合わせと `chk/words_1.jpg`, `chk/words_2.jpg`。`python3 $PL/sheets.py /home/user/epNN intro` → `chk/intro.jpg`。
   `sandbox_exec` の `image_paths` でこの3枚を**必ず目で見る**：
   - 耳の数（ぽん2・ホップ2・マフィン2）、ホップの耳が頭についている、マフィンのしっぽが1本で太く体についている、手足が2本ずつ、目が2つ
   - 絵の中に文字・数字・看板がない／主役の物が大きくはっきり／上の35%が空いている
   - 1コマ目と2コマ目で、同じ物・同じキャラに見える（色・形・持ち物が同じ）。動き（`obj_change`/`char_change`）がちゃんと描かれている。
     `images` は2コマ目を基本そのまま使い、地面の線の高さ（3px以上）や大きさ（3%以上）がずれているときだけ自動で補正する（`register.json` に記録）。
     終了コード3＝地面の線が見つからない／大きさが15%を超えてずれている語がある → その語の2コマ目を描き直す。
   - 導入：手前にぽん、奥に4人が小さく低く並ぶ。上のほうは空だけで、字幕に何も重ならない（2. の5番で確認済み）。
   問題のある語は、1コマ目なら stage `redo N` → `generate_image_batch`（その語の2コマ目も stage `b` の N 番目だけで作り直す）、2コマ目だけなら stage `b` の N 番目だけを送る。
   **描き直しは1話で合計6枚まで**。作り直したら `fetch.py` で取り込み直して `images` をやり直す。
4. **導入動画**：`bash $PL/run.sh clip /home/user/epNN` と `chk/clip/*_sheet.jpg` の目視。
   崩れ疑い（終了コード1）で、目で見ても耳・しっぽ・顔が崩れていたら、1回だけ作り直す。2回目も崩れていたら、良い方を使い `notes` に書く。
   **手前のぽんの塗りが体と一緒に動いているか**も必ず見る。Kling の動画は輪郭は動くのに中のクレヨンの塗りが画面に貼り付いたまま
   （透けているように見える）になりやすい。`clip` の数値では見つからない。動画を再生して、ぽんの頭やおなかの模様が体と一緒に動くかを見る。
   **貼り付いていても作り直さない・直さない**。そのまま組み立てと納品まで進め、`notes` と `LOG.md` に書いて `status` を `done_with_notes` にし、
   最後の報告と通知の**いちばん最初**に「導入のぽんの塗りが動いていません（作り直していません）」と書く。直すかどうかは人が決める。
   （人に頼まれたときの直し方：`pipeline/ponwarp.py`。導入の絵のぽんを動画の動きに合わせて変形して重ねる。手順は ponwarp.py の先頭。
     必要なもの：`python3 $PL/ponmask.py <ep>` で `img/pon_mask.png`、ぽんを消した背景の絵 `img/intro_plate.png`（generate_image 0.5cr、
     medias=[jobs.intro]、「手前の象と持ち物・かばんを消して同じ草と花で埋める、ほかは全部そのまま」）。
     `cp vid/intro_raw.mp4 vid/intro_raw_kling.mp4` → ponwarp.py → `ffmpeg -c:v libx264 -crf 14 -pix_fmt yuv420p -r 24 vid/intro_raw.mp4` → build）

## 4. 組み立て（縦・横長）

1. `bash $PL/run.sh build /home/user/epNN` を **`background: true`** で動かし、`cat /home/user/epNN/build.status` を数十秒おきに見る（10分ほど）。
2. `BUILD_OK` と `build_verify.log` の `完成動画チェック: OK` を確かめる。NG なら `build_*.log` を読んで直し、やり直す。
3. `chk/final_v.jpg`, `chk/final_l.jpg` を `image_paths` で目視（導入の文字、単語の字幕、おさらいのカード、締めのカット）。

## 5. 納品

1. `state.json` の `project_id` が空なら（初回だけ）`create_project`（名前「ぽんの英単語（自動）」、workspace は `series.json` の `workspace_id`）。`project_id` と `default_folder_id`（→ `folder_id`）を `state.json` に書く。
2. `media_upload`（`files: [{filename: "epNN_v.mp4"}, {filename: "epNN_l.mp4"}]`）で upload_url を2つもらい、サンドボックスで
   `curl -f -X PUT -H 'Content-Type: video/mp4' -H 'If-None-Match: *' --upload-file /home/user/epNN/epNN_v.mp4 '<url>'`（横長も同様。返答の instructions にあるヘッダーに従う）。
   HTTP 200 を確かめてから `media_confirm`（type `video`）。
3. `attach_project_asset`（source `{type: "video_input", id: <media_id>}`、folder は `state.json` の `folder_id`）で2本ともプロジェクトに入れる。
4. media_id と URL を `epNN.json` の `deliverables` に書く。`status` を `"done"`（目視で気になる点が残れば `"done_with_notes"`）。
5. **キャプション**：`python3 $PL/caption.py $P/episodes/epNN.json` で `$P/episodes/epNN_caption.txt` を作る（第1〜20回と同じ固定の形。冒頭の絵文字だけ `caption_emoji` の1つ目でテーマに合わせる。手で書き換えない）。
   中身は最後の返答にそのまま（コードブロックで）載せる。

## 5.5 YouTube ショートへの投稿（Metricool）

`state.json` の `youtube.enabled` が true のときだけ行う（false なら飛ばす）。

**決まった時刻の実行（スケジュールされたタスク）では予約しない**（`youtube.post_in_scheduled_run` が false のとき）。その場合は `youtube_queue.json` の末尾に `metricool_id: null`・`when: null` で回を足し（episode, theme_ja, video, video_ready, title, text, ai_label: true）、報告に「YouTube 未予約: 第N回」と書くだけにする。予約は、人が見ている対話セッションで「未予約の回を予約して」と頼まれたときに、null の回を番号順に、最後の予約の次の枠から入れる。Metricool コネクタ（`mcp__Metricool_Social_Media_Management__*`）を使う。見えなければ ToolSearch で「Metricool createScheduledPost」を読み込む。使えなければ投稿だけ飛ばして、報告に書く。

**横長の通常動画（YouTube の「動画」）**：第10回から投稿中。予約は対話セッションで「横の動画も予約して」と頼まれたときに行う。タイトル『テーマ』のえいご10こ、説明文はショートのキャプション（冒頭の絵文字はテーマに合わせる）、type "video"、タグはショートの5つ＋「ぽんの英単語」＋テーマ名、公開・子ども向け・AI申告あり・EDUCATION。枠は毎日 07:00 / 12:00 / 17:00 / 21:00。サムネイルは付けない（videoThumbnailUrl は使わない。YouTube 側で「Could not upload video thumbnail」になるため）。予約の記録は GitHub の pon/youtube_long_queue.json。決まった時刻の実行では予約しない。

1. 予約時刻：`youtube.post_time` が `"queue"` なら、`youtube_queue.json` の `queue` の最後の `when` の**次の枠**（`youtube.slots` = 07:30 と 17:00、日本時間。07:30 の次は同じ日の 17:00、17:00 の次は翌日 07:30）。その枠が今から30分以内か過去なら、さらに次の枠にずらす。`"next_slot"` なら今から15分後、`"HH:MM"` なら今日のその時刻。
   - キューの前の回（第2〜20回など）の `metricool_id` が null のまま残っていたら、先にそれらを予約する（`when` がまだ先ならその時刻、過ぎていれば次の空き枠に。`video_ready` が false なら、サンドボックスの `/home/user/epNN/epNN_v.mp4` を media_upload → curl PUT → media_confirm してから。URL は `video` の値と同じ ID になる）。
2. `createScheduledPost`（`blogId` = `youtube.metricool_blog_id`、`date` = 予約時刻 `+09:00`）。`info` は次の形（`text` は `epNN_caption.txt` の中身そのまま）:
   `{"autoPublish": true, "descendants": [], "draft": false, "firstCommentText": "", "hasNotReadNotes": false,
     "media": ["<deliverables.v.url（縦の動画）>"], "mediaAltText": [], "providers": [{"network": "youtube"}],
     "publicationDate": {"dateTime": "<YYYY-MM-DDTHH:MM:SS>", "timezone": "Asia/Tokyo"}, "shortener": false, "smartLinkData": {"ids": []},
     "text": "<キャプション>",
     "youtubeData": {"title": "「<theme_ja>」のえいご10こ！", "type": "short", "privacy": "<youtube.privacy>",
       "tags": ["幼児英語", "おうち英語", "英語あそび", "知育動画", "こども英語"], "category": "EDUCATION", "madeForKids": true, "isAiGeneratedContent": true}}`（AI生成の申告は常にオン）
3. 返ってきた `id` と `plannerUrl` を `epNN.json` の `youtube` に書き、`youtube_queue.json` の `queue` の末尾に `{episode, theme_ja, when, video, video_ready: true, title, text, metricool_id}` を足す（次の回の枠はここから決まる）。1回だけ送る（失敗したら原因を報告に書き、同じ回を二重に予約しない。`getScheduledPosts` で予約済みか確かめてから再送する）。
4. 横長の動画は投稿しない（YouTube ショートは縦だけ）。

## 6. 記録・保存・終了

1. `used_words.json` の `episodes` に N（theme_en, theme_ja, words）を足す。`theme_ideas.md` の使ったテーマに「第N回」と書く。
2. `state.json`：`next_episode` を N+1、`in_progress` を null、`last_intro_image` を `jobs.intro.id`、`history` に1行。
3. `$P/LOG.md` の2行目の後ろに1行（日付・回・テーマ・使ったクレジット・納品先・気になった点）。
4. **保存**：`cd /home/user/pon-repo && tar czf /home/user/pon_state.tgz pon` → `media_upload`（`filename: "pon_state_epNN.tgz"`, `source_type: "file_input"`）
   → サンドボックスで `curl -f -X PUT -H 'Content-Type: application/gzip' -H 'If-None-Match: *' --upload-file /home/user/pon_state.tgz '<url>'`
   → `media_confirm`（type `file`, source_type `file_input`）→ `attach_project_asset`（source `{type: "file_input", id}`、同じフォルダ）。
5. 最後の返答に、テーマ・10語・使ったクレジット・残高・納品先（プロジェクト名と動画の URL）・YouTube の予約（時刻・公開設定・plannerUrl、または飛ばした理由）・目視で気になった点を短く書き、
   そのあとに投稿用キャプション（`epNN_caption.txt` の中身）をコピーしやすいようにコードブロックで載せる。

## 止める条件（作らずに/途中で止めて報告する）

- クレジット残高が60cr未満、またはこの回の消費が30crを超えそう。
- `prompts.py check` が直せない／Higgsfield の生成が3回続けて失敗。
- サンドボックスの素材がなく、復元もできない。
- 完成動画チェックが NG のまま直せない。

止めるときは `in_progress` を残したまま（次回に再開できる）、`LOG.md` に理由を書き、6.4 の保存を行ってから報告する。
同じ理由で2回続けて止まったら `paused: true` にする（人が直して `false` に戻すまで作らない）。

## 復元（サンドボックスが初期化されていたとき）

1. **素材**（フォント・第11回の締め）：`state.json` が無くても、スケジュールの指示文にある `ASSETS_URL`（`pon_assets.tgz`）を使う。
   `cd /home/user && curl -fsSL -o pon_assets.tgz '<ASSETS_URL>' && tar xzf pon_assets.tgz && rm pon_assets.tgz`（`fonts/`, `ref/` が戻る）。
2. **正本 `pon/`**：`list_project_assets`（workspace `3b2a839d-7814-4dd2-bfba-5fd6435829d8`、project `74816559-c020-431a-9dbd-d7be7959fece`、
   `source_types: ["file_input"]`, `order_by: "created_at"`, `ordering: "desc"`）で、素材の tgz（item_id `3088cdd7-1543-480f-9167-8fc9a4e7b6d8`）以外の
   いちばん新しい file_input の `item_id` を取る。URL は `https://d2ol7oe51mr4n9.cloudfront.net/user_3L8YlIoEYhXdySR9OTlopevQUK6/<item_id>.tgz`。
   `mkdir -p /home/user/pon-repo && cd /home/user/pon-repo && rm -rf pon && curl -fsSL -o s.tgz '<url>' && tar xzf s.tgz && rm s.tgz`。
   `tar tzf` で中身が `pon/` で始まることを確かめてから展開する（違う物なら次に新しい file_input を試す）。
3. 前の回の作業フォルダ（`/home/user/epNN`）は戻らないが、制作には要らない（`verify_final` の前回比較が省かれるだけ）。
