"""Read-only acceptance review of frozen run evidence; never retries or changes limits."""
import pathlib,json,sys,collections,hashlib
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'copy-result.json').read_text())['workspace']);sys.path.insert(0,str(C));import cleanup_checker
F=pathlib.Path(sys.argv[1]);assert F.parent==C and F.name.startswith('protected-')
read=lambda n:json.loads((F/n).read_text(encoding='utf-8-sig'))
errors=[];summary=dict(run=str(F),status='INCONCLUSIVE',errors=errors)
def require(ok,label):
 if not ok:errors.append(label)
try:
 producer=read('stress-result.json');summary['producerStatus']=producer['status'];summary['primaryFailure']=producer.get('primary_failure');require(producer['status']=='DIAGNOSTIC_COMPLETE' and not producer.get('primary_failure'),'PRODUCER_FAILURE')
 v=cleanup_checker.evaluate(F);summary['lifecycle']=v;require(v['status']=='PASS','DUAL_EVIDENCE_LIFECYCLE')
 one=read('hash-pass-1.json');two=read('hash-pass-2.json');contract=read('contract.json');total=sum(x['bytes'] for x in one['files'].values());require(one['files']==two['files'],'HASH_MISMATCH');require(one['endQpcNs']<=two['beginQpcNs'],'HASH_PASS_ORDER')
 copied=json.loads(pathlib.Path(json.loads((R/'copy-result.json').read_text())['run'],'dataset-manifest.json').read_text());expected={x['path']:x for x in copied['files']}
 require(set(expected)==set(two['files']) and all(expected[n]['sha256']==x['sha256'] for n,x in two['files'].items()),'CALIBRATION_COPY_HASH_MISMATCH')
 durations=[(p['endQpcNs']-p['beginQpcNs'])/1e9 for p in (one,two)];summary['hashes']=dict(fileCount=len(two['files']),totalBytes=total,largestFile=max(two['files'].values(),key=lambda x:x['bytes']),durations=durations,totalSeconds=sum(durations),bytesPerSecond=[total/d for d in durations],equality=one['files']==two['files'],perFileSeconds=[p['perFileSeconds'] for p in (one,two)])
 require(read('metadata-verified.json')['status']=='PASS','METADATA_FAILURE')
 samples=read('hash-health-samples.json')+read('collector-health-samples.json');hb=read('app-heartbeats.json');summary['maxHeartbeatInterval']=max(x['interval'] for x in hb);summary['maxHeartbeatAge']=max(x['age'] for x in samples);require(summary['maxHeartbeatInterval']<10 and summary['maxHeartbeatAge']<10,'HEARTBEAT_LIMIT')
 t=read('stage-timing.json');spans=t['spans'];freq=t['frequency'];require(t['overflow']==0,'TIMING_OVERFLOW');require(all(x['start']<=x['end'] and abs((x['end']-x['start'])/freq-x['seconds'])<1e-8 for x in spans),'TIMING_INVALID')
 groups=collections.defaultdict(list)
 for x in spans:groups[x['stage']].append(x['seconds'])
 required=['loop.wake','event.source.read','callback.A-callback','callback.A-enqueue','queue.lock.acquire.Select','event.selection','event.serialization','evidence.path','event.File.AppendAllText','queue.exact.RemoveAt','heartbeat.creation','heartbeat.history.append','heartbeat.publish.overwrite','flush.durable','control.file.check','process.inspection.preflight','process.inspection.identity','wait.event']
 require(all(groups[x] for x in required),'TIMING_STAGE_MISSING');summary['timing']=dict(spans=len(spans),points=len(t['points']),stages=len(groups),overflow=t['overflow'],longest=max(spans,key=lambda x:x['seconds']),maxima={k:max(a) for k,a in groups.items() if a})
 sampler=read('sampler-results.json');queries=sampler['queries'];summary['sampler']=dict(queries=len(queries),missing=sampler['missing'],reasons=dict(collections.Counter(x.get('reason','AVAILABLE') for x in queries)),threadExited=sampler['threadExited']);require(sampler['threadExited'] and queries and all(x.get('allExited') and x.get('handleClosed') and x.get('jobActiveBeforeClose')==0 for x in queries),'SAMPLER_CLEANUP')
 probes=read('probe-timings.json');summary['probes']=dict(count=len(probes),deadlineViolations=sum(bool(p['hardDeadlineFailure']) for p in probes),independentFailures=sum(bool(p['independentObserverFailed']) for p in probes),maxLifetimeSeconds=max((int(p['finalKernelTimes'][1])-int(p['finalKernelTimes'][0]))/1e7 for p in probes));require(not summary['probes']['deadlineViolations'] and not summary['probes']['independentFailures'],'PROBE_POLICY')
 app=read('app-result.json');summary['queue']=app['queue'];summary['durableObserverFinalization']=app['durableFinalization'];require(app['success'] and app['durableFinalization'],'OBSERVER_FAILURE')
 for x in read('source-hashes.json'):require(hashlib.sha256((C/x['name']).read_bytes()).hexdigest()==x['sha256'],'SOURCE_DRIFT:'+x['name'])
 summary['state']=read('state.json')['phase'];require(summary['state']=='OBSERVERS_CLOSED','STATE_NOT_CLOSED')
except Exception as ex:errors.append('MISSING_OR_INVALID_EVIDENCE: '+repr(ex))
summary['status']='PASS_PENDING_HOST_AND_SOURCE_METADATA' if not errors else 'FAIL'
with (R/'run-review.json').open('x') as f:json.dump(summary,f,indent=2)
print(json.dumps({k:v for k,v in summary.items() if k not in ('lifecycle','hashes','timing')}))
sys.exit(bool(errors))
