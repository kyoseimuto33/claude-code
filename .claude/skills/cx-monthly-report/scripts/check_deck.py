#!/usr/bin/env python3
"""生成したスライド（project/slides/*.html）と content.json を品質ルールで機械チェックする。

使い方:
  python3 check_deck.py OUT_ROOT [content.json]

終了コード 0 = 問題なし、1 = 要修正（ERROR あり）。WARN は目視確認を促すもの。
ルールの根拠は references/writing.md と references/design.md。
"""
import glob
import json
import os
import re
import sys

MIN_PX = 24          # どの文字もこれ未満は不可
BODY_MIN_PX = 34     # 本文（p の既定）の最小
TITLE_MAX = 60       # タイトル（1メッセージ）の最大文字数
TITLE_MIN = 20       # これより短いタイトルは抽象的すぎる可能性
BANNED_IN_TITLE = ["暫定", "について", "の報告", "活動内容"]
BANNED_ANY = ["gradient"]
LABEL_WORDS = ["論点", "根拠", "示唆", "意思決定"]  # 思考過程のラベルはスライドに出さない
NO_NEXT_TYPES = {"kpi_chart", "grid4", "announcement", "cover"}  # FIX版で⇒行を持たない型


def main():
    root = sys.argv[1]
    content = json.load(open(sys.argv[2], encoding="utf-8")) if len(sys.argv) > 2 else None
    errs, warns = [], []
    types = {s["id"]: s["type"] for s in content.get("slides", [])} if content else {}
    files = sorted(glob.glob(os.path.join(root, "project", "slides", "*.html")))
    if not files:
        print("ERROR: slides not found under", root)
        sys.exit(1)
    for f in files:
        sid = os.path.basename(f)[:-5]
        h = open(f, encoding="utf-8").read()
        for px in map(int, re.findall(r"font-size:(\d+)px", h)):
            if px < MIN_PX:
                errs.append(f"{sid}: font-size {px}px < {MIN_PX}px")
        if "background:#FFFFFF" not in h.split(">")[0]:
            errs.append(f"{sid}: section background must be #FFFFFF")
        for w in BANNED_ANY:
            if w in h:
                errs.append(f"{sid}: '{w}' is not allowed (white, flat design)")
        visible = re.sub(r"<aside>.*?</aside>", "", h, flags=re.S)
        text = re.sub(r"<[^>]+>", "", visible)
        for w in LABEL_WORDS:
            if re.search(rf"(^|\n){w}(\n|$)", text):
                errs.append(f"{sid}: thinking label '{w}' shown on slide")
        m = re.search(r"<h2[^>]*>(.*?)</h2>", h, re.S)
        if m:
            t = re.sub(r"<[^>]+>", "", m.group(1)).strip()
            if len(t) > TITLE_MAX:
                warns.append(f"{sid}: title {len(t)} chars > {TITLE_MAX} (3行以上になり得る)")
            if len(t) < TITLE_MIN:
                warns.append(f"{sid}: title {len(t)} chars — 結論＋数値/状態の1文になっているか")
            for w in BANNED_IN_TITLE:
                if w in t:
                    errs.append(f"{sid}: title contains '{w}' (結論を書く／暫定は※注記へ)")
            if not re.search(r"\d|見込み|完了|白紙|異動|達成|維持|改善|作った|できた", t):
                warns.append(f"{sid}: title has no number/state — 抽象的すぎないか")
            if "⇒" not in text and types.get(sid) not in NO_NEXT_TYPES:
                warns.append(f"{sid}: '⇒ 次のアクション' 行なし（次の打ち手・期日があるなら明示）")
        bodies = re.findall(r'<p style="font-size:(\d+)px;line-height:1.55;color:#1A1A22;font-weight:400', h)
        for px in map(int, bodies):
            if px < BODY_MIN_PX:
                errs.append(f"{sid}: body text {px}px < {BODY_MIN_PX}px")
        if h.count("#E60000") > 3:
            warns.append(f"{sid}: 赤の強調が多い（1スライド2か所まで）")
    if content:
        for s in content.get("slides", []):
            k = s.get("kpi")
            if k and k.get("value"):
                nums = re.findall(r"\d+", k["value"])
                if nums and not any(n in s.get("title", "") for n in nums):
                    warns.append(f"{s['id']}: タイトルとKPI（{k['value']}）の数値・指標がそろっていない（1枚1メッセージ）")
            if s["type"] != "cover" and not s.get("sources"):
                warns.append(f"{s['id']}: content.json に sources（根拠のURL）がない")
    for e in errs:
        print("ERROR:", e)
    for w in warns:
        print("WARN: ", w)
    print(f"checked {len(files)} slides: {len(errs)} error(s), {len(warns)} warning(s)")
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
