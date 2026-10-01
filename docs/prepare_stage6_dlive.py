import pathlib,json,hashlib,shutil,uuid,difflib
DOC=pathlib.Path(__file__).resolve().parent
OLD=DOC/'stage6-eventdrain-resume-20260920';TEST=DOC/'stage6-eventidentity-fix-20260920'
OUT=DOC/'stage6-dlive-20260920';OUT.mkdir(exist_ok=False)
CODE=OUT/'candidate';CODE.mkdir();BEFORE=OUT/'before';BEFORE.mkdir()
names=['monitor.ps1','event_queue.cs','LoopTiming.cs','EventTap.cs','journal.py','workload.py','resources.ps1','J6Probe.exe','queue_tests.cs','test_queue.ps1','collect.py','analyze.py','event_analysis.py']
tests=['finalize.py','process_fixture.py','test_journal.py','test_processes.py','test_finalization.py','test_extended_finalization.py','test_probe_handles.py','test_event_rejection.py','test_queue_finalization.py','test_failure_campaigns.py','queue_crash_fixture.ps1','hash_sources.py']
manifest=[]
for source,ns in ((OLD,names),(TEST,tests)):
 for n in ns:
  p=source/n;data=p.read_bytes();manifest.append(dict(path=str(p),name=n,size=len(data),mtime_ns=p.stat().st_mtime_ns,sha256=hashlib.sha256(data).hexdigest()))
  (CODE/n).write_bytes(data);(BEFORE/n).write_bytes(data)
(OUT/'pre-change-hashes.json').write_text(json.dumps(manifest,indent=2))
campaign=uuid.uuid4().hex;live=pathlib.Path('D:/JARVIS-STAGE6-LIVE')/campaign/'code'
(OUT/'workspace-plan.json').write_text(json.dumps(dict(campaign=campaign,live_code=str(live),archive=r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 D LIVE WORKSPACE 20260920',threshold=10,probe_timeout=5,protected_access=False),indent=2))
def edit(n,fn):
 p=CODE/n;p.write_text(fn(p.read_text(encoding='utf-8-sig')),encoding='utf-8')
def once(s,a,b):
 if a not in s:raise RuntimeError('Missing source anchor '+a)
 return s.replace(a,b,1)
def monitor(s):
 s=once(s,"$ErrorActionPreference='Stop';$root=Join-Path $PSScriptRoot $Run","$ErrorActionPreference='Stop';. (Join-Path $PSScriptRoot 'workspace.ps1');$root=Get-LiveRun $Run;Set-LiveTemp $root")
 s=once(s,"if($config.journalVolume -eq 'D'){$journalPath=Join-Path ('D:\\JARVIS-STAGE6-EVENTDRAIN-20260920\\'+$Run) 'heartbeat.jsonl'}","if($config.journalVolume -ne 'D' -or $config.eventVolume -ne 'D' -or $config.controlVolume -ne 'D'){throw 'D-only live workspace required'}")
 s=once(s,";if($config.eventVolume -eq 'D'){$eventPath=Join-Path ('D:\\JARVIS-STAGE6-EVENTDRAIN-20260920\\'+$Run) 'events.jsonl'}",'')
 return s
edit('monitor.ps1',monitor)
edit('resources.ps1',lambda s:once(s,"$root=Join-Path $PSScriptRoot $Run;",". (Join-Path $PSScriptRoot 'workspace.ps1');$root=Get-LiveRun $Run;Set-LiveTemp $root;"))
def collect(s):
 s=once(s,"R=pathlib.Path(__file__).resolve().parent;run=sys.argv[1];out=R/run","from workspace import CODE as R,run_dir,activate_temp\nrun=sys.argv[1];out=run_dir(run);activate_temp(out)")
 s=once(s,"assert run in ('smoke','a1','a2','a3','minimal','persist-d','none','dhash') and duration in (5,150)","assert mode in ('idle','disk','sustained','cpu','Dhash','dry') and 0<duration<=160")
 s=once(s,"journal=out/'heartbeat.jsonl' if config['journalVolume']=='C' else pathlib.Path('D:/JARVIS-STAGE6-HEARTBEAT-STALL-20260920')/run/'heartbeat.jsonl'","journal=out/'heartbeat.jsonl';assert all(config[k]=='D' for k in ('journalVolume','eventVolume','controlVolume'))")
 s=s.replace("status='DIAGNOSTIC_COLLECTION_COMPLETED'","status='LIVE_MONITOR_HEALTHY'")
 s=once(s,"[sys._base_executable,'-B',str(R/'workload.py'),run,mode,str(duration)]","([sys._base_executable,'-B',str(R/'dry_worker.py'),run] if mode=='dry' else [sys._base_executable,'-B',str(R/'workload.py'),run,mode,str(duration)])")
 # D event/journal paths are already authoritative; no live C copy or fallback.
 start=s.index(" if config.get('eventVolume')=='D':")
 end=s.index(" if code.value:raise",start)
 s=s[:start]+s[end:]
 return s
edit('collect.py',collect)
def workload(s):
 s=once(s,"R=pathlib.Path(__file__).parent","from workspace import CODE as R,run_dir,activate_temp")
 s=once(s,"out=R/run;assert out.is_dir()","out=run_dir(run);activate_temp(out)")
 s=once(s,"source=R.parent/'stage6-heartbeat-journal-20260918'/'sacrificial'/'large.bin'",f"source=pathlib.Path({str(DOC/'stage6-heartbeat-journal-20260918'/'sacrificial'/'large.bin')!r})")
 return s
edit('workload.py',workload)
edit('queue_crash_fixture.ps1',lambda s:once(s,"Add-Type -Path (Join-Path $PSScriptRoot 'event_queue.cs')","Add-Type -Path @((Join-Path $PSScriptRoot 'LoopTiming.cs'),(Join-Path $PSScriptRoot 'event_queue.cs'))"))
edit('finalize.py',lambda s:once(s,"root=pathlib.Path(root).resolve()","from workspace import check_path\n root=check_path(pathlib.Path(root))"))
# Keep all original sources/evidence immutable; write only the new candidate.
groups=[
 ('heartbeat.jsonl','monitor','Reader','each heartbeat/poll','FileStream.Length/Write/Flush(false); stat/read','YES'),
 ('events.jsonl','monitor','offline reconciler','each event','Test-Path/Get-Item.Length/File.AppendAllText','YES'),
 ('case.json;ready.json;monitor-config.json;launch.json;source-hashes.json','launcher/monitor','monitor/collector','startup','read_text/Get-Content/WriteAllText/GetFileHash','startup'),
 ('collector-finished.json;workload-stop','collector','monitor/workload/resource sampler','every loop/block','Test-Path/Path.exists/touch/WriteAllText','YES'),
 ('probes.json;phases.json;collector-samples.json;collector-failure.json;rejected-poll.json','collector','offline verifier','per probe/phase/error/end','write_text/open/json.dump','YES collector'),
 ('monitor-failure.json','monitor','collector','error/per poll','WriteAllText/Path.exists','YES'),
 ('monitor-result.json;monitor-exit.json;retained-handle-verification.json;resource-exit.json;workload-forced-cleanup.json','monitor/collector','finalizer','freeze/cleanup','WriteAllText/open/json.dump','finalization'),
 ('queue-state.json;queue-entries.json;queue-failure.json;tap.json;tap-state.json;pipeline.json;hooks.json','monitor','analysis','startup/final freeze','WriteAllText','startup/finalization'),
 ('loop-trace.json;fine-trace.json;runtime-samples.json;scheduler-observer.json;timing-state.json','monitor','analysis','final freeze','WriteAllText','finalization; trace live in bounded memory'),
 ('resources.json;resources-complete;resource-failure.txt;workload-<mode>.json','sampler/workload','collector/analysis','completion/error','WriteAllText/write_text','completion'),
 ('console.txt;temp/*','launcher/runtime','owner/runtime','stream/temporary','Tee-Object/runtime compilation temp','YES possible'),
 ('source-before.json;source-after.json;baseline-manifest.json;analysis.json;event-analysis.json;storage-correlations.json','dry worker/offline analysis','finalizer','during dry hashing/after freeze','read/write/hash','dry active; analysis offline'),
 ('evidence-manifest.json;EVIDENCE-DURABLY-FINALIZED.json;archive/*;acceptance.json','finalizer','verifier','after monitoring stops','fsync/hash/copy','NO live; D finalization'),
 ]
inventory=[]
for names,writer,reader,freq,ops,critical in groups:inventory.append(dict(files=names,previous_path=str(OLD/'<run>'),previous_volume='C (persist-d events-only exception)',new_path=str(live/'<unique-run>'),new_volume='D',reader=reader,writer=writer,frequency=freq,synchronous_operations=ops,critical_path=critical))
inventory.append(dict(files='monitor/helper code;J6Probe.exe;process-local TEMP/TMP;analysis fixtures',previous_path=str(OLD),new_path=str(live),new_volume='D',reader='monitor/collector/workloads',writer='preparation then immutable code',frequency='load/temporary',synchronous_operations='module load/compilation/process launch',critical_path='startup and probe launch'))
inventory.append(dict(files='installed Python/PowerShell/.NET/Windows components;Windows-managed logging/pagefile/prefetch;C sacrificial input',previous_path='installed C paths',new_path='unchanged',new_volume='C',reader='OS/runtime/workload',writer='OS only; no validation control artifacts',frequency='startup/lazy load/page-in/hash input',synchronous_operations='OS load/paging;read-only fixed test source',critical_path='unavoidable external dependency may affect scheduling; no guarantee of latency; any failure still rejects'))
(OUT/'live-path-inventory.json').write_text(json.dumps(inventory,indent=2))
(OUT/'D1-PATH-REVIEW.md').write_text('# Pre-edit live-path inventory\n\nSee live-path-inventory.json for every grouped literal/dynamic artifact, reader, writer, frequency and synchronous operation. Previous live artifact root was C; the new sole live root is '+str(live)+'.\n\nScripts and fixed probe executable are copied, never moved. No existing evidence is modified. Installed runtimes/Windows components remain C read-only external dependencies; OS-managed writes cannot be redirected comprehensively without forbidden system changes. They are not heartbeat state; any induced latency still fails the existing limits. TEMP/TMP are set for child processes only to D before runtime use; no permanent environment change. Windows logging/prefetch/pagefile remain OS-managed. No protected VM or normal VirtualBox configuration is accessed.\n')
print(json.dumps(dict(candidate=str(CODE),live=str(live),prechange_files=len(manifest))))
