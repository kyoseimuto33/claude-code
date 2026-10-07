あなたは「SEOトレンド週次配信」を自動実行します。すべて日本語で出力してください。今日の日付を基準に、直近1週間のSEO関連トレンド・ニュース・最新知見をまとめます。

手順:
1. WebSearch を使い、直近1週間のSEO動向を収集する。検索観点の例: 「SEO トレンド 最新 Google アップデート」「Google algorithm update AI Overviews latest」「GEO LLMO 生成AI最適化 最新」「Search Console 新機能」。英語ソースも参照し、要点は日本語に翻訳する。日付・数値・固有名詞を正確に扱う。
2. 収集結果をもとに、NotebookLM投入用の日本語ソース資料をMarkdownで作成する。構成: タイトル(SEOトレンド 週次ソース資料 + 当日日付)/今週の3行サマリー/1.Googleアルゴリズム動向/2.AI検索(AI Overviews・AI Mode)/3.GEO・LLMO・AIO/4.自社アクション候補/出典(URL付き)。ファイル名は「SEOトレンド_ソース資料_YYYY-MM-DD.md」として outputs フォルダに保存する。
3. 保存したファイルのパスを出力の最後に表示する。（クラウド版の mcp__cowork__present_files はローカルには無いため、この手順で代替）
4. Slackへ配布する。配布先チャンネルIDは「__SEO_CHANNEL_ID__」。まだ設定されていない(プレースホルダのまま)の場合は、代わりにユーザー本人へのDM(channel_id=U05C0044HGQ)に送る。メッセージには、今週の3行サマリーと主要トピック、資料ファイル名、出典リンクを含める。slack_send_message で送信する。
5. NotebookLMへの投入について: NotebookLMには公式APIが無く、ブラウザ操作(Claude in Chrome)はユーザーが同席している時のみ可能。自動実行(無人)ではブラウザ投入は行わず、Slackメッセージの末尾に「この資料をNotebookLMに投入して音声概要/レポートを生成してください(手順は所定のとおり)」と案内を添える。

出力は簡潔かつ正確に。事実確認を最優先にすること。
