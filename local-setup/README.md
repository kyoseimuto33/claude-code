# Claude Code ローカル移行パッケージ（はじめにお読みください）

claude.ai のクラウド環境（Claude Code on the web）で設定・接続・構築したものを、
自分の PC のローカル Claude Code でも同じように使えるようにするための指示書・設定ファイル・データ一式です。

作成日: 2026-10-07 / 対象リポジトリ: `kyoseimuto33/claude-code`

## 最短手順（15分）

1. **Claude Code をインストール**
   - Mac / Linux: `curl -fsSL https://claude.ai/install.sh | bash`
   - Windows (PowerShell): `irm https://claude.ai/install.ps1 | iex`
2. **この zip を展開し、セットアップを実行**
   - Mac / Linux: `bash scripts/setup.sh`
   - Windows: `powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1`
   - 最後に「検証結果: すべて一致」と出れば、クラウドと同じ計算結果がローカルで再現できています
3. **ログイン**: `cd repo` → `claude` → クラウドと**同じ claude.ai アカウント**でログイン
4. **確認**: Claude Code 内で `/mcp` → Gmail・Google Drive・Slack・Ahrefs などが出ていれば完了（コネクタは自動で引き継がれます）
5. （ルーティンを手元で動かす場合のみ）`.env` に認証情報を記入 → `docs/05` の手順へ

## 中身

```
claude-local-setup/
├── README.md                         ← このファイル
├── docs/                             ← 指示書・仕様書
│   ├── 01_クラウド構成一覧.md          クラウドに何があるかの棚卸しと移行区分
│   ├── 02_ローカル環境構築手順.md      インストール〜ログイン〜動作確認
│   ├── 03_コネクタ設定手順.md          Gmail/Drive/Slack/Ahrefs 等の使い方と困ったとき
│   ├── 04_シークレット管理.md          認証情報の扱い（.env）と再発行の推奨
│   └── 05_ルーティン移行手順.md        定期実行4件をクラウドに残す/ローカルに移す
├── project/                          ← リポジトリの成果物一式（clone できない場合の予備）
│   ├── build_simulation.py / index.html / README.md
│   └── armtechstore_収益シミュレーション_改訂版.xlsx
├── config/                           ← ローカル用設定ファイル
│   ├── claude/CLAUDE.md                プロジェクト指示書（Claude が毎回読む）
│   ├── claude/settings.json            権限設定（.claude/settings.json に配置）
│   ├── requirements.txt                Python 依存（openpyxl）
│   ├── gitignore.append                .gitignore 追記分
│   └── .env.example                    シークレットのテンプレート（値は空）
├── routines/                         ← 定期実行の設定・プロンプト・実行スクリプト
│   ├── routines.json                   4件のスケジュール・モデル・コネクタ定義
│   ├── prompts/*.md                    プロンプト全文（シークレット除去済み）
│   ├── scripts/popularity_score.py     archi-dog 用スクリプト
│   ├── run_routine.sh / .ps1           1回実行ランナー
│   └── scheduler/                      cron / Windows タスクスケジューラ登録
└── scripts/                          ← セットアップ・検証
    ├── setup.sh / setup.ps1
    └── verify_project.py
```

## 引き継ぎの全体像

| 対象 | ローカルでの扱い | 作業 |
|---|---|---|
| リポジトリ（収益シミュレーション） | clone して使う | setup が自動実行 |
| Python 環境（openpyxl） | pip でインストール | setup が自動実行 |
| Claude 用プロジェクト設定 | CLAUDE.md / settings.json を新規作成して同梱 | setup が自動配置 |
| コネクタ 8件（Gmail, Calendar, Drive, Sheets, Slides, Slack, Ahrefs, higgsfield）＋ Claude Docs | **claude.ai ログインで自動的に使える** | なし |
| アカウント同期スキル（docx, xlsx, pdf, pptx, deep-research 等） | claude.ai ログインで自動同期 | なし |
| ルーティン 4件 | **クラウドで動き続ける**（ローカル作業の影響なし） | 不要。ローカル実行したい場合のみ `.env` 記入 |
| 認証情報（Shopify・flumo API） | zip には**含めていない** | 必要時に `.env` へ記入（docs/04） |

## 重要な注意

- **この zip にはパスワード・API キー等は入っていません**（GitHub にも保存されるため）。
  クラウドのルーティン本文に平文で書かれていた認証情報があったため、再発行を推奨します（docs/04）。
- `.env` を作成した後は、この zip フォルダごと他人に渡さないでください。
- archi-dog / SEO Pipeline のルーティンは本番の Shopify・API を書き換えます。手元で実行する前に docs/05 を読んでください。

## 公式ドキュメント

- セットアップ: https://code.claude.com/docs/en/setup
- MCP / コネクタ: https://code.claude.com/docs/en/mcp
- 設定ファイル: https://code.claude.com/docs/en/settings
- ルーティン: https://code.claude.com/docs/en/routines
- クラウド⇔ローカル（teleport）: https://code.claude.com/docs/en/claude-code-on-the-web
