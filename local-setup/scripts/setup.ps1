# ------------------------------------------------------------------
# ローカル環境セットアップ（Windows PowerShell）
#   使い方: パッケージを展開したフォルダで
#           powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
#   処理内容は scripts/setup.sh と同じ（ツール確認→clone→設定配置→pip→.env→動作確認）
# ------------------------------------------------------------------
$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$RepoUrl = "https://github.com/kyoseimuto33/claude-code.git"
$WorkBranch = "claude/great-mccarthy-f4v1v3"
$RepoDir = Join-Path $Root "repo"

function Ok($m)   { Write-Host "  [OK] $m" -ForegroundColor Green }
function Warn($m) { Write-Host "  [!]  $m" -ForegroundColor Yellow }

Write-Host "[1/6] ツール確認"
if (Get-Command git -ErrorAction SilentlyContinue) { Ok (git --version) } else { Warn "git がありません（https://git-scm.com/ ※Git Bash も同梱）" }
$py = if (Get-Command python3 -ErrorAction SilentlyContinue) { "python3" } elseif (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { $null }
if ($py) { Ok (& $py --version) } else { Warn "Python がありません（https://www.python.org/ 3.9 以上）"; exit 1 }
if (Get-Command claude -ErrorAction SilentlyContinue) { Ok ("claude " + (claude --version)) }
else { Warn "Claude Code 未インストール → irm https://claude.ai/install.ps1 | iex" }

Write-Host "[2/6] リポジトリ取得"
if (Test-Path "$RepoDir\.git") { Ok "既存の clone を使用: $RepoDir" }
else {
    git clone -q $RepoUrl $RepoDir 2>$null
    if ($LASTEXITCODE -eq 0) { git -C $RepoDir checkout -q $WorkBranch 2>$null; Ok "clone 完了: $RepoDir" }
    else { Warn "clone できませんでした。同梱の project\ をコピーして使います"; Copy-Item -Recurse "$Root\project" $RepoDir }
}

Write-Host "[3/6] プロジェクト設定を配置"
New-Item -ItemType Directory -Force "$RepoDir\.claude" | Out-Null
if (-not (Test-Path "$RepoDir\CLAUDE.md"))             { Copy-Item "config\claude\CLAUDE.md" $RepoDir; Ok "CLAUDE.md" }
if (-not (Test-Path "$RepoDir\.claude\settings.json")) { Copy-Item "config\claude\settings.json" "$RepoDir\.claude\"; Ok ".claude\settings.json" }
if (-not (Test-Path "$RepoDir\requirements.txt"))      { Copy-Item "config\requirements.txt" $RepoDir; Ok "requirements.txt" }
$gi = "$RepoDir\.gitignore"
if (-not ((Test-Path $gi) -and (Select-String -Path $gi -Pattern "claude-local-setup" -Quiet))) {
    Get-Content "config\gitignore.append" -Encoding UTF8 | Add-Content $gi -Encoding UTF8; Ok ".gitignore 追記"
}

Write-Host "[4/6] Python 依存をインストール"
& $py -m pip install -q -r config\requirements.txt
if ($LASTEXITCODE -eq 0) { Ok "openpyxl インストール済み" } else { Warn "pip install に失敗しました" }

Write-Host "[5/6] .env"
if (Test-Path ".env") { Ok ".env は既に存在（変更しません）" }
else { Copy-Item "config\.env.example" ".env"; Warn ".env を作成しました → __XXX__ を実際の値に書き換えてください（docs\04 参照）" }

Write-Host "[6/6] 動作確認"
$env:PYTHONIOENCODING = "utf-8"
& $py scripts\verify_project.py $RepoDir

Write-Host ""
Write-Host "完了。次の手順:"
Write-Host "  cd `"$RepoDir`"; claude     # 初回は /login で claude.ai アカウントにログイン → /mcp でコネクタ確認"
