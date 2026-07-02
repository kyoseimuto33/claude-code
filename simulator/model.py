# -*- coding: utf-8 -*-
"""armtechstore.jp 収益シミュレーションモデル

実績データ（2025/03〜2026/06）に基づき、以下を推定・生成する:
  1. 実績ベースのパラメータ推定（CVR・平均購入単価・粗利率、Wilson信頼区間つき）
  2. 3シナリオ（保守・標準・強気）の12ヶ月予測（2026/07〜2027/06）
  3. Poissonモンテカルロによる P10/P50/P90 レンジ
  4. 料金プラン3案（現行月額 / 提案プラン / 粗利レベシェア50%）の手残り比較

出力: output/simulation_results.json
"""
import csv
import json
import math
import os

import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RNG = np.random.default_rng(20260702)

# ---------------------------------------------------------------- 実績データ
def load_actuals():
    path = os.path.join(BASE, "data", "monthly_actuals.csv")
    rows = []
    with open(path, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            rows.append({
                "month": r["month"],
                "visits": int(r["visits"]),
                "orders": int(r["orders"]),
                "revenue": int(r["revenue_jpy"]),
                "gp": int(r["gross_profit_jpy"]),
            })
    return rows


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


# ------------------------------------------------------------ パラメータ推定
def estimate_params(actuals):
    active = [a for a in actuals if a["month"] >= "2025-09"]  # 売上発生期間
    V = sum(a["visits"] for a in active)
    O = sum(a["orders"] for a in active)
    R = sum(a["revenue"] for a in active)
    G = sum(a["gp"] for a in active)
    cvr_lo, cvr_hi = wilson(O, V)

    # 月次AOV（注文があった月のみ）— 単価ばらつきのモンテカルロ用
    aov_samples = [a["revenue"] / a["orders"] for a in active if a["orders"] > 0]
    log_aov = np.log(aov_samples)

    # 直近6ヶ月のトラフィック月次成長率（幾何平均）
    recent = [a["visits"] for a in actuals if a["month"] >= "2026-01"]
    traffic_cagr = (recent[-1] / recent[0]) ** (1 / (len(recent) - 1)) - 1

    return {
        "pooled_visits": V,
        "pooled_orders": O,
        "pooled_revenue": R,
        "pooled_gp": G,
        "cvr": O / V,
        "cvr_ci95": [cvr_lo, cvr_hi],
        "aov": R / O,
        "gross_margin": G / R,
        "aov_log_mu": float(log_aov.mean()),
        "aov_log_sigma": float(log_aov.std(ddof=1)),
        "traffic_mom_recent": traffic_cagr,
        "last_visits": actuals[-1]["visits"],
    }


# ---------------------------------------------------------------- シナリオ
# 根拠:
#  - トラフィック成長率: 直近6ヶ月の実測月次成長 ≈ +2.0%。KW順位改善による
#    ポテンシャル +48%（追跡KWのCTRカーブ推定 1,799→2,657クリック/月）と
#    月20記事の新規コンテンツ投入を織り込み、保守+1%/標準+2.5%/強気+5%。
#  - CVR: 実測プール値 0.0640%（95%CI 0.044%〜0.093%）。保守=CI下限近傍、
#    標準=実測値、強気=CI上限近傍（CVR改善施策の効果を織り込む）。
#  - 平均購入単価: 実測プール値 ¥14,141。月次ばらつき（¥7,963〜¥23,196）を考慮。
#  - 粗利率: 実測 49.0%。
SCENARIOS = {
    "conservative": {
        "label": "保守",
        "traffic_growth": 0.01,
        "cvr": 0.00045,
        "aov": 12000,
        "note": "成長鈍化・CVR横ばい（CI下限）",
    },
    "base": {
        "label": "標準",
        "traffic_growth": 0.025,
        "cvr": 0.00065,
        "aov": 14000,
        "note": "直近実績の成長・CVRを維持",
    },
    "optimistic": {
        "label": "強気",
        "traffic_growth": 0.05,
        "cvr": 0.00090,
        "aov": 15000,
        "note": "KW順位改善+CVR施策が奏功（CI上限）",
    },
}

GROSS_MARGIN = 0.49
FORECAST_MONTHS = [
    "2026-07", "2026-08", "2026-09", "2026-10", "2026-11", "2026-12",
    "2027-01", "2027-02", "2027-03", "2027-04", "2027-05", "2027-06",
]

# 料金プラン
FEE_PLANS = {
    "current": {"label": "現行: 月額55,000円", "fixed": 55000, "rev_share": 0.0, "gp_share": 0.0},
    "proposed": {"label": "提案: 月額88,000円+売上5%", "fixed": 88000, "rev_share": 0.05, "gp_share": 0.0},
    "gp_share_50": {"label": "希望: 粗利レベシェア50%", "fixed": 0, "rev_share": 0.0, "gp_share": 0.50},
}


def forecast_scenario(params, sc):
    visits = params["last_visits"]
    months = []
    for m in FORECAST_MONTHS:
        visits = visits * (1 + sc["traffic_growth"])
        orders = visits * sc["cvr"]
        revenue = orders * sc["aov"]
        gp = revenue * GROSS_MARGIN
        months.append({
            "month": m,
            "visits": round(visits),
            "orders": round(orders, 2),
            "revenue": round(revenue),
            "gp": round(gp),
        })
    return months


def monte_carlo(params, sc, n_sim=20000):
    """注文数=Poisson(訪問数×CVR)、注文単価=対数正規（実測月次AOVにフィット）。"""
    visits = params["last_visits"]
    mu, sigma = params["aov_log_mu"], params["aov_log_sigma"]
    out = []
    for m in FORECAST_MONTHS:
        visits = visits * (1 + sc["traffic_growth"])
        lam = visits * sc["cvr"]
        orders = RNG.poisson(lam, n_sim)
        # 各シミュレーションの売上 = Σ(対数正規単価)。近似: 注文数×単価サンプル平均
        rev = np.zeros(n_sim)
        nz = orders > 0
        # 注文ごとの単価を厳密にサンプリング（合計をガンマ近似せず直接計算）
        max_o = orders.max() if orders.size else 0
        if max_o > 0:
            price_draws = RNG.lognormal(mu, sigma, (n_sim, max_o))
            mask = np.arange(max_o) < orders[:, None]
            rev = (price_draws * mask).sum(axis=1)
        # シナリオAOVと実測AOV水準の比率で補正（シナリオ単価想定を中心にする）
        rev = rev * (sc["aov"] / math.exp(mu + sigma**2 / 2))
        gp = rev * GROSS_MARGIN
        out.append({
            "month": m,
            "revenue_p10": float(np.percentile(rev, 10)),
            "revenue_p50": float(np.percentile(rev, 50)),
            "revenue_p90": float(np.percentile(rev, 90)),
            "gp_p10": float(np.percentile(gp, 10)),
            "gp_p50": float(np.percentile(gp, 50)),
            "gp_p90": float(np.percentile(gp, 90)),
            "prob_gp_over_55k": float((gp >= 55000).mean()),
        })
    return out


def apply_fee_plans(months):
    plans = {}
    for key, p in FEE_PLANS.items():
        rows = []
        for m in months:
            fee = p["fixed"] + m["revenue"] * p["rev_share"] + m["gp"] * p["gp_share"]
            rows.append({
                "month": m["month"],
                "fee": round(fee),
                "client_net": round(m["gp"] - fee),
            })
        plans[key] = {
            "label": p["label"],
            "months": rows,
            "total_fee": sum(r["fee"] for r in rows),
            "total_client_net": sum(r["client_net"] for r in rows),
        }
    return plans


def main():
    actuals = load_actuals()
    params = estimate_params(actuals)

    scenarios = {}
    for key, sc in SCENARIOS.items():
        months = forecast_scenario(params, sc)
        mc = monte_carlo(params, sc)
        scenarios[key] = {
            "label": sc["label"],
            "assumptions": {
                "traffic_growth_mom": sc["traffic_growth"],
                "cvr": sc["cvr"],
                "aov": sc["aov"],
                "gross_margin": GROSS_MARGIN,
                "note": sc["note"],
            },
            "months": months,
            "monte_carlo": mc,
            "fee_plans": apply_fee_plans(months),
            "total_revenue": sum(m["revenue"] for m in months),
            "total_gp": sum(m["gp"] for m in months),
        }

    result = {
        "site": "https://www.armtechstore.jp",
        "generated": "2026-07-02",
        "forecast_period": [FORECAST_MONTHS[0], FORECAST_MONTHS[-1]],
        "params": params,
        "actuals": actuals,
        "scenarios": scenarios,
    }
    out = os.path.join(BASE, "output", "simulation_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print(f"written: {out}")

    # サマリー表示
    print(f"\n実測パラメータ（2025/09〜2026/06プール）:")
    print(f"  CVR      : {params['cvr']*100:.4f}%  (95%CI {params['cvr_ci95'][0]*100:.4f}%〜{params['cvr_ci95'][1]*100:.4f}%)")
    print(f"  平均単価 : ¥{params['aov']:,.0f}")
    print(f"  粗利率   : {params['gross_margin']*100:.1f}%")
    print(f"  直近成長 : {params['traffic_mom_recent']*100:+.1f}%/月")
    for key, s in scenarios.items():
        last = s["months"][-1]
        mc_last = s["monte_carlo"][-1]
        print(f"\n[{s['label']}] 12ヶ月累計売上 ¥{s['total_revenue']:,} / 粗利 ¥{s['total_gp']:,}")
        print(f"  2027/06: 売上 ¥{last['revenue']:,} (P10 ¥{mc_last['revenue_p10']:,.0f}〜P90 ¥{mc_last['revenue_p90']:,.0f})")
        print(f"  粗利が現行月額55,000円を上回る確率(2027/06): {mc_last['prob_gp_over_55k']*100:.0f}%")
        for pk, plan in s["fee_plans"].items():
            print(f"  {plan['label']}: 年間費用 ¥{plan['total_fee']:,} / クライアント手残り ¥{plan['total_client_net']:,}")


if __name__ == "__main__":
    main()
