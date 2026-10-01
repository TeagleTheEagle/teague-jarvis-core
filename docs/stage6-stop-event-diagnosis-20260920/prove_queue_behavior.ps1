# Diagnostic reproduction inside this disposable PowerShell session only.
$ErrorActionPreference='Stop'
$out=Join-Path $PSScriptRoot 'queue-mechanism-proof.json'
if(Test-Path -LiteralPath $out){throw 'Do not overwrite evidence'}
$tag='J6Synthetic-'+[guid]::NewGuid().ToString('N')
$a=New-Event -SourceIdentifier ($tag+'-start')
$b=New-Event -SourceIdentifier ($tag+'-stop')
$property=[System.Management.Automation.PSEventArgs].GetProperty('EventIdentifier')
# Intentionally inject exactly the collision observed in real CIM-delivered events.
$property.SetValue($b,$a.EventIdentifier)
$before=@(Get-Event|Where-Object SourceIdentifier -like ($tag+'*')|Select-Object SourceIdentifier,EventIdentifier)
Remove-Event -EventIdentifier $a.EventIdentifier
$after=@(Get-Event|Where-Object SourceIdentifier -like ($tag+'*')|Select-Object SourceIdentifier,EventIdentifier)
$method=[System.Management.Automation.PSEventManager].GetMethod('GetNextEventId',[Reflection.BindingFlags]'Instance,NonPublic')
$il=$method.GetMethodBody().GetILAsByteArray()
$fieldToken=[BitConverter]::ToInt32($il,3)
$field=$method.Module.ResolveField($fieldToken)
$result=@{purpose='Diagnostic injected queue collision, not correction';before=$before;after=$after;both_removed=($before.Count -eq 2 -and $after.Count -eq 0);powershell=$PSVersionTable.PSVersion.ToString();assembly=[System.Management.Automation.PSEventManager].Assembly.Location;assemblyHash=(Get-FileHash -LiteralPath ([System.Management.Automation.PSEventManager].Assembly.Location)).Hash;getNextEventIdIL=[Convert]::ToHexString($il);counterField=$field.Name;interpretation='Installed GetNextEventId reads field, adds 1, writes field, returns old value; no interlocked operation in this method';warning='Synthetic collision alone does not prove historical cause; real campaign independently recorded duplicated IDs.'}
if(-not $result.both_removed){throw 'Removal behavior differs from hypothesized mechanism'}
$result|ConvertTo-Json -Depth 6|Set-Content -LiteralPath $out
$result|ConvertTo-Json -Depth 6
