$ErrorActionPreference='Stop';. (Join-Path $PSScriptRoot 'workspace.ps1');Assert-LiveCode
$name='finalization-tests-'+[guid]::NewGuid().ToString('N');$root=Join-Path $PSScriptRoot $name
New-Item -ItemType Directory -Path (Join-Path $root 'temp')|Out-Null;Set-LiveTemp $root
try{
 Add-Type -Path @((Join-Path $PSScriptRoot 'LoopTiming.cs'),(Join-Path $PSScriptRoot 'event_queue.cs'),(Join-Path $PSScriptRoot 'FinalizationGate.cs'),(Join-Path $PSScriptRoot 'finalization_tests.cs'))
 $result=[FinalizationTests]::Run($root)
 $result|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $root 'result.json')
 Write-Output ($result|ConvertTo-Json -Depth 12 -Compress)
}catch{
 @{status='FAIL';error=$_.ToString();stack=$_.ScriptStackTrace}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'failure.json');throw
}
