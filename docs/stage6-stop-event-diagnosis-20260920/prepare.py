"""E1/E2 preparation. Reads only sacrificial evidence and validation source."""
import datetime as dt,hashlib,json,pathlib,shutil
R=pathlib.Path(__file__).resolve().parent
OLD=R.parent/'stage6-heartbeat-decoupled-20260918'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,v):
 with (R/n).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,sort_keys=True)
def utc(filetime):return (dt.datetime(1601,1,1,tzinfo=dt.timezone.utc)+dt.timedelta(microseconds=int(filetime)//10)).isoformat()
if __name__=='__main__':
 import os
 rows=[]
 def fail(e):raise e
 for base,dirs,files in os.walk(OLD,onerror=fail):
  for n in files:
   p=pathlib.Path(base)/n;s=p.stat();rows.append({'path':str(p.relative_to(OLD)),'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'sha256':sha(p)})
 write('original-inventory.json',sorted(rows,key=lambda r:r['path']))
 d=OLD/'loads2';probes=read(d/'probes.json');events=[json.loads(s) for s in (d/'events.jsonl').read_text().splitlines()];tr=read(d/'loop-trace.json');f=read(d/'ready.json')['frequency']
 beats=[json.loads(s) for s in (d/'heartbeat.jsonl').read_text().splitlines()];anchor=beats[0]
 def qutc(q):return (dt.datetime.fromisoformat(anchor['utc'].replace('Z','+00:00'))+dt.timedelta(seconds=(q-anchor['ticks'])/f)).isoformat()
 freeze=next(t for t in tr if t['stage']=='collection.freeze');missing=[]
 for p in probes:
  if any(e['pid']==p['pid'] and e['kind']=='stop' for e in events):continue
  near=[t for t in tr if abs(t['qpc']-p['end_qpc'])<=10*f and t['stage'] in ('queue.query.end','queue.backlog.end','drain.begin','drain.end','wait.begin','wait.end')]
  missing.append({'probe':p,'created_utc':utc(p['created']),'launch_utc_estimated_from_qpc':qutc(p['start_qpc']),
   'wait_completion_utc_estimated_from_qpc':qutc(p['end_qpc']),'actual_kernel_exit_time':'NOT_RECORDED',
   'normal_exit_evidence':'Popen.wait returned; exit code 0 recorded with retained handle, not current PID absence',
   'start_notifications':[dict(e,notification_utc=utc(e['nativeTime'])) for e in events if e['pid']==p['pid'] and e['kind']=='start'],
   'queue_near_exit':near,'seconds_wait_to_collection_freeze':(freeze['qpc']-p['end_qpc'])/f,
   'last_stop_stage':'UNKNOWN: no historical callback/enqueue trace; no persisted STOP',
   'finalization_freeze_qpc':freeze['qpc'],'finalization_freeze_utc_estimated':qutc(freeze['qpc'])})
 write('historical-missing-identities.json',missing)
 write('historical-shutdown-timeline.json',[dict(t,utc_estimated=qutc(t['qpc'])) for t in tr if t['stage'].startswith(('grace','final.','collection.','durable.','journal.close','unsubscribe'))])
 src=R/'source-snapshot';src.mkdir()
 for n in ('monitor.ps1','campaign.py','journal.py','finalize.py','resources.ps1','workload.py','J6Probe.exe'):
  shutil.copyfile(OLD/n,src/n)
 # The following supporting scripts remain byte-identical; only a new monitor copy will be instrumented.
 for n in ('journal.py','workload.py','resources.ps1','J6Probe.exe'):shutil.copyfile(OLD/n,R/n)
 write('source-hashes.json',[{'path':p.name,'sha256':sha(p)} for p in sorted(src.iterdir())])
 print(json.dumps({'preserved_files':len(rows),'missing':[{k:v for k,v in r.items() if k in ('created_utc','seconds_wait_to_collection_freeze','last_stop_stage','probe')} for r in missing]}))
