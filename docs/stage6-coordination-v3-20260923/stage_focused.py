import pathlib,json,shutil,hashlib,subprocess,sys,uuid,ast
R=pathlib.Path(__file__).resolve().parent;cfg=json.loads((R/'before.json').read_text());C=pathlib.Path(cfg['candidate'])
for n in ('external_driver_v3.py','test_coordination_v3.py','native_receipt_fixture.cpp'):shutil.copyfile(R/n,C/n)
# No source modifications to either historical candidate.
allow=json.loads((C/'baseline-allowlist.json').read_text());allow['syntheticRoots']=[str(C/'small-synthetic')];assert allow['approvedProtectedRoots']==[] and allow['realProtectedAccess'] is False
(C/'baseline-allowlist.json').write_text(json.dumps(allow,indent=2))
records=[];old=pathlib.Path(cfg['original'])/'small-synthetic';new=C/'small-synthetic';assert new.is_dir()
for p in sorted(old.iterdir()):
 assert p.is_file() and not p.is_symlink();s=p.stat();b=p.read_bytes();records.append(dict(path=str(p),bytes=s.st_size,mtimeNs=s.st_mtime_ns,sha256=hashlib.sha256(b).hexdigest()));assert (new/p.name).read_bytes()==b
with (R/'additional-inputs.json').open('x') as f:json.dump(records,f,indent=2)
build=R/'build_native_focused.cmd'
with build.open('x') as f:f.write('@echo off\ncall "C:\\Program Files (x86)\\Microsoft Visual Studio\\2022\\BuildTools\\VC\\Auxiliary\\Build\\vcvars64.bat"\nif errorlevel 1 exit /b %errorlevel%\ncd /d "'+str(C)+'"\ncl /nologo /EHsc /std:c++17 /O2 /DUNICODE /D_UNICODE authority_trace_v3.cpp /Fe:J6AuthorityTraceV3.exe /Fo:authority_trace_v3.obj advapi32.lib tdh.lib ole32.lib bcrypt.lib\nif errorlevel 1 exit /b %errorlevel%\ncl /nologo /EHsc /std:c++17 /O2 /DUNICODE /D_UNICODE native_receipt_fixture.cpp /Fe:J6ReceiptFixtureV3.exe /Fo:native_receipt_fixture.obj advapi32.lib tdh.lib ole32.lib bcrypt.lib\nexit /b %errorlevel%\n')
result=subprocess.run(['cmd','/d','/c',str(build)],capture_output=True,text=True,timeout=60)
with (R/'build-focused.json').open('x') as f:json.dump(dict(command=['cmd','/d','/c',str(build)],returncode=result.returncode,stdout=result.stdout,stderr=result.stderr),f,indent=2)
print(result.stdout,result.stderr);assert result.returncode==0
run=C/('offline-native-'+uuid.uuid4().hex);run.mkdir()
command=[str(C/'J6ReceiptFixtureV3.exe'),str(run)]
result=subprocess.run(command,capture_output=True,text=True,timeout=10)
with (R/'native-focused.json').open('x') as f:json.dump(dict(command=command,returncode=result.returncode,stdout=result.stdout,stderr=result.stderr,qualification=False),f,indent=2)
print(result.stdout,result.stderr);assert result.returncode==0
