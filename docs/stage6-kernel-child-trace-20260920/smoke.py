import pathlib,sys,subprocess,time,json,os
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from probe_timing import process_times
root=pathlib.Path(sys.argv[1]); code=pathlib.Path(__file__).parent
records=[]
for i in range(10):
    start=time.perf_counter_ns()
    p=subprocess.Popen([str(code/'J6Probe.exe')],cwd=code,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,close_fds=True,creationflags=0x08000000)
    returned=time.perf_counter_ns(); before=process_times(p)
    try:p.wait(timeout=13.6)
    except subprocess.TimeoutExpired:
        records.append(dict(pid=p.pid,failure='HARD_DEADLINE',before=before));break
    records.append(dict(pid=p.pid,parentPid=os.getpid(),launchNs=start,returnNs=returned,observedExitNs=time.perf_counter_ns(),times=process_times(p),exit=p.returncode))
    time.sleep(.15)
with (root/'explicit-launches.json').open('x') as f:json.dump(records,f,indent=2)
print(json.dumps(dict(count=len(records),pids=[r['pid'] for r in records])))
