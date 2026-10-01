import pathlib,json,hashlib,collections,statistics
R=pathlib.Path(__file__).parent;read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=read(R/'followup-plan.json');F=pathlib.Path(p['root']);C=pathlib.Path(p['code']);load=lambda n:read(F/n)
calls=load('calls.json');result=load('result.json');kernel=load('etw-result.json');probes=load('probes.json');samplers=load('samplers.json');pressure=load('pressure.json')
assert result['status']=='BOUNDED_DIAGNOSTIC_COMPLETE' and calls['overflow']==0
for k in ('flushResult','stopResult','consumerResult','eventsLost','realtimeBuffersLost','buffersLost','faults'):assert kernel[k]==0
assert kernel['requestedStop'] and load('observer-exit.json')['exited'] and load('observer-exit.json')['exitCode']==0
driver=load('driver-identity.json');rows=kernel['rows'];root=next(x for x in rows if x['pid']==driver['pid']);scope={root['sequence']}
while True:
 new=scope|{x['sequence'] for x in rows if x['parentSequence'] in scope}
 if new==scope:break
 scope=new
tracked=[x for x in rows if x['sequence'] in scope];byseq={x['sequence']:x for x in rows};proof=[]
for x in tracked:
 assert x['startQpc'] and x['stopQpc']>x['startQpc'] and int(x['exitFiletime'])>=int(x['created']) and x['exitCodeKnown']
 if x['sequence']!=root['sequence']:
  parent=byseq[x['parentSequence']];assert parent['pid']==x['parentPid'] and int(parent['created'])<=int(x['created'])<=int(parent['exitFiletime'])
 if x['handleRetained']:assert x['handleClosed'] and x['signalObservedQpc'] and x['metadataError']==0
 else:assert x['openError']==87 and x['reason']=='OPEN_PROCESS_FAILED' and x['stopQpc']<x['handleAttemptBeginQpc']<=x['handleAttemptQpc']
 proof.append(dict(pid=x['pid'],created=x['created'],sequence=x['sequence'],parentSequence=x['parentSequence'],image=x['image'],exitFiletime=x['exitFiletime'],exitCode=x['exitCode'],retained=x['handleRetained']))
helpers=[];internal=[]
for item in probes+samplers:
 created=item.get('initialKernelTimes',[None])[0] if 'initialKernelTimes' in item else item['created'];k=next(x for x in tracked if x['pid']==item['pid'] and x['created']==created)
 children=[x for x in tracked if x['parentSequence']==k['sequence']]
 for child in children:helpers.append(dict(mainPid=k['pid'],mainCreated=k['created'],pid=child['pid'],created=child['created'],image=child['image'],parentSequence=child['parentSequence'],fromMainStartSeconds=(int(child['created'])-int(k['created']))/1e7,lifetimeSeconds=(int(child['exitFiletime'])-int(child['created']))/1e7,exitsAfterMainSeconds=(int(child['exitFiletime'])-int(k['exitFiletime']))/1e7))
 if 'case' in item:
  marks=[x for x in calls['internal'] if x['pid']==item['pid']];m={x['stage']:x['perfCounterNs'] for x in marks}
  # Python perf_counter_ns is QPC-derived on this host; preserve raw bridge as well.
  groups={}
  for name,a,b in [('imports','runtime_imports_begin','runtime_imports_end'),('path_validation','path_validation_begin','path_validation_end'),('memory_query','memory_query_begin','memory_query_end'),('system_times','system_times_begin','system_times_end'),('query_body','query_work_begin','query_work_end'),('serialization','serialization_begin','serialization_end'),('result_mapping','result_mapping_begin','result_mapping_end')]:
   groups[name]=(m[b]-m[a])/1e9 if a in m and b in m else None
  internal.append(dict(case=item['case'],pid=item['pid'],created=created,firstScriptMarkerAfterKernelStartSeconds=(m['script_entry_observed']/100-k['startQpc'])/1e7 if 'script_entry_observed' in m else None,stages=groups,rawMarkers=marks,postScriptRuntimeTeardown='NOT_INSTRUMENTED'))
groups=collections.defaultdict(list)
for x in calls['rows']:groups[x['call']].append(x)
probeApis=[x for x in calls['rows'] if x['scope'].startswith(('probe:','probe-independent')) and x['call'].startswith(('probe_timing.','winapi.'))]
samplerApis=[x for x in calls['rows'] if x['scope'].startswith('sampler:') and x['call'].startswith('bounded_sampler.')]
pressureRanges={}
for row in pressure['rows']:
 for name,v in row['counters'].items():
  if v['value'] is not None:pressureRanges.setdefault(name,[]).append(v['value'])
pressureRanges={k:dict(min=min(v),max=max(v),validSamples=len(v)) for k,v in pressureRanges.items()}
stats={}
for condition in ('idle','D-small-hash'):
 selected=[x for x in probes if x['condition']==condition];v=[(int(x['finalKernelTimes'][1])-int(x['finalKernelTimes'][0]))/1e7 for x in selected]
 stats[condition]=dict(count=len(v),min=min(v),median=statistics.median(v),max=max(v))
out=dict(status='INCONCLUSIVE',boundedRun=result['status'],records=len(calls['rows']),overflow=calls['overflow'],internalMarkers=len(calls['internal']),probeStats=stats,slowestProbeApi=max(probeApis,key=lambda x:x['seconds']),slowestSamplerApi=max(samplerApis,key=lambda x:x['seconds']),callMaxima={k:max(x['seconds'] for x in v) for k,v in groups.items()},slow2=calls['slow2'],slow5=calls['slow5'],samplerInternal=internal,samplerCleanup=[dict(case=x['case'],seconds=(x['cleanupEndQpc']-x['cleanupBeginQpc'])/1e7,allExited=x['allExited'],handleClosed=x['handleClosed'],observationTimeout=x['cleanupObservationTimedOut']) for x in samplers],trackedKernelIdentities=len(tracked),kernelRetainedExits=sum(x['retained'] for x in proof),kernelPostExit=len(proof)-sum(x['retained'] for x in proof),helpers=helpers,pressureRanges=pressureRanges,pressureSamples=len(pressure['rows']),pressureErrors=pressure['errors'],observerShutdown=load('observer-exit.json'),probeClassification='INCONCLUSIVE',samplerClassification='PROCESS_CREATION_DELAY in preserved failure; underlying cause INCONCLUSIVE',commonCause='NOT_ESTABLISHED',protectedAccess=False,productionChanged=False)
with (R/'analysis.json').open('x') as f:json.dump(out,f,indent=2)
identities=proof+[load('launcher.json'),load('observer-identity.json')]
for planfile in ('plan.json',):
 old=read(R/planfile);of=pathlib.Path(old['root']);identities.extend(dict(pid=x['pid'],created=x['created'],image=x['image']) for x in read(of/'etw-result.json')['rows']);identities.extend([read(of/'launcher.json'),read(of/'observer-identity.json')])
with (R/'recorded-identities.json').open('x') as f:json.dump(identities,f,indent=2)
print(json.dumps({k:out[k] for k in ('status','records','overflow','internalMarkers','probeStats','slowestProbeApi','slowestSamplerApi','samplerCleanup','trackedKernelIdentities','kernelRetainedExits','kernelPostExit','pressureSamples','pressureErrors')},indent=2))
