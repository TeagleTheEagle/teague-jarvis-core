import pathlib,json,subprocess,hashlib,uuid
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'candidate.json').read_text())['code'])
V=pathlib.Path(r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207');S=pathlib.Path(r'C:\Program Files (x86)\Windows Kits\10');version='10.0.26100.0'
for name in ('durable_sink.hpp','durable_test.cpp'):
 if (C/name).exists():
  b=(C/name).read_bytes()
  with (R/(name+'.before-'+uuid.uuid4().hex)).open('xb') as f:f.write(b)
 with (C/name).open('wb') as f:f.write((R/name).read_bytes())
args=[str(V/'bin/Hostx64/x64/cl.exe'),'/nologo','/std:c++17','/EHsc','/MT','/O2','/W4',str(C/'durable_test.cpp'),'/Fo'+str(C/'durable_test.obj'),'/Fe'+str(C/'J6DurableTest.exe'),'/I'+str(V/'include')]+['/I'+str(S/'Include'/version/x) for x in ('ucrt','shared','um')]+['/link','/LIBPATH:'+str(V/'lib/x64')]+['/LIBPATH:'+str(S/'Lib'/version/x/'x64') for x in ('ucrt','um')]+['bcrypt.lib']
p=subprocess.run(args,cwd=C,capture_output=True,text=True)
with (R/('build-'+uuid.uuid4().hex+'.json')).open('x') as f:json.dump(dict(args=args,exit=p.returncode,stdout=p.stdout,stderr=p.stderr),f,indent=2)
print(p.stdout,p.stderr);raise SystemExit(p.returncode)
