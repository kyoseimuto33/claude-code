#!/usr/bin/env bash
# local-setup/ と リポジトリ直下の成果物から claude-local-setup.zip を作る
#   使い方: bash local-setup/build_zip.sh   （出力: リポジトリ直下の claude-local-setup.zip）
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
STAGE="$(mktemp -d)"
PKG="$STAGE/claude-local-setup"
trap 'rm -rf "$STAGE"' EXIT

mkdir -p "$PKG/project"
cp -R "$HERE/README.md" "$HERE/docs" "$HERE/config" "$HERE/routines" "$HERE/scripts" "$PKG/"
cp "$REPO/README.md" "$REPO/build_simulation.py" "$REPO/index.html" "$REPO"/armtechstore_*.xlsx "$PKG/project/"
rm -rf "$PKG/routines/logs"; find "$PKG" -name __pycache__ -prune -exec rm -rf {} +
chmod +x "$PKG/scripts/setup.sh" "$PKG/routines/run_routine.sh"

# シークレットらしき文字列が紛れ込んでいないか最終確認
if grep -rEn 'shpss_[0-9a-f]{8,}|Basic [A-Za-z0-9+/=]{12,}' "$PKG" ; then
  echo "シークレットらしき文字列が含まれています。中止します" >&2; exit 1
fi

rm -f "$REPO/claude-local-setup.zip"
# Python の zipfile は日本語ファイル名に UTF-8 フラグを立てる（Windows エクスプローラーで文字化けしない）
python3 -I - "$STAGE" "$REPO/claude-local-setup.zip" <<'PY'
import os, sys, zipfile
stage, out = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for d, dirs, files in os.walk(os.path.join(stage, "claude-local-setup")):
        dirs.sort()
        for f in sorted(files):
            p = os.path.join(d, f)
            z.write(p, os.path.relpath(p, stage))   # 実行権限（setup.sh 等）も保持される
PY
echo "作成: $REPO/claude-local-setup.zip"
unzip -l "$REPO/claude-local-setup.zip"
