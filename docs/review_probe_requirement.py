"""Offline source/evidence review only. Does not launch probes or import harness code."""
import pathlib,json,hashlib,subprocess,os,re,statistics,datetime
DOC=pathlib.Path(__file__).parent;REPO=DOC.parent;R=DOC/'stage6-probe-requirement-review-20260920';R.mkdir(exist_ok=False)
inputs={}
def read(p):
 data=p.read_bytes();inputs[str(p)]=dict(sha256=hashlib.sha256(data).hexdigest(),size=len(data));return json.loads(data.decode('utf-8-sig'))
def text(p):
 data=p.read_bytes();inputs[str(p)]=dict(sha256=hashlib.sha256(data).hexdigest(),size=len(data));return data.decode('utf-8-sig')
def save(n,v):
 with (R/n).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
history=[]
for args in (['log','--all','--oneline','-S','J6Probe','--','docs','tests'],['ls-files','docs/stage6-heartbeat-journal-20260918/dryrun.py','docs/stage6-heartbeat-decoupled-20260918/campaign.py'],['rev-parse','HEAD']):
 q=subprocess.run(['git','-C',str(REPO),*args],capture_output=True,text=True);history.append(dict(command=['git',*args],exit=q.returncode,stdout=q.stdout,stderr=q.stderr))
save('git-history-search.json',history)
files=subprocess.run(['rg','--files',str(DOC),'-g','*.py','-g','*.ps1','-g','*.md'],capture_output=True,text=True,check=True).stdout.splitlines()
locations=[];docrefs=[];scanned=0
for fn in files:
 p=pathlib.Path(fn)
 if p.is_relative_to(R) or any(x in p.parts for x in ('archive','preserved-original')):continue
 # Only validation documentation/source; never VM configuration or protected source trees.
 s=p.read_text(encoding='utf-8-sig',errors='replace');scanned+=1
 for i,line in enumerate(s.splitlines(),1):
  if re.search(r'wait\(timeout\s*=\s*5\)|WaitForExit\(5000\)|WaitForSingleObject\([^\n]*5000',line) and ('J6Probe' in s or 'probe_timing' in s or p.name in ('probe_timing.py','control_timing.py','test_probe_handles.py')):
   locations.append(dict(path=str(p),line=i,text=line,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
  if p.suffix=='.md' and re.search(r'(five[- ]second|5[- ]second|timeout origin|LOCALLY_CHOSEN)',line,re.I) and re.search('probe|timeout|limit',line,re.I):docrefs.append(dict(path=str(p),line=i,text=line))
save('timeout-locations.json',dict(scannedFiles=scanned,definitions=locations,documentation=docrefs,exclusions=['archive directory copies','preserved-original directory copies','binary/VM/configuration files'],note='Executable live D source separately inspected; definitions include repeated diagnostic source snapshots, not independent origin evidence.'))
roots=[DOC/'stage6-eventdrain-resume-20260920',pathlib.Path('D:/JARVIS-STAGE6-LIVE')]
rows={};runs=[];failures=[]
for root in roots:
 for directory,dirs,names in os.walk(root,followlinks=False):
  dirs[:]=[n for n in dirs if n not in ('archive','temp','__pycache__') and not (pathlib.Path(directory)/n).is_symlink() and not (pathlib.Path(directory)/n).is_junction()]
  d=pathlib.Path(directory)
  if 'case.json' not in names or 'retained-handle-verification.json' not in names:continue
  cfg=read(d/'case.json');handles=read(d/'retained-handle-verification.json')
  timings=read(d/'probe-timings.json') if 'probe-timings.json' in names else []
  timing={x['pid']:x for x in timings};evpath=d/'events.jsonl'
  ev=[json.loads(x) for x in text(evpath).splitlines()] if evpath.exists() else []
  hb=[json.loads(x) for x in text(d/'heartbeat.jsonl').splitlines()] if 'heartbeat.jsonl' in names else []
  maxhb=max(((b['ticks']-a['ticks'])/a['frequency'] for a,b in zip(hb,hb[1:])),default=None)
  failure=text(d/'collector-failure.json') if 'collector-failure.json' in names else ''
  runs.append(dict(path=str(d),mode=cfg['mode'],probes=len(handles),maxHeartbeat=maxhb,collectorFailure=bool(failure),timingInstrumented=bool(timings)))
  if 'TimeoutExpired' in failure:failures.append(dict(path=str(d),failure=failure))
  for h in handles:
   ts=h['times'];pid=h['pid'];key=(pid,ts[0]);t=timing.get(pid,{});life=(int(ts[1])-int(ts[0]))/1e7
   if int(ts[1])<=int(ts[0]):raise RuntimeError('Incomplete retained kernel exit')
   row=dict(run=d.name,path=str(d),mode=cfg['mode'],pid=pid,created=ts[0],lifetime=life,exitCode=t.get('actualExitCode',h.get('exit')),createProcessSeconds=(t['createProcessReturnedQpc']-t['createProcessCalledQpc'])/t['frequency'] if t else None,starts=sum(x['pid']==pid and x['kind']=='start' for x in ev),stops=sum(x['pid']==pid and x['kind']=='stop' for x in ev),maxHeartbeat=maxhb,retainedExit=True,timedOut=t.get('timedOut'),kind=t.get('helper','whoami'),record=str(d/'retained-handle-verification.json'),timingRecord=str(d/'probe-timings.json') if t else None)
   if key in rows:
    if abs(rows[key]['lifetime']-life)>1e-9:raise RuntimeError('Conflicting identity evidence')
    continue
   rows[key]=row
def stats(v):
 v=sorted(v);n=len(v)
 def pct(p):
  z=(n-1)*p;i=int(z);return v[i]+(v[min(i+1,n-1)]-v[i])*(z-i)
 return dict(n=n,median=statistics.median(v),p95=pct(.95) if n>=20 else None,p99=pct(.99) if n>=100 else None,max=max(v),above5=sum(x>5 for x in v),above10=sum(x>10 for x in v)) if v else None
values=list(rows.values());slow=[r for r in values if r['lifetime']>5]
# Main comparison uses unchanged whoami D: instrumented diagnosis, plus finalization campaign.
codes={'fb8ef11d2c4d44cca4d352d4a9fdfc93','0c5c564771a0475da2d8da4d655574e9'}
comparisons=[r for r in values if any(x in r['path'] for x in codes)]
distributions={m:stats([r['lifetime'] for r in comparisons if r['mode']==m]) for m in ('idle','disk','sustained','cpu','Dhash')}
save('probe-evidence.json',dict(runs=runs,uniqueProbes=len(values),slowIncidents=slow,timeoutFailures=failures,rows=values))
save('lifetime-distributions.json',dict(cohort='Preserved unchanged whoami D-workspace instrumented diagnosis plus latest finalization campaign; not fresh runs. Truncated at first failure, nonrandomized, not unbiased tail estimates.',distributions=distributions,wholeHistoricalMaximum=max(r['lifetime'] for r in values),allKnownAbove5=len(slow),allKnownAbove10=sum(r['lifetime']>10 for r in values)))
# Read exact current sources and preserve line-addressable audit extracts.
current=pathlib.Path('D:/JARVIS-STAGE6-LIVE/0c5c564771a0475da2d8da4d655574e9/code')
for name in ('probe_timing.py','collect.py','FinalizationGate.cs','accept_run.py','journal.py','test_probe_handles.py'):
 s=text(current/name);(R/(name+'.numbered.txt')).write_text(''.join(f'{i}: {line}\n' for i,line in enumerate(s.splitlines(),1)),encoding='utf-8')
stdlib=pathlib.Path(r'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\subprocess.py')
ss=text(stdlib).splitlines();save('stdlib-wait.json',dict(path=str(stdlib),public=[dict(line=i+1,text=ss[i]) for i in range(1257,1280)],windows=[dict(line=i+1,text=ss[i]) for i in range(1578,1597)]))
save('read-input-hashes.json',inputs)
print(json.dumps(dict(report=str(R),definitions=len(locations),documentation=len(docrefs),historicalProbes=len(values),slow=slow,distributions=distributions),indent=2))
