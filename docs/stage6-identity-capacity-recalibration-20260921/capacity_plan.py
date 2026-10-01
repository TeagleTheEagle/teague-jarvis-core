import pathlib,json,collections,math,hashlib
R=pathlib.Path(__file__).parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
m=read(R/'capacity-measurement.json');freq=10000000
roots=[pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\7a3f06371aa14bb18e08339837103d62\code\protected-cda0e6c7d5774746afaef2d4e93602f8'),pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\3316657ba1864413a0c95ea1dc7bf6ff\code\protected-5d26ae153ea2490da7ca1ec16d97c124')]
comp=[]
for r in roots:
 raw=read(r/'startup-events.json')
 if isinstance(raw,list):rows=raw
 elif 'events' in raw:
  assert raw['overflow']==0
  rows=raw['events']
 else:
  rows=[]
  for s in raw['segments']:
   p=r/s['name'];assert hashlib.sha256(p.read_bytes()).hexdigest()==s['sha256']
   rows.extend(json.loads(l) for l in p.read_text().splitlines())
 qs=sorted(x['qpc'] for x in rows);out={}
 for sec in (1,5,10):
  j=0;peak=0
  for i,q in enumerate(qs):
   while j<len(qs) and qs[j]<q+sec*freq:j+=1
   peak=max(peak,j-i)
  out[str(sec)]=dict(records=peak,rate=peak/sec)
 comp.append(dict(path=str(r),records=len(qs),seconds=(qs[-1]-qs[0])/freq,rolling=out))
 print(comp[-1],flush=True)
C=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\f469b94b665e4808af1c5bb6aa46b207\code');F=C/'protected-00a17b2c499c4966a5113c30924b367a'
state=read(F/'state.json');h={x['phase']:x['qpc']/1e9 for x in state['history']};cal=m['calibration'];passes=cal['passes']
hashSeconds=sum(p['seconds'] for p in passes);slow=2*max(p['seconds'] for p in passes)
ready=read(F/'etw-ready.json');marks=read(F/'integration-launcher.json');shutdown=next(x['qpc']/x['frequency'] for x in marks if x['event']=='FINAL_SHUTDOWN')
work=h['WORKLOAD_CLOSED']-h['WORKLOAD_RUNNING'];overhead=work-90;closure=h['OBSERVERS_CLOSED']-h['WORKLOAD_CLOSED'];before=h['WORKLOAD_RUNNING']-ready['qpc']/freq
expected=max(slow,cal['longRunTargetSeconds'])+overhead+closure+before
durationBound=1200;conservative=cal['campaignSeconds']+closure+before
peak=max([m['rolling']['1']['perSecond']]+[c['rolling']['1']['rate'] for c in comp]);minimumPeak=min(c['rolling']['1']['rate'] for c in comp)
factor=peak/minimumPeak
rowsExpected=math.ceil(m['meanRate']*expected)
sustained=max(m['rolling']['60']['perSecond'],max(c['records']/c['seconds'] for c in comp))
rowsConservative=math.ceil(sustained*conservative)
empiricalUpper=math.ceil(peak*durationBound);envelope=math.ceil(empiricalUpper*factor)
traceBytes=math.ceil(envelope*m['bytesPerRecord']['max'])
tap=len(read(F/'app-tap.json'));app=len(read(F/'app-receipts.json'));native=280
other=[p for p in F.iterdir() if p.is_file() and not p.name.startswith('trace-')]
otherBytes=sum(p.stat().st_size for p in other);projectedOther=math.ceil(otherBytes/m['eventSpanSeconds']*durationBound*factor)
# Disk reserve is an explicitly conditional empirical envelope, not an enforced total-artifact bound.
# Source remains in place: no duplicate of the 59.7GB synthetic data is included.
live=traceBytes+projectedOther
zipOverhead=math.ceil(live/16384)*5+len(m['segments'])*512
reserve=2*live+zipOverhead # live plus one uncompressed-size archive; same-volume duplicate archive would need another live.
result=dict(comparableRollingMeasurements=comp,hashOnlyMeasuredSeconds=hashSeconds,hashOnlySlowPassProjectionSeconds=slow,throughputBytesSecond=cal['bytesPerSecond'],calibrationCachedLogicalReads=cal['cachedLogicalReads'],medium=dict(workloadSeconds=work,observationHoldSeconds=90,workOverheadSeconds=overhead,observerClosureSeconds=closure,tracerReadyToWorkSeconds=before,tracerReadyToFinalShutdownSeconds=shutdown-ready['qpc']/freq,preparedToClosedSeconds=h['OBSERVERS_CLOSED']-h['PREPARED']),duration=dict(expectedIllustrativeSeconds=expected,conservativeIllustrativeSeconds=conservative,existingTracerCollectionLimitSeconds=durationBound,note='1200 is collection-loop limit, not a proven bound on blocked API calls, close/flush or archive. Medium finalization failed; successful large finalization duration is unmeasured.'),projection=dict(expectedRecords=rowsExpected,conservativeRecords=rowsConservative,empiricalPeakSustainedUpperRecords=empiricalUpper,variabilityFactor=factor,marginRecords=envelope,expectedTraceBytes=math.ceil(rowsExpected*m['bytesPerRecord']['mean']),conservativeTraceBytes=math.ceil(rowsConservative*m['bytesPerRecord']['max']),marginTraceBytes=traceBytes,existingRecordBudget=m['sinkManifest']['recordBudget'],existingStorageBudget=m['sinkManifest']['storageBudgetBytes'],note='Empirical conditional scenarios only; max measured record 632, parser permits 8192. Not guaranteed future record lengths/rate.'),auxiliary=dict(measuredNonSegmentBytes=otherBytes,projectedNonSegmentBytes=projectedOther,tapRows=tap,tapLimit=20000,tapProjectedExpected=math.ceil(tap/m['eventSpanSeconds']*expected),tapProjectedConservative=math.ceil(tap/m['eventSpanSeconds']*conservative),tapProjected1200=math.ceil(tap/m['eventSpanSeconds']*1200),applicationEvents=app,projectedApplicationEvents1200=math.ceil(app/m['eventSpanSeconds']*1200),nativeEntries=native,projectedNativeEntries1200=math.ceil(native/m['eventSpanSeconds']*1200),processIdentityLimit=8192,projectedKernelIdentities1200=math.ceil(563/m['eventSpanSeconds']*1200)),storage=dict(empiricalLiveAndOneArchiveReserveBytes=reserve,additionalTemporaryArchiveCopyBytes=live,existingTraceHardCapPlusOneArchiveBytes=2*m['sinkManifest']['storageBudgetBytes'],measuredFreeBytes=1795659227136,validCompleteUpperBound=False,reason='Auxiliary artifact byte quotas and worst-case archive/finalizer working storage are not enforced; EventTap conservative projection exceeds its existing limit. Do not claim a complete safe reserve.'),decision='STOP: capacity safety not established for complete observer/evidence pipeline; do not launch fresh stress/medium/large campaign before review.',noCandidateChanges=True)
(R/'capacity-plan.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
