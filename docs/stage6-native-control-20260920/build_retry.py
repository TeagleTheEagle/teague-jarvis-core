import pathlib,json,hashlib,shutil,subprocess,os
R=pathlib.Path(__file__).resolve().parent;plan=json.loads((R/'plan.json').read_text());D=pathlib.Path(plan['live_code']);D.mkdir(parents=True,exist_ok=True)
for p in (R/'candidate').iterdir():shutil.copyfile(p,D/p.name)
temp=D/'build-temp';temp.mkdir(exist_ok=True);env=os.environ.copy();env['TEMP']=env['TMP']=str(temp)
vc=pathlib.Path(r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207')
sdk=pathlib.Path(r'C:\Program Files (x86)\Windows Kits\10');version='10.0.26100.0';cl=vc/'bin/Hostx64/x64/cl.exe'
env['PATH']=str(cl.parent)+os.pathsep+env.get('PATH','')
records=[]
for name,token in [('J6ProbeNative',False),('J6ProbeToken',True)]:
 command=[str(cl),'/nologo','/O2','/W4','/WX','/TC','/c',str(D/'native_probe.c'),'/Fo'+str(D/(name+'.obj')),'/I'+str(vc/'include')]
 command+=['/I'+str(sdk/'Include'/version/p) for p in ('um','shared','ucrt')]
 if token:command+=['/DJ6_TOKEN_CONTROL']
 completed=subprocess.run(command,cwd=D,env=env,text=True,capture_output=True);records.append(dict(command=command,exit=completed.returncode,stdout=completed.stdout,stderr=completed.stderr))
 if completed.returncode:break
 command=[str(cl.parent/'link.exe'),'/NOLOGO','/NODEFAULTLIB','/ENTRY:ProbeEntry','/SUBSYSTEM:CONSOLE','/DYNAMICBASE','/NXCOMPAT','/HIGHENTROPYVA','/CETCOMPAT','/OUT:'+str(D/(name+'.exe')),str(D/(name+'.obj')),'/LIBPATH:'+str(sdk/'Lib'/version/'um/x64'),'kernel32.lib']
 if token:command+=['advapi32.lib']
 completed=subprocess.run(command,cwd=D,env=env,text=True,capture_output=True);records.append(dict(command=command,exit=completed.returncode,stdout=completed.stdout,stderr=completed.stderr))
 if completed.returncode:break
 with (R/'images'/f'{name}.exe').open('wb') as f:f.write((D/f'{name}.exe').read_bytes())
 with (R/'candidate'/f'{name}.exe').open('wb') as f:f.write((D/f'{name}.exe').read_bytes())
with (R/'build-retry-evidence.json').open('x') as f:json.dump(records,f,indent=2)
if any(x['exit'] for x in records):raise RuntimeError('Build failure preserved; no probe launched')
print(json.dumps(dict(code=str(D),builds=len(records),success=True)))
