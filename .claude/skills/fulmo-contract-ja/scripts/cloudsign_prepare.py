#!/usr/bin/env python3
"""クラウドサインに下書き（書類・PDF・宛先）を作る。送信はしない。

既定では API を呼ばず、送る内容を表示するだけ。--execute を付けたときだけ API を呼ぶ。
クライアントID は環境変数 CLOUDSIGN_CLIENT_ID から読む（引数やファイルには書かない）。

使い方:
  python3 cloudsign_prepare.py --pdf 書類.pdf --title "変更覚書_〇〇御中" \
      --name "山田 太郎" --email "taro@example.co.jp" --organization "〇〇株式会社" [--message "..."] \
      [--sandbox] [--execute]
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

PRODUCTION = "https://api.cloudsign.jp"
SANDBOX = "https://api-sandbox.cloudsign.jp"
WAIT_SECONDS = 5  # 公式ガイド: 作成・更新の直後は反映まで数秒〜10秒待つことを推奨


def request(method, url, token=None, form=None, files=None):
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if files:
        boundary = uuid.uuid4().hex
        parts = []
        for key, value in (form or {}).items():
            parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
        for key, (filename, content, ctype) in files.items():
            disp = f'form-data; name="{key}"; filename="{urllib.parse.quote(filename)}"'
            parts.append(f"--{boundary}\r\nContent-Disposition: {disp}\r\nContent-Type: {ctype}\r\n\r\n".encode() + content + b"\r\n")
        parts.append(f"--{boundary}--\r\n".encode())
        data = b"".join(parts)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif form is not None:
        data = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            body = res.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:500]
        sys.exit(f"クラウドサイン API エラー: {method} {urllib.parse.urlparse(url).path} → {e.code} {detail}")
    except urllib.error.URLError as e:
        sys.exit(f"クラウドサインに接続できません（{e.reason}）。入力シートで準備してください（references/cloudsign.md の3）。")


def main():
    p = argparse.ArgumentParser(description="クラウドサインに下書きを作る（送信はしない）")
    p.add_argument("--pdf", required=True, help="添付する最終版の PDF")
    p.add_argument("--title", required=True, help="書類名")
    p.add_argument("--name", required=True, help="宛先の氏名")
    p.add_argument("--email", required=True, help="宛先のメールアドレス")
    p.add_argument("--organization", default="", help="宛先の会社名")
    p.add_argument("--message", default="", help="先方へのメッセージ（任意）")
    p.add_argument("--sandbox", action="store_true", help="試験用環境を使う")
    p.add_argument("--execute", action="store_true", help="実際に API を呼んで下書きを作る")
    a = p.parse_args()

    pdf = Path(a.pdf)
    if pdf.suffix.lower() != ".pdf" or not pdf.is_file():
        sys.exit(f"PDF が見つかりません: {pdf}")
    base = SANDBOX if a.sandbox else PRODUCTION

    print("作成する下書き")
    print(f"  環境: {'試験用' if a.sandbox else '本番'}（{base}）")
    print(f"  書類名: {a.title}")
    print(f"  添付: {pdf.name}（{pdf.stat().st_size:,} バイト）")
    print(f"  宛先: {a.organization} {a.name} <{a.email}>")
    if a.message:
        print(f"  メッセージ: {a.message}")
    if not a.execute:
        print("\n確認のみ（API は呼んでいません）。作成するときは --execute を付けて実行してください。")
        return

    client_id = os.environ.get("CLOUDSIGN_CLIENT_ID", "").strip()
    if not client_id:
        sys.exit("環境変数 CLOUDSIGN_CLIENT_ID が設定されていません。入力シートで準備してください（references/cloudsign.md の3）。")

    token = request("POST", f"{base}/token", form={"client_id": client_id}).get("access_token")
    if not token:
        sys.exit("アクセストークンを取得できませんでした。クライアントID と環境（本番／試験用）を確かめてください。")

    doc_form = {"title": a.title}
    if a.message:
        doc_form["message"] = a.message
    doc = request("POST", f"{base}/documents", token, form=doc_form)
    doc_id = doc.get("id")
    if not doc_id:
        sys.exit(f"書類を作成できませんでした: {json.dumps(doc, ensure_ascii=False)[:300]}")

    time.sleep(WAIT_SECONDS)
    request("POST", f"{base}/documents/{doc_id}/files", token, form={"name": pdf.name},
            files={"uploadfile": (pdf.name, pdf.read_bytes(), "application/pdf")})
    participant = {"email": a.email, "name": a.name}
    if a.organization:
        participant["organization"] = a.organization
    time.sleep(WAIT_SECONDS)
    request("POST", f"{base}/documents/{doc_id}/participants", token, form=participant)

    print(f"\n下書きを作成しました（送信はしていません）。書類ID: {doc_id}")
    print("クラウドサインの画面の下書き一覧で、書類・宛先・押印欄を確認してから送信してください。")


if __name__ == "__main__":
    main()
