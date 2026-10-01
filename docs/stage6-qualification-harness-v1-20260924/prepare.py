import pathlib,json,hashlib,shutil
R=pathlib.Path(__file__).parent;D=R.parent
P=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\a34f91e1db274bf78fc5a80e2a9d417c\code')
S=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\timestamp-reuse-v1-20260924')
C=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\qualification-harness-v1-20260924')
def load(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with pathlib.Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def rec(p):
 p=pathlib.Path(p);s=p.stat();assert not s.st_file_attributes&0x400
 h=sha(p);t=p.stat();assert (s.st_size,s.st_mtime_ns)==(t.st_size,t.st_mtime_ns)
 return dict(path=str(p),sha256=h,bytes=s.st_size,mtimeNs=s.st_mtime_ns)
def write(p,obj):
 with pathlib.Path(p).open('x',encoding='utf8') as f:json.dump(obj,f,indent=2)
def function(text,marker):
 start=text.index(marker);begin=text.index('{',start);depth=0
 for i in range(begin,len(text)):
  depth+=int(text[i]=='{')-int(text[i]=='}')
  if not depth:return text[start:i+1]
 raise AssertionError(marker)
if __name__=='__main__':
 assert not C.exists()
 inputs={}
 def keep(x):
  a=rec(x['path']);assert a==x,x['path'];inputs[x['path']]=a
 for x in load(D/'stage6-timestamp-reuse-v1-20260924'/'before.json')['inputs']:keep(x)
 for x in load(D/'stage6-timestamp-reuse-v1-20260924'/'final-candidate-manifest.json')['files']:keep(x)
 for name in ['stage6-timestamp-reuse-v1-20260924','stage6-final-overhead-preflight-20260924']:
  for p in sorted((D/name).iterdir()):
   if p.is_file():inputs[str(p)]=rec(p)
 write(R/'before.json',dict(inputs=list(inputs.values()),workspace=str(C),benchmarkExecuted=False))
 C.mkdir();(C/'temp').mkdir()
 arms=[('A',P),('B',S/'reference'),('C',S/'code')]
 binding=[]
 for arm,base in arms:
  dest=C/arm;dest.mkdir()
  for name in ['trace_telemetry.hpp','loss_diagnostic_v2.hpp']+([] if arm=='A' else ['loss_measurement_v3.hpp']):
   shutil.copy2(base/name,dest/name);binding.append(dict(arm=arm,source=rec(base/name),copy=rec(dest/name)))
  # The reference differs only in its timer; both instrumented selector bodies are the accepted successor.
  selector=P if arm=='A' else S/'code'
  for kind,file in [('authority','authority_trace_v3.cpp'),('detail','startup_trace.cpp')]:
   source=(selector/file).read_text();body=''
   if kind=='detail':
    body+=function(source,'static void LifecycleEvent')+'\n'
    outer=function(source,'static void WINAPI Event')
    # Lifecycle event IDs exit here. Keep the exact prefix; unrelated detail events use explicit out-of-scope controls.
    body+=outer[:outer.index('  if(sched&&op!=36&&op!=50)return;')]+'  return; }catch(...){++faults;'+('timing.lifecycle.exception();' if arm!='A' else '')+'}\n}\n'
   else:body=function(source,'static void WINAPI Event')+'\n'
   (dest/f'{kind}.inc').write_text(body)
   binding.append(dict(arm=arm,kind=kind,selectorSource=rec(selector/file),extracted=rec(dest/f'{kind}.inc')))
 write(R/'source-binding.json',binding)
 protocol=dict(schema='j6.final-overhead.protocol.v1',arms={'A':'unchanged predecessor baseline','B':'separate-clock reference','C':'semantic timestamp reuse'},primaryComparison='C/A-1',requestAlias={'baseline A':'protocol A','optimized B':'protocol C'},schedule=['ABC','BCA','CAB','ACB','CBA','BAC']*10,blocks=60,warmupPerArm=20000,measuredPerArm=1000000,chunkLimit=8192,finalMeasuredChunk=576,measuredTotal=180000000,warmupTotal=3600000,launcherSeconds=1200,groups=6,blocksPerGroup=10,confidence=.95,studentTCriticalDf5=2.570581835636305,screenUpperPercent=1.0,retries=0,extensions=0,trim=False,liveETW=False,UAC=False,
 workload=dict(cases=['ADMITTED_START','ADMITTED_STOP','UNKNOWN_PARENT','UNKNOWN_PROCESS_INSTANCE','DUPLICATE_START','DUPLICATE_STOP','INVALID_IDENTITY','DECODE_FAILURE','CAPACITY_REJECTION','EXCEPTION','OUT_OF_SCOPE'],channels=['authority','detail'],selection='chunk ordinal modulo 22; cases cycle within each channel; same schedule restarts independently for warmup and measurement',input='fixed event provider/version/fields; per-callback PID selected from prebuilt array; exact hashes in executable binding',adapters='fixed scalar decoding and preallocated deterministic selector storage; no live TDH, acquisition, filesystem or ETW; same dependencies in every arm',limitations='qualification applies to this synthetic callback workload; does not establish live ETW overhead',existingDiagnosticState='v2 diagnostic disabled identically; original timer/metrics remain enabled',reset='outside each measured chunk; warmup excluded; data digest outside timing'),drift=dict(blockPosition='report per-position means and ranges',temporal='report first/last half and linear slope',groupedResidual='report lag-1 autocorrelation and group means',inference='never automatically pass while material drift/dependence remains unresolved; no alternative estimator'))
 write(C/'protocol.json',protocol);shutil.copy2(C/'protocol.json',R/'protocol.json')
 print(json.dumps(dict(preserved=len(inputs),workspace=str(C),protocol=sha(C/'protocol.json'))))
