import pathlib,json,shutil
R=pathlib.Path(__file__).resolve().parent;C=pathlib.Path(json.loads((R/'before.json').read_text())['candidate'])
for n in ('coordination_v3.py','evidence_support_v3.py','terminal_receipt_v3.hpp','completed_v3.py','terminal_control_v3.ps1'):shutil.copyfile(R/n,C/n)
def new(n,s):
 with (C/n).open('x',encoding='utf8',newline='\n') as f:f.write(s)
def rep(s,a,b):assert a in s,a;return s.replace(a,b)
s=(C/'authority_trace_v3.cpp').read_text()
s=rep(s,'bool receiptPublished=false;','bool receiptPublished=false;bool tailPublished=false;')
s=rep(s,' if(GetFileAttributesW((folder+L"\\\\etw-stop")', ''' if(receiptPublished&&!tailPublished){try{tailPublished=terminal_v3::TailReceipt();}catch(const std::exception&e){++faults;Write(L"tail-failure-v3.json",std::string("{\\"error\\":")+J(e.what())+"}");break;}}
 if(GetFileAttributesW((folder+L"\\\\etw-stop")''')
(C/'authority_trace_v3.cpp').write_text(s)
s=(C/'small_launch_v2.ps1').read_text().replace('small_binding_v2.py','small_binding_v3.py').replace('small-declaration-v2.json','small-declaration-v3.json').replace('J6AuthorityTrace.exe','J6AuthorityTraceV3.exe')
s=s.replace('2d922197cf7d4bb098d8da6e070cbff2',C.parent.name)
s=rep(s,"$marks=[Collections.Generic.List[object]]::new()", "$marks=[Collections.Generic.List[object]]::new()\n. (Join-Path $PSScriptRoot 'terminal_control_v3.ps1')\n$phase=$null;$shutdownAllowed=$false;$observerExits=@{}")
s=rep(s," Mark 'HELPER_INVOCATION' 'collector'", " Mark 'RUN_ACTIVE' @{run=$Run}\n $controller=ReadRecord 'external-controller-v3.json'\n $management=@(@{pid=$PID;created=$me.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=$me.Path})+@((ReadRecord 'observer-identities.json').Values)+@($controller)\n Mark 'HELPER_INVOCATION' 'collector'")
s=rep(s," if($workExit -ne 0 -and $case -eq 'normal'){throw 'Collector failed'}", ''' if($workExit -ne 0){throw 'Collector failed; terminal acceptance prohibited'}
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
 State 'OBSERVER_SHUTDOWN_ALLOWED' @{acceptance=$false};$shutdownAllowed=$true''')
start=s.index('finally {\n Save \'app-stop\'');end=s.index("if($errorText -or",start)
s=s[:start]+'''finally {
 try {
  if(!$shutdownAllowed){throw 'No success shutdown authorization'}
  [void](Budget);Save 'app-stop' @{reason='terminal receipt and workload census verified';binding=$phase.binding}
  $observerExits.application=ExitBounded $app 60 'application';$appExited=$true
  Save 'release-handles' @{observerExited=$true}
  [void](Budget);Save 'detail\\etw-stop' @{reason='application observer exited'}
  $observerExits.detail=ExitBounded $detail 30 'detail';$detailExited=$true
  Save 'observer-tail-request-v3.json' @{phaseASHA256=(Hash 'phase-a-v3.json');binding=$phase.binding}
  while(!(Test-Path -LiteralPath (Join-Path $root 'observer-tail-v3.json'))){[void](Budget);Need (!$kernel.HasExited) 'Authority exited before tail evidence';Need (!(Test-Path -LiteralPath (Join-Path $root 'tail-failure-v3.json'))) 'Tail failed';Start-Sleep -Milliseconds 10}
  $tail=ReadRecord 'observer-tail-v3.json';Need ($tail.sequence -eq 2 -and $tail.phaseASHA256 -ceq (Hash 'phase-a-v3.json')) 'Stale tail'
  [void](Budget);Save 'etw-stop' @{reason='subordinate terminal evidence captured';tailSHA256=(Hash 'observer-tail-v3.json')}
  $observerExits.authority=ExitBounded $kernel 30 'authority';$kernelExited=$true
 } catch {
  if(!$errorText){$errorText=$_.ToString()}
  if(!(Test-Path -LiteralPath (Join-Path $root 'rejected-v3.json'))){Save 'rejected-v3.json' @{state='REJECTED';error=$errorText;qpc=(Now)}}
  # Failure-only cleanup: preserves the original bounds; never restores acceptance.
  foreach($x in @(@('app-stop',$app,60000),@('detail\\etw-stop',$detail,30000),@('etw-stop',$kernel,30000))){
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
''' + s[end:]
new('small_launch_v3.ps1',s)
s=(C/'small_check_v2.py').read_text().replace('small_binding_v2','small_binding_v3').replace('small-declaration-v2','small-declaration-v3').replace('tracker_adapter_v2','tracker_adapter_v3').replace('small-check-result-v2','small-check-result-v3')
s=rep(s,"  load=lambda", "  load=lambda") if '  load=lambda' in s else s
s=rep(s," load=lambda n:q.load(root/n)"," from completed_v3 import verify_complete\n phase=verify_complete(root)\n load=lambda n:q.load(root/n)")
s=rep(s,"q.require(tree['allExited'] and tree['allHandlesClosed'] and tree['threadStopped'],'TREE_CLOSURE')", "q.require(tree['localFinalized'] and tree['allHandlesClosed'] and tree['threadStopped'],'TREE_LOCAL_CLOSURE')")
new('small_check_v3.py',s)
s=(C/'small_finalize_v2.py').read_text().replace('small_binding_v2','small_binding_v3').replace('small_check_v2','small_check_v3').replace('v2-','v3-').replace('integration-v2','coordination-v3').replace('small-declaration-v2','small-declaration-v3')
s=rep(s,"TOP=set(", "TOP=set('cleanup-origin-v3.json phase-a-v3.json terminal-v3.json terminal-observed-v3.json workload-census-v3.json observer-tail-request-v3.json observer-tail-v3.json observer-exits-v3.json external-controller-v3.json external-exits-v3.json final-census-v3.json coordination-states-v3.json'.split()) | set(")
s=rep(s,"  no_live_identities(root)","  no_live_identities(root)") if '  no_live_identities(root)' in s else s
s=rep(s," frozen();before=inventory(root);result=check(root)", " from completed_v3 import verify_complete\n verify_complete(root)\n frozen();before=inventory(root);result=check(root)")
new('small_finalize_v3.py',s)
print('VERSIONED_WIRING_WRITTEN_NOT_RUN')
