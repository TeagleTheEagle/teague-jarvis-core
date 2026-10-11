import pathlib,json,hashlib,shutil,uuid,subprocess,os,difflib
R=pathlib.Path(__file__).parent;read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=read(R/'plan.json');old=pathlib.Path(p['code']);root=pathlib.Path(p['root'])
freeze=[dict(path=str(x),sha256=sha(x),bytes=x.stat().st_size,mtime=x.stat().st_mtime_ns) for x in sorted(root.rglob('*')) if x.is_file() and x.name!='D-load.bin']
with (R/'first-failure-freeze.json').open('x') as f:json.dump(freeze,f,indent=2)
C=pathlib.Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code';C.mkdir(parents=True)
for x in read(R/'diagnostic-hashes.json'):assert sha(old/x['name'])==x['sha256'];shutil.copy2(old/x['name'],C/x['name'])
run='startup-'+uuid.uuid4().hex;(C/run/'temp').mkdir(parents=True)
e=(C/'entry_observer.cpp').read_text()
oldtext='if(observer.joinable())observer.join();if(independent)CloseHandle(independent);CloseHandle(pi.hThread);CloseHandle(pi.hProcess);'
newtext='if(observer.joinable())observer.join();finalWait=WaitForSingleObject(pi.hProcess,0);signal=Q();GetExitCodeProcess(pi.hProcess,&exitCode);GetProcessTimes(pi.hProcess,&created,&exited,&kt,&ut);if(FT(exited)&&double(FT(exited)-FT(created))/10000000.0>=13.6)deadline=true;if(independent)CloseHandle(independent);CloseHandle(pi.hThread);CloseHandle(pi.hProcess);'
assert oldtext in e;e=e.replace(oldtext,newtext)
(C/'entry_observer.cpp').write_text(e);(R/'entry_observer-followup.cpp').write_text(e)
(R/'exit-check.diff').write_text(''.join(difflib.unified_diff((old/'entry_observer.cpp').read_text().splitlines(True),e.splitlines(True))))
s=(C/'startup_trace.cpp').read_text()
s=s.replace('static std::vector<std::string> Schemas(EVENT_RECORD* e)', 'static std::vector<std::string> RawSchemas(EVENT_RECORD* e)')
pos=s.index('struct Row{')
s=s[:pos]+'''static std::vector<std::string> Schemas(EVENT_RECORD* e){static std::map<std::string,std::vector<std::string>> cache;std::string key(reinterpret_cast<const char*>(&e->EventHeader.ProviderId),sizeof(GUID));key.append(reinterpret_cast<const char*>(&e->EventHeader.EventDescriptor),sizeof(EVENT_DESCRIPTOR));auto it=cache.find(key);if(it!=cache.end())return it->second;return cache[key]=RawSchemas(e);}
'''+s[pos:]
s=s.replace('(v.size()==4||v.size()==8)','(v.size()==1||v.size()==2||v.size()==4||v.size()==8)')
s=s.replace('static const GUID RegProvider=', 'static const GUID ClassicReg={0xae53722e,0xc863,0x11d2,{0x86,0x59,0x00,0xc0,0x4f,0xa3,0x21,0xa1}};\nstatic const GUID RegProvider=')
s=s.replace('EVENT_TRACE_FLAG_CSWITCH|EVENT_TRACE_FLAG_DISPATCHER;', 'EVENT_TRACE_FLAG_CSWITCH|EVENT_TRACE_FLAG_DISPATCHER|EVENT_TRACE_FLAG_REGISTRY;')
s=s.replace('reg=IsEqualGUID(e->EventHeader.ProviderId,RegProvider)', 'reg=(IsEqualGUID(e->EventHeader.ProviderId,RegProvider)||IsEqualGUID(e->EventHeader.ProviderId,ClassicReg))')
s=s.replace('reg?"registry":"scheduler"', 'reg?(IsEqualGUID(e->EventHeader.ProviderId,ClassicReg)?"registry_classic":"registry"):"scheduler"')
s=s.replace('for(auto n:nums){bool found=false;', 'auto schema=Schemas(e);for(auto n:nums){if(std::find(schema.begin(),schema.end(),U(n))==schema.end())continue;bool found=false;')
s=s.replace('L"KeyName"};','L"KeyName",L"BaseName",L"RelativeName"};')
s=s.replace('for(auto n:texts){auto v=', 'for(auto n:texts){if(std::find(schema.begin(),schema.end(),U(n))==schema.end())continue;auto v=')
# Only actual probe's console helper; exclude collector/debug-controller consoles from detailed tracing.
oldtarget='r.image.find(L"conhost.exe")!=std::wstring::npos'
newtarget='(r.image.find(L"conhost.exe")!=std::wstring::npos&&std::any_of(rows.begin(),rows.end(),[&](const auto& p){return p.second.pid==r.parent&&p.second.sequence==r.parentSequence&&p.second.image.find(L"J6Probe.exe")!=std::wstring::npos;}))'
assert oldtarget in s;s=s.replace(oldtarget,newtarget)
(C/'startup_trace.cpp').write_text(s);(R/'startup_trace-followup.cpp').write_text(s)
(R/'trace-metadata.diff').write_text(''.join(difflib.unified_diff((old/'startup_trace.cpp').read_text().splitlines(True),s.splitlines(True))))
cp=R.parents[3]/('stage6-startup-load-'+uuid.uuid4().hex);cp.mkdir();(C/'startup-config.json').write_text(json.dumps(dict(cPayload=str(cp/'C-load.bin')),indent=2))
results=[];env=os.environ.copy();env['TEMP']=env['TMP']=str(C/run/'temp')
for b in read(R/'build.json'):
 args=[a.replace(str(old),str(C)) for a in b['args']];res=subprocess.run(args,cwd=C,env=env,capture_output=True,text=True);results.append(dict(args=args,returncode=res.returncode,stdout=res.stdout,stderr=res.stderr))
with (R/'followup-build.json').open('x') as f:json.dump(results,f,indent=2)
assert all(x['returncode']==0 for x in results)
manifest=[dict(name=f.name,sha256=sha(f)) for f in sorted(C.iterdir()) if f.is_file()]
(C/'startup-source.json').write_text(json.dumps(manifest,indent=2))
with (R/'followup-plan.json').open('x') as f:json.dump(dict(code=str(C),run=run,root=str(C/run),diagnosticHashes=manifest,source=p['source'],sourceHashes=p['sourceHashes'],firstFailedRun=str(root)),f,indent=2)
print(json.dumps(dict(code=str(C),run=run,root=str(C/run),builds=[x['returncode'] for x in results])))
