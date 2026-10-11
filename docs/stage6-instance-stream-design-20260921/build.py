import pathlib,json,subprocess,hashlib
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'plan.json').read_text())['code'])
V=pathlib.Path(r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207')
S=pathlib.Path(r'C:\Program Files (x86)\Windows Kits\10');version='10.0.26100.0'
args=[str(V/'bin/Hostx64/x64/cl.exe'),'/nologo','/std:c++17','/EHsc','/MT','/O2','/W4',str(C/'stream_bench.cpp'),'/Fo'+str(C/'stream_bench.obj'),'/Fe'+str(C/'J6StreamBench.exe'),'/I'+str(V/'include')]+['/I'+str(S/'Include'/version/x) for x in ('ucrt','shared','um')]+['/link','/LIBPATH:'+str(V/'lib/x64')]+['/LIBPATH:'+str(S/'Lib'/version/x/'x64') for x in ('ucrt','um')]+['bcrypt.lib']
p=subprocess.run(args,cwd=C,capture_output=True,text=True)
with (R/'build.json').open('x') as f:json.dump(dict(args=args,exit=p.returncode,stdout=p.stdout,stderr=p.stderr),f,indent=2)
print(p.stdout,p.stderr);raise SystemExit(p.returncode)
