# armtechstore.jp 収益シミュレーション（プロジェクト指示書）

このリポジトリは ECサイト armtechstore.jp の収益シミュレーションです。詳細は README.md を参照。

## ファイル
- `build_simulation.py` … Excel モデルの生成スクリプト（openpyxl）。実績データ・シナリオ定義はファイル先頭の定数
- `armtechstore_収益シミュレーション_改訂版.xlsx` … 生成物（数式連動）。手で編集せず、スクリプトを直して再生成する
- `index.html` … 外部依存なしのブラウザ版シミュレーター

## ルール
- Excel 数式・Python（`run_scenario`）・`index.html` の JS は丸めまで含めて同一結果を返すこと。
  どれか1つのロジックや前提値を変えたら、残り2つも合わせて更新し、`python3 build_simulation.py` の出力サマリーと
  HTML の表示値が一致することを確認する
- 丸めは「半分は切り上げ」（Excel ROUND / JS Math.round と同じ）
- 実績データを更新したら README.md の「結果」表も更新する
- 文書・コメントは日本語

## 実行
```bash
python3 -m pip install -r requirements.txt   # 初回のみ（openpyxl）
python3 build_simulation.py                  # xlsx を再生成し、シナリオ別サマリーを表示
```
