"""Read-only historical collection; writes only this new diagnostic folder."""
from pathlib import Path
import datetime as dt
import hashlib,json,re,subprocess,sys,time
D=Path(__file__).resolve().parent; R=D.parents[2]
A=R/'docs/deployment-completion-20260916/blank-ui-final-acceptance-0e09edabe3084197b3b7741807475e02'
ROOT=R/'tests/lifecycle_stage1/evidence/TEST-STAGE4-54d0867bae6a4d5b85a687940dbb36fd'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(D/n).write_text(json.dumps(v,indent=2),encoding='utf-8')
def utc(t):return dt.datetime.fromtimestamp(t,dt.timezone.utc).isoformat()
receipt=json.loads((A/'archive-verification.json').read_text());archive=Path(receipt['destination'])
checks=[]
for x in receipt['files']:
 p=A/x['path'];q=archive/x['path'];checks.append({'path':x['path'],'expected':x['sha256'],'local':sha(p),'archive':sha(q),'match':sha(p)==sha(q)==x['sha256']})
checks.append({'path':'archive-verification.json','match':sha(A/'archive-verification.json')==sha(archive/'archive-verification.json'),'local':sha(A/'archive-verification.json'),'archive':sha(archive/'archive-verification.json')})
assert all(x['match'] for x in checks)
pre=json.loads((A/'preflight.json').read_text());sources=[]
for x in pre['source_hashes']:
 p=R/x['path'];sources.append({**x,'current_sha256':sha(p),'match':sha(p)==x['sha256']})
assert all(x['match'] for x in sources)
save('preservation.json',{'at':utc(time.time()),'original':str(A),'archive':str(archive),'original_files_plus_receipt':checks,'source_entries':sources,'no_original_writes':True})
raw=D/'historical';raw.mkdir(exist_ok=False)
inventory=[];events=[];timeline=[]
for p in sorted(ROOT.rglob('*')):
 if p.is_file():
  s=p.stat();row={'path':p.relative_to(ROOT).as_posix(),'bytes':s.st_size,'sha256':sha(p),'mtime_ns':s.st_mtime_ns,'mtime_utc':utc(s.st_mtime_ns/1e9)};inventory.append(row)
  if p.parent==ROOT and (re.match(r'^\d+-\d+-[\w]+\.json$',p.name) or p.name.startswith('coordinator-') or p.name in ('stage4-ready.json','core.json','stop','TEST_ONLY') or p.suffix=='.log'):
   (raw/p.name).write_bytes(p.read_bytes())
   if re.match(r'^\d+-\d+-[\w]+\.json$',p.name):
    e=json.loads(p.read_text());events.append({'path':p.name,'data':e});timeline.append({'utc':utc(int(p.name.split('-')[0])/1e9),'source':p.name,'basis':'event filename wall-clock ns (not OS operation trace)','event':e['kind']})
   if p.name.startswith('coordinator-'):
    v=json.loads(p.read_text());timeline.extend([{'utc':utc((v['peer']['created']-116444736000000000)/1e7),'event':'coordinator process creation','peer':v['peer'],'source':p.name,'basis':'Windows FILETIME'}, {'utc':row['mtime_utc'],'event':'readiness content file last-write','peer':v['peer'],'source':p.name,'basis':'file mtime; NOT exact replace completion or failing read timestamp'}])
save('historical-file-inventory.json',inventory)
save('historical-events.json',events)
records=json.loads((A/'raw-evidence/full-start-crash-restart-restart-campaign-039fa2c9b9794b72b10b208d8095312c.json').read_text())['records']
save('historical-record-extract.json',[{'index':i,**x} for i,x in enumerate(records) if 373<=i<=387 or i==430])
reg=json.loads((A/'regressions.json').read_text())[-1]
timeline.extend([{'utc':utc(reg['started']),'event':'restart command wrapper starts','source':'regressions.json','basis':'wrapper wall clock','pid':reg['pid']}, {'utc':utc(reg['started']+reg['elapsed']),'event':'wrapper observes failed command completion','source':'regressions.json','basis':'start + elapsed; upper bound on original failure/cleanup; not exact failure timestamp'}, {'utc':utc(json.loads((A/'process-census.json').read_text())['at']),'event':'126 historical TEST identities recorded absent','source':'process-census.json','basis':'later census; not proof of normal authenticated cleanup'}])
save('historical-timeline.json',sorted(timeline,key=lambda x:x['utc']))
fail_sources=['stage4_runtime.py','tests/lifecycle_stage4/fixtures.py','tests/lifecycle_stage1/harness.py']
save('source-comparison.json',[{'path':p,'current':sha(R/p),'preserved_failure_source':sha(A/'failure-source'/p),'match':sha(R/p)==sha(A/'failure-source'/p)} for p in fail_sources])
save('git-preflight.json',{'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'tree':subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=R,text=True).strip(),'status':subprocess.check_output(['git','status','--short'],cwd=R,text=True).splitlines(),'staged':subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R,text=True).splitlines()})
print(json.dumps({'historical_files_verified':len(checks),'source_entries_unchanged':len(sources),'historical_inventory_files':len(inventory),'events':len(events),'destination':str(D)}))
