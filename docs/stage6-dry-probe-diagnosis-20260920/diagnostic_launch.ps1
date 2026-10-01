param([ValidateSet('A','B','C','D','E','F')][string]$Phase)
$ErrorActionPreference='Stop';. (Join-Path $PSScriptRoot 'workspace.ps1');Assert-LiveCode;Set-Location -LiteralPath $PSScriptRoot
if(@(Get-Process|Where-Object ProcessName -match '^(VBox|VirtualBox)').Count){throw 'VirtualBox must remain closed'}
$Run='ladder-'+$Phase.ToLower()+'-'+[guid]::NewGuid().ToString('N');$root=Join-Path $PSScriptRoot $Run
New-Item -ItemType Directory -Path (Join-Path $root 'temp') -ErrorAction Stop|Out-Null;Set-LiveTemp $root
@{run=$Run;mode='diagnostic';phase=$Phase;journalVolume='D';eventVolume='D';controlVolume='D';telemetry='full';threshold=10;acceptance=$false;probeWarning=5;probeHardDeadline=13.6;observerMilliseconds=15000}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'case.json')
@(Get-ChildItem -LiteralPath $PSScriptRoot -File|Where-Object Extension -in '.ps1','.py','.cs','.exe'|ForEach-Object {@{path=$_.FullName;sha256=(Get-FileHash -LiteralPath $_.FullName).Hash}})|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'source-hashes.json')
$pwsh='C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
$p=Start-Process -FilePath $pwsh -ArgumentList @('-NoProfile','-File',('"'+(Join-Path $PSScriptRoot 'monitor.ps1')+'"'),'-Run',$Run) -WorkingDirectory $PSScriptRoot -Verb RunAs -WindowStyle Hidden -PassThru
@{pid=$p.Id;created=$p.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();executable=$pwsh;sha256=(Get-FileHash -LiteralPath $pwsh).Hash;run=$Run}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'launch.json')
& 'C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\.venv\Scripts\python.exe' -B (Join-Path $PSScriptRoot 'diagnose.py') $Run $Phase 2>&1|Tee-Object -FilePath (Join-Path $root 'console.txt')
if($LASTEXITCODE){throw 'Diagnostic stop: preserve case; no later ladder case authorized after hard-deadline reproduction'}
