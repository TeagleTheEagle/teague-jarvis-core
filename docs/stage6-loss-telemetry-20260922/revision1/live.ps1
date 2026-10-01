param([Parameter(Mandatory=$true)][ValidateSet('authority','detail','combined')][string]$Mode,[Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{32}$')][string]$RunId)
$ErrorActionPreference='Stop'
$code=$PSScriptRoot;$run=Join-Path $code ('diagnostic-'+$RunId)
if(Test-Path -LiteralPath $run){throw 'Fresh run required'}
New-Item -ItemType Directory -Path $run | Out-Null
New-Item -ItemType Directory -Path (Join-Path $run 'detail') | Out-Null
New-Item -ItemType Directory -Path (Join-Path $run 'temp') | Out-Null
$env:TEMP=Join-Path $run 'temp';$env:TMP=$env:TEMP
function Save($name,$value){$p=Join-Path $run $name;$f=[IO.FileStream]::new($p,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read);try{$b=[Text.Encoding]::UTF8.GetBytes(($value|ConvertTo-Json -Depth 20));$f.Write($b,0,$b.Length);$f.Flush($true)}finally{$f.Dispose()}}
Add-Type -TypeDefinition @'
using System;using System.Runtime.InteropServices;using System.Text;
public static class J6Identity {
 [DllImport("kernel32",SetLastError=true)] public static extern bool GetProcessTimes(IntPtr h,out long c,out long e,out long k,out long u);
 [DllImport("kernel32",CharSet=CharSet.Unicode,SetLastError=true)] public static extern bool QueryFullProcessImageName(IntPtr h,int f,StringBuilder s,ref int n);
}
'@
function Identity($p){[long]$c=0;[long]$e=0;[long]$k=0;[long]$u=0;if(![J6Identity]::GetProcessTimes($p.Handle,[ref]$c,[ref]$e,[ref]$k,[ref]$u)){throw 'Handle creation identity failed'};$b=[Text.StringBuilder]::new(32768);$n=32768;if(![J6Identity]::QueryFullProcessImageName($p.Handle,0,$b,[ref]$n)){throw 'Handle image identity failed'};return @{pid=$p.Id;created=$c.ToString();exitFiletime=$e.ToString();image=$b.ToString();captureQpc=[Diagnostics.Stopwatch]::GetTimestamp()}}
function Ready($p,$path){$s=[Diagnostics.Stopwatch]::StartNew();while(!(Test-Path -LiteralPath $path)){if($p.HasExited -or $s.Elapsed.TotalSeconds -ge 30){throw 'Observer readiness failed'};Start-Sleep -Milliseconds 100}}
$me=Get-Process -Id $PID;$mine=Identity $me
$observers=[Collections.Generic.List[object]]::new();$probes=[Collections.Generic.List[object]]::new();$failure=$null
Save 'declaration.json' @{mode=$Mode;runId=$RunId;root=$mine;diagnosticOnly=$true;acceptance=$false;probeCount=3;hardDeadlineSeconds=13.6;independentWaitSeconds=15;captureSettingsChanged=$false}
try{
 foreach($kind in @('authority','detail')){
  if($Mode -ne 'combined' -and $Mode -ne $kind){continue}
  $folder=$(if($kind -eq 'authority'){$run}else{Join-Path $run 'detail'})
  $exe=Join-Path $code $(if($kind -eq 'authority'){'J6AuthorityTrace.exe'}else{'J6StartupTrace.exe'})
  Write-Output ('OWNER ACTION REQUIRED: approve '+$exe)
  $p=Start-Process -FilePath $exe -ArgumentList @($folder,$PID,$mine.created) -Verb RunAs -WindowStyle Hidden -PassThru
  $observers.Add(@{process=$p;kind=$kind;folder=$folder})
  Ready $p (Join-Path $folder 'etw-ready.json')
  Save ($kind+'-identity.json') (Identity $p)
 }
 # Fixed observation windows exercise periodic queries; not acceptance waits/retries.
 Start-Sleep -Seconds 2
 for($i=0;$i -lt 3;$i++){
  $info=[Diagnostics.ProcessStartInfo]::new((Join-Path $code 'J6TelemetryTest.exe'));$info.WorkingDirectory=$run;$info.UseShellExecute=$false;$info.CreateNoWindow=$true;$info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
  $start=[Diagnostics.Stopwatch]::GetTimestamp();$p=[Diagnostics.Process]::Start($info);$returned=[Diagnostics.Stopwatch]::GetTimestamp()
  $record=@{process=$p;index=$i;launchQpc=$start;createdReturnQpc=$returned};$probes.Add($record)
  $record.identity=Identity $p
  Save ('probe-'+$i+'-created.json') @{identity=$record.identity;launchQpc=$start;createdReturnQpc=$returned}
  $exit=$p.WaitForExit(13600);$observed=[Diagnostics.Stopwatch]::GetTimestamp()
  $record.exited=$exit;$record.observedQpc=$observed
  if(!$exit){throw 'Probe hard deadline exceeded; no retry'}
  $record.exitCode=$p.ExitCode;$record.stdout=$p.StandardOutput.ReadToEnd();$record.stderr=$p.StandardError.ReadToEnd();$record.finalIdentity=Identity $p
  Save ('probe-'+$i+'-exit.json') @{identity=$record.finalIdentity;observedQpc=$observed;exitCode=$record.exitCode;stdout=$record.stdout;stderr=$record.stderr}
  if($p.ExitCode -ne 0){throw 'Diagnostic native workload failed'}
 }
 Start-Sleep -Seconds 2
}catch{$failure=$_.ToString();Save 'failure.json' @{error=$failure}}
finally{
 $cleanup=[Collections.Generic.List[object]]::new()
 foreach($o in (@($observers.ToArray()) | Sort-Object kind -Descending)){
  $stop=Join-Path $o.folder 'etw-stop';$f=[IO.File]::Open($stop,[IO.FileMode]::CreateNew);$f.Dispose()
  $closed=$o.process.WaitForExit(30000)
  $cleanup.Add(@{role=$o.kind;pid=$o.process.Id;exited=$closed;exitCode=$(if($closed){$o.process.ExitCode})})
  if($closed){$o.process.Dispose()}
 }
 foreach($r in $probes){$closed=$r.process.WaitForExit(15000);$cleanup.Add(@{role='probe';pid=$r.process.Id;exited=$closed;exitCode=$(if($closed){$r.process.ExitCode})});if($closed){$r.process.Dispose()}}
 Save 'cleanup.json' @($cleanup.ToArray())
 Save 'result.json' @{failure=$failure;cleanup=@($cleanup.ToArray());mode=$Mode;acceptance=$false;finalQpc=[Diagnostics.Stopwatch]::GetTimestamp()}
}
if($failure){throw 'Diagnostic failed; preserved; no retry'}
Write-Output ('DIAGNOSTIC_CLOSED '+$run)
