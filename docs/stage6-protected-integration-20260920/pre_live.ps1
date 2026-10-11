param([string]$Label='large-validation')
$ErrorActionPreference='Stop'
if($Label -notmatch '^[a-z0-9-]+$'){throw 'Invalid label'}
$candidate=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'candidate.json') -Raw|ConvertFrom-Json
$runFragment=Split-Path (Split-Path $candidate.code) -Leaf
$self=Get-Process -Id $PID
$all=@(Get-CimInstance Win32_Process)
$scope=@($all|Where-Object { $_.ProcessId -ne $PID -and ($_.Name -match '^(VBox|VirtualBox|J6Probe|J6KernelTrace|J6BaselineTrace)' -or ($_.Name -in 'python.exe','pwsh.exe' -and $_.CommandLine -like ('*'+$runFragment+'*'))) }|Select-Object ProcessId,Name,CreationDate,ExecutablePath)
$traces=& 'C:\Windows\System32\logman.exe' query -ets 2>&1
$queryExit=$LASTEXITCODE;$ours=@($traces|Where-Object {$_ -match 'J6Kernel-'})
$result=@{self=@{pid=$PID;created=$self.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=$self.Path};processes=$scope;traceExit=$queryExit;traces=$ours;utc=[datetime]::UtcNow.ToString('o')}
$path=Join-Path $PSScriptRoot ('pre-live-'+$Label+'.json')
if(Test-Path -LiteralPath $path){throw 'Evidence already exists'}
$result|ConvertTo-Json -Depth 6|Set-Content -LiteralPath $path
if($scope.Count -or $ours.Count -or $queryExit -ne 0){throw 'Live preflight failed'}
'LIVE PREFLIGHT PASS'
