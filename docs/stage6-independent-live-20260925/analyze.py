import pathlib,json,hashlib,sys,subprocess
R=pathlib.Path(__file__).parent
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2)
v=load(R/'preflight-result.json');C=pathlib.Path(v['candidate']);root=pathlib.Path(v['runRoot'])
assert load(R/'postrun-census.json')['status']=='PASS'
sys.path.insert(0,str(C))
import analyze_lifecycle_witness_v1 as a
import failure_preserve_v4 as f
objects={str(p.relative_to(root)).replace('\\','/'):load(p) for p in root.rglob('*.json')}
exact=f.instance_census(objects);save(R/'recorded-instance-postrun.json',exact)
assert exact['clean'],exact
cmd=[sys.executable,'-B',str(C/'preserve_lifecycle_witness_v1.py'),'--run-root',str(root),'--archive',str(R/'lifecycle-witness-nonacceptance.zip'),'--first-failure','Management census incomplete; detailed EventsLost nonzero; run remains REJECTED']
result=subprocess.run(cmd,capture_output=True,text=True)
save(R/'witness-preservation-command.json',dict(command=cmd,exitCode=result.returncode,stdout=result.stdout,stderr=result.stderr));assert result.returncode==0
tree=load(root/'tree-handles.json')['rows'];stress=load(root/'stress-result.json');probes=load(root/'probe-timings.json')
direct={x['role']:x for x in stress['launched'] if x['role']!='lifecycle-probe'}
spec=[('sampler',direct['secondary-sampler']),('hash_worker',direct['hash-worker'])]+[(f'probe_{i+1}',dict(pid=p['pid'],created=p['initialKernelTimes'][0])) for i,p in enumerate(probes)]
targets=[];provenance=[]
for role,identity in spec:
 pid=identity['pid'];created=identity['created'];np=root/f'native-{pid}-{created}.json';n=load(np)
 t=next(x for x in tree if x['pid']==pid and x['created']==created)
 early=root/f'early-image-{pid}-{created}.json';e=load(early)
 assert n['finalWait']==0 and not n['fault'] and n['created']==created and t['exitFiletime']==n['exitFiletime']
 target=dict(role=role,pid=pid,created=created,exitFiletime=n['exitFiletime'],identitySource='creator-retained-handle',identityEvidenceSHA256=sha(np),processSequence=None,eventWindows={'START':[n['createBeginQpc'],n['createEndQpc']],'STOP':[n['createBeginQpc'],max(n['signalObservedQpc'],t['signalObservedQpc'])]})
 targets.append(target)
 provenance.append(dict(role=role,native=str(np),nativeSHA256=sha(np),earlyImageSHA256=sha(early),treeSHA256=sha(root/'tree-handles.json'),windowRule='Independent native CreateProcess bounds for START; creation-to-confirmed-handle-signal bound for STOP. No witness-derived window.'))
 helpers=[x for x in tree if x['parentPid']==pid and x['image'].lower().endswith('\\conhost.exe') and int(created)<=int(x['created'])<=int(n['exitFiletime'])]
 assert len(helpers)==1
 h=helpers[0];assert h['imageCapture']['valid'] and h['stateAtClose']==0 and h['exitFiletime']
 hrole={'sampler':'sampler_console','hash_worker':'hash_console','probe_1':'probe_1_console','probe_2':'probe_2_console'}[role]
 targets.append(dict(role=hrole,pid=h['pid'],created=h['created'],exitFiletime=h['exitFiletime'],identitySource='creation-verified-tracer-handle',identityEvidenceSHA256=sha(root/'tree-handles.json'),processSequence=None,eventWindows={'START':[n['createBeginQpc'],h['handleRetainedQpc']],'STOP':[n['createBeginQpc'],h['signalObservedQpc']]}))
 provenance.append(dict(role=hrole,treeSHA256=sha(root/'tree-handles.json'),windowRule='Independent tree tracker opened creation-verified live handle and image; parent creation/lifetime encloses helper creation; START bounded by parent creation begin and helper handle retention; STOP by parent creation begin and helper handle signal.',qualification='Independent diagnostic correlation only; does not replace missing authoritative kernel lifecycle.'))
tv=dict(run=v['run'],frequency=10000000,instances=targets)
save(R/'independent-targets.json',tv);save(R/'correlation-provenance.json',provenance)
summary={}
for channel,base,exe in [('authority',root,'J6AuthorityTraceV3.exe'),('detailed',root/'detail','J6StartupTrace.exe')]:
 side=C/(v['run']+'.'+channel+'-lifecycle-witness-v1.json');w=load(side);ready=load(base/'etw-ready.json');tele=load(base/'loss-diagnostic-v2.json');end=load(base/'etw-result.json')
 binding=dict(run=v['run'],session=ready['session'],channel=channel,candidateSHA256=v['witnessManifestSHA256'],observerSHA256=sha(C/exe),frequency=ready['frequency'])
 loss=dict(run=v['run'],session=ready['session'],frequency=ready['frequency'],samples=[{k:x[k] for k in ('beginQpc','endQpc','eventsLost','status')} for x in tele['samples']])
 save(R/(channel+'-binding.json'),binding);save(R/(channel+'-loss-input.json'),loss)
 output=R/(channel+'-analysis.json')
 command=[sys.executable,'-B',str(C/'analyze_lifecycle_witness_v1.py'),'--witness',str(side),'--binding',str(R/(channel+'-binding.json')),'--targets',str(R/'independent-targets.json'),'--loss',str(R/(channel+'-loss-input.json')),'--output',str(output)]
 run=subprocess.run(command,capture_output=True,text=True)
 save(R/(channel+'-analysis-command.json'),dict(command=command,exitCode=run.returncode,stdout=run.stdout,stderr=run.stderr));assert run.returncode==0
 increments=[dict(fromCount=x['eventsLost'],toCount=y['eventsLost'],beginQpc=x['beginQpc'],endQpc=y['endQpc']) for x,y in zip(loss['samples'],loss['samples'][1:]) if y['eventsLost']>x['eventsLost']]
 save(R/(channel+'-loss-increments.json'),increments)
 summary[channel]=dict(finalEventsLost=end['eventsLost'],witnessCount=w['count'],overflow=w['overflow'],quiesced=w['quiesced'],incrementWindows=increments,minFreeBuffers=min(x['freeBuffers'] for x in tele['samples']),maxBuffers=max(x['numberOfBuffers'] for x in tele['samples']),queueHighItems=tele['queueHighItems'],queueHighBytes=tele['queueHighBytes'],telemetryErrors=tele['errors'],telemetryOverflow=tele['overflow'],targets=load(output)['instances'])
save(R/'analysis-summary.json',summary)
print(json.dumps({c:{k:x for k,x in row.items() if k not in ('targets','incrementWindows')} for c,row in summary.items()}))
