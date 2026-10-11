import pathlib,json,subprocess,uuid,hashlib,re
R=pathlib.Path(__file__).resolve().parent;cfg=json.loads((R/'candidate.json').read_text());C=pathlib.Path(cfg['code']);run=C/('focused-'+uuid.uuid4().hex);run.mkdir()
results=[]
def execute(exe,args,expected):
 p=subprocess.run([str(C/exe),*map(str,args)],cwd=run,capture_output=True,text=True,timeout=30)
 row=dict(exe=exe,args=list(map(str,args)),returncode=p.returncode,expected=expected,stdout=p.stdout,stderr=p.stderr)
 results.append(row)
 with (run/f'result-{len(results):02}.json').open('x') as f:json.dump(row,f,indent=2)
 assert p.returncode==expected,row
 return p
p=execute('J6TelemetryTest.exe',[],0);native=json.loads(p.stdout)
for fault in (0,1,2,3):
 d=run/f'sink-{fault}';d.mkdir();execute('J6SinkTest.exe',[d,25,100,fault,100000],0 if fault==0 else 1)
 data=json.loads((d/'sink-result.json').read_text());assert bool(data['fault'])==(fault!=0)
 if not fault:
  assert data['accepted']==data['persisted']==25
  for x in data['segments']:assert hashlib.sha256((d/x['name']).read_bytes()).hexdigest()==x['sha256']
for fault in range(12):
 d=run/f'durable-{fault}';d.mkdir();execute('J6DurableTest.exe',[d,fault,1000],0 if fault==0 else 2)
# Preserve security/filter/capture code by checking each original statement remains,
# allowing only the explicitly reviewed telemetry wrappers.
for name in ('authority_trace.cpp','startup_trace.cpp'):
 s=(C/name).read_text();oldpath=next(x['path'] for x in cfg['before'] if pathlib.Path(x['path']).name==name);old=pathlib.Path(oldpath).read_text()
 for pattern in [r'p->BufferSize=\d+',r'p->MinimumBuffers=\d+',r'p->MaximumBuffers=\d+',r'p->FlushTimer=\d+',r'p->LogFileMode=[^;]+',r'p->EnableFlags=[^;]+',r'freq.QuadPart\)<\d+',r'0x[0-9a-f]+(?:ULL)?']:
  assert re.findall(pattern,s)==re.findall(pattern,old),(name,pattern)
 assert 'p->EventsLost||p->RealTimeBuffersLost?95:0' in s
 assert 'j6t::telemetry.errors.load())++faults' in s
for x in cfg['before']:assert hashlib.sha256(pathlib.Path(x['path']).read_bytes()).hexdigest()==x['sha256']
summary=dict(status='PASS',nativeAssertions=native['checks'],concurrentCallbacks=native['concurrentCallbacks'],executableCases=len(results),captureSettingsUnchanged=True,originalSourcesUnchanged=True,run=str(run))
with (R/('focused-summary-'+run.name+'.json')).open('x') as f:json.dump(summary,f,indent=2)
print(json.dumps(summary,indent=2))
