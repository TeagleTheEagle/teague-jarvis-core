$ErrorActionPreference='Stop'
$plan=Get-Content -LiteralPath (Join-Path (Split-Path $PSScriptRoot) 'stage6-kernel-child-trace-20260920\plan.json') -Raw|ConvertFrom-Json
$observer=Get-Process -Id $PID
$all=@(Get-CimInstance Win32_Process)
$matching=@($all|Where-Object { $_.ProcessId -ne $PID -and ($_.Name -match '^(VBox|VirtualBox|J6Probe|J6KernelTrace)' -or ($_.Name -in 'python.exe','pwsh.exe' -and $_.CommandLine -like ('*'+$plan.live_code+'*'))) }|ForEach-Object {@{pid=$_.ProcessId;name=$_.Name;created=$_.CreationDate.ToUniversalTime().ToFileTimeUtc().ToString();image=$_.ExecutablePath}})
@{utc=[datetime]::UtcNow.ToString('o');observer=@{pid=$PID;created=$observer.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=$observer.Path};matchingProcesses=$matching;note='Observer identity recorded separately; script path is outside the diagnostic workspace, avoiding command-text self-match.'}|ConvertTo-Json -Depth 6|Set-Content -LiteralPath (Join-Path $PSScriptRoot 'final-host-snapshot.json')
@{matchingProcesses=$matching.Count;observerPid=$PID}|ConvertTo-Json
