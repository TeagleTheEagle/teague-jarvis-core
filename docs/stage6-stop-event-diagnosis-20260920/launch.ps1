param([ValidateSet('smoke','repeat1','repeat2')][string]$Run)
$ErrorActionPreference='Stop';$root=Join-Path $PSScriptRoot $Run
if(Test-Path -LiteralPath $root){throw 'Existing run cannot be overwritten'}
if(@(Get-Process|Where-Object ProcessName -match '^(VBox|VirtualBox)').Count){throw 'VirtualBox must remain closed'}
New-Item -ItemType Directory -Path $root | Out-Null
$pwsh='C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
$script=Join-Path $PSScriptRoot 'monitor.ps1'
$p=Start-Process -FilePath $pwsh -ArgumentList @('-NoProfile','-File',('"'+$script+'"'),'-Run',$Run) -WorkingDirectory $PSScriptRoot -Verb RunAs -WindowStyle Hidden -PassThru
@{pid=$p.Id;created=$p.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();executable=$pwsh;sha256=(Get-FileHash -LiteralPath $pwsh).Hash;run=$Run;role='read-only process monitor; writes sacrificial diagnostic evidence only'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $root 'launch.json')
$python=Join-Path $PSScriptRoot '..\..\.venv\Scripts\python.exe'
& $python -B (Join-Path $PSScriptRoot 'collect.py') $Run 2>&1 | Tee-Object -FilePath (Join-Path $root 'console.txt')
if($LASTEXITCODE){throw 'Diagnostic collector failed; preserve run'}
