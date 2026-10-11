import json,hashlib,uuid,shutil,subprocess
from pathlib import Path
R=Path(__file__).parent;P=R.parent/'stage6-required-coverage-20260921';pre=json.loads((R/'preflight.json').read_text());old=Path(pre['code'])
assert json.loads((R/'final'/pre['hostRun']/'final-host-state.json').read_text())['status']=='PASS'
C=Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code';C.mkdir(parents=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before=[]
for p in old.iterdir():
 if p.is_file():shutil.copy2(p,C/p.name);before.append(dict(path=str(p),name=p.name,sha256=sha(p)))
s=(C/'owned_entry.cpp').read_text()
needle='auto acquired=Q();HANDLE independent=nullptr;'
assert s.count(needle)==1
insert=r'''auto acquired=Q();
 // Direct process identity comes from the creator's handle, before any debug continuation.
 auto imageBegin=Q();wchar_t imageBuffer[32768]{};DWORD imageCount=32768;
 BOOL imageOK=QueryFullProcessImageNameW(ph,0,imageBuffer,&imageCount);
 DWORD imageError=imageOK?0:GetLastError();auto imageEnd=Q();
 DWORD identityWait=WaitForSingleObject(ph,0);auto stateQpc=Q();
 std::wstring fullImage=imageOK?std::wstring(imageBuffer,imageCount):L"";
 bool identityOK=imageOK&&imageCount>0&&imageCount<32768&&identityWait==WAIT_TIMEOUT;
 std::ostringstream early;
 early<<"{\"source\":\"creator-owned-handle\",\"recordId\":"<<J(std::to_string(pid)+"-"+std::to_string(FT(created)))<<",\"creatorPid\":"<<GetCurrentProcessId()<<",\"pid\":"<<pid<<",\"tid\":"<<tid<<",\"handlePid\":"<<GetProcessId(ph)<<",\"handleIdentity\":\""<<reinterpret_cast<ULONG_PTR>(ph)<<"\",\"created\":\""<<FT(created)<<"\",\"handleCreated\":\""<<FT(created)<<"\",\"frequency\":"<<freq.QuadPart<<",\"createBeginQpc\":"<<cb<<",\"createEndQpc\":"<<ce<<",\"handleAcquiredQpc\":"<<acquired<<",\"queryBeginQpc\":"<<imageBegin<<",\"queryEndQpc\":"<<imageEnd<<",\"stateQpc\":"<<stateQpc<<",\"processState\":"<<identityWait<<",\"image\":"<<J(U(fullImage))<<",\"imageError\":"<<imageError<<",\"imageCharacters\":"<<imageCount<<",\"success\":"<<(identityOK?"true":"false")<<"}";
 bool identityWritten=Write(root+L"\\early-image-"+std::to_wstring(pid)+L"-"+std::to_wstring(FT(created))+L".json",early.str());
 auto identityPersisted=identityWritten?Q():0;if(!identityOK||!identityWritten)fault=true;
 HANDLE independent=nullptr;'''
s=s.replace(needle,insert)
needle='s<<"{\\\"mode\\\":"';assert s.count(needle)==1
s=s.replace(needle,'s<<"{\\\"identityPersistedQpc\\\":"<<identityPersisted<<",\\\"mode\\\":"')
(C/'owned_entry.cpp').write_text(s)
# Only relocation of the explicit DLL binding, preserving launcher behavior.
p=C/'qualified_launch.ps1';s=p.read_text();s=s.replace(str(old).replace('\\','\\\\'),str(C).replace('\\','\\\\'));p.write_text(s)
args=json.loads((P/'candidate.json').read_text())['builds'][1]['args']
args=[a.replace(str(old),str(C)) for a in args]
pr=subprocess.run(args,cwd=C,capture_output=True,text=True)
with (R/'candidate.json').open('x') as f:json.dump(dict(code=str(C),before=before,build=dict(args=args,exit=pr.returncode,stdout=pr.stdout,stderr=pr.stderr)),f,indent=2)
print(json.dumps(dict(code=str(C),exit=pr.returncode,stdout=pr.stdout,stderr=pr.stderr)))
assert pr.returncode==0
