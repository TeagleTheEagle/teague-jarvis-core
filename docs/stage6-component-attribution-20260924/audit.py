import subprocess,json,hashlib,difflib
from prepare import R,W,C,sha,put
DUMP=r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\dumpbin.exe'
def functions(p):
 out=subprocess.run([DUMP,'/disasm:nobytes',str(p)],capture_output=True,text=True,errors='replace',check=True).stdout.splitlines();found={}
 for i,line in enumerate(out):
  if line.startswith('?dispatch'):
   body=[]
   for x in out[i+1:]:
    if x and not x[0].isspace():break
    if x.strip():body.append(x.strip())
   found[line.split('@@')[0]]='\n'.join(body)
 return found
if __name__=='__main__':
 old=functions(C/'loss_measurement_fixture_v3.obj');new=functions(W/'attribution_fixture.obj')
 with (R/'dispatch-disassembly.json').open('x') as f:json.dump(dict(old=old,new=new),f,indent=2)
 equal=old['?dispatch']==new['?dispatch']
 result=dict(referenceDispatchObjectInstructionsIdentical=equal,originalObjectSHA256=sha(C/'loss_measurement_fixture_v3.obj'),newObjectSHA256=sha(W/'attribution_fixture.obj'),headerUnchanged=sha(C/'loss_measurement_v3.hpp')==sha(W/'loss_measurement_v3.hpp'),variants={name:dict(qpcCallSites=body.count('__imp_QueryPerformanceCounter'),newLockPrefixes=body.count('lock '),lines=len(body.splitlines())) for name,body in new.items()})
 put(R/'generated-code-audit.json',result)
 print(json.dumps(result))
 if not equal:
  print('\n'.join(difflib.unified_diff(old['?dispatch'].splitlines(),new['?dispatch'].splitlines())))
  raise SystemExit(2)
