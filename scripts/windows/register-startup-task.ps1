<#
.SYNOPSIS
  Register the Player Agent to auto-start at user logon via Task Scheduler.
.DESCRIPTION
  Creates a scheduled task "LivingWaterPlayerAgent" that runs the agent at logon
  and restarts it on failure. Runs in the user session (needed for audio access).
#>
$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$Py = Join-Path $Root ".venv\Scripts\python.exe"
$WorkDir = Join-Path $Root "apps\player-agent"
if (-not (Test-Path $Py)) { throw "Virtualenv missing. Run install.ps1 first." }

$TaskName = "LivingWaterPlayerAgent"

$action = New-ScheduledTaskAction -Execute $Py -Argument "-m agent.main" -WorkingDirectory $WorkDir
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) `
    -StartWhenAvailable `
    -ExecutionTimeLimit ([TimeSpan]::Zero)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Settings $settings -Principal $principal -Force | Out-Null

Write-Host "==> Registered scheduled task '$TaskName' (auto-start at logon)." -ForegroundColor Green
Write-Host "    Tip: disable Windows sleep so audio keeps playing:  powercfg /change standby-timeout-ac 0"
Write-Host "    Start now:  Start-ScheduledTask -TaskName $TaskName"
