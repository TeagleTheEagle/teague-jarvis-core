# Fixed TEST run evidence only; dot-sourced by the versioned launcher.
function Need($ok,$why){if(!$ok){throw $why}}
function Now{[Diagnostics.Stopwatch]::GetTimestamp()}
function Hash($name){(Get-FileHash -LiteralPath (Join-Path $root $name) -Algorithm SHA256).Hash.ToLowerInvariant()}
function CheckJson($node){
 if($node.ValueKind -eq [Text.Json.JsonValueKind]::Object){$keys=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal);foreach($p in $node.EnumerateObject()){Need ($keys.Add($p.Name)) 'Duplicate JSON key';CheckJson $p.Value}}
 elseif($node.ValueKind -eq [Text.Json.JsonValueKind]::Array){foreach($p in $node.EnumerateArray()){CheckJson $p}}
}
function ReadRecord($name){
 Need ($name -notmatch '[\\/:]' -and $name -notin @('.','..')) 'Fixed artifact only'
 $path=Join-Path $root $name;$f=Get-Item -LiteralPath $path
 Need ($f.Length -gt 0 -and $f.Length -le 1048576 -and !($f.Attributes -band [IO.FileAttributes]::ReparsePoint)) 'Record bound/path'
 $raw=[IO.File]::ReadAllText($path);$doc=[Text.Json.JsonDocument]::Parse($raw)
 try{CheckJson $doc.RootElement}finally{$doc.Dispose()}
 return ($raw|ConvertFrom-Json -AsHashtable)
}
function Budget{
 Need (!(Test-Path -LiteralPath (Join-Path $root 'rejected-v3.json'))) 'Permanent rejection'
 Need ($null -ne $script:phase) 'Phase A unavailable'
 Need ($phase.deadlineQpc -eq $phase.cleanupEntryQpc+20*$phase.binding.frequency) 'Deadline reset'
 $left=($phase.deadlineQpc-(Now))/$phase.binding.frequency;Need ($left -gt 0) 'Absolute cleanup deadline exceeded';return $left
}
function Same($a,$b){return ($a.pid -eq $b.pid -and $a.created -ceq $b.created)}
function State($name,$detail){[void](Budget);Mark $name $detail}
function WaitEvidence($name){
 while(!(Test-Path -LiteralPath (Join-Path $root $name))){
  [void](Budget)
  Need (!$kernel.HasExited -and !$detail.HasExited -and !$app.HasExited) 'Observer failed during terminal phase'
  Need (!(Test-Path -LiteralPath (Join-Path $root 'terminal-failure-v3.json'))) 'Authority terminal failure'
  Start-Sleep -Milliseconds ([Math]::Max(1,[Math]::Min(20,[Math]::Floor((Budget)*1000))))
 }
 [void](Budget);return ReadRecord $name
}
function AssertTerminal($r){
 [void](Budget)
 Need ($r.schema -ceq 'stage6-terminal-v3' -and $r.kind -ceq 'workload-terminal' -and $r.sequence -eq 1) 'Receipt schema'
 Need ($r.phaseASHA256 -ceq (Hash 'phase-a-v3.json')) 'Stale Phase A'
 foreach($k in @('schema','run','declarationSHA256','sourceManifestSHA256','kernelSession','observerSHA256','frequency')){Need ($r.binding[$k] -ceq $phase.binding[$k]) ('Receipt binding '+$k)}
 Need ($r.cleanupEntryQpc -eq $phase.cleanupEntryQpc -and $r.deadlineQpc -eq $phase.deadlineQpc) 'Receipt deadline'
 Need ((Same $r.observer $phase.authorityObserver) -and $r.observer.image -ieq $phase.authorityObserver.image) 'Receipt observer'
 Need ($r.faults -eq 0 -and $r.eventsLost -eq 0 -and $r.buffersLost -eq 0 -and $r.coordinationOnly -eq $true -and $r.acceptance -eq $false) 'Receipt failure'
 $expected=@($phase.collector)+@($phase.helpers);Need ($r.rows.Count -eq $expected.Count) 'Receipt completeness'
 $seq=[Collections.Generic.HashSet[string]]::new()
 foreach($want in $expected){
  $xs=@($r.rows|Where-Object {Same $_ $want});Need ($xs.Count -eq 1) 'Exact process instance missing';$x=$xs[0]
  Need ($seq.Add([string]$x.sequence) -and [UInt64]$x.sequence -gt 0) 'Sequence identity'
  Need ($x.handleCreated -ceq $want.created -and $x.handleImage -ieq $want.image -and $x.handleRetained -eq $true -and $x.imageError -eq 0 -and $x.metadataError -eq 0) 'Handle identity/image'
  Need ($x.stopQpc -gt $x.startQpc -and $x.stopQpc -lt $phase.deadlineQpc -and $x.signalObservedQpc -ge $x.handleAttemptQpc -and $x.signalObservedQpc -lt $phase.deadlineQpc -and $x.imageEndQpc -lt $x.stopQpc -and $x.stopCallbackQpc -le $r.capturedQpc) 'Terminal timing'
  Need ($x.exitFiletime -ceq $x.kernelExitFiletime -and $x.exitCode -eq $x.kernelExitCode) 'Terminal contradiction'
  if(!(Same $want $phase.collector)){
   $parent=@($r.rows|Where-Object {Same $_ $phase.collector})[0]
   Need ($x.parentPid -eq $parent.pid -and $x.parentSequence -ceq $parent.sequence -and $x.handleAttemptQpc -lt $want.localCloseQpc -and $x.imageBeginQpc -lt $want.localCloseQpc -and $want.localClosed -eq $true) 'Parent/handoff'
  }else{
   $n=ReadRecord ('native-'+$x.pid+'-'+$x.created+'.json')
   Need ((Same $n $x) -and $n.finalWait -eq 0 -and !$n.fault -and !$n.deadlineExceeded -and $n.exitCode -eq 0 -and $x.exitCode -eq 0 -and $n.exitFiletime -ceq $x.exitFiletime -and $n.entryQpc -ge $x.startQpc -and $n.entryQpc -lt $x.stopQpc) 'Collector native terminal proof'
  }
 }
 Need ($r.capturedQpc -le (Now)) 'Future receipt'
}
function WorkloadCensus($receipt){
 [void](Budget)
 foreach($x in $receipt.rows){
  $p=Get-Process -Id $x.pid -ErrorAction SilentlyContinue
  if($p){try{Need ($p.StartTime.ToUniversalTime().ToFileTimeUtc().ToString() -cne $x.created -or $p.HasExited) 'Workload remains'}finally{$p.Dispose()}}
 }
 # Broad query is read-only; unavailable identity fields are failures, not zero.
 $seconds=[Math]::Floor((Budget));Need ($seconds -ge 1) 'Insufficient census budget'
 $all=@(Get-CimInstance Win32_Process -OperationTimeoutSec ([Math]::Min(10,$seconds)) -ErrorAction Stop)
 $expected=@($script:management)
 $found=@()
 foreach($p in $all){
  $match=$p.Name -match '^(J6|VBox|VirtualBox)' -or ($p.Name -match '^(python|pwsh|powershell)' -and $p.CommandLine -like '*D:\JARVIS-STAGE6-LIVE*')
  if($match){
   $nativeProcess=Get-Process -Id $p.ProcessId -ErrorAction Stop
   try{$nativeCreated=$nativeProcess.StartTime.ToUniversalTime().ToFileTimeUtc().ToString()}finally{$nativeProcess.Dispose()}
   $known=@($expected|Where-Object {$_.pid -eq $p.ProcessId -and $_.created -ceq $nativeCreated})
   Need ($known.Count -eq 1) 'Unexpected live diagnostic process';$found+=,$known[0]
  }
 }
 Need ($found.Count -eq $expected.Count) 'Management census incomplete'
 $v=@{kind='workload-only';binding=$phase.binding;available=$true;unknown=@();workloadRemaining=@();matchingProcesses=$expected;expectedManagement=$expected;completedQpc=(Now)}
 [void](Budget);Save 'workload-census-v3.json' $v
}
function ExitBounded($p,$limit,$role){
 $ms=[Math]::Floor([Math]::Min($limit,(Budget))*1000);Need ($ms -gt 0) 'No shutdown budget'
 Need ($p.WaitForExit([int]$ms)) ($role+' shutdown deadline');[void](Budget)
 Need ($p.ExitCode -eq 0) ($role+' observer failure')
 return @{pid=$p.Id;created=$p.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();exitQpc=(Now);exitCode=$p.ExitCode;exitVerified=$true}
}
