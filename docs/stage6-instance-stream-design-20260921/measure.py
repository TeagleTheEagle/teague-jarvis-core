import pathlib,json,statistics,hashlib,zipfile,math,collections
R=pathlib.Path(__file__).parent;P=R.parent/'stage6-identity-capacity-recalibration-20260921';read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
M=read(P/'capacity-measurement.json');oldplan=read(P/'capacity-plan.json');F=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\f469b94b665e4808af1c5bb6aa46b207\code\protected-00a17b2c499c4966a5113c30924b367a')
lengths=[];pts=[];peakLengths=[];lo=M['rolling']['1']['startQpc'];hi=M['rolling']['1']['exclusiveEndQpc']
for seg in M['segments']:
 p=F/seg['name'];assert hashlib.sha256(p.read_bytes()).hexdigest()==seg['sha256']
 with p.open('rb') as f:
  for line in f:
   r=json.loads(line);n=len(line);lengths.append(n);pts.append((r['qpc'],n))
   if lo<=r['qpc']<hi:peakLengths.append(n)
lengths.sort();pts.sort();j=0;total=0;maxBytes=0;maxWindow=None
for i,(q,n) in enumerate(pts):
 while j<len(pts) and pts[j][0]<q+10000000:total+=pts[j][1];j+=1
 if total>maxBytes:maxBytes=total;maxWindow=q
 total-=n
archive=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 TRACE CAPACITY NATIVE ENTRY 20260921\evidence.zip')
with zipfile.ZipFile(archive) as z:
 zs=[x for x in z.infolist() if x.filename.startswith('medium-candidate/protected-00a17b2c499c4966a5113c30924b367a/trace-')]
 assert len(zs)==48;raw=sum(x.file_size for x in zs);compressed=sum(x.compress_size for x in zs)
seconds=oldplan['duration']['expectedIllustrativeSeconds'];conservative=oldplan['duration']['conservativeIllustrativeSeconds'];windows=M['rolling'];rate60=windows['60']['perSecond']
# A measured burst allowance above the 60-second sustained rate, not peak sustained forever.
burst=max(v['records']-rate60*int(k) for k,v in windows.items());sustainedExpected=math.ceil(M['meanRate']*seconds);burstExpected=math.ceil(rate60*seconds+burst);burstConservative=math.ceil(rate60*conservative+burst);burstEnvelope=math.ceil(rate60*1200+burst)
totalCap=137438953472;maxSegments=16384;descriptor=512;controlFiles=16;controlCap=65536;rootManifestCap=65536
metadataCap=maxSegments*descriptor+controlFiles*controlCap+rootManifestCap;live=totalCap+metadataCap
members=maxSegments+controlFiles+2;zipHeaders=members*(30+46+2*96+64)+98
# Candidate proposal only: ZIP_STORED, bounded 96-byte member names, streaming verification.
archiveMax=live+zipHeaders;tmp=maxSegments*descriptor+rootManifestCap
cluster=4096;allocationSlack=(members+2)*(cluster-1);reserve=live+archiveMax+tmp+allocationSlack
amb=read(P/'events-22.json');counts=collections.Counter(x['status'] for x in amb)
result=dict(mediumRecords=len(lengths),size=dict(total=sum(lengths),mean=statistics.mean(lengths),median=statistics.median(lengths),p95=lengths[math.ceil(len(lengths)*.95)-1],p99=lengths[math.ceil(len(lengths)*.99)-1],max=max(lengths)),recordPeakByteRate=sum(peakLengths),recordPeakMeanSize=statistics.mean(peakLengths),maximumRollingByteRate=maxBytes,maximumByteWindowStart=maxWindow,compression=dict(raw=raw,compressed=compressed,ratio=raw/compressed,notUsedToReduceReserve=True),rate=dict(mean=M['meanRate'],peak=97212,peakMeanRatio=97212/M['meanRate'],rolling=windows),duration=oldplan['duration'],countModels=dict(sustainedExpected=sustainedExpected,burstAllowanceRecords=burst,expectedWithBurst=burstExpected,conservativeWithBurst=burstConservative,empirical1200EnvelopeWithBurst=burstEnvelope,note='Burst allowance treats observed maximum excess as one burst; recurrence uncertainty is unmeasured, so not a validated upper bound. Instantaneous peak is NOT assumed sustained for 1200 seconds.',configuredHardRecordLimit=196531200),proposedReserve=dict(status='DESIGN ONLY; NOT ENFORCED BY CURRENT COLLECTOR',totalAuthoritativeBytes=totalCap,maxSegments=maxSegments,maxDescriptorBytes=descriptor,controlFiles=controlFiles,maxControlBytes=controlCap,metadataCap=metadataCap,liveBytes=live,archiveFormat='ZIP_STORED',archiveMaxBytes=archiveMax,temporaryFinalizationBytes=tmp,clusterAssumption=cluster,allocationSlack=allocationSlack,requiredReserve=reserve,verifyAdditionalDiskBytes=0,note='Requires single shared quota across EVERY authoritative artifact, bounded names/counts, quota-aware control files, and measured cluster size <=4096. No separate D: archive copy permitted within this reserve. Not implemented or accepted.'),historicalClassification=counts,mediumHeartbeat=max(r['interval'] for r in read(F/'app-heartbeats.json')),mediumEtwLoss=read(F/'etw-result.json')['eventsLost'])
(R/'measurements.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ('rate',)},indent=2))
