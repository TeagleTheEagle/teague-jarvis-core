import pathlib,json,subprocess,uuid
R=pathlib.Path(__file__).resolve().parent;C=pathlib.Path(json.loads((R/'before.json').read_text())['candidate'])
p=C/'native_receipt_fixture.cpp';s=p.read_text();a='std::string declaration="{\\"run\\":"';b='std::string declaration="{\\"heartbeat\\":10.0,\\"probe\\":13.6,\\"run\\":"';assert a in s;p.write_text(s.replace(a,b))
result=subprocess.run(['cmd','/d','/c',str(R/'build_native_focused.cmd')],capture_output=True,text=True,timeout=60)
run=C/('offline-native-'+uuid.uuid4().hex);run.mkdir();command=[str(C/'J6ReceiptFixtureV3.exe'),str(run)]
check=subprocess.run(command,capture_output=True,text=True,timeout=10) if result.returncode==0 else None
with (R/'native-real-format-before-fix.json').open('x') as f:json.dump(dict(buildReturncode=result.returncode,buildStdout=result.stdout,buildStderr=result.stderr,command=command,returncode=check.returncode if check else None,stdout=check.stdout if check else None,stderr=check.stderr if check else None),f,indent=2)
print(check.stdout,check.stderr,check.returncode)
