$ErrorActionPreference='Stop'
function Measure([string]$Name,[scriptblock]$Code){ & $Code }
Get-Command Measure -All|Select-Object CommandType,Name,Definition|ConvertTo-Json
try{Measure 'diagnostic-stage' {'OK'}}catch{$_.Exception.ToString();exit 1}
