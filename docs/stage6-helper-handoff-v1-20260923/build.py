import pathlib,json,subprocess,shutil,uuid
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'before.json').read_text())['candidate'])
shutil.copy2(R/'native_handoff_fixture.cpp',C/'native_handoff_fixture.cpp')
p=subprocess.run(['cmd.exe','/d','/c',str(R/'build.cmd')],capture_output=True,text=True,timeout=180)
with (R/('build-'+uuid.uuid4().hex+'.json')).open('x') as f:json.dump(dict(command=str(R/'build.cmd'),returncode=p.returncode,stdout=p.stdout,stderr=p.stderr),f,indent=2)
print(p.stdout,p.stderr);raise SystemExit(p.returncode)
