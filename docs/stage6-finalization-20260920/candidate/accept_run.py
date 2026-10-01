import json,sys,pathlib,collections,traceback
from workspace import run_dir
from finalize import finalize,accepted,durable_write
R=run_dir(sys.argv[1])
def read(n):return json.loads((R/n).read_text(encoding='utf-8-sig'))
try:
 a=read('analysis.json');h=read('retained-handle-verification.json');p=read('probes.json');t=read('tap.json');q=read('queue-state.json')
 if a['monitorHealth']!='PASS_FOR_THIS_DIAGNOSTIC_RUN' or a['coverage']!='PASS':raise RuntimeError('Live health/coverage failure')
 if len(h)!=len(p) or any(int(x['times'][1])<=int(x['times'][0]) or x['exit']!=0 for x in h):raise RuntimeError('Retained-handle exit failure')
 if read('resource-exit.json')['exit']!=0:raise RuntimeError('Resource sampler failure')
 counts=collections.Counter((x['pid'],x['kind'],x['stage']) for x in t)
 for x in p:
  for kind in ('start','stop'):
   for stage in ('A-callback','A-enqueue'):
    if counts[x['pid'],kind,stage]!=1:raise RuntimeError('Callback/enqueue coverage')
 if a['internalCollisions'] or q['remaining']:raise RuntimeError('Queue identity/residue')
 f=read('finalization-state.json')
 if f['state']!='SEALED' or f['failure'] or f['active'] or not f['allHandlesConfirmed'] or f['expected']!=len(p) or f['starts']!=len(p) or f['stops']!=len(p):raise RuntimeError('Finalization barrier not proved')
 if read('monitor-result.json').get('finalization')!='SEALED':raise RuntimeError('Missing finalization receipt')
 result=finalize(R)
 if not accepted(R,0):raise RuntimeError('Final durable receipt invalid')
 durable_write(R/'acceptance.json',dict(status='SACRIFICIAL_RUN_ACCEPTED',expectedStarts=len(p),callbackStarts=len(p),enqueuedStarts=len(p),persistedStarts=len(p),expectedStops=len(p),callbackStops=len(p),enqueuedStops=len(p),persistedStops=len(p),externalCollisions=a['externalCollisions'],internalCollisions=a['internalCollisions'],heartbeatInterval=a['maxHeartbeatInterval'],heartbeatAge=a['maxHeartbeatAge'],manifest_sha256=result['manifest_sha256'],protectedAccess=False))
 print(json.dumps(dict(run=R.name,status='PASS',probes=len(p),heartbeat=a['maxHeartbeatInterval'])))
except BaseException:
 durable_write(R/'acceptance-failure.json',dict(status='MONITOR_STILL_DEFECTIVE',error=traceback.format_exc()))
 raise
