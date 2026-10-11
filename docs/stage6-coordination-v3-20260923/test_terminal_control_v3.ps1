param([Parameter(Mandatory=$true)][string]$Candidate,[Parameter(Mandatory=$true)][string]$Fixture)
$ErrorActionPreference='Stop'
. (Join-Path $Candidate 'terminal_control_v3.ps1')
$v=Get-Content -LiteralPath $Fixture -Raw|ConvertFrom-Json -AsHashtable
$phase=$v[0];$receipt=$v[1];$native=$v[2];$script:checks=0
$root=Split-Path -Parent $Fixture
# Deliberate offline seams: no processes, CIM queries, tracing or launcher execution.
function Now {1125}
function Hash($name){'d'*64}
function ReadRecord($name){$native}
AssertTerminal $receipt;$script:checks++
function Bad($mutate){
 $script:receipt=($v[1]|ConvertTo-Json -Depth 20 -Compress|ConvertFrom-Json -AsHashtable)
 & $mutate
 $caught=$false;try{AssertTerminal $script:receipt}catch{$caught=$true}
 if(!$caught){throw 'Invalid terminal evidence accepted by actual PowerShell gate'}
 $script:checks++
}
Bad {$script:receipt.rows[1].created='1002'}
Bad {$script:receipt.rows[1].parentSequence='999'}
Bad {$script:receipt.rows[1].handleImage='D:\wrong.exe'}
Bad {$script:receipt.rows[1].stopQpc=0}
Bad {$script:receipt.rows[1].signalObservedQpc=3001}
Bad {$script:receipt.rows[1].handleAttemptQpc=1021}
Bad {$script:receipt.binding.run='stale'}
Bad {$script:receipt.phaseASHA256='e'*64}
Bad {$script:receipt.observer.pid=21}
Bad {$script:receipt.sequence=2}
Bad {$script:receipt.deadlineQpc=4000}
Bad {$script:receipt.faults=1}
Bad {$script:receipt.rows[0].exitCode=1}
$caught=$false;$doc=[Text.Json.JsonDocument]::Parse('{"a":1,"a":2}')
try{CheckJson $doc.RootElement}catch{$caught=$true}finally{$doc.Dispose()}
if(!$caught){throw 'Duplicate key accepted'};$script:checks++
$management=@($phase.authorityObserver);$script:nativeCreated=900
function Get-Process($Id,$ErrorAction){
 if($Id -in @(10,11)){return $null}
 $p=[pscustomobject]@{StartTime=[DateTime]::FromFileTimeUtc($script:nativeCreated);HasExited=$false}
 $p|Add-Member ScriptMethod Dispose {};return $p
}
function Get-CimInstance($ClassName,$OperationTimeoutSec,$ErrorAction){
 return [pscustomobject]@{Name='J6AuthorityTraceV3.exe';ProcessId=20;CreationDate=[DateTime]::FromFileTimeUtc(890);CommandLine='fixed synthetic TEST observer'}
}
function Save($name,$value){$script:savedCensus=$value}
WorkloadCensus $v[1]
if($script:savedCensus.matchingProcesses[0].created -cne '900'){throw 'Native census identity not preserved'};$script:checks++
$script:nativeCreated=901;$caught=$false;try{WorkloadCensus $v[1]}catch{$caught=$true}
if(!$caught){throw 'Reused PID accepted'};$script:checks++
"OFFLINE_POWERSHELL_GATE_CHECKS $script:checks PASS; native-identity seams, no live observers or census"
