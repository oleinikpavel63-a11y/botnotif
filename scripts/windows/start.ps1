<#
.SYNOPSIS
  Start the Living Water Player Agent (foreground).
#>
$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$Py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { throw "Virtualenv missing. Run scripts\windows\install.ps1 first." }

Set-Location (Join-Path $Root "apps\player-agent")
Write-Host "==> Starting Player Agent (Ctrl+C to stop)..." -ForegroundColor Green
& $Py -m agent.main
