$ErrorActionPreference='Stop';. (Join-Path $PSScriptRoot 'workspace.ps1');Assert-LiveCode;Set-Location -LiteralPath $PSScriptRoot
if(@(Get-Process|Where-Object ProcessName -match '^(VBox|VirtualBox)').Count){throw 'VirtualBox must remain closed'}
$Run='kernel-e-'+[guid]::NewGuid().ToString('N');$root=Join-Path $PSScriptRoot $Run
New-Item -ItemType Directory -Path (Join-Path $root 'temp') -ErrorAction Stop|Out-Null;Set-LiveTemp $root
@{run=$Run;mode='diagnostic';phase='E';journalVolume='D';eventVolume='D';controlVolume='D';telemetry='full';threshold=10;acceptance=$false;probeWarning=5;probeHardDeadline=13.6;observerMilliseconds=15000}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'case.json')
@(Get-ChildItem -LiteralPath $PSScriptRoot -File|Where-Object Extension -in '.ps1','.py','.cs','.cpp','.exe'|ForEach-Object {@{path=$_.FullName;sha256=(Get-FileHash -LiteralPath $_.FullName).Hash}})|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'source-hashes.json')
$pwsh='C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
$me=Get-Process -Id $PID
$identity=@{pid=$PID;creationFiletime=$me.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=$me.Path;run=$root}
$identity|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'launcher.json')
$etw=$null;$p=$null;$workExit=$null
try {
 $etw=Start-Process -FilePath (Join-Path $PSScriptRoot 'J6KernelTrace.exe') -ArgumentList @($root,$PID,$identity.creationFiletime) -Verb RunAs -WindowStyle Hidden -PassThru
 $end=[datetime]::UtcNow.AddSeconds(30)
 while(!(Test-Path -LiteralPath (Join-Path $root 'etw-ready.json'))){if($etw.HasExited -or [datetime]::UtcNow -gt $end){throw 'ETW not ready'};Start-Sleep -Milliseconds 100}
 $p=Start-Process -FilePath $pwsh -ArgumentList @('-NoProfile','-File',(Join-Path $PSScriptRoot 'monitor.ps1'),'-Run',$Run) -WorkingDirectory $PSScriptRoot -Verb RunAs -WindowStyle Hidden -PassThru
 @{pid=$p.Id;created=$p.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();executable=$pwsh;sha256=(Get-FileHash -LiteralPath $pwsh).Hash;run=$Run}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'launch.json')
 & 'C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\.venv\Scripts\python.exe' -B (Join-Path $PSScriptRoot 'collect.py') $Run 'E' 1> (Join-Path $root 'work.stdout') 2> (Join-Path $root 'work.stderr')
 $workExit=$LASTEXITCODE
} catch { $_.ToString()|Set-Content -LiteralPath (Join-Path $root 'launcher-error.txt') }
finally {
 [IO.File]::WriteAllText((Join-Path $root 'etw-stop'),'diagnostic completion')
 if($etw){$exited=$etw.WaitForExit(30000);@{pid=$etw.Id;exited=$exited;exitCode=$(if($exited){$etw.ExitCode}else{$null});workExit=$workExit}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'launcher-result.json');$etw.Dispose()}
 if($p){@{pid=$p.Id;exited=$p.HasExited}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'wmi-observer-result.json');$p.Dispose()}
 Write-Output $root
}
