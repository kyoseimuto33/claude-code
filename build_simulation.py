# -*- coding: utf-8 -*-
"""
armtechstore.jp 収益シミュレーション（改訂版）生成スクリプト

元データ: Fulmo月次レポート（2025/07〜2026/06 実績12ヶ月）
出力: armtechstore_収益シミュレーション_改訂版.xlsx
  - シミュレーション（改訂版）: 数式連動の予測モデル（標準シナリオ）+ シナリオ比較 + グラフ
  - 前提条件・根拠: 全パラメータの導出根拠
  - 実績データ: 12ヶ月の実績一覧
"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import LineChart, Reference, Series
from openpyxl.chart.marker import Marker
from openpyxl.drawing.line import LineProperties
from openpyxl.utils import get_column_letter
from datetime import datetime

# ---------------------------------------------------------------- 実績データ
MONTHS_ACT = ["2025/07", "2025/08", "2025/09", "2025/10", "2025/11", "2025/12",
              "2026/01", "2026/02", "2026/03", "2026/04", "2026/05", "2026/06"]
VISITS_ACT = [112, 197, 597, 1153, 2015, 3111, 5241, 5108, 7363, 6053, 5780, 5797]
ORDERS_ACT = [0, 0, 3, 1, 0, 0, 4, 3, 3, 5, 3, 5]
SALES_ACT  = [0, 0, 42780, 9880, 0, 0, 54220, 26160, 23890, 115980, 36060, 72840]
GP_ACT     = [0, 0, 20390, 3940, 0, 0, 28630, 13080, 9223, 61116, 17530, 33200]

MONTHS_FC = ["2026/07", "2026/08", "2026/09", "2026/10", "2026/11", "2026/12",
             "2027/01", "2027/02", "2027/03", "2027/04", "2027/05", "2027/06"]

# 導出値
BASE_VISITS = sum(VISITS_ACT[-3:]) / 3          # 直近3ヶ月平均 = 5,876.7
AOV_ALL   = sum(SALES_ACT) / sum(ORDERS_ACT)    # 14,141
GP_RATE   = sum(GP_ACT) / sum(SALES_ACT)        # 49.0%
CVR_6M    = sum(ORDERS_ACT[-6:]) / sum(VISITS_ACT[-6:])   # 0.0651%
CVR_3M    = sum(ORDERS_ACT[-3:]) / sum(VISITS_ACT[-3:])   # 0.0737%
CVR_BEST  = max(o / v for o, v in zip(ORDERS_ACT[6:], VISITS_ACT[6:]) if o)  # 0.0863%
FEE = 55000

# ---------------------------------------------------------------- シナリオ定義
SCENARIOS = {
    "保守": dict(g1=0.02, g2=0.02, cvr0=0.00065, cvr1=0.00065, aov=13000, gpr=0.47),
    "標準": dict(g1=0.05, g2=0.03, cvr0=0.00070, cvr1=0.00095, aov=14000, gpr=0.49),
    "強気": dict(g1=0.08, g2=0.05, cvr0=0.00070, cvr1=0.00120, aov=14500, gpr=0.50),
}

import math

def _round_half_up(x, nd=0):
    # ExcelのROUND / JSのMath.roundと同じ「半分は切り上げ」方式
    f = 10 ** nd
    return math.floor(x * f + 0.5) / f if nd else int(math.floor(x + 0.5))

def run_scenario(p):
    # シートの数式と同一の丸め: 訪問数=整数, 売上/粗利=円単位
    rows, visits = [], BASE_VISITS
    for i in range(1, 13):
        visits = _round_half_up(visits * (1 + (p["g1"] if i <= 6 else p["g2"])))
        cvr = _round_half_up(p["cvr0"] + (p["cvr1"] - p["cvr0"]) * i / 12, 7)
        orders = visits * cvr
        sales = _round_half_up(orders * p["aov"])
        gp = _round_half_up(sales * p["gpr"])
        rows.append(dict(visits=visits, cvr=cvr, orders=orders, sales=sales, gp=gp))
    return rows

RESULTS = {name: run_scenario(p) for name, p in SCENARIOS.items()}

def summary(rows):
    total_sales = sum(r["sales"] for r in rows)
    total_gp = sum(r["gp"] for r in rows)
    be = next((MONTHS_FC[i] for i, r in enumerate(rows) if r["gp"] > FEE), "予測期間内なし")
    return dict(sales=total_sales, gp=total_gp, last_gp=rows[-1]["gp"],
                breakeven=be, net=total_gp - FEE * 12)

SUMMARIES = {k: summary(v) for k, v in RESULTS.items()}

print("=== 導出パラメータ ===")
print(f"起点訪問数(直近3ヶ月平均): {BASE_VISITS:,.0f}")
print(f"平均購入単価(全期間27件): {AOV_ALL:,.0f}円")
print(f"粗利率(全期間): {GP_RATE:.1%}")
print(f"CVR 直近6ヶ月: {CVR_6M:.4%} / 直近3ヶ月: {CVR_3M:.4%} / 月次最高: {CVR_BEST:.4%}")
for name, s in SUMMARIES.items():
    print(f"[{name}] 12ヶ月累計売上 {s['sales']:,.0f} / 累計粗利 {s['gp']:,.0f} / "
          f"2027/6単月粗利 {s['last_gp']:,.0f} / 粗利>55,000到達 {s['breakeven']} / "
          f"累計(粗利-費用) {s['net']:+,.0f}")

# ---------------------------------------------------------------- スタイル定義
F_TITLE = Font(name="Yu Gothic", size=14, bold=True, color="0B0B0B")
F_SUB   = Font(name="Yu Gothic", size=9, color="52514E")
F_HEAD  = Font(name="Yu Gothic", size=9, bold=True, color="0B0B0B")
F_HEADW = Font(name="Yu Gothic", size=9, bold=True, color="FFFFFF")
F_BODY  = Font(name="Yu Gothic", size=9, color="0B0B0B")
F_MUTED = Font(name="Yu Gothic", size=8, color="898781")
F_BOLD  = Font(name="Yu Gothic", size=9, bold=True, color="0B0B0B")

FILL_ACT  = PatternFill("solid", fgColor="F0EFEC")   # 実績帯
FILL_FC   = PatternFill("solid", fgColor="E8F0FB")   # 予測帯
FILL_HEAD = PatternFill("solid", fgColor="52514E")   # 見出し
FILL_ASSUM = PatternFill("solid", fgColor="FCF6E8")  # 前提セル（入力可能）
HAIR = Side(style="thin", color="E1E0D9")
BORDER = Border(left=HAIR, right=HAIR, top=HAIR, bottom=HAIR)
CENTER = Alignment(horizontal="center", vertical="center")
LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)

def cell(ws, r, c, v=None, font=F_BODY, fill=None, fmt=None, align=None, border=BORDER):
    x = ws.cell(r, c)
    if v is not None:
        x.value = v
    x.font = font
    if fill: x.fill = fill
    if fmt: x.number_format = fmt
    x.alignment = align or CENTER
    if border: x.border = border
    return x

wb = openpyxl.Workbook()

# ================================================================ Sheet 1
ws = wb.active
ws.title = "シミュレーション（改訂版）"
ws.sheet_view.showGridLines = False
ws.column_dimensions["A"].width = 2
ws.column_dimensions["B"].width = 24
for c in range(3, 21):
    ws.column_dimensions[get_column_letter(c)].width = 10.5

cell(ws, 1, 2, "armtechstore.jp 収益シミュレーション（2026年7月 改訂版）", F_TITLE, border=None, align=LEFT)
cell(ws, 2, 2, "根拠: 2025/07〜2026/06 実績12ヶ月（Fulmo月次レポート）。予測列は数式連動 — 黄色セル（成長率・CVR・単価・粗利率・月額費用）を書き換えると全体が再計算されます。",
     F_SUB, border=None, align=LEFT)
ws.merge_cells("C2:T2")

# 帯
ws.merge_cells("C3:H3"); ws.merge_cells("I3:T3")
cell(ws, 3, 3, "実績（2026年上半期）", F_HEADW, FILL_HEAD)
for c in range(4, 9): cell(ws, 3, c, None, F_HEADW, FILL_HEAD)
cell(ws, 3, 9, "予測（標準シナリオ・数式連動）", F_HEADW, PatternFill("solid", fgColor="2A78D6"))
for c in range(10, 21): cell(ws, 3, c, None, F_HEADW, PatternFill("solid", fgColor="2A78D6"))

# 月ヘッダ (row4)  C..H 実績6ヶ月(2026/1-6), I..T 予測12ヶ月
for i, m in enumerate(MONTHS_ACT[6:]):
    cell(ws, 4, 3 + i, m, F_HEAD, FILL_ACT)
for i, m in enumerate(MONTHS_FC):
    cell(ws, 4, 9 + i, m, F_HEAD, FILL_FC)

ROWS = [
    (5,  "サイト訪問数", "#,##0"),
    (6,  "　訪問数成長率（前提）", "0.0%"),
    (7,  "CVR", "0.0000%"),
    (8,  "注文数（期待値）", "0.0"),
    (9,  "平均購入単価", "#,##0"),
    (10, "売上", "#,##0"),
    (11, "粗利率", "0.0%"),
    (12, "粗利", "#,##0"),
    (13, "月額費用", "#,##0"),
    (14, "粗利 − 月額費用", "#,##0;[Red]-#,##0"),
    (15, "累計（粗利−費用）", "#,##0;[Red]-#,##0"),
]
for r, label, fmt in ROWS:
    bold = r in (10, 12, 14)
    cell(ws, r, 2, label, F_BOLD if bold else F_BODY, align=LEFT)

# --- 実績列 C..H (2026/01-06 = index 6..11)
for i in range(6):
    c = 3 + i
    L = get_column_letter(c)
    a_fill = FILL_ACT if False else None
    cell(ws, 5, c, VISITS_ACT[6 + i], fmt="#,##0")
    cell(ws, 6, c, None, F_MUTED)
    cell(ws, 7, c, f"=IFERROR({L}8/{L}5,\"\")", fmt="0.0000%")
    cell(ws, 8, c, ORDERS_ACT[6 + i], fmt="0")
    cell(ws, 9, c, f"=IFERROR(ROUND({L}10/{L}8,0),\"\")", fmt="#,##0")
    cell(ws, 10, c, SALES_ACT[6 + i], F_BOLD, fmt="#,##0")
    cell(ws, 11, c, f"=IFERROR({L}12/{L}10,\"\")", fmt="0.0%")
    cell(ws, 12, c, GP_ACT[6 + i], F_BOLD, fmt="#,##0")
    cell(ws, 13, c, 0, fmt="#,##0")
    cell(ws, 14, c, f"={L}12-{L}13", F_BOLD, fmt="#,##0;[Red]-#,##0")
    cell(ws, 15, c, None, F_MUTED)

# --- 予測列 I..T（数式連動、前提セルは黄色）
std = SCENARIOS["標準"]
for i in range(12):
    c = 9 + i
    L = get_column_letter(c)
    P = get_column_letter(c - 1)
    growth = std["g1"] if i < 6 else std["g2"]
    cvr = _round_half_up(std["cvr0"] + (std["cvr1"] - std["cvr0"]) * (i + 1) / 12, 7)
    if i == 0:
        cell(ws, 5, c, "=ROUND(AVERAGE(F5:H5)*(1+I6),0)", fmt="#,##0")
    else:
        cell(ws, 5, c, f"=ROUND({P}5*(1+{L}6),0)", fmt="#,##0")
    cell(ws, 6, c, growth, fill=FILL_ASSUM, fmt="0.0%")
    cell(ws, 7, c, cvr, fill=FILL_ASSUM, fmt="0.0000%")
    cell(ws, 8, c, f"={L}5*{L}7", fmt="0.0")
    cell(ws, 9, c, std["aov"], fill=FILL_ASSUM, fmt="#,##0")
    cell(ws, 10, c, f"=ROUND({L}8*{L}9,0)", F_BOLD, fmt="#,##0")
    cell(ws, 11, c, std["gpr"], fill=FILL_ASSUM, fmt="0.0%")
    cell(ws, 12, c, f"=ROUND({L}10*{L}11,0)", F_BOLD, fmt="#,##0")
    cell(ws, 13, c, FEE, fill=FILL_ASSUM, fmt="#,##0")
    cell(ws, 14, c, f"={L}12-{L}13", F_BOLD, fmt="#,##0;[Red]-#,##0")
    if i == 0:
        cell(ws, 15, c, f"={L}14", fmt="#,##0;[Red]-#,##0")
    else:
        cell(ws, 15, c, f"={P}15+{L}14", fmt="#,##0;[Red]-#,##0")

# ---------------------------------------------------------------- シナリオ比較
r0 = 18
cell(ws, r0, 2, "シナリオ比較（予測12ヶ月: 2026/07〜2027/06）", F_TITLE, border=None, align=LEFT)
heads = ["シナリオ", "訪問数成長/月", "CVR（開始→12ヶ月後）", "平均単価", "粗利率",
         "累計売上", "累計粗利", "2027/06 単月粗利", "粗利>月額55,000", "累計（粗利−費用）"]
for j, h in enumerate(heads):
    cell(ws, r0 + 1, 2 + j, h, F_HEADW, FILL_HEAD, align=CENTER)
ws.row_dimensions[r0 + 1].height = 26

scen_notes = {
    "保守": "現状維持（施策効果が出ないケース）",
    "標準": "施策継続の中心推計",
    "強気": "主要KWの上位化が進むケース",
}
for k, name in enumerate(SCENARIOS):
    p, s = SCENARIOS[name], SUMMARIES[name]
    r = r0 + 2 + k
    g = f"+{p['g1']:.0%}→+{p['g2']:.0%}" if p["g1"] != p["g2"] else f"+{p['g1']:.0%}"
    cvr_s = f"{p['cvr0']:.3%}" if p["cvr0"] == p["cvr1"] else f"{p['cvr0']:.3%}→{p['cvr1']:.3%}"
    fill = FILL_FC if name == "標準" else None
    vals = [name, g, cvr_s, p["aov"], p["gpr"], round(s["sales"]), round(s["gp"]),
            round(s["last_gp"]), s["breakeven"], round(s["net"])]
    fmts = [None, None, None, "#,##0", "0%", "#,##0", "#,##0", "#,##0", None, "#,##0;[Red]-#,##0"]
    for j, (v, fmt) in enumerate(zip(vals, fmts)):
        cell(ws, r, 2 + j, v, F_BOLD if name == "標準" else F_BODY, fill, fmt)
    cell(ws, r, 12, scen_notes[name], F_MUTED, align=LEFT, border=None)

r = r0 + 6
rs_lines = ["（参考）月額固定55,000円の代替として「粗利レベニューシェア50%」とした場合の12ヶ月累計手残り（クライアント側）:"]
rs_vals = " / ".join(f"{name} {SUMMARIES[name]['gp'] * 0.5:,.0f}円" for name in SCENARIOS)
cell(ws, r, 2, rs_lines[0] + "　" + rs_vals + "　※固定費ゼロのため全シナリオでプラス", F_SUB, border=None, align=LEFT)

# ---------------------------------------------------------------- 注釈
r += 2
notes = [
    "※本数値は、2025/07〜2026/06の実績12ヶ月（訪問数・注文数・売上・粗利）から導出した前提に基づく概算シミュレーションです。各前提の導出根拠は「前提条件・根拠」シートをご参照ください。",
    "※月間注文数が3〜5件と少ないため、単月の実績は期待値に対して大きくブレます（例: 2026/04 売上115,980円 ⇔ 2026/03 23,890円）。単月ではなく6〜12ヶ月累計での評価を推奨します。",
    "※実際の売上推移や成果は、検索順位変動・季節性・外部環境等の影響を受ける可能性があります。あくまで今後の方向性や検討材料の一つとしてご参照いただくことを目的とした資料です。",
]
for i, n in enumerate(notes):
    cell(ws, r + i, 2, n, F_MUTED, border=None, align=LEFT)
    ws.merge_cells(start_row=r + i, start_column=2, end_row=r + i, end_column=20)

# ---------------------------------------------------------------- グラフ用データ + グラフ
gr = r + 4
cell(ws, gr, 2, "グラフ用データ（編集不要）", F_MUTED, border=None, align=LEFT)
labels = ["売上（実績）", "売上（予測）", "粗利（実績）", "粗利（予測）"]
for j, lab in enumerate(labels):
    cell(ws, gr + 1 + j, 2, lab, F_MUTED, align=LEFT, border=None)
for i in range(18):  # C..T
    c = 3 + i
    L = get_column_letter(c)
    if i < 6:  # 実績
        cell(ws, gr + 1, c, f"={L}10", F_MUTED, fmt="#,##0", border=None)
        cell(ws, gr + 3, c, f"={L}12", F_MUTED, fmt="#,##0", border=None)
    if i == 5:  # 接続点（2026/06）
        cell(ws, gr + 2, c, f"={L}10", F_MUTED, fmt="#,##0", border=None)
        cell(ws, gr + 4, c, f"={L}12", F_MUTED, fmt="#,##0", border=None)
    if i >= 6:  # 予測
        cell(ws, gr + 2, c, f"={L}10", F_MUTED, fmt="#,##0", border=None)
        cell(ws, gr + 4, c, f"={L}12", F_MUTED, fmt="#,##0", border=None)

chart = LineChart()
chart.title = "売上・粗利の実績と予測（標準シナリオ）"
chart.height = 9
chart.width = 30
chart.y_axis.numFmt = "#,##0"
chart.y_axis.title = None
chart.x_axis.title = None
chart.y_axis.majorGridlines.spPr = None
chart.legend.position = "b"

cats = Reference(ws, min_col=3, max_col=20, min_row=4)
colors = ["2A78D6", "2A78D6", "1BAF7A", "1BAF7A"]
dashes = [None, "dash", None, "dash"]
for j in range(4):
    ref = Reference(ws, min_col=2, max_col=20, min_row=gr + 1 + j)
    s = Series(Reference(ws, min_col=3, max_col=20, min_row=gr + 1 + j), title=labels[j])
    s.marker = Marker(symbol="none")
    s.smooth = False
    lp = LineProperties(solidFill=colors[j], w=19050)
    if dashes[j]:
        lp.prstDash = dashes[j]
    s.graphicalProperties.line = lp
    chart.series.append(s)
chart.set_categories(cats)
ws.add_chart(chart, f"B{gr + 6}")

# ================================================================ Sheet 2: 前提条件・根拠
ws2 = wb.create_sheet("前提条件・根拠")
ws2.sheet_view.showGridLines = False
ws2.column_dimensions["A"].width = 2
ws2.column_dimensions["B"].width = 22
ws2.column_dimensions["C"].width = 26
ws2.column_dimensions["D"].width = 100

cell(ws2, 1, 2, "前提条件と導出根拠", F_TITLE, border=None, align=LEFT)
cell(ws2, 2, 2, "すべての前提は 2025/07〜2026/06 の実績12ヶ月（Fulmo月次レポート・KW順位データ）から導出。", F_SUB, border=None, align=LEFT)

rows2 = [
    ("項目", "採用値（標準）", "導出根拠"),
    ("起点訪問数", f"{BASE_VISITS:,.0f}/月",
     "直近3ヶ月（2026/04〜06: 6,053 / 5,780 / 5,797）の平均。単月値でなく平均を起点にすることで月次ノイズを除去。"),
    ("訪問数成長率", "2026年下期 +5%/月 → 2027年上期 +3%/月",
     "直近4ヶ月の訪問数は横ばい（5,100〜7,400）。一方でKW順位データでは「アーム モニター」（検索Vol 74,000）が49位、「pc アーム モニター」（Vol 1,000）22位など上位化余地の大きいKWが多数。月20記事+20商品の施策継続を前提に、立ち上げ期（月+68%等）ではなく成熟期の現実的な伸びを設定。"),
    ("CVR", "0.070% → 0.095%（12ヶ月かけて線形改善）",
     f"実績: 直近6ヶ月平均 {CVR_6M:.4%} / 直近3ヶ月平均 {CVR_3M:.4%} / 月次最高 {CVR_BEST:.4%}（2026/06）。開始値0.070%は直近3〜6ヶ月平均の中間。到達値0.095%は月次最高値+10%で、CV系LP流入強化・FAQ・回遊改善・レビュー機能の継続を前提とした改善幅。旧シミュレーションの0.15%は実績最高値の1.7倍で過大と判断し修正。"),
    ("平均購入単価", "14,000円",
     f"全期間の注文27件・売上合計381,810円 → 加重平均 {AOV_ALL:,.0f}円。直近6ヶ月では14,311円。旧シミュレーションの13,000円は実績よりやや過小。"),
    ("粗利率", "49%",
     f"全期間の粗利合計÷売上合計 = {GP_RATE:.1%}（月次では45.6%〜52.8%で推移）。旧シミュレーションの「売上÷2（50%）」を実績値に置換。"),
    ("月額費用", "55,000円",
     "旧シミュレーションの設定値を踏襲（ご提案プランは月額88,000円+レベシェア5%、ご希望は粗利レベシェア50%。シナリオ比較の参考行にレベシェア50%案の試算を記載）。"),
]
r = 4
for i, (a, b, c_) in enumerate(rows2):
    head = i == 0
    cell(ws2, r + i, 2, a, F_HEADW if head else F_BOLD, FILL_HEAD if head else None, align=LEFT)
    cell(ws2, r + i, 3, b, F_HEADW if head else F_BODY, FILL_HEAD if head else None, align=LEFT)
    cell(ws2, r + i, 4, c_, F_HEADW if head else F_BODY, FILL_HEAD if head else None, align=LEFT)
    if not head:
        ws2.row_dimensions[r + i].height = 42

r += len(rows2) + 1
cell(ws2, r, 2, "旧シミュレーションからの主な修正点", F_TITLE, border=None, align=LEFT)
fixes = [
    "① 2026/07の売上が前月実績の固定値（72,840円）のまま数式と不整合だった点を修正し、予測期間全体をモデル数式（訪問数×CVR×単価）に統一。",
    "② CVRの到達値を0.15%→0.095%に修正（実績月次最高0.086%に対し1.7倍は根拠不足のため。強気シナリオでも0.12%）。",
    "③ 平均単価を13,000円→14,000円に修正（実績加重平均14,141円）。",
    "④ 粗利を「売上÷2」→「売上×49%（実績粗利率）」に修正。",
    "⑤ 単一シナリオ→3シナリオ（保守/標準/強気）とし、予測の不確実性を明示。",
    "⑥ 起点訪問数を単月値でなく直近3ヶ月平均（5,877）に変更し、月次ノイズの影響を除去。",
]
for i, f in enumerate(fixes):
    cell(ws2, r + 1 + i, 2, f, F_BODY, border=None, align=LEFT)
    ws2.merge_cells(start_row=r + 1 + i, start_column=2, end_row=r + 1 + i, end_column=4)

r += len(fixes) + 3
cell(ws2, r, 2, "精度に関する注意（重要）", F_TITLE, border=None, align=LEFT)
cautions = [
    f"・月間注文数が0〜5件と少数のため、単月実績のCVRは0.041%〜0.086%の範囲で大きく変動しています。単月の予実差は±50%程度発生し得ます。",
    "・したがって本シミュレーションは「単月の的中」ではなく「6〜12ヶ月累計の中心推計」として設計しています。四半期ごとに実績でパラメータ（CVR・単価・成長率）を更新することを推奨します。",
    "・季節性は実績1年分では分離不能のため未考慮です（2026/04の売上急増が季節要因か一時要因かは現時点で判定不可）。",
    "・検索順位の変動（アルゴリズム更新等）による下振れリスクは保守シナリオでカバーしています。",
]
for i, c_ in enumerate(cautions):
    cell(ws2, r + 1 + i, 2, c_, F_BODY, border=None, align=LEFT)
    ws2.merge_cells(start_row=r + 1 + i, start_column=2, end_row=r + 1 + i, end_column=4)

# ================================================================ Sheet 3: 実績データ
ws3 = wb.create_sheet("実績データ")
ws3.sheet_view.showGridLines = False
ws3.column_dimensions["A"].width = 2
for c in range(2, 10):
    ws3.column_dimensions[get_column_letter(c)].width = 14

cell(ws3, 1, 2, "実績データ（2025/07〜2026/06）", F_TITLE, border=None, align=LEFT)
heads3 = ["年月", "サイト訪問数", "注文数", "売上", "粗利", "CVR", "平均購入単価", "粗利率"]
for j, h in enumerate(heads3):
    cell(ws3, 3, 2 + j, h, F_HEADW, FILL_HEAD)
for i in range(12):
    r = 4 + i
    L = str(r)
    cell(ws3, r, 2, MONTHS_ACT[i])
    cell(ws3, r, 3, VISITS_ACT[i], fmt="#,##0")
    cell(ws3, r, 4, ORDERS_ACT[i], fmt="0")
    cell(ws3, r, 5, SALES_ACT[i], fmt="#,##0")
    cell(ws3, r, 6, GP_ACT[i], fmt="#,##0")
    cell(ws3, r, 7, f"=IFERROR(D{r}/C{r},\"\")", fmt="0.0000%")
    cell(ws3, r, 8, f"=IFERROR(ROUND(E{r}/D{r},0),\"\")", fmt="#,##0")
    cell(ws3, r, 9, f"=IFERROR(F{r}/E{r},\"\")", fmt="0.0%")
r = 16
cell(ws3, r, 2, "合計/平均", F_BOLD)
cell(ws3, r, 3, "=SUM(C4:C15)", F_BOLD, fmt="#,##0")
cell(ws3, r, 4, "=SUM(D4:D15)", F_BOLD, fmt="0")
cell(ws3, r, 5, "=SUM(E4:E15)", F_BOLD, fmt="#,##0")
cell(ws3, r, 6, "=SUM(F4:F15)", F_BOLD, fmt="#,##0")
cell(ws3, r, 7, "=D16/C16", F_BOLD, fmt="0.0000%")
cell(ws3, r, 8, "=ROUND(E16/D16,0)", F_BOLD, fmt="#,##0")
cell(ws3, r, 9, "=F16/E16", F_BOLD, fmt="0.0%")
cell(ws3, 18, 2, "出典: Fulmo月次レポート（元ファイル）各月シートの基本指標。", F_MUTED, border=None, align=LEFT)

OUT = "armtechstore_収益シミュレーション_改訂版.xlsx"
wb.save(OUT)
print(f"\nSaved: {OUT}")
