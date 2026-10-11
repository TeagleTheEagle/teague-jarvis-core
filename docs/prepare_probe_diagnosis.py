import pathlib,json,uuid,hashlib,shutil,inspect,subprocess,sys,pefile
DOC=pathlib.Path(__file__).resolve().parent;R=DOC/'stage6-probe-diagnosis-20260920';R.mkdir(exist_ok=False);C=R/'candidate';C.mkdir()
OLD=pathlib.Path('D:/JARVIS-STAGE6-LIVE/ab1566cc23dd43cab43afef00cba5940/code')
names=['monitor.ps1','workspace.py','workspace.ps1','journal.py','event_queue.cs','LoopTiming.cs','EventTap.cs','workload.py','resources.ps1','J6Probe.exe','collect.py','analyze.py','event_analysis.py','queue_tests.cs','test_queue.ps1']
manifest=[]
for n in names:
 p=OLD/n;b=p.read_bytes();(C/n).write_bytes(b);manifest.append(dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),size=len(b),mtime_ns=p.stat().st_mtime_ns))
(R/'source-before.json').write_text(json.dumps(manifest,indent=2))
campaign=uuid.uuid4().hex;live=pathlib.Path('D:/JARVIS-STAGE6-LIVE')/campaign/'code'
(R/'plan.json').write_text(json.dumps(dict(live_code=str(live),archive=r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 PROBE DIAGNOSIS 20260920',runs=[['idle',120],['disk',100],['sustained',150],['cpu',40],['Dhash',90],['sustained',150],['sustained',150]],acceptance=False),indent=2))
pe=pefile.PE(str(C/'J6Probe.exe'))
(R/'binary-imports.json').write_text(json.dumps({e.dll.decode():[i.name.decode() if i.name else 'ordinal:'+str(i.ordinal) for i in e.imports] for e in pe.DIRECTORY_ENTRY_IMPORT},indent=2))
(R/'python-wait-source.txt').write_text(sys.version+'\n'+sys._base_executable+'\n'+inspect.getsource(subprocess.Popen.wait)+inspect.getsource(subprocess.Popen._wait))
(R/'python-create-source.txt').write_text(inspect.getsource(subprocess.Popen._execute_child))
s=(C/'collect.py').read_text();s=s.replace('from workspace import CODE as R,run_dir,activate_temp','from workspace import CODE as R,run_dir,activate_temp\nfrom probe_timing import Probe')
s=s.replace("samples=[];probes=[];handles=[];child=None", "samples=[];probes=[];handles=[];measured=[];child=None")
start=s.index("   t=ticks();p=subprocess.Popen([str(R/'J6Probe.exe')]")
end=s.index("   if any(x['pid']==p.pid",start)
s=s[:start]+'''   measured_probe=Probe(R/'J6Probe.exe');measured.append(measured_probe)
   p=measured_probe.process;handles.append(p);t=measured_probe.row['launchRequestedQpc']
   created=times(p)[0]
   code=measured_probe.wait_original();ts=times(p)
'''+s[end:]
s=s.replace("save('probes.json',probes);last=time.monotonic()-began", "save('probes.json',probes);measured_probe.row['recordPersistedQpc']=ticks();last=time.monotonic()-began")
s=s.replace(" verified=[]", " for measurement in measured:measurement.finish_observation()\n save('probe-timings.json',[m.row for m in measured])\n verified=[]")
(C/'collect.py').write_text(s)
(R/'PLAN.md').write_text('''# Probe diagnosis only

New D workspace; original D monitor/queue/Reader/workload remain byte-identical. Only the copied collector adds QPC brackets and an independent native handle-wait observer. The original Popen.wait(timeout=5) call remains authoritative and any timeout latches failure. The independent observer has a separate 15-second evidence-collection bound and cannot turn a timeout into success. Following an observed timeout, stop that case, reconcile all retained handles, and only continue a preplanned independent diagnostic case after cleanup. Stop the entire campaign if cleanup is uncertain, a VBox event occurs, monitor errors or identity ambiguity occurs. No acceptance, dry runs or protected hashing.

Seven preplanned cases: idle 120s, C reads 100s, C hash 150s, CPU 40s, D hash 90s, C hash 150s, C hash 150s. Three C hash cases are diagnostic reproduction attempts, NOT the suspended three-run acceptance gate. Probes retain original one-second cadence and DEVNULL stdout/stderr. No output content is captured. A timed-out case may end early and must be reported as truncated; do not retry it away. No alternate probe executable: current probe is already native; P6's managed-runtime condition does not apply. Native loader/work/exit timestamps are unavailable without further instrumentation and will not be invented.

Monotonic timings: request Popen; Popen return; handle identity capture; main wait entry/return or timeout; zero-time handle state immediately after timeout; independent observer wait entry/signaled observation; kernel FILETIME creation/exit plus QPC/UTC bridge; successful record persistence. Kernel process creation is not first user instruction. Kernel exit FILETIME is not exact caller wait wakeup. Bridges record sampling uncertainty and clock drift; no unmeasured T2–T5 timestamps will be claimed.
''')
print(json.dumps(dict(root=str(R),live=str(live))))
