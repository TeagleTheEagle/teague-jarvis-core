"""Offline-only fixed benchmark protocol. No ETW sessions or elevated observers."""
import pathlib,subprocess,json,math,statistics,hashlib,datetime
R=pathlib.Path(__file__).parent
C=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\a34f91e1db274bf78fc5a80e2a9d417c\code')
exe=C/'J6MeasurementFixtureV3.exe'
def put(n,x):
 with (R/n).open('x') as f:json.dump(x,f,indent=2)
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
for mode in ('tests','benchmark'):
 out=R/(mode+'.jsonl');err=R/(mode+'-stderr.txt')
 with out.open('xb') as o,err.open('xb') as e:
  p=subprocess.Popen([str(exe),mode],cwd=C,stdout=o,stderr=e)
  put(mode+'-process.json',dict(pid=p.pid,executable=str(exe),sha256=sha(exe),mode=mode,startedUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),liveETW=False))
  code=p.wait()
 put(mode+'-exit.json',dict(exitCode=code,pid=p.pid,observedExitUtc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
 print(mode,code,flush=True)
 if code:
  put('screen-result.json',dict(status='MEASUREMENT_OVERHEAD_CONFLICT' if mode=='benchmark' else 'FINAL_TRACE_MEASUREMENT_DEFECTIVE',reason='Offline fixture could not complete; no overhead inference',exitCode=code));raise SystemExit(code)
rows=[json.loads(s) for s in (R/'benchmark.jsonl').read_text().splitlines()]
trials=[r for r in rows if r['kind']=='trial'];assert len(trials)==16
pairs=[]
for i in range(8):
 a=next(r for r in trials if r['pair']==i and not r['enabled']);b=next(r for r in trials if r['pair']==i and r['enabled'])
 assert a['callbacks']==b['callbacks'] and a['dispatcherCpu100ns']>0
 pairs.append(dict(pair=i,additionalCpuPercent=100*(b['dispatcherCpu100ns']/a['dispatcherCpu100ns']-1),allocationDelta=b['allocations']-a['allocations'],off=a,on=b))
values=[p['additionalCpuPercent'] for p in pairs];mean=statistics.mean(values);sd=statistics.stdev(values);half=2.364624*sd/math.sqrt(8)
# Predeclared conservative gate: entire paired 95% interval must be <=1%; interval halfwidth <=1 percentage point.
reliable=half<=1 and all(p['off']['dispatcherCpu100ns']>=20000000 and p['on']['dispatcherCpu100ns']>=20000000 for p in pairs)
passed=reliable and mean+half<=1 and all(p['allocationDelta']==0 for p in pairs)
result=dict(status='SCREEN_PASS' if passed else 'MEASUREMENT_OVERHEAD_CONFLICT',executableSHA256=sha(exe),pairs=pairs,meanAdditionalCpuPercent=mean,paired95PercentInterval=[mean-half,mean+half],intervalHalfwidthPercentagePoints=half,reliableForOnePercentScreen=reliable,budgetPercent=1,scope='Recorder feasibility screen only; not integrated observer acceptance',liveETW=False,UAC=False)
put('screen-result.json',result)
print(json.dumps({k:v for k,v in result.items() if k!='pairs'}),flush=True)
