import pathlib,json,subprocess,shutil,hashlib,uuid
R=pathlib.Path(__file__).resolve().parent;C=pathlib.Path(json.loads((R/'candidate.json').read_text())['code'])
shutil.copy2(R/'telemetry_test.cpp',C/'telemetry_test.cpp')
shutil.copy2(R/'trace_telemetry.hpp',C/'trace_telemetry.hpp')
out=R/('build-'+uuid.uuid4().hex);out.mkdir()
base=json.loads((R.parent/'stage6-trace-capacity-native-entry-20260921/batched-candidate/build.json').read_text())[0]['args']
result=[]
for source,exe in [('authority_trace.cpp','J6AuthorityTrace.exe'),('startup_trace.cpp','J6StartupTrace.exe'),('telemetry_test.cpp','J6TelemetryTest.exe'),('sink_test.cpp','J6SinkTest.exe'),('durable_test.cpp','J6DurableTest.exe')]:
 args=[str(C/source) if x.endswith('startup_trace.cpp') else '/Fo'+str(C/(source+'.obj')) if x.startswith('/Fo') else '/Fe'+str(C/exe) if x.startswith('/Fe') else x for x in base]
 p=subprocess.run(args,cwd=C,capture_output=True,text=True,timeout=90)
 result.append(dict(source=source,args=args,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
 with (out/('build-'+source+'.json')).open('x') as f:json.dump(result[-1],f,indent=2)
 print(source,p.returncode)
 if p.returncode:print(p.stdout,p.stderr);raise SystemExit(p.returncode)
files=[dict(name=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(C.iterdir()) if p.is_file()]
with (out/'built-hashes.json').open('x') as f:json.dump(files,f,indent=2)
