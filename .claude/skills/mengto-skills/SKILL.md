---
name: mengto-skills
description: MengTo Skills（Webデザイン102件、3D表現35件、ゲーム開発・戦闘エフェクト31件、イラスト14件、動画・モーション14件、UI 7件など計238件）の索引。ランディングページやWebサイトの見た目の型、Three.js の3D表現、ゲームのエフェクト、イラストの画風、動画・モーションデザインを作るとき、該当する個別スキルを探して取り出して使う。
---

# MengTo Skills の索引

MengTo/Skills（MIT）は件数と容量が大きい（約200MB）ため、本体はこのリポジトリに入れていない。作業に合うものを `references/index.md` から選び、その1件だけを確認済みの版から取り出して使う。

## 使い方

1. `references/index.md` を分類・名前・説明で検索し、作業に合う候補を1〜3件選ぶ。候補が複数なら、違いを一言ずつ添えてユーザーに選んでもらう。
2. 選んだスキルのフォルダだけを、索引に書いたコミットで作業用フォルダ（scratchpad など、リポジトリの外）に取り出す。

   ```bash
   D=<scratchpad>/mengto && rm -rf "$D" && mkdir -p "$D" && cd "$D" && git init -q && git remote add origin https://github.com/MengTo/Skills && git sparse-checkout set --no-cone "/<パス>/" && git fetch -q --depth 1 --filter=blob:none origin f8c8cb84e456ab9ee2b8f9af902d3307684b2499 && git checkout -q FETCH_HEAD
   ```

3. 取り出した `SKILL.md` と、そこから参照される `references/`・`scripts/`・`assets/` を読み、その手順に従って作る。

## 注意

- 版は索引のコミットに固定している。新しい版を使うときは、中身を確認してから `references/index.md` と `.claude/maintenance/vendor-skills.json` のコミットを更新する。
- 一部のスキルは外部サービスを使う（`media/create-ai-avatar` は HeyGen の API キーが必要）。キーが要るものは、使う前にユーザーに伝える。
- 取り出したファイルはリポジトリにコミットしない。
