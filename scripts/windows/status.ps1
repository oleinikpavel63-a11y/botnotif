<#
.SYNOPSIS
  Show Player Agent status. Use -Audio to list audio output devices.
#>
param([switch]$Audio)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$Py = Join-Path $Root ".venv\Scripts\python.exe"
Set-Location (Join-Path $Root "apps\player-agent")

if ($Audio) {
    & $Py -m agent.cli list-audio-devices
} else {
    & $Py -m agent.cli status
    Write-Host ""
    $task = Get-ScheduledTask -TaskName "LivingWaterPlayerAgent" -ErrorAction SilentlyContinue
    if ($task) {
        $info = Get-ScheduledTaskInfo -TaskName "LivingWaterPlayerAgent"
        Write-Host "Scheduled task: $($task.State)  (last run: $($info.LastRunTime))"
    } else {
        Write-Host "Scheduled task: not registered"
    }
}
