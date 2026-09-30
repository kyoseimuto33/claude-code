# 調査手順（cx-report-researcher に渡す内容）

機密を避けるため、ここにはシートIDやチャンネルIDを書かない。毎回、名前で検索して見つける。

## Slack（MCP: slack_search_users / slack_search_public_and_private / slack_read_thread）
1. 重点人物のユーザーIDを `slack_search_users` で取得。
2. `filters: from:<@ID> after:<前月末日> before:<翌月1日>`、`sort: timestamp`、`sort_dir: asc`、`limit: 20`、`response_format: concise` で**最終ページまで**読む（1か月で300件超もある）。
3. 次の投稿はスレッドまで読む：方針・決定（「〜で進めます」「〜の方針」）、数値（算出・集計）、顧客への案内文、他部署への依頼、議事録やシートのリンク。
4. CX系チャンネル（名前に `cx`、`clc_only`、`cs_cx_` を含む）の対象月の主要スレッド、CXメンバーの投稿も補助的に確認。
5. 雑談・リンク共有・スタンプだけの投稿は集計しない。

## Google Drive / Sheets（MCP: search_files / read_file_content / get_values）
`modifiedTime >= '<対象月1日>'` で次を探す：
- 「Mgr会議資料」：対象月のタブのCX行（ミッション／現状／直近1週間の進捗／相談事項）
- 「全社定例」議事録（Gemini メモ）：CX部分
- 「1on1」議事録（重点人物が参加しているもの）
- 「CX定例」「グロース定例」議事録
- 「公式LINE分析」などCX分析シート：結論と主要数値
- KPI算出シート（NRR・チャーン・MRR）。Slackで共有されたリンクを優先
- 組織図・体制変更の資料

## 出力形式（研究者サブエージェントの返却）
```
## 事実一覧
| 日付 | テーマ | 事実（1行） | 数値 | 出典（チャンネル/ファイル名＋リンク） | 重点人物の発信 | 取扱注意 |
## テーマ別まとめ（3〜7テーマ）
## 数値の食い違い・集計できなかったもの
## 取扱注意の一覧
```
推測は「推測」と明記。パスワード・認証情報・個人の連絡先は出力しない。
