import pathlib,hashlib,json,shutil,difflib
R=pathlib.Path(__file__).resolve().parent;O=R.parent/'stage6-eventidentity-fix-20260920'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not (R/'preserved-before.json').exists()
inventory=[dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns) for p in sorted(O.rglob('*')) if p.is_file()]
(R/'preserved-before.json').write_text(json.dumps(inventory,indent=2))
(R/'source-snapshot').mkdir()
for n in ('monitor.ps1','event_queue.cs','EventTap.cs','journal.py','workload.py','resources.ps1','J6Probe.exe','queue_tests.cs','test_queue.ps1'):
 shutil.copyfile(O/n,R/'source-snapshot'/n);shutil.copyfile(O/n,R/n)
shutil.copyfile(O/'reconcile_run.py',R/'reconcile_run.py')
(R/'source-before.json').write_text(json.dumps([dict(path=str(p),sha256=sha(p)) for p in sorted((R/'source-snapshot').iterdir())],indent=2))
# Timings only around the existing identical lock / append / exact-index logic.
p=R/'event_queue.cs';s=p.read_text().replace('lock(queue.SyncRoot)','using(LoopTiming.Lock(queue.SyncRoot))')
s=s.replace('try {File.AppendAllText(path,serialized);}', 'try {using(LoopTiming.Span("event.File.AppendAllText")){File.AppendAllText(path,serialized);}}')
s=s.replace('queue.RemoveAt(Index(e));','using(LoopTiming.Span("queue.exact.RemoveAt")){queue.RemoveAt(Index(e));}')
p.write_text(s)
p=R/'monitor.ps1';s=p.read_text()
s=s.replace("param([ValidatePattern('^[a-z0-9-]+$')][string]$Run)","param([ValidatePattern('^[a-z0-9-]+$')][string]$Run)")
s=s.replace("Add-Type -Path (Join-Path $PSScriptRoot 'event_queue.cs')", "Add-Type -Path @((Join-Path $PSScriptRoot 'LoopTiming.cs'),(Join-Path $PSScriptRoot 'event_queue.cs'))\n$config=Get-Content -LiteralPath (Join-Path $root 'case.json') -Raw|ConvertFrom-Json\n$journalPath=Join-Path $root 'heartbeat.jsonl'\nif($config.journalVolume -eq 'D'){$journalPath=Join-Path ('D:\\JARVIS-STAGE6-HEARTBEAT-STALL-20260920\\'+$Run) 'heartbeat.jsonl'}\n[LoopTiming]::StartObserver()")
s=s.replace("$trace.Add(@{qpc=[Diagnostics.Stopwatch]::GetTimestamp();seq=$script:seq;stage=$stage;detail=$detail})", "$trace.Add(@{qpc=[Diagnostics.Stopwatch]::GetTimestamp();seq=$script:seq;stage=$stage;detail=$detail})\n [LoopTiming]::Note($stage)")
s=s.replace("while($null -ne ($entry=$exact.Select())){", "while($true){\n  Mark 'queue.select.begin';$entry=$exact.Select();Mark 'queue.select.end'\n  if($null -eq $entry){break}")
s=s.replace("$eventPath=Join-Path $root 'events.jsonl'", "Mark 'event.path.begin';$eventPath=Join-Path $root 'events.jsonl';Mark 'event.path.end'")
s=s.replace("if((Test-Path -LiteralPath $eventPath) -and (Get-Item -LiteralPath $eventPath).Length -gt 1044480){throw 'Event capacity reached'}", "Mark 'event.exists.begin';$exists=Test-Path -LiteralPath $eventPath;Mark 'event.exists.end'\n   if($exists){Mark 'event.stat.begin';$length=(Get-Item -LiteralPath $eventPath).Length;Mark 'event.stat.end';if($length -gt 1044480){throw 'Event capacity reached'}}")
s=s.replace("(Join-Path $root 'heartbeat.jsonl'),[IO.FileMode]", "$journalPath,[IO.FileMode]")
s=s.replace("Mark 'loop.begin';if([EventTap]::Errors -or [EventTap]::Overflow){throw 'Diagnostic hook error/overflow'};Drain", "Mark 'loop.begin';Mark 'health.begin';if([EventTap]::Errors -or [EventTap]::Overflow -or [LoopTiming]::Overflow){throw 'Diagnostic hook error/overflow'};Mark 'health.end';Drain")
s=s.replace("Mark 'finish.query.begin';", "Mark 'runtime.telemetry.begin';if($config.telemetry -eq 'full'){[LoopTiming]::RuntimeSample()};Mark 'runtime.telemetry.end'\n  Mark 'finish.query.begin';")
s=s.replace("Save 'loop-trace.json' @($trace.ToArray())", "[LoopTiming]::StopObserver()\n Save 'loop-trace.json' @($trace.ToArray())\n Save 'fine-trace.json' @([LoopTiming]::Snapshot())\n Save 'runtime-samples.json' @([LoopTiming]::RuntimeSnapshot())\n Save 'scheduler-observer.json' @([LoopTiming]::ObserverSnapshot())\n Save 'timing-state.json' @{overflow=[LoopTiming]::Overflow;journalPath=$journalPath;telemetry=$config.telemetry;observerMeaning='100ms independent diagnostic sleep observer, not a health publisher; jitter is not proof of CPU starvation'}")
p.write_text(s)
# Same collision tests against timing-instrumented helper.
p=R/'test_queue.ps1';s=p.read_text().replace("@((Join-Path $PSScriptRoot 'event_queue.cs'),", "@((Join-Path $PSScriptRoot 'LoopTiming.cs'),(Join-Path $PSScriptRoot 'event_queue.cs'),")
p.write_text(s)
# Telemetry remains a separate process; record its own stage latency and extra counters.
p=R/'resources.ps1';s=p.read_text().replace("$c=Get-Counter", "$counterStart=[Diagnostics.Stopwatch]::GetTimestamp();$c=Get-Counter")
s=s.replace("'\\Memory\\Pages/sec'", "'\\Memory\\Pages/sec','\\Memory\\Page Faults/sec'")
s=s.replace("$p=@(Get-Process", "$counterEnd=[Diagnostics.Stopwatch]::GetTimestamp();$processStart=$counterEnd\n  $p=@(Get-Process")
s=s.replace("qpc=$q;endQpc=", "qpc=$q;counterStart=$counterStart;counterEnd=$counterEnd;processStart=$processStart;endQpc=")
p.write_text(s)
# Immutable workload script writes control/results beside itself on C:, all cases keep this constant.
(R/'instrumentation.diff').write_text(''.join(''.join(difflib.unified_diff((R/'source-snapshot'/n).read_text().splitlines(True),(R/n).read_text().splitlines(True),fromfile='frozen/'+n,tofile='diagnostic/'+n)) for n in ('monitor.ps1','event_queue.cs','resources.ps1','test_queue.ps1')))
print(json.dumps(dict(preserved=len(inventory),path=str(R))))
