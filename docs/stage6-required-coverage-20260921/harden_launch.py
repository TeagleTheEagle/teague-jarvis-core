import json,subprocess,hashlib
from pathlib import Path
R=Path(__file__).parent;data=json.loads((R/'candidate.json').read_text());C=Path(data['code']);p=C/'owned_entry.cpp'
s=p.read_text();head,body=s.split('extern "C" __declspec(dllexport) int RunQualification',1)
# Match the old hidden-console worker launch so its OS helper is still exercised.
body=body.replace('si.StartupInfo.dwFlags=STARTF_USESTDHANDLES;','si.StartupInfo.dwFlags=STARTF_USESTDHANDLES|STARTF_USESHOWWINDOW;si.StartupInfo.wShowWindow=SW_HIDE;')
body=body.replace('CREATE_NO_WINDOW|EXTENDED_STARTUPINFO_PRESENT','CREATE_NEW_CONSOLE|EXTENDED_STARTUPINFO_PRESENT')
# Once created, always drive the debug loop/normal worker shutdown even if identity
# publication fails; report the capture error, never accept it or abandon a suspended child.
body=body.replace('if(!DebugSetProcessKillOnExit(FALSE))return 96;FILETIME','int captureError=DebugSetProcessKillOnExit(FALSE)?0:96;FILETIME')
body=body.replace('))return 98;', '))captureError=98;')
body=body.replace('if(!Write(root+L"\\\\worker-created.json",ident.str()))return 99;','if(captureError==0&&!Write(root+L"\\\\worker-created.json",ident.str()))captureError=99;')
body=body.replace('return trace?trace:int(status);','return captureError?captureError:(trace?trace:int(status));')
p.write_text(head+'extern "C" __declspec(dllexport) int RunQualification'+body)
b=data['builds'][1];pr=subprocess.run(b['args'],cwd=C,capture_output=True,text=True)
with (R/'launch-hardening-build.json').open('x') as f:json.dump(dict(args=b['args'],exit=pr.returncode,stdout=pr.stdout,stderr=pr.stderr),f,indent=2)
assert pr.returncode==0
with (R/'candidate-frozen.json').open('x') as f:json.dump(dict(code=str(C),files=[dict(path=str(q),sha256=hashlib.sha256(q.read_bytes()).hexdigest()) for q in C.iterdir() if q.is_file()]),f,indent=2)
print(pr.stdout)
