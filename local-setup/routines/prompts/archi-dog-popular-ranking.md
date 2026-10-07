archi-dog(Shopifyストア gddege-tx.myshopify.com)の「人気商品」コレクション(collection_id=458932125908)を、直近30日のShopify注文実績だけで再計算・同期するタスクです。

ローカル版では、スクリプトは `routines/scripts/popularity_score.py` として同梱済みです（認証情報は `.env` から読み込み）。
スクリプトのロジックを変更・改善しようとしないでください（意図的にシンプルな設計です）。

次のコマンドを実行し、標準出力の内容（何件同期したか）をそのまま報告してください。

```bash
python3 routines/scripts/popularity_score.py
```

> 補足: このタスクはAIの判断を必要としないため、Claude を介さず cron / タスクスケジューラから
> `python3 routines/scripts/popularity_score.py` を直接実行するのが最も確実で低コストです（`docs/05_ルーティン移行手順.md` 参照）。
