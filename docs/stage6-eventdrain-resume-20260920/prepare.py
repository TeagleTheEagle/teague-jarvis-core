import pathlib,hashlib,json,shutil
R=pathlib.Path(__file__).resolve().parent;O=R.parent/'stage6-heartbeat-stall-diagnosis-20260920'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not (R/'preserved-before.json').exists()
inventory=[dict(path=str(p),sha256=sha(p),size=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns) for p in sorted(O.rglob('*')) if p.is_file()]
(R/'preserved-before.json').write_text(json.dumps(inventory,indent=2))
(R/'source-before').mkdir()
for n in ('monitor.ps1','event_queue.cs','EventTap.cs','LoopTiming.cs','journal.py','workload.py','resources.ps1','J6Probe.exe','queue_tests.cs','test_queue.ps1','collect.py','launch.ps1','analyze.py'):
 shutil.copyfile(O/n,R/n);shutil.copyfile(O/n,R/'source-before'/n)
(R/'source-before.json').write_text(json.dumps([dict(path=str(p),sha256=sha(p)) for p in sorted((R/'source-before').iterdir())],indent=2))
print(json.dumps(dict(preserved=len(inventory),path=str(R))))
