param([Parameter(Mandatory=$true)][ValidatePattern('^protected-[a-f0-9]{32}$')][string]$Run)
$ErrorActionPreference='Stop';. (Join-Path $PSScriptRoot 'workspace.ps1')
$root=Get-LiveRun $Run;Set-LiveTemp $root
$py='C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$pwsh='C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
& $py -B (Join-Path $PSScriptRoot 'small_binding_v2.py') verify $Run
if($LASTEXITCODE -ne 0){throw 'Pre-observer binding failed'}
$case=(Get-Content (Join-Path $root 'small-declaration-v2.json') -Raw|ConvertFrom-Json).case
function Save($name,$obj){$f=[IO.FileStream]::new((Join-Path $root $name),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read);try{$b=[Text.Encoding]::UTF8.GetBytes(($obj|ConvertTo-Json -Depth 16));$f.Write($b,0,$b.Length);$f.Flush($true)}finally{$f.Dispose()}}
function Ready($p,$name){$sw=[Diagnostics.Stopwatch]::StartNew();while(!(Test-Path -LiteralPath (Join-Path $root $name))){if($p.HasExited -or $sw.Elapsed.TotalSeconds -gt 30){throw "Observer readiness failed: $name"};Start-Sleep -Milliseconds 100}}
function Gate($name,$process){$sw=[Diagnostics.Stopwatch]::StartNew();Write-Output ('OWNER_GATE '+$name);while(!(Test-Path -LiteralPath (Join-Path $root $name))){if($process.HasExited -or $sw.Elapsed.TotalSeconds -ge 120){throw 'Owner prompt gate expired'};Start-Sleep -Milliseconds 100}}
$me=Get-Process -Id $PID
Save 'launcher-identity.json' @{pid=$PID;created=$me.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=$me.Path;run=$root}
$marks=[Collections.Generic.List[object]]::new()
function Mark($event,$detail){$marks.Add(@{event=$event;pid=$PID;qpc=[Diagnostics.Stopwatch]::GetTimestamp();frequency=[Diagnostics.Stopwatch]::Frequency;detail=$detail})}
Mark 'LAUNCHER_ENTRY' $case
Add-Type -TypeDefinition @'
using System.Runtime.InteropServices;
public static class J6SmallCollector { [DllImport("D:\\JARVIS-STAGE6-LIVE\\2d922197cf7d4bb098d8da6e070cbff2\\code\\J6OwnedEntry.dll",CharSet=CharSet.Unicode)] public static extern int RunCollector(string root,string mode); }
'@
$kernel=$null;$detail=$null;$app=$null;$workExit=$null;$errorText=$null;$appExited=$false;$detailExited=$false;$kernelExited=$false
try {
 $kernel=Start-Process -FilePath (Join-Path $PSScriptRoot 'J6AuthorityTrace.exe') -ArgumentList @($root,$PID,$me.StartTime.ToUniversalTime().ToFileTimeUtc().ToString()) -Verb RunAs -WindowStyle Hidden -PassThru
 Ready $kernel 'etw-ready.json'
 Gate 'allow-detail-prompt' $kernel
 $detail=Start-Process -FilePath (Join-Path $PSScriptRoot 'J6StartupTrace.exe') -ArgumentList @((Join-Path $root 'detail'),$PID,$me.StartTime.ToUniversalTime().ToFileTimeUtc().ToString()) -Verb RunAs -WindowStyle Hidden -PassThru
 Ready $detail 'detail\etw-ready.json'
 Gate 'allow-app-prompt' $kernel
 $app=Start-Process -FilePath $pwsh -ArgumentList @('-NoProfile','-File',(Join-Path $PSScriptRoot 'timed_monitor.ps1'),'-Run',$Run,'-KernelPid',$kernel.Id) -Verb RunAs -WindowStyle Hidden -PassThru
 Ready $app 'app-ready.json'
 Save 'observer-identities.json' @{etw=@{pid=$kernel.Id;created=$kernel.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=(Join-Path $PSScriptRoot 'J6AuthorityTrace.exe')};detail=@{pid=$detail.Id;created=$detail.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=(Join-Path $PSScriptRoot 'J6StartupTrace.exe')};app=@{pid=$app.Id;created=$app.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=$pwsh}}
 Mark 'HELPER_INVOCATION' 'collector'
 $workExit=[J6SmallCollector]::RunCollector($root,$case)
 Mark 'HELPER_RETURN' @{role='collector';exitCode=$workExit}
 if($workExit -ne 0 -and $case -eq 'normal'){throw 'Collector failed'}
}catch{$errorText=$_.ToString();Save 'launcher-failure.json' @{error=$errorText};Mark 'EXCEPTION' $errorText}
finally {
 Save 'app-stop' @{reason='collection ended; no acceptance claim'}
 if($app){$appExited=$app.WaitForExit(60000)}
 Save 'release-handles' @{observerExited=$appExited}
 Save 'detail\etw-stop' @{reason='application observer closure requested'}
 if($detail){$detailExited=$detail.WaitForExit(30000)}
 Save 'etw-stop' @{reason='detailed observer closure requested'}
 if($kernel){$kernelExited=$kernel.WaitForExit(30000)}
 Save 'launcher-result.json' @{error=$errorText;case=$case;workExit=$workExit;applicationExited=$appExited;detailExited=$detailExited;kernelExited=$kernelExited;applicationExit=$(if($app -and $appExited){$app.ExitCode});detailExit=$(if($detail -and $detailExited){$detail.ExitCode});kernelExit=$(if($kernel -and $kernelExited){$kernel.ExitCode})}
 Mark 'FINAL_SHUTDOWN' @{application=$appExited;detail=$detailExited;kernel=$kernelExited}
 Save 'integration-launcher.json' @($marks.ToArray())
 foreach($p in @($app,$detail,$kernel)){if($p -and $p.HasExited){$p.Dispose()}}
}
if($errorText -or !$appExited -or !$detailExited -or !$kernelExited){throw 'Run blocked; evidence preserved; no retry'}
Write-Output ('SMALL_COLLECTION_CLOSED_PENDING_CHECK '+$root)
