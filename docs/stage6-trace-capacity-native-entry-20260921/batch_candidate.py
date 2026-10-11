import pathlib,json,hashlib,uuid,shutil,subprocess
R=pathlib.Path(__file__).parent;old=json.loads((R/'plan.json').read_text());O=pathlib.Path(old['code']);rows=json.loads((R/'candidate-hashes.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for x in rows:assert sha(O/x['name'])==x['sha256']
C=pathlib.Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code';C.mkdir(parents=True)
for x in rows:shutil.copy2(O/x['name'],C/x['name'])
source=C/'small-sacrificial';source.mkdir()
for x in old['files']:shutil.copy2(pathlib.Path(old['source'])/x['name'],source/x['name'])
(C/'baseline-allowlist.json').write_text(json.dumps(dict(approvedProtectedRoots=[],realProtectedAccess=False,syntheticRoots=[str(source)]),indent=2))
p=C/'traced_launch.ps1';p.write_text(p.read_text().replace(str(O).replace('\\','\\\\'),str(C).replace('\\','\\\\')))
p=C/'trace_sink.hpp';s=p.read_text().replace(' std::vector<Segment> segments;', ' std::string segmentBuffer;\n std::vector<Segment> segments;')
s=s.replace('segments.push_back({name,0,0,{}});return true;','segments.push_back({name,0,0,{}});segmentBuffer.clear();return true;')
oldClose='BYTE digest[32];bool ok=FlushFileBuffers(file)!=0;ok=CloseHandle(file)!=0&&ok;file=INVALID_HANDLE_VALUE;'
newClose='''BYTE digest[32];DWORD done=0;auto begin=q();LARGE_INTEGER freq;QueryPerformanceFrequency(&freq);
  bool ok=inject!=1&&inject!=2&&WriteFile(file,segmentBuffer.data(),DWORD(segmentBuffer.size()),&done,nullptr)&&done==segmentBuffer.size();
  ok=FlushFileBuffers(file)!=0&&ok;ok=CloseHandle(file)!=0&&ok;file=INVALID_HANDLE_VALUE;
  auto duration=double(q()-begin)/freq.QuadPart;if(duration>maxWriteSeconds)maxWriteSeconds=duration;
  if(ok)persisted+=segments.back().records;else if(!failure)failure=inject==2?112:7;'''
assert oldClose in s;s=s.replace(oldClose,newClose).replace('if(!ok){failure=6;return false;}','if(!ok){if(!failure)failure=6;return false;}')
a=s.index('   DWORD done=0;auto start=q();');b=s.index('   if(BCryptHashData',a);s=s[:a]+s[b:]
s=s.replace('++s.records;++persisted;','++s.records;segmentBuffer+=row;')
p.write_text(s)
build=json.loads((R/'adjustment-build.json').read_text())['builds'];out=[]
for x in build[:2]:
 args=[a.replace(str(O),str(C)) for a in x['args']];v=subprocess.run(args,cwd=C,capture_output=True,text=True);out.append(dict(args=args,returncode=v.returncode,stdout=v.stdout,stderr=v.stderr));assert v.returncode==0,v.stdout
B=R/'batched-candidate';B.mkdir(exist_ok=False)
plan=dict(old,code=str(C),source=str(source),priorCandidate=str(O),preChangeHashes=rows)
(B/'plan.json').write_text(json.dumps(plan,indent=2));(B/'build.json').write_text(json.dumps(out,indent=2));shutil.copy2(R/'focused.py',B/'focused.py')
newrows=[dict(name=x['name'],sha256=sha(C/x['name'])) for x in rows];(C/'run-source.json').write_text(json.dumps(newrows,indent=2));(B/'candidate-hashes.json').write_text(json.dumps(newrows,indent=2))
print(json.dumps(dict(code=str(C),report=str(B),hashes=len(newrows))))
