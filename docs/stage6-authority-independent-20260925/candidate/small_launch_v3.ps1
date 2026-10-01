param([Parameter(Mandatory=$true)][ValidatePattern('^protected-[a-f0-9]{32}$')][string]$Run)
$ErrorActionPreference='Stop';. (Join-Path $PSScriptRoot 'workspace.ps1')
$root=Get-LiveRun $Run;Set-LiveTemp $root
$py='C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$pwsh='C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
& $py -B (Join-Path $PSScriptRoot 'small_binding_v3.py') verify $Run
if($LASTEXITCODE -ne 0){throw 'Pre-observer binding failed'}
$case=(Get-Content (Join-Path $root 'small-declaration-v3.json') -Raw|ConvertFrom-Json).case
function Save($name,$obj){$f=[IO.FileStream]::new((Join-Path $root $name),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read);try{$b=[Text.Encoding]::UTF8.GetBytes(($obj|ConvertTo-Json -Depth 16));$f.Write($b,0,$b.Length);$f.Flush($true)}finally{$f.Dispose()}}
function Ready($p,$name){$sw=[Diagnostics.Stopwatch]::StartNew();while(!(Test-Path -LiteralPath (Join-Path $root $name))){if($p.HasExited -or $sw.Elapsed.TotalSeconds -gt 30){throw "Observer readiness failed: $name"};Start-Sleep -Milliseconds 100}}
function Gate($name,$process){$sw=[Diagnostics.Stopwatch]::StartNew();Write-Output ('OWNER_GATE '+$name);while(!(Test-Path -LiteralPath (Join-Path $root $name))){if($process.HasExited -or $sw.Elapsed.TotalSeconds -ge 120){throw 'Owner prompt gate expired'};Start-Sleep -Milliseconds 100}}
$me=Get-Process -Id $PID
Save 'launcher-identity.json' @{pid=$PID;created=$me.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=$me.Path;run=$root}
$marks=[Collections.Generic.List[object]]::new()
. (Join-Path $PSScriptRoot 'terminal_control_v3.ps1')
$phase=$null;$shutdownAllowed=$false;$observerExits=@{}
function Mark($event,$detail){$marks.Add(@{event=$event;pid=$PID;qpc=[Diagnostics.Stopwatch]::GetTimestamp();frequency=[Diagnostics.Stopwatch]::Frequency;detail=$detail})}
Mark 'LAUNCHER_ENTRY' $case
Add-Type -TypeDefinition @'
using System.Runtime.InteropServices;
public static class J6SmallCollector { [DllImport("D:\\JARVIS-STAGE6-LIVE\\7f204e14c90a497a8476be0e9927e074\\code\\J6OwnedEntry.dll",CharSet=CharSet.Unicode)] public static extern int RunCollector(string root,string mode); }
'@
$kernel=$null;$detail=$null;$app=$null;$workExit=$null;$errorText=$null;$appExited=$false;$detailExited=$false;$kernelExited=$false
try {
 $kernel=Start-Process -FilePath (Join-Path $PSScriptRoot 'J6AuthorityTraceV3.exe') -ArgumentList @($root,$PID,$me.StartTime.ToUniversalTime().ToFileTimeUtc().ToString()) -Verb RunAs -WindowStyle Hidden -PassThru
 Ready $kernel 'etw-ready.json'
 Gate 'allow-detail-prompt' $kernel
 $detail=Start-Process -FilePath (Join-Path $PSScriptRoot 'J6StartupTrace.exe') -ArgumentList @((Join-Path $root 'detail'),$PID,$me.StartTime.ToUniversalTime().ToFileTimeUtc().ToString()) -Verb RunAs -WindowStyle Hidden -PassThru
 Ready $detail 'detail\etw-ready.json'
 Gate 'allow-app-prompt' $kernel
 $app=Start-Process -FilePath $pwsh -ArgumentList @('-NoProfile','-File',(Join-Path $PSScriptRoot 'timed_monitor.ps1'),'-Run',$Run,'-KernelPid',$kernel.Id) -Verb RunAs -WindowStyle Hidden -PassThru
 Ready $app 'app-ready.json'
 Save 'observer-identities.json' @{etw=@{pid=$kernel.Id;created=$kernel.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=(Join-Path $PSScriptRoot 'J6AuthorityTraceV3.exe')};detail=@{pid=$detail.Id;created=$detail.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=(Join-Path $PSScriptRoot 'J6StartupTrace.exe')};app=@{pid=$app.Id;created=$app.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=$pwsh}}
 Mark 'RUN_ACTIVE' @{run=$Run}
 $controller=ReadRecord 'external-controller-v3.json'
 $management=@(@{pid=$PID;created=$me.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=$me.Path})+@((ReadRecord 'observer-identities.json').Values)+@($controller)
 Mark 'HELPER_INVOCATION' 'collector'
 $workExit=[J6SmallCollector]::RunCollector($root,$case)
 Mark 'HELPER_RETURN' @{role='collector';exitCode=$workExit}
 if($workExit -ne 0){throw 'Collector failed; terminal acceptance prohibited'}
 $phase=ReadRecord 'phase-a-v3.json'
 Need ($phase.binding.run -ceq $Run -and $phase.binding.declarationSHA256 -ceq (Hash 'small-declaration-v3.json') -and $phase.binding.observerSHA256 -ceq (Hash 'observer-identities.json')) 'Phase binding'
 foreach($flag in @('admissionsStopped','localDurable','trackerStopped','localHandlesClosed')){Need ($phase[$flag] -eq $true) ('Phase A '+$flag)}
 Need ($phase.cleanupPass -eq $false -and $phase.acceptance -eq $false) 'Premature acceptance'
 State 'COLLECTOR_LOCAL_FINALIZING' @{cleanupEntryQpc=$phase.cleanupEntryQpc}
 State 'LOCAL_EVIDENCE_FINALIZED_PENDING_EXTERNAL_EXIT' @{phaseASHA256=(Hash 'phase-a-v3.json')}
 $receipt=WaitEvidence 'terminal-v3.json';AssertTerminal $receipt
 Save 'terminal-observed-v3.json' @{receiptSHA256=(Hash 'terminal-v3.json');observedQpc=(Now);binding=$phase.binding}
 State 'COLLECTOR_EXITED' @{evidence='native + kernel + retained handle'}
 State 'TERMINAL_EVIDENCE_PENDING' @{phaseASHA256=(Hash 'phase-a-v3.json')}
 State 'TERMINAL_EVIDENCE_COMPLETE' @{receiptSHA256=(Hash 'terminal-v3.json')}
 WorkloadCensus $receipt
 State 'PRE_SHUTDOWN_WORKLOAD_CENSUS_COMPLETE' @{censusSHA256=(Hash 'workload-census-v3.json')}
 State 'OBSERVER_SHUTDOWN_ALLOWED' @{acceptance=$false};$shutdownAllowed=$true
}catch{$errorText=$_.ToString();Save 'launcher-failure.json' @{error=$errorText};Mark 'EXCEPTION' $errorText}
finally {
 try {
  if(!$shutdownAllowed){throw 'No success shutdown authorization'}
  [void](Budget);Save 'app-stop' @{reason='terminal receipt and workload census verified';binding=$phase.binding}
  $observerExits.application=ExitBounded $app 60 'application';$appExited=$true
  Save 'release-handles' @{observerExited=$true}
  [void](Budget);Save 'detail\etw-stop' @{reason='application observer exited'}
  $observerExits.detail=ExitBounded $detail 30 'detail';$detailExited=$true
  Save 'observer-tail-request-v3.json' @{phaseASHA256=(Hash 'phase-a-v3.json');binding=$phase.binding}
  while(!(Test-Path -LiteralPath (Join-Path $root 'observer-tail-v3.json'))){[void](Budget);Need (!$kernel.HasExited) 'Authority exited before tail evidence';Need (!(Test-Path -LiteralPath (Join-Path $root 'tail-failure-v3.json'))) 'Tail failed';Start-Sleep -Milliseconds ([Math]::Max(1,[Math]::Min(10,[Math]::Floor((Budget)*1000))))}
  $tail=ReadRecord 'observer-tail-v3.json';Need ($tail.sequence -eq 2 -and $tail.phaseASHA256 -ceq (Hash 'phase-a-v3.json')) 'Stale tail'
  [void](Budget);Save 'etw-stop' @{reason='subordinate terminal evidence captured';tailSHA256=(Hash 'observer-tail-v3.json')}
  $observerExits.authority=ExitBounded $kernel 30 'authority';$kernelExited=$true
 } catch {
  if(!$errorText){$errorText=$_.ToString()}
  if(!(Test-Path -LiteralPath (Join-Path $root 'rejected-v3.json'))){Save 'rejected-v3.json' @{state='REJECTED';error=$errorText;qpc=(Now)}}
  # Failure-only cleanup: preserves the original bounds; never restores acceptance.
  foreach($x in @(@('app-stop',$app,60000),@('detail\etw-stop',$detail,30000),@('etw-stop',$kernel,30000))){
   try{if(!(Test-Path -LiteralPath (Join-Path $root $x[0]))){Save $x[0] @{reason='REJECTED failure cleanup only'}};if($x[1]){[void]$x[1].WaitForExit($x[2])}}catch{}
  }
 }
 if($app){$appExited=$app.HasExited};if($detail){$detailExited=$detail.HasExited};if($kernel){$kernelExited=$kernel.HasExited}
 Save 'observer-exits-v3.json' @{binding=$(if($phase){$phase.binding});observers=$observerExits;completedQpc=(Now);error=$errorText}
 Save 'launcher-result.json' @{error=$errorText;case=$case;workExit=$workExit;applicationExited=$appExited;detailExited=$detailExited;kernelExited=$kernelExited;applicationExit=$(if($appExited){$app.ExitCode});detailExit=$(if($detailExited){$detail.ExitCode});kernelExit=$(if($kernelExited){$kernel.ExitCode})}
 Mark 'FINAL_SHUTDOWN' @{application=$appExited;detail=$detailExited;kernel=$kernelExited}
 Save 'integration-launcher.json' @($marks.ToArray())
 foreach($p in @($app,$detail,$kernel)){if($p -and $p.HasExited){$p.Dispose()}}
}
if($errorText -or !$appExited -or !$detailExited -or !$kernelExited){throw 'Run blocked; evidence preserved; no retry'}
Write-Output ('SMALL_COLLECTION_CLOSED_PENDING_CHECK '+$root)
