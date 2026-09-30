#!/usr/bin/env python3
"""content.json → Slides アーティファクト用ファイル（project/deck.json + project/slides/*.html）を生成する。

使い方:
  python3 build_deck.py content.json OUT_ROOT

  OUT_ROOT/project/deck.json と OUT_ROOT/project/slides/<id>.html が書き出される。
  その後 Artifact ツールで url / root=OUT_ROOT / file_path=<deck.json> / files=<各スライド> を publish する。

デザイン規約は references/design.md、content.json の書式は examples/content.example.json を参照。
デザイン値はこのファイルの定数だけで管理する（スライドごとに直書きしない）。
"""
import datetime
import html
import json
import os
import sys

# ---- デザイントークン（references/design.md と一致させること） -------------------------
INK = "#1A1A22"      # 本文・見出し
SUB = "#33364A"      # 補足
MUTED = "#4A4F5E"    # フッター・グレータグ
LINE = "#D5D8E2"     # カード枠
ACC = "#4A3FB0"      # Fulmo パープル（アクセント）
ACC_SOFT = "#B3ADE8" # グラフの通常バー
TINT = "#F4F3FC"     # ごく薄い面（数式ボックス・KPIパネルのみ）
BLUE = "#3F5FA6"     # 肯定タグ
BROWN = "#8A3F0A"    # 注意タグ
RED = "#E60000"      # 強調（1スライド1か所まで）
FONT = "'Noto Sans JP', Arial, sans-serif"
TONES = {"accent": ACC, "blue": BLUE, "brown": BROWN, "gray": MUTED}

# 文字サイズ（px, 1920×1080 キャンバス。pt 換算は ÷2）
FS = {"crumb": 28, "title": 48, "h3": 40, "body": 34, "sub": 30, "note": 28, "tag": 28,
      "foot": 24, "kpi": 96, "cover_title": 132, "cover_eyebrow": 48, "cover_agenda": 56}

CARD = f"background:#FFFFFF;border:2px solid {LINE};border-radius:16px"
HCARD = f"background:#FFFFFF;border:3px solid {ACC};border-radius:16px"


def esc(t):
    """content.json の文字列は HTML エスケープ。**太字** だけ <b> に変換する。"""
    s = html.escape(str(t), quote=False)
    parts = s.split("**")
    return "".join(f"<b>{p}</b>" if i % 2 else p for i, p in enumerate(parts))


def p(t, size=None, color=INK, weight=400, extra=""):
    size = size or FS["body"]
    return (f'<p style="font-size:{size}px;line-height:1.55;color:{color};'
            f'font-weight:{weight};{extra}">{esc(t)}</p>')


def h3(t, size=None, color=INK):
    return f'<h3 style="font-size:{size or FS["h3"]}px;font-weight:700;line-height:1.4;color:{color}">{esc(t)}</h3>'


def tag(t, tone="accent"):
    bg = TONES.get(tone, tone)
    return (f'<p style="font-size:{FS["tag"]}px;font-weight:700;color:#FFFFFF;background:{bg};'
            f'padding:6px 20px;border-radius:999px;align-self:start">{esc(t)}</p>')


def next_line(t):
    """「⇒ 次のアクション」行。各スライドの結論の受け皿。"""
    return p("⇒ " + t, FS["body"], INK, 700) if t else ""


def footnotes(items, size=None):
    return "".join(p(x, size or FS["note"], SUB) for x in (items or []))


def checks(items):
    return "".join(p("✓ " + x, FS["note"], SUB) for x in (items or []))


def shell(s, body, page, logo):
    note = f"<aside>{esc(s['notes'])}</aside>" if s.get("notes") else ""
    return f'''<section id="{s['id']}" data-transition="fade" style="background:#FFFFFF;color:{INK};font-family:{FONT};padding:56px 96px 112px;display:flex;flex-direction:column;gap:24px">
<img src="{logo}" alt="Fulmo ロゴ" style="position:absolute;right:96px;top:48px;width:180px;height:58px;object-fit:contain">
<div style="display:flex;flex-direction:column;gap:10px;width:1480px">
<p style="font-size:{FS['crumb']}px;font-weight:700;color:{ACC}">{esc(s['crumb'])}</p>
<h2 style="font-size:{FS['title']}px;font-weight:700;line-height:1.35;color:{INK}">{esc(s['title'])}</h2>
</div>
<div style="height:4px;background:{ACC}"></div>
{body}
<p style="position:absolute;left:96px;bottom:44px;width:900px;font-size:{FS['foot']}px;color:{MUTED}">© Fulmo Inc. All rights reserved</p>
<p style="position:absolute;right:96px;bottom:44px;width:200px;text-align:right;font-size:{FS['foot']}px;color:{MUTED}">{page}</p>
{note}
</section>
'''


# ---- スライド型 -------------------------------------------------------------------------

def t_cover(s, logo):
    return f'''<section id="{s['id']}" data-transition="fade" style="background:#FFFFFF;color:{INK};font-family:{FONT};padding:128px 160px;display:flex;flex-direction:column;justify-content:center;gap:32px">
<img src="{logo}" alt="Fulmo ロゴ" style="position:absolute;left:160px;top:96px;width:240px;height:77px;object-fit:contain">
<p style="font-size:{FS['cover_eyebrow']}px;font-weight:700;color:{ACC}">{esc(s['eyebrow'])}</p>
<h1 style="font-size:{FS['cover_title']}px;font-weight:700;line-height:1.2;color:{INK}">{esc(s['title'])}</h1>
<div style="width:1600px;height:4px;background:{ACC}"></div>
<p style="font-size:{FS['cover_agenda']}px;line-height:1.6;color:{SUB}">{esc(s.get('agenda', ''))}</p>
</section>
'''


def t_kpi_chart(s):
    ex, ch = s["explain"], s["chart"]
    ymin, ymax, hmax = ch.get("ymin", 85), ch.get("ymax", 100), 250
    series = ch["series"]
    hl = ch.get("highlight", series[-1][0])
    cols, labs = [], []
    for lab, v in series:
        on = lab == hl
        h = max(40, round((v - ymin) / (ymax - ymin) * hmax))
        cols.append(f'<div style="flex:1;height:{h}px;background:{ACC if on else ACC_SOFT};border-radius:6px 6px 0 0;display:flex;justify-content:center">'
                    f'<p style="font-size:30px;font-weight:700;color:{"#FFFFFF" if on else INK};padding-top:6px">{esc(v)}</p></div>')
        labs.append(f'<p style="flex:1;text-align:center;font-size:30px;color:{INK};font-weight:{700 if on else 400}">{esc(lab)}</p>')
    pills = []
    for pl in ex.get("pills", []):
        row = tag(pl["text"], pl.get("tone", "accent"))
        if pl.get("callout"):
            row += (f'<p style="font-size:{FS["body"]}px;font-weight:700;color:{RED};'
                    f'border-bottom:6px solid {RED};align-self:center">{esc(pl["callout"])}</p>')
        pills.append(f'<div style="display:flex;gap:24px;align-items:center">{row}</div>')
    definition = p(ex["definition"], FS["body"], RED if ex.get("emphasize_definition") else INK, 700 if ex.get("emphasize_definition") else 400)
    body = f'''<div style="flex:1;display:flex;gap:40px">
<div style="flex:1;display:flex;flex-direction:column;gap:18px">
{h3(ex['heading'])}
{definition}
<div style="background:{TINT};border-radius:14px;padding:22px 28px;display:flex;flex-direction:column;gap:4px">
{p(ex['formula'], FS['sub'], INK, 700)}
{p(ex.get('formula_note', ''), FS['note'], SUB) if ex.get('formula_note') else ''}
</div>
{p(ex['example'], FS['sub'], SUB) if ex.get('example') else ''}
{''.join(pills)}
</div>
<div style="flex:1;display:flex;flex-direction:column;gap:14px;{CARD};padding:28px 36px">
<div style="display:flex;align-items:end;justify-content:space-between">
{h3(ch['title'], 36)}
<p style="font-size:44px;font-weight:700;color:{ACC}">{esc(ch.get('headline', ''))}</p>
</div>
<div style="display:flex;align-items:end;gap:14px;height:{hmax}px;border-top:2px dashed {ACC};border-bottom:2px solid {SUB}">{''.join(cols)}</div>
<div style="display:flex;gap:14px">{''.join(labs)}</div>
{footnotes(ch.get('footnotes'), FS['foot'])}
{checks(ch.get('points'))}
</div>
</div>'''
    return body


def t_flow3(s):
    arrow = f'<x-shape kind="arrow-right" style="width:56px;height:36px;background:{ACC}"></x-shape>'
    cards = []
    steps = s["steps"]
    for i, st in enumerate(steps):
        last = i == len(steps) - 1
        inner = st.get("list")
        text = (f'<ul style="font-size:{FS["body"]}px;line-height:1.55;color:{INK}">' +
                "".join(f"<li>{esc(x)}</li>" for x in inner) + "</ul>") if inner else p(st.get("body", ""))
        nxt = next_line(s.get("next")) if last else ""
        cards.append(f'''<div style="flex:1;align-self:stretch;display:flex;flex-direction:column;gap:18px;{HCARD if last else CARD};padding:36px">
{tag(st['tag'], st.get('tone', 'accent'))}
{h3(st['heading'])}
{text}
{nxt}
</div>''')
    return '<div style="flex:1;display:flex;align-items:center;gap:24px">' + arrow.join(cards) + "</div>"


def t_before_after_kpi(s):
    k = s["kpi"]

    def row(label, text, hi):
        return (f'<div style="display:flex;gap:28px;align-items:center;{HCARD if hi else CARD};padding:30px">'
                f'<p style="font-size:32px;font-weight:700;color:#FFFFFF;background:{ACC if hi else MUTED};padding:8px 0;border-radius:10px;width:180px;text-align:center">{esc(label)}</p>'
                f'{p(text, extra="flex:1")}</div>')
    effects = "".join(tag(e, "blue") for e in s.get("effects", []))
    return f'''<div style="flex:1;display:flex;gap:40px">
<div style="flex:4;display:flex;flex-direction:column;justify-content:center;gap:18px">
{row(s['before']['label'], s['before']['text'], False)}
<x-shape kind="arrow-down" style="width:44px;height:44px;background:{ACC};align-self:center"></x-shape>
{row(s['after']['label'], s['after']['text'], True)}
<div style="display:flex;gap:16px">{effects}</div>
</div>
<div style="flex:3;display:flex;flex-direction:column;justify-content:center;gap:18px;background:{TINT};border-radius:16px;padding:44px">
{tag(k['status']) if k.get('status') else ''}
{p(k['label'], FS['body'], SUB, 700)}
<p style="font-size:{FS['kpi']}px;font-weight:700;line-height:1.15;color:{ACC}">{esc(k['value'])}</p>
{footnotes(k.get('footnotes'), 32)}
{next_line(k.get('next'))}
</div>
</div>'''


def t_grid4(s):
    cards = []
    for i, it in enumerate(s["items"], 1):
        cards.append(f'''<div style="display:flex;gap:28px;align-items:start;{CARD};padding:32px 36px">
<p style="font-size:52px;font-weight:700;color:{ACC};line-height:1.1">{i:02d}</p>
<div style="flex:1;display:flex;flex-direction:column;gap:12px">
{h3(it['title'])}
{p(it['body'])}
</div>
</div>''')
    grid = f'<div style="flex:1;display:grid;grid-template-columns:1fr 1fr;grid-template-rows:1fr 1fr;gap:20px">{"".join(cards)}</div>'
    return grid + (next_line(s["next"]) if s.get("next") else "")


def t_announcement(s):
    b = s["block"]
    photo = (f'<img src="{b["photo"]}" alt="{esc(b.get("photo_alt", ""))}" style="position:absolute;left:566px;top:342px;width:364px;height:452px;object-fit:contain">'
             if b.get("photo") else "")
    sticker = (f'<img src="{s["sticker"]}" alt="" style="width:217px;height:217px;object-fit:contain;align-self:center">'
               if s.get("sticker") else "")
    items = "".join(f'''<div style="display:flex;gap:24px;align-items:center;{CARD};padding:26px 32px">
<p style="font-size:40px;font-weight:700;color:{ACC}">{i:02d}</p>
{p(t, extra="flex:1")}
</div>''' for i, t in enumerate(s["items"], 1))
    main = "<br>".join(esc(x) for x in b["main_lines"])
    msg = b.get("message", "")
    msg_style = "font-size:40px;font-weight:700;line-height:1.55;color:#F2F1FD"
    # 写真があるときは一言を写真の下（y=846）に固定して重なりを防ぐ（FIX版の配置）
    msg_flow = f'<p style="{msg_style}">{esc(msg)}</p>' if msg and not b.get("photo") else ""
    msg_pinned = (f'<p style="position:absolute;left:152px;top:830px;width:800px;{msg_style}">{esc(msg)}</p>'
                  if msg and b.get("photo") else "")
    return f'''<div style="flex:1;display:flex;gap:40px">
<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:24px;background:{ACC};border-radius:16px;padding:56px">
<p style="font-size:40px;font-weight:700;color:#E6E4FA">{esc(b['eyebrow'])}</p>
<p style="font-size:80px;font-weight:700;line-height:1.3;color:#FFFFFF">{main}</p>
{msg_flow}
</div>
<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:20px">
{h3(s['list_heading'])}
{items}
{sticker}
</div>
</div>
{photo}
{msg_pinned}'''


TYPES = {"kpi_chart": t_kpi_chart, "flow3": t_flow3, "before_after_kpi": t_before_after_kpi,
         "grid4": t_grid4, "announcement": t_announcement}


def main():
    src, root = sys.argv[1], sys.argv[2]
    c = json.load(open(src, encoding="utf-8"))
    logo = c["logo"]
    sd = os.path.join(root, "project", "slides")
    os.makedirs(sd, exist_ok=True)
    order, sections = [], {}
    for n, s in enumerate(c["slides"], 1):
        if s["type"] == "cover":
            out = t_cover(s, logo)
        else:
            out = shell(s, TYPES[s["type"]](s), n, logo)
        open(os.path.join(sd, s["id"] + ".html"), "w", encoding="utf-8").write(out)
        order.append(s["id"])
        sections[f"s{n}"] = {"description": s.get("crumb", s.get("title", "")), "start": s["id"]}
    deck = {"v": 4, "createdOnFiles": {"v": 1, "at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")},
            "lists": "css", "title": c["deck_title"], "order": order, "sections": sections,
            "faces": {"noto-sans-jp": {"family": "Noto Sans JP",
                                       "href": "https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap"}}}
    json.dump(deck, open(os.path.join(root, "project", "deck.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print("wrote", len(order), "slides:", ", ".join(order))


if __name__ == "__main__":
    main()
