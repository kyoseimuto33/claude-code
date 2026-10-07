# ------------------------------------------------------------------
# Windows タスクスケジューラへルーティンを登録する
#   実行: powershell -ExecutionPolicy Bypass -File .\routines\scheduler\register_windows_tasks.ps1
#   削除: Unregister-ScheduledTask -TaskName "Claude-*" -Confirm:$false
#
#   - ログオン中のみ実行（PC スリープ中は実行されない。復帰後の実行は StartWhenAvailable で補う）
#   - SEO自動パイプラインはクラウドで無効化中のため既定では登録しない（-IncludeSeoPipeline で登録）
# ------------------------------------------------------------------
param([switch]$IncludeSeoPipeline)
$ErrorActionPreference = "Stop"

$Root   = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Runner = Join-Path $Root "routines\run_routine.ps1"

function Register-Routine([string]$Id, $Trigger) {
    $action = New-ScheduledTaskAction -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Runner`" $Id" -WorkingDirectory $Root
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 6)
    Register-ScheduledTask -TaskName "Claude-$Id" -Action $action -Trigger $Trigger -Settings $settings -Force | Out-Null
    Write-Host "登録しました: Claude-$Id"
}

Register-Routine "weekly-ai-trend"           (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "10:00")
Register-Routine "weekly-seo-trend"          (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "10:10")
Register-Routine "archi-dog-popular-ranking" (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "02:07")
if ($IncludeSeoPipeline) {
    Register-Routine "seo-pipeline-monthly"  (New-ScheduledTaskTrigger -Daily -At "00:00")
}
