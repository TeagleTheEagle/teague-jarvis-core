param([ValidateSet('a1','a2','a3','minimal','persist-d','none','dhash')][string]$Run)
$ErrorActionPreference='Stop';$root=Join-Path $PSScriptRoot $Run
if(Test-Path -LiteralPath $root){throw 'Never overwrite a diagnostic run'}
if(@(Get-Process|Where-Object ProcessName -match '^(VBox|VirtualBox)').Count){throw 'VirtualBox must remain closed'}
$mode='sustained';$volume='C';$eventVolume='C';$telemetry='full';$duration=150
if($Run -eq 'dhash'){$mode='Dhash'}
if($Run -eq 'minimal'){$telemetry='minimal'}
if($Run -eq 'none'){$telemetry='none'}
if($Run -eq 'persist-d'){$eventVolume='D'}
New-Item -ItemType Directory -Path $root|Out-Null
if($eventVolume -eq 'D'){
 $droot='D:\JARVIS-STAGE6-EVENTDRAIN-20260920\'+$Run
 if(Test-Path -LiteralPath $droot){throw 'D journal directory already exists'}
 New-Item -ItemType Directory -Path $droot|Out-Null
}
@{run=$Run;mode=$mode;journalVolume=$volume;eventVolume=$eventVolume;controlVolume='C';telemetry=$telemetry;duration=$duration;threshold=10;acceptance=$false}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'case.json')
$pwsh='C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
$script=Join-Path $PSScriptRoot 'monitor.ps1'
@(Get-ChildItem -LiteralPath $PSScriptRoot -File|Where-Object Extension -in '.ps1','.py','.cs','.exe'|ForEach-Object {@{path=$_.FullName;sha256=(Get-FileHash -LiteralPath $_.FullName).Hash}})|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'source-hashes.json')
$p=Start-Process -FilePath $pwsh -ArgumentList @('-NoProfile','-File',('"'+$script+'"'),'-Run',$Run) -WorkingDirectory $PSScriptRoot -Verb RunAs -WindowStyle Hidden -PassThru
@{pid=$p.Id;created=$p.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();executable=$pwsh;sha256=(Get-FileHash -LiteralPath $pwsh).Hash;run=$Run;role='read-only process monitor; sacrificial evidence only'}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'launch.json')
$python=Join-Path $PSScriptRoot '..\..\.venv\Scripts\python.exe'
& $python -B (Join-Path $PSScriptRoot 'collect.py') $Run 2>&1|Tee-Object -FilePath (Join-Path $root 'console.txt')
if($LASTEXITCODE){throw 'Collector/cleanup failed; preserve evidence and stop batch'}
