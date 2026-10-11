import pathlib
R=pathlib.Path(__file__).resolve().parent
p=R/'collect.py';s=p.read_text()
s=s.replace("('smoke','repeat1','repeat2')","('smoke','loads','dry1','dry2')")
s=s.replace("else [('idle',20),('disk',100),('sustained',40),('cpu',20),('Dhash',40)]", "else ([('idle',30),('disk',100),('sustained',150),('cpu',40),('Dhash',90)] if run=='loads' else [('hash-before',60),('sustained',120),('hash-after',60)])")
s=s.replace("status='DIAGNOSTIC_COMPLETED'","status='LIVE_MONITOR_HEALTHY'")
s=s.replace("child=subprocess.Popen([sys._base_executable,'-B',str(R/'workload.py'),run,mode,str(duration)],", "command=[sys._base_executable,'-B',str(R/'hash_sources.py'),run,mode.split('-')[1]] if mode.startswith('hash-') else [sys._base_executable,'-B',str(R/'workload.py'),run,mode,str(duration)]\n   child=subprocess.Popen(command,")
s=s.replace("print(json.dumps({'run':run,'status':status,'probes':len(probes),'acceptance':False}),flush=True)", """from reconcile_run import reconcile
result=reconcile(run);save('reconciliation.json',result)
if result['status']!='PASS':raise RuntimeError('Pipeline reconciliation failed; stop campaign')
from finalize import finalize,accepted,durable_write,sha
if run!='smoke':
 p=subprocess.run([sys._base_executable,'-B',str(R/'finalize.py'),run],capture_output=True,timeout=60)
 save('finalizer-process.json',{'exit_code':p.returncode,'stdout':p.stdout.decode(errors='replace'),'stderr':p.stderr.decode(errors='replace')})
 if not accepted(out,p.returncode):raise RuntimeError('Durable finalization/archive failed')
 durable_write(out/'acceptance.json',{'status':'SACRIFICIAL_RUN_ACCEPTED','manifest_sha256':sha(out/'evidence-manifest.json')})
print(json.dumps({'run':run,'status':status,'probes':len(probes),'acceptance':run!='smoke'}),flush=True)""")
p.write_text(s)
p=R/'launch.ps1';s=p.read_text().replace("'smoke','repeat1','repeat2'","'loads','dry1','dry2'")
s=s.replace("if(Test-Path -LiteralPath $root)", "if($Run -eq 'dry2' -and -not(Test-Path -LiteralPath (Join-Path $PSScriptRoot 'dry1\\acceptance.json'))){throw 'Dry1 acceptance required'}\nif(Test-Path -LiteralPath $root)")
p.write_text(s)
