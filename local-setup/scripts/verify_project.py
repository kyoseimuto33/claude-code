# -*- coding: utf-8 -*-
"""
ローカル環境の動作確認: build_simulation.py を一時フォルダで実行し、
クラウドで検証済みの結果（README の「結果」表）と一致するか確認する。

  使い方: python3 scripts/verify_project.py [プロジェクトのフォルダ]   （省略時は ./project）
"""
import os, shutil, subprocess, sys, tempfile
from pathlib import Path

EXPECTED = {   # シナリオ: (12ヶ月累計売上, 累計粗利, 粗利>月額費用の到達月)
    "保守": ("679,294", "319,269", "予測期間内なし"),
    "標準": ("1,116,879", "547,270", "2027/04"),
    "強気": ("1,641,419", "820,711", "2026/11"),
}

proj = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "project")
src = proj / "build_simulation.py"
if not src.is_file():
    sys.exit(f"NG: {src} が見つかりません")

with tempfile.TemporaryDirectory() as tmp:
    shutil.copy(src, tmp)
    r = subprocess.run([sys.executable, "build_simulation.py"], cwd=tmp,
                       capture_output=True, text=True, encoding="utf-8",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    if r.returncode != 0:
        sys.exit("NG: build_simulation.py の実行に失敗しました\n" + r.stderr[-2000:]
                 + "\n→ `python3 -m pip install -r requirements.txt` を実行済みか確認してください")
    out = r.stdout
    ok = True
    for name, (sales, gp, be) in EXPECTED.items():
        line = next((l for l in out.splitlines() if l.startswith(f"[{name}]")), "")
        good = all(x in line for x in (sales, gp, be))
        ok &= good
        print(("OK " if good else "NG ") + (line or f"[{name}] 出力なし"))
    xlsx = Path(tmp) / "armtechstore_収益シミュレーション_改訂版.xlsx"
    print(("OK " if xlsx.is_file() else "NG ") + "Excel ファイル生成")
    ok &= xlsx.is_file()

print("\n検証結果: " + ("すべて一致（ローカル環境はクラウドと同じ結果を再現）" if ok else "不一致あり"))
sys.exit(0 if ok else 1)
