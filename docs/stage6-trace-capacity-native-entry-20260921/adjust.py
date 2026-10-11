import pathlib,json,hashlib,subprocess
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'plan.json').read_text())['code']);before={n:hashlib.sha256((C/n).read_bytes()).hexdigest() for n in ('native_bridge.py','owned_entry.cpp','trace_sink.hpp')}
p=C/'native_bridge.py';s=p.read_text().replace('w.LPCWSTR,c.c_longlong,w.BOOL]','w.LPCWSTR,c.c_longlong,w.BOOL,c.c_longlong,c.c_longlong]')
s=s.replace('original,ph,th,pid,tid=create()','original,ph,th,pid,tid,cb,ce=create()').replace('str(self.root),launch,is_probe)','str(self.root),launch,is_probe,cb,ce)').replace('result not in (0,97)','result!=0')
s=s.replace('result=self.original(*a);return result,*result','cb=ticks();result=self.original(*a);ce=ticks();return result,*result,cb,ce')
s=s.replace('ok=self.originalSampler(*a)','cb=ticks();ok=self.originalSampler(*a);ce=ticks()').replace('return ok,pi.process,pi.thread,pi.pid,pi.tid','return ok,pi.process,pi.thread,pi.pid,pi.tid,cb,ce');p.write_text(s)
p=C/'owned_entry.cpp';s=p.read_text().replace('LONGLONG launch,BOOL isProbe){','LONGLONG launch,BOOL isProbe,LONGLONG cb,LONGLONG ce){').replace('auto cb=launch,ce=Q(),acquired=Q();','auto acquired=Q();')
s=s.replace('DeleteProcThreadAttributeList(si.lpAttributeList);for(auto h:handles)','auto createEnd=Q();DeleteProcThreadAttributeList(si.lpAttributeList);for(auto h:handles)')
s=s.replace('path,launch,FALSE);','path,launch,FALSE,launch,createEnd);')
s=s.replace('if(!GetProcessTimes(ph,&created,&exited,&kt,&ut))return 92;','if(GetProcessId(ph)!=pid||GetThreadId(th)!=tid||!GetProcessTimes(ph,&created,&exited,&kt,&ut))return 92;')
p.write_text(s)
p=C/'trace_sink.hpp';s=p.read_text().replace('if(persisted!=accepted)failure=10;','if(persisted!=accepted&&!failure)failure=10;');p.write_text(s)
build=json.loads((R/'build.json').read_text());results=[]
for x in build:
 p=subprocess.run(x['args'],cwd=C,capture_output=True,text=True);results.append(dict(args=x['args'],returncode=p.returncode,stdout=p.stdout,stderr=p.stderr));assert p.returncode==0,p.stdout
(R/'adjustment-build.json').write_text(json.dumps(dict(before=before,reason='Record actual native CreateProcess call interval; reject every native trace fault; preserve first writer failure classification.',builds=results),indent=2))
print('Three adjusted builds PASS')
