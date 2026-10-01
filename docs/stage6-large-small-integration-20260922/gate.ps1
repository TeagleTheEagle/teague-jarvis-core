param([ValidateSet('normal','hash-start-failure')][string]$Case='normal',[Parameter(Mandatory=$true)][ValidateSet('allow-detail-prompt','allow-app-prompt')][string]$Gate)
$ErrorActionPreference='Stop'
$run=Get-Content -LiteralPath (Join-Path $PSScriptRoot ($Case+'-run.json')) -Raw|ConvertFrom-Json
$p=Join-Path $run.root $Gate
$f=[IO.File]::Open($p,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
try{$b=[Text.Encoding]::UTF8.GetBytes('Known read-only Stage 6 observer prompt released');$f.Write($b,0,$b.Length);$f.Flush($true)}finally{$f.Dispose()}
