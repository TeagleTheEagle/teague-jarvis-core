param([Parameter(Mandatory=$true)][ValidatePattern('^identity-[a-f0-9]{32}$')][string]$Run)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'workspace.ps1')
$root=Get-LiveRun $Run;Set-LiveTemp $root
function Save($name,$obj){$f=[IO.FileStream]::new((Join-Path $root $name),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read);try{$b=[Text.Encoding]::UTF8.GetBytes(($obj|ConvertTo-Json -Depth 15));$f.Write($b,0,$b.Length);$f.Flush($true)}finally{$f.Dispose()}}
function Ready($p,$name){$sw=[Diagnostics.Stopwatch]::StartNew();while(!(Test-Path -LiteralPath (Join-Path $root $name))){if($p.HasExited -or $sw.Elapsed.TotalSeconds -gt 30){throw "Observer readiness failed: $name"};Start-Sleep -Milliseconds 100}}
$me=Get-Process -Id $PID
Save 'launcher-identity.json' @{pid=$PID;created=$me.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=$me.Path;run=$root}
$tracer=$null;$observer=$null;$worker=$null;$errorText=$null
$pwsh='C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
$python='C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'

Add-Type -TypeDefinition @'
using System.Runtime.InteropServices;
using System.Threading.Tasks;
public static class J6Qualification {
 [DllImport("D:\\JARVIS-STAGE6-LIVE\\e55504d627d24f24a6f56f9e2435230b\\code\\J6OwnedEntry.dll",CharSet=CharSet.Unicode)] public static extern int RunQualification(string root);
 public static Task<int> Start(string root) { return Task.Run(() => RunQualification(root)); }
}
'@

try {
 $tracer=Start-Process -FilePath (Join-Path $PSScriptRoot 'J6AuthorityTrace.exe') -ArgumentList @($root,$PID,$me.StartTime.ToUniversalTime().ToFileTimeUtc().ToString()) -Verb RunAs -WindowStyle Hidden -PassThru
 Ready $tracer 'etw-ready.json'
 Write-Output 'KERNEL_READY_WAITING_FOR_SECOND_PROMPT'
 $gate=[Diagnostics.Stopwatch]::StartNew()
 while(!(Test-Path -LiteralPath (Join-Path $root 'allow-app-prompt'))){if($gate.Elapsed.TotalSeconds -gt 120 -or $tracer.HasExited){throw 'Second prompt gate expired'};Start-Sleep -Milliseconds 100}
 $observer=Start-Process -FilePath $pwsh -ArgumentList @('-NoProfile','-File',(Join-Path $PSScriptRoot 'timed_monitor.ps1'),'-Run',$Run,'-KernelPid',$tracer.Id) -Verb RunAs -WindowStyle Hidden -PassThru
 Ready $observer 'app-ready.json'
 $worker=[J6Qualification]::Start($root)
 $born=[Diagnostics.Stopwatch]::StartNew()
 while(!(Test-Path -LiteralPath (Join-Path $root 'worker-created.json'))){if($worker.IsCompleted -or $born.Elapsed.TotalSeconds -gt 30){throw 'Worker creation evidence missing'};Start-Sleep -Milliseconds 100}
 $wi=Get-Content -Raw -LiteralPath (Join-Path $root 'worker-created.json')|ConvertFrom-Json
 Save 'process-identities.json' @(@{role='kernel';pid=$tracer.Id;created=$tracer.StartTime.ToUniversalTime().ToFileTimeUtc().ToString()},@{role='application';pid=$observer.Id;created=$observer.StartTime.ToUniversalTime().ToFileTimeUtc().ToString()},@{role='worker';pid=$wi.pid;created=$wi.created})
 $wait=[Diagnostics.Stopwatch]::StartNew()
 while(!(Test-Path -LiteralPath (Join-Path $root 'identity-probes.json'))){if($worker.IsCompleted -or $observer.HasExited -or $tracer.HasExited -or $wait.Elapsed.TotalSeconds -gt 60){throw 'Identity probe collection failed'};Start-Sleep -Milliseconds 100}
}catch{$errorText=$_.ToString();Save 'launcher-failure.json' @{error=$errorText}}
finally {
 Save 'app-stop' @{reason='identity experiment complete; no acceptance claim'}
 $appExited=if($observer){$observer.WaitForExit(60000)}else{$true}
 Save 'release-handles' @{observerExited=$appExited}
 $workerExited=if($worker){$worker.Wait(20000)}else{$true}
 Save 'etw-stop' @{reason='application and worker closure requested'}
 $kernelExited=if($tracer){$tracer.WaitForExit(30000)}else{$true}
 Save 'launcher-result.json' @{error=$errorText;applicationExited=$appExited;workerExited=$workerExited;kernelExited=$kernelExited;applicationExit=$(if($observer -and $appExited){$observer.ExitCode});workerExit=$(if($worker -and $workerExited){$worker.Result});kernelExit=$(if($tracer -and $kernelExited){$tracer.ExitCode})}
 if($worker -and $workerExited){$worker.Dispose()};if($observer -and $appExited){$observer.Dispose()};if($tracer -and $kernelExited){$tracer.Dispose()}
}
if($errorText -or !$appExited -or !$workerExited -or !$kernelExited){throw 'Identity experiment blocked; failure preserved'}
