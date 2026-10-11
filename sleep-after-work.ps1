Add-Type -AssemblyName System.Windows.Forms
Start-Sleep -Seconds 12
$result = [System.Windows.Forms.Application]::SetSuspendState([System.Windows.Forms.PowerState]::Suspend, $false, $false)
if (-not $result) { 'Sleep request failed.' | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'sleep-result.txt') }
