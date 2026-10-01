param([ValidateSet('smoke','a1','a2','a3','b','c','d','e','f','minimal')][string]$Run)
$ErrorActionPreference='Stop';$root=Join-Path $PSScriptRoot $Run
if(Test-Path -LiteralPath $root){throw 'Never overwrite a diagnostic run'}
if(@(Get-Process|Where-Object ProcessName -match '^(VBox|VirtualBox)').Count){throw 'VirtualBox must remain closed'}
$mode='sustained';$volume='C';$telemetry='full';$duration=150
if($Run -eq 'smoke'){$mode='idle';$duration=5}
if($Run -in @('b','d')){$volume='D'}
if($Run -in @('c','d')){$mode='Dhash'}
if($Run -eq 'e'){$mode='cpu'}
if($Run -eq 'f'){$mode='disk'}
if($Run -eq 'minimal'){$telemetry='minimal'}
New-Item -ItemType Directory -Path $root|Out-Null
if($volume -eq 'D'){
 $droot='D:\JARVIS-STAGE6-HEARTBEAT-STALL-20260920\'+$Run
 if(Test-Path -LiteralPath $droot){throw 'D journal directory already exists'}
 New-Item -ItemType Directory -Path $droot|Out-Null
}
@{run=$Run;mode=$mode;journalVolume=$volume;eventEvidenceVolume='C';controlVolume='C';telemetry=$telemetry;duration=$duration;threshold=10;acceptance=$false}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'case.json')
$pwsh='C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
$script=Join-Path $PSScriptRoot 'monitor.ps1'
$p=Start-Process -FilePath $pwsh -ArgumentList @('-NoProfile','-File',('"'+$script+'"'),'-Run',$Run) -WorkingDirectory $PSScriptRoot -Verb RunAs -WindowStyle Hidden -PassThru
@{pid=$p.Id;created=$p.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();executable=$pwsh;sha256=(Get-FileHash -LiteralPath $pwsh).Hash;run=$Run;role='read-only process monitor; sacrificial evidence only'}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'launch.json')
$python=Join-Path $PSScriptRoot '..\..\.venv\Scripts\python.exe'
& $python -B (Join-Path $PSScriptRoot 'collect.py') $Run 2>&1|Tee-Object -FilePath (Join-Path $root 'console.txt')
if($LASTEXITCODE){throw 'Collector/cleanup failed; preserve evidence and stop batch'}
