#!/usr/bin/env bash
# ------------------------------------------------------------------
# ローカル環境セットアップ（macOS / Linux / WSL）
#   使い方: パッケージを展開したフォルダで  bash scripts/setup.sh
#
#   1. 必要なツール（git / python3 / claude）の有無を確認
#   2. GitHub からリポジトリを clone（失敗時は同梱の project/ を使用）
#   3. プロジェクトに CLAUDE.md / .claude/settings.json / requirements.txt を配置
#   4. Python 依存（openpyxl）をインストール
#   5. .env をテンプレートから作成（既にあれば触らない）
#   6. 動作確認（クラウドと同じ計算結果になるか）
# ------------------------------------------------------------------
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
REPO_URL="https://github.com/kyoseimuto33/claude-code.git"
WORK_BRANCH="claude/great-mccarthy-f4v1v3"
REPO_DIR="$ROOT/repo"

ok()   { printf '  \033[32m✓\033[0m %s\n' "$1"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$1"; }

echo "[1/6] ツール確認"
command -v git     >/dev/null && ok "git $(git --version | awk '{print $3}')" || warn "git がありません（https://git-scm.com/）"
command -v python3 >/dev/null && ok "$(python3 --version)"                  || { warn "python3 がありません（3.9 以上を入れてください）"; exit 1; }
if command -v claude >/dev/null; then ok "claude $(claude --version 2>/dev/null | head -1)"
else warn "Claude Code 未インストール → curl -fsSL https://claude.ai/install.sh | bash"; fi

echo "[2/6] リポジトリ取得"
if [ -d "$REPO_DIR/.git" ]; then
  ok "既存の clone を使用: $REPO_DIR"
elif command -v git >/dev/null && git clone -q "$REPO_URL" "$REPO_DIR" 2>/dev/null; then
  git -C "$REPO_DIR" checkout -q "$WORK_BRANCH" 2>/dev/null || true
  ok "clone 完了: $REPO_DIR（ブランチ: $(git -C "$REPO_DIR" branch --show-current)）"
else
  warn "clone できませんでした（未ログイン/権限なし）。同梱の project/ をコピーして使います"
  cp -R "$ROOT/project" "$REPO_DIR"
fi

echo "[3/6] プロジェクト設定を配置"
mkdir -p "$REPO_DIR/.claude"
[ -f "$REPO_DIR/CLAUDE.md" ]             || { cp config/claude/CLAUDE.md "$REPO_DIR/";          ok "CLAUDE.md"; }
[ -f "$REPO_DIR/.claude/settings.json" ] || { cp config/claude/settings.json "$REPO_DIR/.claude/"; ok ".claude/settings.json"; }
[ -f "$REPO_DIR/requirements.txt" ]      || { cp config/requirements.txt "$REPO_DIR/";          ok "requirements.txt"; }
grep -q "claude-local-setup" "$REPO_DIR/.gitignore" 2>/dev/null || { cat config/gitignore.append >> "$REPO_DIR/.gitignore"; ok ".gitignore 追記"; }

echo "[4/6] Python 依存をインストール"
python3 -m pip install -q -r config/requirements.txt 2>/dev/null \
  || python3 -m pip install -q --user -r config/requirements.txt 2>/dev/null \
  || python3 -m pip install -q --user --break-system-packages -r config/requirements.txt \
  && ok "openpyxl $(python3 -c 'import openpyxl;print(openpyxl.__version__)')"

echo "[5/6] .env"
if [ -f .env ]; then ok ".env は既に存在（変更しません）"
else cp config/.env.example .env; chmod 600 .env; warn ".env を作成しました → __XXX__ を実際の値に書き換えてください（docs/04 参照）"; fi
chmod +x routines/run_routine.sh scripts/*.sh 2>/dev/null

echo "[6/6] 動作確認"
python3 scripts/verify_project.py "$REPO_DIR"

echo
echo "完了。次の手順:"
echo "  cd \"$REPO_DIR\" && claude      # 初回は /login で claude.ai アカウントにログイン → /mcp でコネクタ確認"
