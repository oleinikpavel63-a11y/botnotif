<#
.SYNOPSIS
  Remove the Player Agent auto-start scheduled task.
#>
$ErrorActionPreference = "Stop"
$TaskName = "LivingWaterPlayerAgent"

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($task) {
    Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "==> Removed scheduled task '$TaskName'." -ForegroundColor Yellow
} else {
    Write-Host "Task '$TaskName' is not registered."
}
