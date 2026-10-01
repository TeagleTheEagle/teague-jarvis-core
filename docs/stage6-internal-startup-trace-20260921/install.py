import pathlib,json,hashlib,shutil,uuid,subprocess
R=pathlib.Path(__file__).parent;plan=json.loads((R/'plan.json').read_text());C=pathlib.Path(plan['code']);root=pathlib.Path(plan['root']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
launch=(R.parent/'stage6-call-tracing-20260921'/'trace_launch.ps1').read_text().replace('^calltrace-','^startup-').replace('trace-source.json','startup-source.json').replace('J6BaselineTrace.exe','J6StartupTrace.exe').replace('trace_driver.py','startup_driver.py')
(R/'startup_launch.ps1').write_text(launch)
for n in ('startup_driver.py','startup_launch.ps1'):shutil.copy2(R/n,C/n)
cp=R.parents[3]/('stage6-startup-load-'+uuid.uuid4().hex);cp.mkdir();config=dict(cPayload=str(cp/'C-load.bin'))
(C/'startup-config.json').write_text(json.dumps(config,indent=2));(R/'startup-config.json').write_text(json.dumps(config,indent=2))
compile((C/'startup_driver.py').read_text(),'startup_driver.py','exec')
manifest=[dict(name=p.name,sha256=sha(p)) for p in sorted(C.iterdir()) if p.is_file() and p.name not in ('startup-source.json',)]
(C/'startup-source.json').write_text(json.dumps(manifest,indent=2));(R/'diagnostic-hashes.json').write_text(json.dumps(manifest,indent=2))
tests=[]
for args in ([],[str(root),'arbitrary','0'],[str(root),'entry','../0'],[r'C:\Windows','entry','0']):
 p=subprocess.run([str(C/'J6EntryObserve.exe')]+args,capture_output=True);tests.append(dict(args=args,returncode=p.returncode));assert p.returncode in (90,91)
assert sha(C/'J6Probe.exe')=='23240ef9f8b0a9a324110b1c2331de31dc1b0e08f5359cb707e51a939af56cd3'
for x in plan['sourceHashes']:assert sha(C/x['name'])==x['sha256']
(R/'focused-static-tests.json').write_text(json.dumps(dict(invalidInvocationTests=tests,syntax=True,frozenSourceChecks=len(plan['sourceHashes']),unchangedProbe=True),indent=2))
print(json.dumps(dict(code=str(C),root=str(root),staticTests=4,sourceHashes=len(plan['sourceHashes']))))
