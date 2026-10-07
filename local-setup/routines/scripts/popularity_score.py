#!/usr/bin/env python3
"""
archi-dog 人気商品ランキング 週次更新（ローカル実行版）

クラウドのルーティン「archi-dog 人気商品ランキング 週次更新」がプロンプト内に
埋め込んでいたスクリプトと同一のロジックです。違いは認証情報だけで、
ソースに直書きせず環境変数（または同じフォルダの .env）から読み込みます。

  必要な環境変数:
    SHOPIFY_READ_ORDERS_CLIENT_ID / SHOPIFY_READ_ORDERS_CLIENT_SECRET
    SHOPIFY_WRITE_CLIENT_ID       / SHOPIFY_WRITE_CLIENT_SECRET

Claude を介さず `python3 popularity_score.py` で直接実行できます（推奨）。
"""
import json, os, time, urllib.error, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _load_dotenv():
    # 依存ライブラリなしで KEY=VALUE 形式の .env を読む（既存の環境変数を優先）
    here = Path(__file__).resolve().parent  # routines/scripts → パッケージ直下まで遡って探す
    for p in (here / ".env", here.parent / ".env", here.parent.parent / ".env", Path.cwd() / ".env"):
        if p.is_file():
            for line in p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
            break


_load_dotenv()


def _env(name):
    v = os.environ.get(name, "")
    if not v or v.startswith("__"):
        raise SystemExit(f"環境変数 {name} が未設定です（.env を確認してください）")
    return v


SHOP = os.environ.get("SHOPIFY_SHOP", "gddege-tx.myshopify.com")
API_VERSION = "2024-01"
POPULAR_COLLECTION_ID = int(os.environ.get("SHOPIFY_POPULAR_COLLECTION_ID", "458932125908"))

READ_ORDERS_CLIENT_ID = _env("SHOPIFY_READ_ORDERS_CLIENT_ID")
READ_ORDERS_CLIENT_SECRET = _env("SHOPIFY_READ_ORDERS_CLIENT_SECRET")

WRITE_CLIENT_ID = _env("SHOPIFY_WRITE_CLIENT_ID")
WRITE_CLIENT_SECRET = _env("SHOPIFY_WRITE_CLIENT_SECRET")

TOP_N = 12


def get_token(client_id, client_secret):
    url = f"https://{SHOP}/admin/oauth/access_token"
    data = json.dumps({"client_id": client_id, "client_secret": client_secret, "grant_type": "client_credentials"}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())["access_token"]


def shopify_get(path, token):
    url = f"https://{SHOP}/admin/api/{API_VERSION}/{path}"
    req = urllib.request.Request(url, headers={"X-Shopify-Access-Token": token})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read()), resp.headers.get("Link", "")


def shopify_request(method, path, token, body=None):
    url = f"https://{SHOP}/admin/api/{API_VERSION}/{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={"X-Shopify-Access-Token": token, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
        return json.loads(raw) if raw else {}


def fetch_active_products(token):
    products = []
    path = "products.json?status=active&limit=250&fields=id,title"
    while True:
        body, link = shopify_get(path, token)
        products.extend(body.get("products", []))
        next_url = None
        for part in link.split(","):
            if 'rel="next"' in part:
                next_url = part.split(";")[0].strip().strip("<>")
        if not next_url:
            break
        path = next_url.split(f"/{API_VERSION}/")[-1]
        time.sleep(0.3)
    return products


def fetch_orders_quantity(token, created_at_min):
    qty = {}
    path = f"orders.json?status=any&created_at_min={created_at_min}&limit=250&fields=id,line_items"
    while True:
        body, link = shopify_get(path, token)
        for order in body.get("orders", []):
            for li in order.get("line_items", []):
                pid = li.get("product_id")
                if pid is None:
                    continue
                qty[pid] = qty.get(pid, 0) + int(li.get("quantity") or 0)
        next_url = None
        for part in link.split(","):
            if 'rel="next"' in part:
                next_url = part.split(";")[0].strip().strip("<>")
        if not next_url:
            break
        path = next_url.split(f"/{API_VERSION}/")[-1]
        time.sleep(0.3)
    return qty


def sync_collection(token, ranked_ids):
    existing, _ = shopify_get(f"collects.json?collection_id={POPULAR_COLLECTION_ID}&limit=250&fields=id,product_id,position", token)
    existing = existing.get("collects", [])
    existing_by_pid = {c["product_id"]: c for c in existing}
    desired = {pid: i + 1 for i, pid in enumerate(ranked_ids)}

    to_add = [pid for pid in desired if pid not in existing_by_pid]
    to_remove = [c for pid, c in existing_by_pid.items() if pid not in desired]
    to_update = [(existing_by_pid[pid]["id"], pos) for pid, pos in desired.items() if pid in existing_by_pid and existing_by_pid[pid]["position"] != pos]

    print(f"sync plan: add={len(to_add)} remove={len(to_remove)} reposition={len(to_update)}")

    for pid in to_add:
        shopify_request("POST", "collects.json", token, {"collect": {"collection_id": POPULAR_COLLECTION_ID, "product_id": pid, "position": desired[pid]}})
        time.sleep(0.3)
    for c in to_remove:
        shopify_request("DELETE", f"collects/{c['id']}.json", token)
        time.sleep(0.3)
    for collect_id, pos in to_update:
        shopify_request("PUT", f"collects/{collect_id}.json", token, {"collect": {"id": collect_id, "position": pos}})
        time.sleep(0.3)


def main():
    write_token = get_token(WRITE_CLIENT_ID, WRITE_CLIENT_SECRET)
    read_token = get_token(READ_ORDERS_CLIENT_ID, READ_ORDERS_CLIENT_SECRET)

    products = fetch_active_products(write_token)
    active_ids = {p["id"] for p in products}
    title_by_id = {p["id"]: p["title"] for p in products}
    print(f"active products: {len(products)}")

    created_at_min = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    orders_qty = fetch_orders_quantity(read_token, created_at_min)
    orders_qty = {pid: q for pid, q in orders_qty.items() if pid in active_ids}
    print(f"products with orders in last 30d: {len(orders_qty)}")

    ranked = sorted(orders_qty, key=lambda pid: orders_qty[pid], reverse=True)[:TOP_N]
    if not ranked:
        print("直近30日で注文実績のある商品がありません。コレクションは変更せず終了します。")
        return

    for pid in ranked:
        print(f"  {title_by_id.get(pid, pid)}: qty={orders_qty[pid]}")

    sync_collection(write_token, ranked)
    print("done")


if __name__ == "__main__":
    main()
