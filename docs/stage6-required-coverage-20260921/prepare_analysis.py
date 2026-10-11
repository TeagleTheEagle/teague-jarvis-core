from pathlib import Path
R=Path(__file__).parent
s=(R.parent/'stage6-kernel-resume-20260921/analyze.py').read_text()
s=s.replace("C=Path(json.loads((R/'preflight.json').read_text())['code'])","C=Path(json.loads((R/'candidate-frozen.json').read_text())['code'])")
s=s.replace("result=q.qualify(events,kernel,handles,native,cim)","result=q.qualify(events,kernel,handles,native,cim)\nprobeIndependentHandles=list(handles)")
insert='''
from coverage import coverage,identity
declared=load('process-identities.json');wi=load('worker-created.json')
worker=next(d for d in declared if d['role']=='worker');application=next(d for d in declared if d['role']=='application')
q.require(identity(worker)==identity(wi),'WORKER_LAUNCH_IDENTITY')
workerNative=load(f"native-{worker['pid']}-{worker['created']}.json");native.append(workerNative)
probeKeys={identity(h) for h in probeIndependentHandles}
expected=[];handleEvidence=[]
for r in kernel['rows']:
 key=identity(r)
 if key==identity(worker):role='worker';q.require(norm(wi['image'])==norm(r['image']),'WORKER_LAUNCH_IMAGE')
 elif key in probeKeys:role='probe'
 elif key==identity(application):role='infrastructure'
 elif norm(r['image'])=='c:\\\\windows\\\\system32\\\\conhost.exe':role='console'
 else:raise ValueError('UNCLASSIFIED_KERNEL_INSTANCE: '+str(key))
 expected.append(dict(r,role=role,parentVerified=True))
 handleEvidence.append(dict(pid=r['pid'],created=r['created'],handleCreated=r.get('handleCreated'),image=r.get('handleImage',''),imageError=r.get('imageError'),
  retained=r['handleRetained'],exited=r['signalObservedQpc']>0,closed=r['handleClosed'],exitFiletime=r['exitFiletime'],exitCode=r['exitCode'],
  qualifiedPostExit=not r['handleRetained'],reason=r['reason'],openError=r['openError'],attemptBegin=r['handleAttemptBeginQpc'],attemptEnd=r['handleAttemptQpc']))
coverageInputs=dict(expected=expected,events=events,handles=handleEvidence,natives=native,mapping=mapping)
cov=coverage(**coverageInputs)
save('coverage-live-inputs.json',coverageInputs);save('coverage-live-result.json',cov)
result.update(coverage=cov,status=cov['status'],workerNativeEntryVerified=workerNative['entryQpc']>0,realNativeCount=len(native))
'''
s=s.replace("save('cim-correlations.json',cim);",insert+"\nsave('cim-correlations.json',cim);")
s=s.replace("if k not in ('identities','writer','applicationAuthority','queue')","if k not in ('identities','writer','applicationAuthority','queue','coverage')")
s+="\nq.require(cov['status']=='PASS','REQUIRED_EVIDENCE_COVERAGE_FAILED')\n"
with (R/'analyze.py').open('x') as f:f.write(s)
print('analysis prepared')
