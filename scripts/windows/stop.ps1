<#
.SYNOPSIS
  Emergency-stop the audio and stop the Player Agent process.
.DESCRIPTION
  Writes the stop-file (immediate audio stop even without backend), then stops
  the scheduled task / python process if running.
#>
$ErrorActionPreference = "SilentlyContinue"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$Py = Join-Path $Root ".venv\Scripts\python.exe"

# 1. Emergency stop the audio via the CLI (creates the stop-file).
Set-Location (Join-Path $Root "apps\player-agent")
& $Py -m agent.cli stop

# 2. Stop the scheduled task if registered.
$task = Get-ScheduledTask -TaskName "LivingWaterPlayerAgent" -ErrorAction SilentlyContinue
if ($task) { Stop-ScheduledTask -TaskName "LivingWaterPlayerAgent" }

# 3. As a last resort, stop lingering agent python processes.
Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
    Where-Object { $_.CommandLine -like "*agent.main*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }

Write-Host "==> Player Agent stopped." -ForegroundColor Yellow
