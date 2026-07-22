<#
.SYNOPSIS
  Install the Living Water Player Agent on Windows 10/11.
.DESCRIPTION
  Creates a Python virtualenv and installs the player-agent + shared-contracts.
  Requires Python 3.11+ and mpv (see README section 6).
#>
param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $Root

Write-Host "==> Living Water Player Agent — install" -ForegroundColor Green

# Check Python
try { & $Python --version } catch { throw "Python not found. Install Python 3.11+ from python.org and re-run." }

# Check mpv
$mpv = Get-Command mpv -ErrorAction SilentlyContinue
if (-not $mpv) {
    Write-Warning "mpv not found in PATH. Download from https://mpv.io/installation/ and set MPV_EXECUTABLE_PATH in .env"
} else {
    Write-Host "mpv: $($mpv.Source)"
}

$Venv = ".venv"
if (-not (Test-Path $Venv)) {
    Write-Host "==> Creating virtualenv $Venv"
    & $Python -m venv $Venv
}

$Pip = Join-Path $Venv "Scripts\pip.exe"
& $Pip install -U pip
& $Pip install -e ".\packages\shared-contracts\python"
& $Pip install -e ".\apps\player-agent[dev]"

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "==> Created .env from .env.example — EDIT IT before starting." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==> Done. Next steps:" -ForegroundColor Green
Write-Host "   1. Edit .env: AGENT_SERVER_URL, AGENT_DEVICE_ID, AGENT_DEVICE_TOKEN, MPV_AUDIO_DEVICE"
Write-Host "   2. List audio devices:  .\scripts\windows\status.ps1 -Audio"
Write-Host "   3. Test audio:          .venv\Scripts\python -m agent.cli test-audio  (run in apps\player-agent)"
Write-Host "   4. Start:               .\scripts\windows\start.ps1"
Write-Host "   5. Auto-start on logon: .\scripts\windows\register-startup-task.ps1"
