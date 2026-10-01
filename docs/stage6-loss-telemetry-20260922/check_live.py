import pathlib,json,sys,re,hashlib
R=pathlib.Path(__file__).resolve().parent;C=pathlib.Path(json.loads((R/'candidate.json').read_text())['code'])
rid=sys.argv[1];assert re.fullmatch('[a-f0-9]{32}',rid);run=C/('diagnostic-'+rid)
def read(p):return json.loads(p.read_text())
result=read(run/'result.json');assert not result['failure'];assert all(x['exited'] and x['exitCode']==0 for x in result['cleanup'])
probes=[]
for i in range(3):
 a=read(run/f'probe-{i}-created.json');b=read(run/f'probe-{i}-exit.json')
 assert a['identity']['created']==b['identity']['created'];assert b['identity']['kernelExitVerified'];assert b['exitCode']==0
 # Kernel lifetime is FILETIME-based, not delay in the parent observing the exit.
 lifetime=(int(b['identity']['exitFiletime'])-int(b['identity']['created']))/10000000
 assert 0<=lifetime<13.6
 assert pathlib.Path(a['identity']['image']).resolve()==(C/'J6TelemetryTest.exe').resolve()
 probes.append(dict(pid=a['identity']['pid'],created=a['identity']['created'],lifetime=lifetime))
channels={}
for kind in ('authority','detail'):
 if result['mode'] not in (kind,'combined'):continue
 d=run if kind=='authority' else run/'detail'
 t=read(d/'loss-telemetry.json');e=read(d/'etw-result.json')
 assert t['errors']==0;assert t['callbacks']==t['selected']+t['rejected'];assert t['callbacks']>0
 assert all(p['end']>=p['begin'] and p['status']==0 for p in t['phases'])
 assert {'StartTrace','OpenTrace','EnableProviderProcess','ProcessTraceEntry','ProcessTraceReturn','ReadyPublished','StopRequestedOrLoopEnded','FlushTrace','StopTrace'}<=set(p['name'] for p in t['phases'])
 assert any(p['phase']=='periodic' for p in t['snapshots'])
 assert all(p['status']==0 and p['end']>=p['begin'] and p['numberOfBuffers']>0 for p in t['snapshots'])
 assert not any(e[k] for k in ('faults','eventsLost','buffersLost','realtimeBuffersLost','consumerResult','flushResult','stopResult'))
 for p in probes:
  matches=[x for x in e['rows'] if x['pid']==p['pid'] and x['created']==p['created']]
  assert len(matches)==1 and matches[0]['startQpc']>0 and matches[0]['stopQpc']>=matches[0]['startQpc']
 for m in ('callback','guardWait','guardHold','metadata','admission','write','flush','close'):
  assert t['metrics'][m]['count']>0,(kind,m)
 channels[kind]=dict(callbacks=t['callbacks'],selected=t['selected'],rejected=t['rejected'],snapshots=len(t['snapshots']),actualBuffers=sorted(set(p['numberOfBuffers'] for p in t['snapshots'])),eventsLost=e['eventsLost'],reconciledProbes=len(probes),maxCallbackSeconds=t['metrics']['callback']['maxTicks']/t['frequency'],maxQuerySeconds=max((p['end']-p['begin'])/t['frequency'] for p in t['snapshots']))
report=dict(status='PASS',diagnosticOnly=True,mode=result['mode'],run=str(run),channels=channels,probes=probes,cleanup=result['cleanup'])
with (R/('checked-'+rid+'.json')).open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(report,indent=2))
