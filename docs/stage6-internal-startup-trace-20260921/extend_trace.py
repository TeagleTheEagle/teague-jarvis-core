import pathlib,json,shutil,subprocess,os,hashlib
R=pathlib.Path(__file__).parent;plan=json.loads((R/'plan.json').read_text());C=pathlib.Path(plan['code'])
s=(C/'baseline_kernel_trace.cpp').read_text()
s=s.replace('static void WINAPI Event(EVENT_RECORD* e)', 'static void LifecycleEvent(EVENT_RECORD* e)')
extra=r'''
static const GUID FileProvider={0xedd08927,0x9cc4,0x4e65,{0xb9,0x70,0xc2,0x56,0x0f,0xb5,0xc2,0x89}};
static const GUID RegProvider={0x70eb4f03,0xc1de,0x4f73,{0xa0,0x51,0x33,0xd1,0x3d,0x54,0x13,0xbd}};
static const GUID ThreadProvider={0x3d6fa8d1,0xfe05,0x11d0,{0x9d,0xda,0x00,0xc0,0x4f,0xd7,0xba,0x7c}};
static std::vector<std::string> startup;
static unsigned startupOverflow=0;
static std::map<DWORD,std::pair<DWORD,ULONGLONG>> tids;
static std::map<ULONGLONG,std::pair<DWORD,ULONGLONG>> irps;
static Row* Target(DWORD pid,LONGLONG q){for(auto& a:rows){auto&r=a.second;if(r.pid==pid&&q>=r.start&&(!r.stop||q<=r.stop)&&(r.image.find(L"J6Probe.exe")!=std::wstring::npos||r.image.find(L"conhost.exe")!=std::wstring::npos))return &r;}return nullptr;}
static void WINAPI Event(EVENT_RECORD* e){
 LifecycleEvent(e);
 try {
  bool proc=IsEqualGUID(e->EventHeader.ProviderId,Provider),file=IsEqualGUID(e->EventHeader.ProviderId,FileProvider),reg=IsEqualGUID(e->EventHeader.ProviderId,RegProvider),sched=IsEqualGUID(e->EventHeader.ProviderId,ThreadProvider);
  if(!proc&&!file&&!reg&&!sched)return;
  unsigned id=e->EventHeader.EventDescriptor.Id,op=e->EventHeader.EventDescriptor.Opcode;
  if(proc&&(id<3||id>6))return;
  if(sched&&op!=36&&op!=50)return;
  auto q=e->EventHeader.TimeStamp.QuadPart;DWORD pid=e->EventHeader.ProcessId,tid=e->EventHeader.ThreadId;ULONGLONG irp=0;
  std::lock_guard<std::mutex> l(guard);Row* target=nullptr;
  if(proc){pid=static_cast<DWORD>(Number(e,L"ProcessID"));target=Target(pid,q);}
  else if(sched){
   DWORD candidates[2]={0,0};if(op==36&&e->UserDataLength>=8)memcpy(candidates,e->UserData,8);else if(op==50&&e->UserDataLength>=4)memcpy(candidates,e->UserData,4);
   for(auto t:candidates){auto it=tids.find(t);if(it!=tids.end()){auto r=Target(it->second.first,q);if(r&&r->created==it->second.second){target=r;pid=r->pid;tid=t;break;}}}
  }else if(file&&id==24){irp=Number(e,L"Irp");auto it=irps.find(irp);if(it!=irps.end()){target=Target(it->second.first,q);if(target&&target->created!=it->second.second)target=nullptr;}}
  else target=Target(pid,q);
  if(!target)return;
  if(proc&&id==3){DWORD t=static_cast<DWORD>(Number(e,L"ThreadID"));if(t)tids[t]={target->pid,target->created};}
  if(file&&!irp)irp=Number(e,L"Irp");
  if(file&&irp&&id!=24)irps[irp]={target->pid,target->created};
  if(startup.size()>=200000){++startupOverflow;return;}
  std::ostringstream o;o<<"{\"provider\":"<<J(proc?"process":file?"file":reg?"registry":"scheduler")<<",\"id\":"<<id<<",\"opcode\":"<<op<<",\"version\":"<<unsigned(e->EventHeader.EventDescriptor.Version)<<",\"qpc\":"<<q<<",\"callbackQpc\":"<<Q()<<",\"pid\":"<<target->pid<<",\"created\":\""<<target->created<<"\",\"headerPid\":"<<e->EventHeader.ProcessId<<",\"tid\":"<<tid<<",\"fields\":{";
  bool first=true;
  // Explicit metadata allowlist: no command line, environment, registry value or file bytes.
  const wchar_t* nums[]={L"ProcessID",L"ThreadID",L"StartAddr",L"Win32StartAddr",L"ImageBase",L"ImageSize",L"Irp",L"FileObject",L"FileKey",L"IssuingThreadId",L"IoSize",L"ByteOffset",L"NtStatus",L"Status",L"ElapsedTime",L"InitialTime",L"KeyObject",L"Index",L"NewThreadId",L"OldThreadId",L"TThreadId",L"OldThreadState",L"OldThreadWaitReason",L"OldThreadWaitMode"};
  for(auto n:nums){bool found=false;auto v=Number(e,n,&found);if(found){if(!first)o<<",";first=false;o<<J(U(n))<<":"<<v;}}
  const wchar_t* texts[]={L"ImageName",L"FileName",L"OpenPath",L"KeyName"};
  for(auto n:texts){auto v=Text(e,n);if(!v.empty()){if(!first)o<<",";first=false;o<<J(U(n))<<":"<<J(U(v));}}
  if(sched&&op==36&&e->UserDataLength>=8){DWORD ts[2];memcpy(ts,e->UserData,8);if(!first)o<<",";o<<"\"newTid\":"<<ts[0]<<",\"oldTid\":"<<ts[1];}
  o<<"},\"schema\":"<<List(Schemas(e))<<"}";startup.push_back(o.str());if(file&&id==24)irps.erase(irp);
 }catch(...){++faults;}
}
'''
# List declaration is needed by callback.
pos=s.index('static std::vector<std::string> Schemas')
s=s[:pos]+'static std::string List(const std::vector<std::string>& names);\n'+s[pos:]
pos=s.index('static void Sample()');s=s[:pos]+extra+s[pos:]
s=s.replace('session=L"J6Kernel-"','session=L"J6Startup-"')
s=s.replace('p->LogFileMode=EVENT_TRACE_REAL_TIME_MODE;', 'p->LogFileMode=EVENT_TRACE_REAL_TIME_MODE|EVENT_TRACE_SYSTEM_LOGGER_MODE;p->EnableFlags=EVENT_TRACE_FLAG_CSWITCH|EVENT_TRACE_FLAG_DISPATCHER;')
s=s.replace('TRACE_LEVEL_INFORMATION,0x10,0,0,nullptr)', 'TRACE_LEVEL_INFORMATION,0x70,0,0,nullptr)')
needle=' if(enable){ControlTraceW'
s=s.replace(needle,' if(!enable)enable=EnableTraceEx2(sessionHandle,&FileProvider,EVENT_CONTROL_CODE_ENABLE_PROVIDER,TRACE_LEVEL_VERBOSE,0x1f0,0,0,nullptr);\n if(!enable)enable=EnableTraceEx2(sessionHandle,&RegProvider,EVENT_CONTROL_CODE_ENABLE_PROVIDER,TRACE_LEVEL_VERBOSE,0x400000000000ac33ULL,0,0,nullptr);\n'+needle)
needle=' out<<"]}";bool wrote='
replace=' out<<"]}";std::ostringstream st;st<<"{\\\"overflow\\\":"<<startupOverflow<<",\\\"events\\\":[";for(size_t i=0;i<startup.size();i++){if(i)st<<",";st<<startup[i];}st<<"]}";if(!Write(L"startup-events.json",st.str()))++faults;if(startupOverflow)++faults;bool wrote='
assert needle in s;s=s.replace(needle,replace)
(R/'startup_trace.cpp').write_text(s);shutil.copy2(R/'startup_trace.cpp',C/'startup_trace.cpp');shutil.copy2(R/'entry_observer.cpp',C/'entry_observer.cpp')
vc=pathlib.Path(r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207');sdk=pathlib.Path(r'C:\Program Files (x86)\Windows Kits\10')
env=os.environ.copy();env['TEMP']=env['TMP']=str(pathlib.Path(plan['root'])/'temp')
results=[]
for source,exe in [('entry_observer.cpp','J6EntryObserve.exe'),('startup_trace.cpp','J6StartupTrace.exe')]:
 args=[str(vc/'bin/Hostx64/x64/cl.exe'),'/nologo','/std:c++17','/EHsc','/MT','/O2','/W4',str(C/source),'/I'+str(vc/'include')]+['/I'+str(sdk/'Include/10.0.26100.0'/x) for x in ('um','shared','ucrt')]+['/Fo'+str(C/source.replace('.cpp','.obj')),'/Fe'+str(C/exe),'/link','/LIBPATH:'+str(vc/'lib/x64')]+['/LIBPATH:'+str(sdk/'Lib/10.0.26100.0'/x/'x64') for x in ('um','ucrt')]+['tdh.lib','advapi32.lib','ole32.lib']
 p=subprocess.run(args,cwd=C,env=env,capture_output=True,text=True);results.append(dict(args=args,code=p.returncode,stdout=p.stdout,stderr=p.stderr))
 if p.returncode:break
with (R/'build.json').open('x') as f:json.dump(results,f,indent=2)
print(json.dumps(results));assert all(x['code']==0 for x in results)
