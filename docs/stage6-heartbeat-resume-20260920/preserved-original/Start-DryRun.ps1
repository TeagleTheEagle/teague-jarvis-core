param([ValidateSet('dry1','dry2')][string]$Run)
$ErrorActionPreference='Stop'
$root=Join-Path $PSScriptRoot $Run
if(Test-Path -LiteralPath (Join-Path $root 'launch.json')){throw 'Refusing to overwrite a prior run'}
if($Run -eq 'dry2'){
 $prior=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'dry1\acceptance.json') -Raw|ConvertFrom-Json
 if($prior.status -ne 'SACRIFICIAL_RUN_ACCEPTED'){throw 'Dry1 has not passed'}
}
$diagPwsh='C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
$monitorArgs='-NoProfile -NonInteractive -File "'+(Join-Path $PSScriptRoot 'monitor.ps1')+'" -Run '+$Run
$p=Start-Process -FilePath $diagPwsh -Verb RunAs -WindowStyle Hidden -ArgumentList $monitorArgs -PassThru
@{pid=$p.Id;run=$Run;executable=$diagPwsh;sha256=(Get-FileHash -LiteralPath $diagPwsh).Hash}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'launch.json')
$until=[DateTime]::UtcNow.AddSeconds(15)
while(-not(Test-Path -LiteralPath (Join-Path $root 'ready.json'))){if([DateTime]::UtcNow -gt $until){throw 'Monitor readiness failed'};Start-Sleep -Milliseconds 100}
$resourceArgs='-NoProfile -NonInteractive -File "'+(Join-Path $PSScriptRoot 'resources.ps1')+'" -Run '+$Run
$sampler=Start-Process -FilePath $diagPwsh -WindowStyle Hidden -ArgumentList $resourceArgs -PassThru
$sampler.Id|Set-Content -LiteralPath (Join-Path $root 'sampler-pid.txt')
& (Join-Path $PSScriptRoot '..\..\.venv\Scripts\python.exe') -B (Join-Path $PSScriptRoot 'campaign.py') $Run 2>&1|Tee-Object -FilePath (Join-Path $PSScriptRoot ($Run+'-console.txt'))
exit $LASTEXITCODE
