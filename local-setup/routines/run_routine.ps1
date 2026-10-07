# ------------------------------------------------------------------
# クラウドのルーティンをローカルで1回実行する（Windows PowerShell）
#
#   使い方:  powershell -ExecutionPolicy Bypass -File .\routines\run_routine.ps1 <routine-id>
#   一覧:    weekly-ai-trend | weekly-seo-trend | archi-dog-popular-ranking | seo-pipeline-monthly
#
#   - パッケージ直下の .env を読み込み、環境変数として子プロセスに渡す
#   - claude -p（非対話モード）+ dontAsk（許可リスト外の操作は自動拒否）で実行
#   - ログは routines\logs\<routine-id>_<日時>.log
#   - モデルを変えたい場合: $env:ROUTINE_MODEL = "sonnet" を設定してから実行
#
#   注意: seo-pipeline-monthly はプロンプト内で bash 構文（curl, sleep, TZ=...）を
#         使うため、Windows では Git for Windows（Git Bash）または WSL が必要です。
# ------------------------------------------------------------------
param([Parameter(Mandatory = $true)][string]$Id)
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$envFile = Join-Path $Root ".env"
if (Test-Path $envFile) {
    Get-Content $envFile -Encoding UTF8 | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
            $k, $v = $line.Split("=", 2)
            [Environment]::SetEnvironmentVariable($k.Trim(), $v.Trim().Trim('"').Trim("'"), "Process")
        }
    }
}

New-Item -ItemType Directory -Force -Path "$Root\routines\logs", "$Root\outputs" | Out-Null
$log = Join-Path $Root ("routines\logs\{0}_{1}.log" -f $Id, (Get-Date -Format "yyyyMMdd_HHmmss"))

function Invoke-ClaudeRoutine([string]$PromptFile, [string]$Model, [string[]]$Allowed) {
    $prompt = Get-Content $PromptFile -Raw -Encoding UTF8
    $ai  = if ($env:AI_TREND_SLACK_CHANNEL_ID)  { $env:AI_TREND_SLACK_CHANNEL_ID }  else { "__AI_CHANNEL_ID__" }
    $seo = if ($env:SEO_TREND_SLACK_CHANNEL_ID) { $env:SEO_TREND_SLACK_CHANNEL_ID } else { "__SEO_CHANNEL_ID__" }
    $prompt = $prompt.Replace("__AI_CHANNEL_ID__", $ai).Replace("__SEO_CHANNEL_ID__", $seo)
    $cliArgs = @("-p", $prompt, "--permission-mode", "dontAsk", "--output-format", "text", "--allowedTools") + $Allowed
    if ($env:ROUTINE_MODEL) { $Model = $env:ROUTINE_MODEL }
    if ($Model) { $cliArgs += @("--model", $Model) }
    & claude @cliArgs
}

& {
    "=== $Id  start $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="
    switch ($Id) {
        { $_ -in "weekly-ai-trend", "weekly-seo-trend" } {
            Invoke-ClaudeRoutine "routines\prompts\$Id.md" "" @(
                "WebSearch", "WebFetch", "Read", "Write", "Edit", "mcp__claude_ai_Slack")
        }
        "archi-dog-popular-ranking" {
            if ($env:USE_CLAUDE -eq "1") {
                Invoke-ClaudeRoutine "routines\prompts\$Id.md" "claude-sonnet-5" @(
                    "Bash(python3 routines/scripts/popularity_score.py)", "Bash(python routines/scripts/popularity_score.py)")
            } else {
                $py = if (Get-Command python3 -ErrorAction SilentlyContinue) { "python3" } else { "python" }
                & $py "routines\scripts\popularity_score.py"
            }
        }
        "seo-pipeline-monthly" {
            Invoke-ClaudeRoutine "routines\prompts\$Id.md" "claude-sonnet-4-6" @(
                "Read", "Write", "Bash(curl:*)", "Bash(python3:*)", "Bash(date:*)", "Bash(TZ=Asia/Tokyo date:*)", "Bash(sleep:*)")
        }
        default { throw "不明な routine-id: $Id" }
    }
    "=== $Id  end   $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="
} *>&1 | Tee-Object -FilePath $log
