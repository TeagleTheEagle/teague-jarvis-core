import json,subprocess,uuid,hashlib
from pathlib import Path
R=Path(__file__).parent;C=Path(json.loads((R/'candidate.json').read_text())['code'])
V=Path(r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207');S=Path(r'C:\Program Files (x86)\Windows Kits\10');ver='10.0.26100.0'
for src,out,libs in [('durable_test.cpp','J6DurableTest.exe',['bcrypt.lib']),('authority_trace.cpp','J6AuthorityTrace.exe',['bcrypt.lib','advapi32.lib','tdh.lib','ole32.lib'])]:
 args=[str(V/'bin/Hostx64/x64/cl.exe'),'/nologo','/std:c++17','/EHsc','/MT','/O2','/W4',str(C/src),'/Fo'+str(C/(src+'.obj')),'/Fe'+str(C/out),'/I'+str(V/'include')]+['/I'+str(S/'Include'/ver/x) for x in ('ucrt','shared','um')]+['/link','/LIBPATH:'+str(V/'lib/x64')]+['/LIBPATH:'+str(S/'Lib'/ver/x/'x64') for x in ('ucrt','um')]+libs
 p=subprocess.run(args,cwd=C,capture_output=True,text=True,timeout=60)
 record=dict(command=args,exit=p.returncode,stdout=p.stdout,stderr=p.stderr)
 if p.returncode==0:record['sha256']=hashlib.sha256((C/out).read_bytes()).hexdigest()
 with (R/('build-'+uuid.uuid4().hex+'.json')).open('x') as f:json.dump(record,f,indent=2)
 print(json.dumps(record));assert p.returncode==0
