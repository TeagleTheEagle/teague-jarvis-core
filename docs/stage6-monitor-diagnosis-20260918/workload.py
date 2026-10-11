import datetime as dt, hashlib, json, os, pathlib, subprocess, sys, threading, time
R=pathlib.Path(__file__).parent
DATA=R/'synthetic-1GiB.bin'
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def log(name,row):
 with (R/name).open('a',encoding='utf-8') as f:f.write(json.dumps(row)+'\n')
def worker(seconds):
 end=time.monotonic()+seconds;total=0;passes=0
 while time.monotonic()<end and not (R/'stop.json').exists():
  h=hashlib.sha256()
  with DATA.open('rb') as f:
   while time.monotonic()<end and not (R/'stop.json').exists():
    b=f.read(4*1024*1024)
    if not b:passes+=1;break
    h.update(b);total+=len(b)
 log('workers.jsonl',{'PID':os.getpid(),'BytesHashed':total,'CompletePasses':passes,'Utc':utc()})
if len(sys.argv)>1:worker(float(sys.argv[1]));sys.exit()
children=[]
try:
 if DATA.exists():raise RuntimeError('Do not overwrite synthetic file')
 print('Preparing 1 GiB sacrificial file on C:',flush=True)
 with DATA.open('xb') as f:
  for _ in range(128):f.write(os.urandom(8*1024*1024))
 deadline=time.monotonic()+90
 while not (R/'ready.json').exists():
  if (R/'monitor-failure.json').exists() or time.monotonic()>deadline:raise RuntimeError('Monitor not ready')
  time.sleep(.2)
 for phase,duration,count in [('idle',30,0),('single_hasher',90,1),('two_hashers',90,2)]:
  log('phases.jsonl',{'Phase':phase,'Utc':utc(),'Monotonic':time.monotonic(),'Event':'start'})
  print('PHASE '+phase,flush=True)
  children=[subprocess.Popen([sys.executable,'-B',__file__,str(duration)]) for _ in range(count)]
  end=time.monotonic()+duration;next_probe=0;probes=0
  while time.monotonic()<end:
   t0=time.perf_counter();w0=time.time()
   if (R/'monitor-failure.json').exists():raise RuntimeError('Monitor failed')
   h=json.loads((R/'heartbeat.json').read_text())
   t1=time.perf_counter();age=time.time()-dt.datetime.fromisoformat(h['Utc'].replace('Z','+00:00')).timestamp()
   log('observations.jsonl',{'Phase':phase,'Utc':utc(),'ReadStartMonotonic':t0,'ReadEndMonotonic':t1,'WallBefore':w0,'Age':age,'Sequence':h['Sequence'],'MonitorTicks':h['Ticks'],'ObserverCPU':os.times().user+os.times().system})
   if age>10 or h['Violations']:raise RuntimeError('Unchanged 10-second health rule failed')
   if time.monotonic()>=next_probe and probes<20:
    before=utc();p=subprocess.Popen([str(R/'Stage6EventProbe.exe')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);p.wait(timeout=10)
    log('probes.jsonl',{'Phase':phase,'PID':p.pid,'BeforeUtc':before,'AfterUtc':utc(),'ReturnCode':p.returncode})
    next_probe=time.monotonic()+duration/20;probes+=1
   time.sleep(.1)
  for p in children:p.wait(timeout=10)
  children=[]
  log('phases.jsonl',{'Phase':phase,'Utc':utc(),'Event':'end'})
 # Allow queued stop events to drain, without running any VirtualBox executable.
 time.sleep(3)
 (R/'workload-result.json').write_text(json.dumps({'Status':'COMPLETED','Utc':utc()}))
except BaseException as exc:
 (R/'workload-failure.json').write_text(json.dumps({'Status':'BLOCKED','Error':str(exc),'Utc':utc()}))
 raise
finally:
 (R/'stop.json').write_text(json.dumps({'Utc':utc()}))
 for p in children:p.wait(timeout=15)
