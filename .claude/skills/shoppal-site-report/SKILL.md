---
name: shoppal-site-report
description: Shoppal（Fulmo）ECサイトの現状報告書（事業レポート / 現状のご報告）を、任意の1〜3サイトについて .pptx で作成する。管理画面・GA4・Search Console・Slack・Google Drive・月次レポートPDFから数値を集め、決まったフォーマット（表紙→ご判断時期→現況→サイト別の売上とアクセス・検索順位と取り組み→重点施策→資産価値の試算→進め方）で出力する。「〇〇サイトの現状報告を作って」「事業レポート」「資産価値の試算」「月次報告のpptx」などの依頼で使う。
---

# Shoppal サイト現状報告書

クライアント向けの「事業レポート（現状のご報告）」を作る。中身は数値の収集 → 設定JSONの作成 → `build_report.js` での生成 → 目視QA の4段階。デザインとページ構成はスクリプトが固定で持つので、作業者はJSONの中身（数値と短い文章）だけを考えればよい。

## 0. 準備（セッションごとに1回）

```bash
bash .claude/skills/shoppal-site-report/scripts/setup.sh
```

ライブラリ、ブラウザの証明書、日本語フォント、LibreOfficeを入れ、必要な環境変数の有無を表示する。`MISSING` が出たら、セッション上部の環境メニュー →「Edit」で次を登録してもらう（値をチャットに貼らせない）。

| 環境変数 | 内容 |
|---|---|
| `SHOPPAL_ADMIN_USER` / `SHOPPAL_ADMIN_PASS` | Shoppal管理画面のログイン |
| `GOOGLE_SA_KEY_JSON` | GA4・Search Console用サービスアカウントのJSONキー |

ネットワークの許可ドメインに `*.flumo-admin-server.com` が必要。Search Consoleで「not shared」と出たサイトは、そのプロパティにサービスアカウント（JSONの `client_email`）を「フル」で追加してもらう。

## 1. 数値を集める

サイトは service_id（例：`yosozee`、`shouldagg`）で指定する。スクリプトは `.claude/skills/shoppal-site-report/scripts/` にある。

| 取りたいもの | コマンド / 取得元 |
|---|---|
| 月別の注文件数・売上 | `node orders_monthly.js <service_id>`（管理画面の注文一覧。全月を同じ基準で集計できるので売上グラフはこれを使う） |
| 今月の追加商品・記事・注文数、入金額・原価 | `node admin_summary.js <service_id>` |
| GA4のプロパティID | `python3 ga4_find.py <service_id> <カタカナ名>`（例：ヨソジー、ショルダッグ） |
| 月別セッション（全体・自然検索） | `python3 ga4_monthly.py <開始日> <終了日> <プロパティID>` |
| 表示回数・クリック・平均掲載順位 | `python3 gsc_monthly.py <ドメイン> <開始日> <終了日>` |
| キーワード順位、健康診断、カニバリ組数、上位化候補、売れ筋 | 月次レポートPDF：`python3 extract_report_pdf.py <pdf>`（1ページ目の画像も出るのでグラフを読む） |
| 契約終了日・ご判断時期・経緯 | Slack検索（`#cx_買取その他プラン連携`、`#clc_only`、サイト名・顧客名）、Drive「修正版_週次モニタリング」「client_fulmo」CSV |
| 9月など直近の購入明細 | Slack `#購入通知`（毎日の購入一覧。管理画面に入れない場合の代替） |

月次レポートPDFは管理画面のダッシュボード「月次レポートダウンロード」から出せるが、前月分は毎月6営業日目ごろに公開される。公開前は上の表の他の情報源でまとめる。

注意：
- **数値の基準をそろえる。** 売上の推移は注文一覧の集計で通す。PDFの「売上サマリー（暫定）」は原価未確定分が抜けて少なく出ることがあるので、注文一覧の数値と混ぜて比べない。
- **個人情報を残さない。** 注文一覧には顧客の氏名・住所・メールが含まれる。スクリプトは日付と金額しか読まないので、画面のテキストやスクリーンショットを保存しない。
- **社内事情を書かない。** 返金・督促・トラブル対応・他顧客の情報など、Slackで見つけた社内のやり取りはレポートに載せない。必要なら作業者への報告にだけ書く。
- 確認できない日付や数値は推測で埋めず、報告時に「未確認」と伝える。

## 2. 設定JSONを書く

`templates/example.json`（Shiju-more・Shouldaggの実例）をコピーして書き換える。主な項目：

- `date` / `asOf`：作成日と数値の時点。
- `decision`：ご判断時期のページ。契約終了日が分からなければ項目ごと消す（ページが出なくなる）。
- `asset`：`multiple`（標準36倍）と `marginRate`（標準0.4）。実際の粗利を使う行は `grossProfit` を指定する。資産価値・粗利はスクリプトが計算するので、JSONに手で書かない。
- `sites[]`（1〜3件）：`summary`（現況ページの4行と一言）、`sales`（グラフの月と金額、右側の3指標、まとめ）、`detail.cards`（3枚：アイコンは search / refresh / eye / card / yen / filter / trend / user / check）、`priorities`（3つ）、`asset`（試算の行）。
- `summaryTakeaway` / `prioritiesTakeaway` / `assetTakeaway` / `roadmap`：各ページ下のまとめと進め方。`assetTakeaway` の合計金額は、生成時にコンソールへ出る `asset ... value` を見て書く。

文章のルール：
- 1行で言い切る短い文。作業過程・データの出所・注釈はスライドに書かない（例外：資産価値の算出式の1行）。
- 数値は比較つきで示す（「3月の約3.3倍」「7月→9月」など）。割合や倍率は電卓で確かめる。
- カードの太字（`big`）は12文字以内。長いと自動で小さくなるが、短いほうが読みやすい。

## 3. 生成する

```bash
node .claude/skills/shoppal-site-report/scripts/build_report.js config.json 事業レポート_<サイト名>_<YYYYMMDD>.pptx
```

`pptxgenjs` が見つからない場合は `npm install -g pptxgenjs` を実行する。

## 4. 目視QA

```bash
soffice --headless --convert-to pdf --outdir <dir> <pptx>   # pptxスキルの scripts/office/soffice.py があればそちらを使う
```

PDFを画像にして全ページを見る（`pymupdf` で `page.get_pixmap(dpi=80)`）。確認点：文字のはみ出し・不自然な折り返し、表と算出式の重なり、グラフの金額ラベル、数値の打ち間違い。直すのはJSON（文章を短くする）で、スクリプトはいじらない。

最後に .pptx を共有し、報告には「使ったデータの出所」「未確認の点」「取れなかったデータ」を短く添える。
