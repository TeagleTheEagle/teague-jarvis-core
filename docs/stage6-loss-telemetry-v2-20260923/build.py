import pathlib,json,subprocess,uuid
R=pathlib.Path(__file__).parent;C=R/'candidate';out=R/('build-'+uuid.uuid4().hex);out.mkdir()
base=json.loads((R.parent/'stage6-trace-capacity-native-entry-20260921/batched-candidate/build.json').read_text())[0]['args']
for source,exe in [('authority_trace_v3.cpp','J6AuthorityTraceV3.exe'),('startup_trace.cpp','J6StartupTrace.exe'),('diagnostic_test.cpp','DiagnosticOfflineTest.exe'),('overhead_test.cpp','OverheadCandidate.exe'),('overhead_test.cpp','OverheadReference.exe')]:
 args=[str(C/source) if x.endswith('startup_trace.cpp') else '/Fo'+str(out/(source+'.obj')) if x.startswith('/Fo') else '/Fe'+str(C/exe) if x.startswith('/Fe') else x for x in base]
 if exe=='OverheadReference.exe':args.insert(1,'/DREFERENCE')
 p=subprocess.run(args,cwd=out,capture_output=True,text=True,timeout=90)
 (out/(exe+'.json')).write_text(json.dumps(dict(args=args,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr),indent=2))
 print(source,p.returncode)
 if p.returncode:print(p.stdout,p.stderr);raise SystemExit(1)
print('All builds passed. No tracer executed.')
