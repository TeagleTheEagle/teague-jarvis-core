import pathlib,json,hashlib,shutil,uuid,collections,difflib,sys,ctypes
R=pathlib.Path(__file__).parent;read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=read(R/'plan.json');S=pathlib.Path(plan['code']);F=pathlib.Path(plan['root']);result=read(F/'result.json');calls=read(F/'calls.json')
assert result['overflow']>0 and result['cleanup']['allExited'] and result['cleanup']['allHandlesClosed']
assert all(not x['hardDeadlineFailure'] and not x['independentObserverFailed'] for x in read(F/'probes.json'))
assert all(not x['cleanupObservationTimedOut'] and x['allExited'] for x in read(F/'samplers.json'))
freeze=[dict(path=str(p),bytes=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns,sha256=sha(p)) for p in sorted(F.rglob('*')) if p.is_file()]
with (R/'overflow-failure-freeze.json').open('x') as f:json.dump(dict(status='FAILED_TRACE_OVERFLOW',files=freeze,overflow=result['overflow'],counts=collections.Counter(x['call'] for x in calls['rows'])),f,indent=2)
C=pathlib.Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code';C.mkdir(parents=True)
for x in plan['diagnosticHashes']:assert sha(S/x['name'])==x['sha256'];shutil.copy2(S/x['name'],C/x['name'])
before=(C/'call_trace.py').read_text();shutil.copy2(R/'call_trace.py',C/'call_trace.py');after=(C/'call_trace.py').read_text()
(R/'trace-volume-correction.diff').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='preserved-first-diagnostic/call_trace.py',tofile='followup-diagnostic/call_trace.py')))
compile(after,str(C/'call_trace.py'),'exec');sys.path.insert(0,str(C));import call_trace as ct
ct.label('probe:test');assert ct.wrap('test',lambda:7)()==7
ctypes.set_last_error(123);ct.wrap('test.last_error',lambda:None)();assert ctypes.get_last_error()==123
beforeCount=len(ct.ROWS);ct.label('background');assert ct.wrap('probe_timing.Process32NextW',lambda:8)()==8;assert len(ct.ROWS)==beforeCount
ct.wrap('tree.scan',lambda:None)();assert len(ct.ROWS)==beforeCount+1
ct.label('probe-independent-observer:test');ct.wrap('probe_timing.WaitForSingleObject',lambda a,b:0)(1,15000);assert ct.ROWS[-1]['requestedMilliseconds']==15000
assert ct.LIMIT==200000 and ct.OVERFLOW==0
rows=[dict(name=x['name'],sha256=sha(C/x['name'])) for x in plan['diagnosticHashes']];(C/'trace-source.json').write_text(json.dumps(rows,indent=2))
run='calltrace-'+uuid.uuid4().hex;(C/run/'temp').mkdir(parents=True)
out=dict(code=str(C),run=run,root=str(C/run),diagnosticHashes=rows,change='Only filter repetitive background per-process enumeration APIs; retain scan/discovery spans and all labelled launcher/sampler/observer calls',previousFailure=str(F),limitUnchanged=200000,originalCandidateUnchanged=True)
with (R/'followup-plan.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k!='diagnosticHashes'}))
