import pathlib,json,hashlib,zipfile,collections,math,bisect
R=pathlib.Path(__file__).parent
P=R.parent/'stage6-large-small-integration-20260922'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):
 with (R/n).open('x',encoding='utf8') as f:json.dump(v,f,indent=2)
run=load(P/'normal-run.json');C=pathlib.Path(run['code']);root=pathlib.Path(run['root'])
receipt=load(P/'archive-verification.json');archive=pathlib.Path(receipt['archive']);manifest=load(archive.parent/'manifest.json')
assert sha(archive)==receipt['archiveSHA256'] and sha(archive.parent/'manifest.json')==receipt['manifestSHA256']
with zipfile.ZipFile(archive) as z:
 assert set(z.namelist())==set(manifest)
 for n,v in manifest.items():
  b=z.read(n);assert len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==v['sha256']
  if n.startswith('candidate/'+root.name+'/'):
   p=C/n.removeprefix('candidate/');assert p.stat().st_size==v['bytes'] and sha(p)==v['sha256']
for v in load(C/'small-source.json'):
 p=C/v['name'];assert p.stat().st_size==v['bytes'] and sha(p)==v['sha256']
snapshot=[]
for p in sorted(root.rglob('*')):
 if p.is_file():snapshot.append(dict(path=str(p),bytes=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns,sha256=sha(p)))
save('preservation-before.json',dict(archiveMembersVerified=len(manifest),archiveSHA256=sha(archive),files=snapshot))
def stats(xs):
 xs=sorted(xs)
 return dict(count=len(xs),min=xs[0],median=xs[len(xs)//2],p95=xs[math.ceil(.95*len(xs))-1],p99=xs[math.ceil(.99*len(xs))-1],max=xs[-1],mean=sum(xs)/len(xs)) if xs else None
kernel=load(root/'etw-result.json');detail=load(root/'detail/etw-result.json');kr=load(root/'etw-ready.json');dr=load(root/'detail/etw-ready.json');ar=load(root/'app-ready.json');f=kr['frequency'];origin=kr['qpc']
assert f==dr['frequency']==ar['frequency']
rows=[]
for s in load(root/'detail/startup-events.json')['segments']:
 p=root/'detail'/s['name'];assert sha(p)==s['sha256']
 with p.open() as stream:rows.extend(json.loads(line) for line in stream)
assert len(rows)==151173
timeline=[dict(stage=n,qpc=x,secondsAfterAuthorityReady=(x-origin)/f) for n,x in [('authority_ready',kr['qpc']),('detail_ready',dr['qpc']),('application_ready',ar['qpc'])]]
for x in load(root/'integration-launcher.json'):
 timeline.append(dict(stage='launcher:'+x['event'],qpc=x['qpc'],secondsAfterAuthorityReady=(x['qpc']-origin)/f,detail=x['detail']))
for p in root.glob('integration-*.json'):
 if p.name=='integration-launcher.json':continue
 for x in load(p):timeline.append(dict(stage=x['role']+':'+x['event'],pid=x['pid'],qpc=x['qpc'],secondsAfterAuthorityReady=(x['qpc']-origin)/f))
for n in (1,2):
 v=load(root/f'hash-pass-{n}.json')
 # Python perf_counter_ns shares the clock basis, but uses nanoseconds rather than native ticks.
 for edge in ('begin','end'):
  x=v[edge+'QpcNs']*f/1e9;timeline.append(dict(stage=f'hash{n}:{edge}',qpc=x,secondsAfterAuthorityReady=(x-origin)/f,clock='perf_counter_ns scaled by recorded QPC frequency'))
save('timeline.json',sorted(timeline,key=lambda x:x['qpc']))
lag=[(x['callbackQpc']-x['qpc'])/f for x in rows]
perprovider={p:stats([(x['callbackQpc']-x['qpc'])/f for x in rows if x['provider']==p]) for p in sorted({x['provider'] for x in rows})}
lags=sorted(rows,key=lambda x:x['callbackQpc']-x['qpc'],reverse=True)[:20]
save('longest-deliveries.json',[dict(provider=x['provider'],pid=x['pid'],created=x['created'],eventQpc=x['qpc'],callbackQpc=x['callbackQpc'],lagSeconds=(x['callbackQpc']-x['qpc'])/f) for x in lags])
def rolling(qs,width):
 qs=sorted(qs);j=0;best=(0,0)
 for i,x in enumerate(qs):
  while qs[j]<=x-width:j+=1
  if i-j+1>best[0]:best=(i-j+1,qs[j])
 return dict(count=best[0],beginQpc=best[1],seconds=width/f)
kernel_lags=[];identities=[]
for r in kernel['rows']:
 for edge in ('start','stop'):
  kernel_lags.append(dict(pid=r['pid'],created=r['created'],edge=edge,eventQpc=r[edge+'Qpc'],callbackQpc=r[edge+'CallbackQpc'],lagSeconds=(r[edge+'CallbackQpc']-r[edge+'Qpc'])/f))
 identities.append(dict(pid=r['pid'],created=r['created'],image=r['image'],sequence=r['sequence'],startQpc=r['startQpc'],stopQpc=r['stopQpc'],handleRetained=r['handleRetained'],handleClosed=r['handleClosed']))
save('authority-deliveries.json',kernel_lags)
observer=load(root/'observer-identities.json')
perpid=[]
for key,cnt in collections.Counter((x['pid'],x['created']) for x in rows).most_common():
 rr=[x for x in rows if (x['pid'],x['created'])==key]
 image=next((x['image'] for x in detail['rows'] if (x['pid'],x['created'])==key),'UNKNOWN')
 perpid.append(dict(pid=key[0],created=key[1],image=image,records=cnt,providerCounts=dict(collections.Counter(x['provider'] for x in rr)),deliveryLag=stats([(x['callbackQpc']-x['qpc'])/f for x in rr])))
manifest_detail=load(root/'detail/startup-events.json');writer=load(root/'kernel-authority-result.json');telemetry=load(root/'kernel-authority-telemetry.json')
timings=load(root/'stage-timing.json')['spans']
periods=[]
sortedrows=sorted(rows,key=lambda x:x['callbackQpc'])
for a,b in zip(sortedrows,sortedrows[1:]):
 periods.append(dict(seconds=(b['callbackQpc']-a['callbackQpc'])/f,beforeQpc=a['callbackQpc'],afterQpc=b['callbackQpc'],beforeProvider=a['provider'],afterProvider=b['provider']))
result=dict(status='DIAGNOSIS_NOT_ACCEPTANCE',lossCounters={k:{n:v[n] for n in ('eventsLost','realtimeBuffersLost','buffersLost','faults','flushResult','stopResult','consumerResult')} for k,v in [('authority',kernel),('detail',detail)]},detailRecords=len(rows),detailProviderCounts=dict(collections.Counter(x['provider'] for x in rows)),detailDeliveryLag=stats(lag),detailDeliveryLagByProvider=perprovider,authorityDeliveryLag=stats([x['lagSeconds'] for x in kernel_lags]),detailEventPeak1s=rolling([x['qpc'] for x in rows],f),detailCallbackPeak1s=rolling([x['callbackQpc'] for x in rows],f),detailEventWindow=(max(x['qpc'] for x in rows)-min(x['qpc'] for x in rows))/f,detailCallbackWindow=(max(x['callbackQpc'] for x in rows)-min(x['callbackQpc'] for x in rows))/f,perProcess=perpid,detailWriter={k:manifest_detail[k] for k in ('fault','accepted','persisted','bytes','peakQueueBytes','maximumWriteSeconds')},authorityWriter=writer,authorityTelemetry=telemetry,applicationLongestStages=sorted(timings,key=lambda x:x['seconds'],reverse=True)[:20],persistedCallbackGaps=sorted(periods,key=lambda x:x['seconds'],reverse=True)[:10],observers=observer,missingMeasurements=['loss-counter timeline','actual NumberOfBuffers/FreeBuffers','provider-enable duration','ProcessTrace entry timestamp','callback duration and filtering count before persistence','consumer lock wait/hold duration','detail segment flush timestamps','CPU scheduling of tracer threads','system-wide event arrival rate before filtering'])
save('analysis.json',result)
old=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\89b6e99f90a747108e7c5aa2ce15dacc\code')
lineage={n:dict(current=sha(C/n),older=sha(old/n),matches=sha(C/n)==sha(old/n)) for n in ('J6StartupTrace.exe','startup_trace.cpp')}
lineage['trace_sink.hpp']=dict(currentPresent=(C/'trace_sink.hpp').exists(),older=str(old/'trace_sink.hpp'),olderSHA256=sha(old/'trace_sink.hpp'),note='Historical header inspection only; current copied candidate omits build header')
save('source-lineage.json',lineage)
for v in snapshot:
 p=pathlib.Path(v['path']);assert p.stat().st_size==v['bytes'] and p.stat().st_mtime_ns==v['mtime_ns'] and sha(p)==v['sha256']
save('preservation-after.json',dict(status='PASS',filesVerified=len(snapshot),archiveSHA256=sha(archive),archiveUnchanged=sha(archive)==receipt['archiveSHA256']))
print(json.dumps({k:result[k] for k in ('detailProviderCounts','detailDeliveryLag','authorityDeliveryLag','detailEventPeak1s','detailCallbackPeak1s','detailEventWindow','detailCallbackWindow','detailWriter')}))
print(json.dumps(dict(perProcess=[dict(pid=x['pid'],image=x['image'],records=x['records'],maxLag=x['deliveryLag']['max']) for x in perpid],sourceLineage=lineage)))
