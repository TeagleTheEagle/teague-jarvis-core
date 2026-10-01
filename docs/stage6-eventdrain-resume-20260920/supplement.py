"""Derive scheduling observations and failure reconciliation without altering raw evidence."""
import pathlib,json,collections,hashlib,difflib
R=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def put(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
def gap(seq):return max((b-a for a,b in zip(seq,seq[1:])),default=0)
allresults=[]
for name in ('a1','minimal','persist-d','none','dhash','a2','a3'):
 d=R/name;e=read(d/'event-analysis.json');freq=read(d/'ready.json')['frequency'];taps=read(d/'tap.json');entries=read(d/'queue-entries.json')
 events=[json.loads(x) for x in (d/'events.jsonl').read_text().splitlines()]
 retained=read(d/'retained-handle-verification.json');probes=read(d/'probes.json');known={p['pid'] for p in probes}
 counts=collections.Counter((r['pid'],r['kind']) for r in events)
 each=all(counts[(p['pid'],'start')]==counts[(p['pid'],'stop')]==1 for p in retained)
 timed=[p for p in retained if p['pid'] not in known]
 target=d/'timeout-probe-reconciliation.json'
 if timed and not target.exists():put(target,dict(status='FAILED_RUN_PRESERVED',timed_out_probe_records=timed,retained_identities=len(retained),kernel_exits_confirmed=sum(int(p['times'][1])>int(p['times'][0]) for p in retained),starts=e['starts'],stops=e['stops'],each_retained_identity_has_one_start_stop=each,note='Successful-probe list omits the timeout probe. Retained handles and kernel exit times verify exits; unavailable cached exit codes remain null. This does not make the failed run pass.'))
 eventmap={r['queueSequence']:r for r in events}
 residences=[(eventmap[r['queueSequence']]['receivedQpc']-r['enqueueQpc'])/freq for r in entries if r['queueSequence'] in eventmap]
 enqueue=sorted(t['qpc']/freq for t in taps if t['stage']=='A-enqueue')
 callbacks=sorted(t['qpc']/freq for t in taps if t['stage']=='A-callback')
 result=dict(run=name,retainedIdentities=len(retained),startStopPairsExact=each,timeoutProbeIdentities=timed,maximumConsumerDrainStartGap=gap([r['start']/freq for r in e['drains']]),maximumProducerCallbackInterarrival=gap(callbacks),maximumEnqueueInterarrival=gap(enqueue),maximumEnqueueToProcessingSeconds=max(residences,default=None),minimumSignedCallbackToEnqueue=min((v['signedCallbackToEnqueue'] for v in e['producerObserverLags']),default=None),maximumSignedCallbackToEnqueue=max((v['signedCallbackToEnqueue'] for v in e['producerObserverLags']),default=None),interpretation='Interarrival includes workload pacing and probe waits; drain start gaps include Wait-Event and filesystem blocking. These are not kernel scheduler latency. Queue residence uses QPC on the same host.')
 rejected=d/'rejected-poll.json'
 if rejected.exists():
  v=read(rejected);result['rejectedPoll']=dict(elapsedSeconds=(v['after']-v['before'])/freq,lastHeartbeatAgeAtEntry=(v['before']-v['last']['ticks'])/freq,lastHeartbeatAgeAtCatch=(v['after']-v['last']['ticks'])/freq,note='Catch-time age bounds the rejection; exact age computed inside Reader was not recorded.')
 put(d/'supplemental-analysis.json',result);allresults.append(result)
put(R/'supplemental-campaign.json',allresults)
diffs=[]
for p in sorted((R/'pre-refinement').iterdir()):
 target=R/p.name
 if target.is_file() and p.suffix in ('.ps1','.cs','.py'):
  diffs.extend(difflib.unified_diff(p.read_text(encoding='utf-8-sig').splitlines(True),target.read_text(encoding='utf-8-sig').splitlines(True),fromfile='pre-refinement/'+p.name,tofile=p.name))
with (R/'diagnostic-instrumentation.diff').open('x',encoding='utf-8') as f:f.writelines(diffs)
print(json.dumps(dict(runs=len(allresults),allRetainedPairsExact=all(v['startStopPairsExact'] for v in allresults))))
