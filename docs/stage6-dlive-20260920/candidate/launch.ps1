param([ValidateSet('idle','disk','sustained','cpu','Dhash','dry')][string]$Mode,[ValidateRange(5,160)][int]$Duration=150,[ValidatePattern('^[a-z][a-z0-9-]{0,20}$')][string]$Label)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'workspace.ps1');Assert-LiveCode;Set-Location -LiteralPath $PSScriptRoot
if(@(Get-Process|Where-Object ProcessName -match '^(VBox|VirtualBox)').Count){throw 'VirtualBox must remain closed'}
$Run=$Label+'-'+[guid]::NewGuid().ToString('N');$root=Join-Path $PSScriptRoot $Run
if(Test-Path -LiteralPath $root){throw 'No reuse'}
New-Item -ItemType Directory -Path $root -ErrorAction Stop|Out-Null
New-Item -ItemType Directory -Path (Join-Path $root 'temp') -ErrorAction Stop|Out-Null
Set-LiveTemp $root
@{run=$Run;mode=$Mode;journalVolume='D';eventVolume='D';controlVolume='D';telemetry='full';duration=$Duration;threshold=10;acceptance=$false}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'case.json')
@(Get-ChildItem -LiteralPath $PSScriptRoot -File|Where-Object Extension -in '.ps1','.py','.cs','.exe'|ForEach-Object {@{path=$_.FullName;sha256=(Get-FileHash -LiteralPath $_.FullName).Hash}})|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'source-hashes.json')
$pwsh='C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
$python='C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\.venv\Scripts\python.exe'
$exeHash=(Get-FileHash -LiteralPath $pwsh).Hash
$p=Start-Process -FilePath $pwsh -ArgumentList @('-NoProfile','-File',('"'+(Join-Path $PSScriptRoot 'monitor.ps1')+'"'),'-Run',$Run) -WorkingDirectory $PSScriptRoot -Verb RunAs -WindowStyle Hidden -PassThru
@{pid=$p.Id;created=$p.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();executable=$pwsh;sha256=$exeHash;run=$Run}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'launch.json')
& $python -B (Join-Path $PSScriptRoot 'collect.py') $Run 2>&1|Tee-Object -FilePath (Join-Path $root 'console.txt')
if($LASTEXITCODE){throw 'Collector/cleanup failed; stop acceptance'}
# All analysis, hash/finalization and copying occurs only after retained monitor exit.
& $python -B (Join-Path $PSScriptRoot 'analyze.py') $Run
if($LASTEXITCODE){throw 'Analysis failure'}
& $python -B (Join-Path $PSScriptRoot 'event_analysis.py') $Run
if($LASTEXITCODE){throw 'Event analysis failure'}
& $python -B (Join-Path $PSScriptRoot 'accept_run.py') $Run
if($LASTEXITCODE){throw 'MONITOR_STILL_DEFECTIVE; evidence preserved; stop campaign'}
