# ぽんの英単語 — 自動制作の手順書（スケジュール実行用）

この手順書は、スケジュールで起動した Claude のセッションが **1回の実行で1話（縦＋横長の2本）** を作るためのもの。
1日2回起動するので、1日2話になる。人の確認を待たずに最後まで進めるが、下の「止める条件」に当たったら作らずに止めて報告する。

使う道具：
- **このリポジトリ**（`pon/`）… 設定・使用済み単語・回ごとの記録・スクリプト。作業ブランチは `claude/pon-english-word-video-auto-1uw057`（`config/series.json` の `repo_branch`）。
- **Higgsfield コネクタ** … 絵・動画・声の生成（`generate_image_batch` / `generate_image` / `generate_video` / `generate_audio_batch` / `jobs_wait`）、サンドボックス（`sandbox_exec`）、納品（`media_upload` → `media_confirm` → `attach_project_asset`）。
- **Higgsfield のサンドボックス** `/home/user` … 合成・チェック用。リポジトリは `/home/user/pon-repo` に clone する（公開リポジトリなので認証不要）。各回の作業フォルダは `/home/user/epNN`。

> この会話のコンテナは Higgsfield の CDN に届かない。ファイルの受け渡しはすべてサンドボックスの中で行う（生成結果の URL を `fetch.py` がサンドボックス内でダウンロードする）。

---

## 0. 始める前の確認（毎回）

1. `git fetch origin <branch> && git checkout <branch> && git pull` で最新にする。
2. `pon/state.json` を読む。
   - `paused: true` なら何もせず、「一時停止中（理由: …）」とだけ報告して終わる。
   - `in_progress` に回の番号が入っていたら、前回の実行が途中で止まっている。**新しい回を始めずに、その回を再開する**（`pon/episodes/epNN.json` の `jobs` にある ID は生成済みなので、もう一度生成しない）。
3. Higgsfield の `balance` でクレジットを確かめる。`series.json` の `budget.min_balance_to_start`（60）未満なら作らない。`state.json` を `paused: true, pause_reason: "クレジット不足"` にして push し、報告して終わる。
4. サンドボックスの準備：`sandbox_exec` で
   `cd /home/user && ( [ -d pon-repo ] || git clone -q -b claude/pon-english-word-video-auto-1uw057 https://github.com/Polar-Bear-001/github-slideshow.git pon-repo ) && bash pon-repo/pon/pipeline/run.sh setup`
   `SETUP_OK` が出ればよい。`MISSING` が出たら「素材の復元」（最後の節）を行う。

## 1. 回の企画（テーマと10語）

`state.json` の `next_episode` を回の番号 N とする。

1. `pon/config/used_words.json` と `pon/config/theme_ideas.md` を読み、まだ使っていないテーマを1つ選ぶ。
   - 幼児（2〜5歳）が日常で見聞きする、**絵1枚で迷わず分かる具体物・動作**のテーマ。直前の2回と同じジャンルは避ける。
   - 英語は先頭大文字で11文字以内、記号なし（`Fire truck` のような2語は可）。和訳はひらがな中心（カタカナ語はカタカナ）。
   - 10語すべて、使用済み語（単数・複数も同じとみなす）と `also_avoid` に重ならないこと。
   - 担当は1語目から ぽん→ホップ→マフィン→スカイ→ベン を2周（`char`: `pon, hop, muffin, sky, ben, pon, …`）。
2. `pon/episodes/epNN.json` を `ep20.json` と同じ形で書く。各語の英文：
   - `hero`: 主役の物を英語で、形と色が分かるように（例 `The bakery (yellow walls, a brown roof with a chimney, …)`）。**文字・数字・看板は入れない**。食べ物・乗り物など過去の単語と同じ物は主役にしない。
   - `scene`: 担当キャラがその物のそばで何をしているか1文（例 `Ben stands in front smiling with both hands at the chest.`）。
     速く振る・物を振り回すなどの大きな動きは書かない。ホップの耳、マフィンのしっぽの決まりは `prompts.py` が自動で足す。
   - `changes`: 2コマ目の小さな違い（例 `both hands move slightly, …, and the two sparkles shift a little`）。物の位置や大きさは変えない。
   - `intro`: 導入の絵で手前のぽんが持つ/示す物（`front_scene`）、その物の名前（`prop`）、ぽんの動き（`front_motion`、とても小さい動き）、物が崩れない決まり（`prop_rule`）。`ep20.json` の地図の例にならう。
   - 動物そのものがテーマの場合など、追加の解剖の決まりが要る語は `extra_anatomy` に書く（例 Zoo のキリン）。
3. `python3 pon/pipeline/prompts.py pon/episodes/epNN.json check` が `OK` になるまで直す。
4. `state.json` の `in_progress` を N にし、`epNN.json` と一緒に commit して push する（途中で止まっても再開できるように）。

## 2. 生成（クレジットを使う。上限は1話30cr）

生成のたびに、返ってきた job ID を `epNN.json` の `jobs` に `{"id": …}` で書く。`jobs_wait` で完了したら `url`（result_url）も書く。キーは `a01..a10`, `b01..b10`, `intro`, `video`, `vintro`, `v01..v10`。区切りごとに commit/push する。

1. **1コマ目10枚**：`prompts.py … a` の出力をそのまま `generate_image_batch` の `requests` に渡す。`jobs_wait`（12件まで、15秒ずつ）で完了を待つ。
2. **導入の絵**：`prompts.py … intro` の出力を `generate_image` の `params` に渡す。
3. **声11本**：`prompts.py … voice` の出力を `generate_audio_batch` に渡す（index 0 = `vintro`, 1..10 = `v01..v10`）。送る前に、サンドボックスで `voice_spec.py <ep> pre` が OK になること（4. の取り込みのあとでもよい）。
4. **2コマ目10枚**：`jobs.aNN.id` が全部そろってから `prompts.py … b` → `generate_image_batch`。
5. **導入動画**：`jobs.intro.id` がそろってから `prompts.py … video` → `generate_video`（Kling 3.0 Turbo、5秒、約7.5cr）。
   - モデル名などが変わって拒否されたら `models_explore` で同等のもの（Kling 3.0 系、5秒、720p、start_image）を探し、`epNN.json` の `notes` に書く。

## 3. サンドボックスに取り込んでチェック

1. 作業フォルダを作り、回の設定を置く：`sandbox_exec` で `mkdir -p /home/user/epNN && cat > /home/user/epNN/episode.json <<'EOF'`（epNN.json の中身）`EOF`。
   `jobs` を書き足したら、そのつど同じ方法で置き直す。
2. `python3 /home/user/pon-repo/pon/pipeline/fetch.py /home/user/epNN` で全部ダウンロード。
3. **声**：`bash run.sh voices /home/user/epNN`。
   - `VOICES_NG` の語は、その1本だけ `generate_audio`（同じ params）で録り直す（`--retake`）。1語につき1回まで。
4. **絵**：`bash run.sh images /home/user/epNN` → `register.py` が2コマ目を位置合わせし、`chk/words_1.jpg`, `chk/words_2.jpg` を作る。
   `sandbox_exec` の `image_paths` でこの2枚と `bash …/sheets.py /home/user/epNN intro` の `chk/intro.jpg` を**必ず目で見る**。見ること：
   - 耳の数（ぽん2・ホップ2・マフィン2）、ホップの耳が頭についている、マフィンのしっぽが1本で太く体についている、手足が2本ずつ、目が2つ
   - 絵の中に文字・数字・看板がない／主役の物が大きくはっきり／上の35%が空いている
   - 1コマ目と2コマ目で物の形と位置が同じ（終了コード3＝大きくずれている語がある）
   - 導入：手前にぽん、奥に4人が並ぶ。空が上32%、太陽が小さい。
   問題のある語は、1コマ目なら `prompts.py … redo N` → `generate_image_batch`（その語の2コマ目も作り直す）、2コマ目だけなら `prompts.py … b` の N 番目だけを送る。
   **描き直しは1話で合計6枚まで**（`budget.max_redraw_images_per_episode`）。
5. **導入動画**：`bash run.sh clip /home/user/epNN` と `chk/clip/*_sheet.jpg` の目視。
   崩れ疑い（終了コード1）で、目で見ても耳・しっぽ・顔が崩れていたら、1回だけ作り直す（`max_intro_video_retries`）。2回目も崩れていたら、より良い方を使い、記録の `notes` に書く。

## 4. 組み立て（縦・横長）

1. `bash /home/user/pon-repo/pon/pipeline/run.sh build /home/user/epNN` を **`background: true`** で動かし、`/home/user/epNN/build.status` を数十秒おきに見る（15分以内に終わる）。
2. `BUILD_OK` と `完成動画チェック: OK` を確かめる。`build_verify.log` に NG があれば原因を直してやり直す（`build_*.log` を読む）。
3. `chk/final_v.jpg`, `chk/final_l.jpg` を `image_paths` で目視（導入の文字、単語の字幕、おさらいのカード、締めのカット）。

## 5. 納品

1. 初回だけ：`state.json` の `project_id` が空なら `create_project`（名前「ぽんの英単語（自動）」、workspace は `series.json` の `workspace_id`）を作り、`project_id` と `default_folder_id` を `state.json` に書く。
2. `media_upload` に `files: [{filename: "epNN_v.mp4"}, {filename: "epNN_l.mp4"}]` を渡して upload_url を2つもらい、サンドボックスで
   `curl -f -X PUT --upload-file /home/user/epNN/epNN_v.mp4 '<url>'`（横長も同様）。HTTP 200 を確かめてから `media_confirm`（type `video`）。
3. `attach_project_asset`（source `{type: "video_input", id: <media_id>}`、folder は `state.json` の `folder_id`）で2本ともプロジェクトに入れる。
4. 返ってきた URL / media_id を `epNN.json` の `deliverables` に書く。`status` を `"done"`（目視で気になる点が残れば `"done_with_notes"`）にする。

## 6. 記録と終了

1. `used_words.json` の `episodes` に N を足す。
2. `state.json`：`next_episode` を N+1、`in_progress` を null、`last_intro_image` を `jobs.intro.id`、`last_published_v` を `/home/user/epNN/epNN_v.mp4`、`history` に1行。
3. `pon/LOG.md` の先頭に1行（日付・回・テーマ・使ったクレジット・納品先・気になった点）。
4. commit（`pon: 第N回「テーマ」を自動制作`）して push。push が通信エラーなら 2,4,8,16 秒あけて4回まで再試行。
5. 最後の返答に、テーマ・10語・使ったクレジット・残高・納品先（プロジェクト名と動画の URL）・目視で気になった点を短く書く。

## 止める条件（作らずに/途中で止めて報告する）

- クレジット残高が60cr未満、またはこの回の消費が30crを超えそう。
- `prompts.py check` が直せない／Higgsfield の生成が3回続けて失敗。
- サンドボックスの素材（`/home/user/fonts`, `/home/user/ref`）がなく、復元もできない。
- 完成動画チェックが NG のまま直せない。

止めるときは、`state.json` の `in_progress` は残したまま（次回に再開できる）、`LOG.md` に理由を書いて push する。
同じ理由で2回続けて止まったら `paused: true` にする（人が直して `false` に戻すまで作らない）。

## 素材の復元（サンドボックスが初期化されたとき）

サンドボックスの `/home/user` は最後に使ってから24時間で消えることがある（1日2回動いていれば消えない）。
必要なのは `/home/user/fonts/`（Fredoka.ttf, ZenMaru-Bold.ttf, HachiMaruPop-Regular.ttf）と `/home/user/ref/`（ep11_v.mp4, ep11_l.mp4, ref11.wav）。
`state.json` の `backup` に、これらをまとめた `pon_assets.tar` の URL がある。サンドボックスで
`cd /home/user && curl -fsSL -o pon_assets.tar '<backup url>' && tar xf pon_assets.tar` で戻す。
`backup` がない・URL が切れている場合は止めて報告する（第11回の完成動画がないと締めのカットが作れない）。
