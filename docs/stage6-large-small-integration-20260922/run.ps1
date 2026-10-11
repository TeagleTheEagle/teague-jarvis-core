param([ValidateSet('normal','hash-start-failure')][string]$Case='normal')
$ErrorActionPreference='Stop'
$candidate=Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'candidate.json')|ConvertFrom-Json
$py='C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$root=& $py -B (Join-Path $candidate.code 'small_binding.py') prepare $Case
if($LASTEXITCODE -ne 0){throw 'Small preflight failed'}
$record=[ordered]@{case=$Case;root=$root;code=$candidate.code;created=[DateTime]::UtcNow.ToString('o')}
$file=Join-Path $PSScriptRoot ($Case+'-run.json')
$stream=[IO.File]::Open($file,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
try{$bytes=[Text.Encoding]::UTF8.GetBytes(($record|ConvertTo-Json));$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}
& (Join-Path $candidate.code 'small_launch.ps1') -Run (Split-Path $root -Leaf)
