#!/usr/bin/env bash
# ------------------------------------------------------------------
# クラウドのルーティンをローカルで1回実行する（macOS / Linux / WSL）
#
#   使い方:  ./routines/run_routine.sh <routine-id>
#   一覧:    weekly-ai-trend | weekly-seo-trend | archi-dog-popular-ranking | seo-pipeline-monthly
#
#   - パッケージ直下の .env を読み込み、環境変数として子プロセスに渡す
#   - claude -p（非対話モード）+ dontAsk（許可リスト外の操作は自動拒否）で実行
#   - ログは routines/logs/<routine-id>_<日時>.log
#   - モデルを変えたい場合: ROUTINE_MODEL=sonnet ./routines/run_routine.sh ...
# ------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ID="${1:-}"
[ -z "$ID" ] && { sed -n '3,12p' "$0"; exit 1; }

# cron は PATH が最小限なので、Claude Code の既定インストール先を補う
export PATH="$HOME/.local/bin:$HOME/.claude/local:/usr/local/bin:/opt/homebrew/bin:$PATH"

if [ -f "$ROOT/.env" ]; then
  set -a; . "$ROOT/.env"; set +a
fi

mkdir -p "$ROOT/routines/logs" "$ROOT/outputs"
LOG="$ROOT/routines/logs/${ID}_$(date +%Y%m%d_%H%M%S).log"
cd "$ROOT"

run_claude() {  # $1=prompt file, $2=model(空なら既定), 残り=許可ツール
  local prompt_file="$1" model="$2"; shift 2
  local prompt
  prompt="$(cat "$prompt_file")"
  # Slack 配布先のプレースホルダを .env の値で置換（未設定なら本人DMにフォールバックする元の挙動のまま）
  prompt="${prompt//__AI_CHANNEL_ID__/${AI_TREND_SLACK_CHANNEL_ID:-__AI_CHANNEL_ID__}}"
  prompt="${prompt//__SEO_CHANNEL_ID__/${SEO_TREND_SLACK_CHANNEL_ID:-__SEO_CHANNEL_ID__}}"
  local args=(-p "$prompt" --permission-mode dontAsk --output-format text --allowedTools "$@")
  model="${ROUTINE_MODEL:-$model}"
  [ -n "$model" ] && args+=(--model "$model")
  claude "${args[@]}"
}

{
  echo "=== $ID  start $(date '+%Y-%m-%d %H:%M:%S %Z') ==="
  case "$ID" in
    weekly-ai-trend|weekly-seo-trend)
      # Slack は claude.ai コネクタ（claude.ai アカウントでログインしていれば自動で利用可能）
      run_claude "routines/prompts/$ID.md" "" \
        "WebSearch" "WebFetch" "Read" "Write" "Edit" "Bash(mkdir:*)" "Bash(date:*)" \
        "mcp__claude_ai_Slack"
      ;;
    archi-dog-popular-ranking)
      # AI判断が不要な決定的処理なので Claude を介さず直接実行（推奨）
      # Claude 経由で実行したい場合は USE_CLAUDE=1 を付ける
      if [ "${USE_CLAUDE:-0}" = "1" ]; then
        run_claude "routines/prompts/$ID.md" "claude-sonnet-5" "Bash(python3 routines/scripts/popularity_score.py)"
      else
        python3 routines/scripts/popularity_score.py
      fi
      ;;
    seo-pipeline-monthly)
      run_claude "routines/prompts/$ID.md" "claude-sonnet-4-6" \
        "Read" "Write" "Bash(curl:*)" "Bash(python3:*)" "Bash(date:*)" "Bash(TZ=Asia/Tokyo date:*)" "Bash(sleep:*)"
      ;;
    *)
      echo "不明な routine-id: $ID" >&2; exit 2 ;;
  esac
  echo "=== $ID  end   $(date '+%Y-%m-%d %H:%M:%S %Z') ==="
} 2>&1 | tee "$LOG"
