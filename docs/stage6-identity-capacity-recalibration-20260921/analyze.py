"""Read preserved diagnostic evidence only; write new analysis, never source evidence."""
import collections, datetime, hashlib, json, pathlib, re, statistics, sys, zipfile, math
R=pathlib.Path(__file__).parent
OLD=R.parent/'stage6-trace-capacity-native-entry-20260921'
C=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\f469b94b665e4808af1c5bb6aa46b207\code')
F=C/'protected-00a17b2c499c4966a5113c30924b367a'
A=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 TRACE CAPACITY NATIVE ENTRY 20260921')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(name,obj):
 with (R/name).open('x',encoding='utf-8') as f:json.dump(obj,f,indent=2)
def inventory(p):
 result=[]
 for f in sorted(p.rglob('*')):
  if f.is_file():
   s=f.stat(); h=digest(f); t=f.stat()
   assert (s.st_size,s.st_mtime_ns)==(t.st_size,t.st_mtime_ns),str(f)
   result.append(dict(path=str(f),name=f.relative_to(p).as_posix(),bytes=s.st_size,mtimeNs=s.st_mtime_ns,sha256=h))
 return result
if sys.argv[1]=='freeze':
 hashes=read(OLD/'medium-candidate/candidate-hashes.json')
 for row in hashes:assert digest(C/row['name'])==row['sha256'],row['name']
 before=inventory(F)
 expected=read(OLD/'archive-verification.json')
 assert digest(A/'evidence.zip')==expected['zipSHA256']
 assert digest(A/'archive-manifest.json')==expected['manifestSHA256']
 manifest=read(A/'archive-manifest.json')
 with zipfile.ZipFile(A/'evidence.zip') as z:
  assert len(z.infolist())==len(manifest)+1==1078
  assert sorted(z.namelist())==sorted([x['name'] for x in manifest]+['archive-manifest.json'])
  assert z.read('archive-manifest.json')==(A/'archive-manifest.json').read_bytes()
  for row in manifest:
   with z.open(row['name']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['sha256'],row['name']
   assert z.getinfo(row['name']).file_size==row['bytes']
 save('freeze.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidateHashes=hashes,mediumEvidence=before,archive=expected,archiveMembersVerified=len(manifest)+1,protectedAccess=False,productionWrites=False))
 print('FREEZE PASS',len(hashes),len(before),len(manifest),flush=True)
elif sys.argv[1]=='identity':
 kernel=read(F/'etw-result.json'); rows=kernel['rows']; checker=read(F/'integrated-cleanup.json')
 native=[read(p) for p in F.glob('native-*.json') if re.fullmatch(r'native-\d+-\d+\.json',p.name)]
 handles=read(F/'tree-handles.json')['rows']; tap=read(F/'app-tap.json'); receipts=read(F/'app-receipts.json')
 events=[json.loads(l) for l in (F/'app-events.jsonl').read_text(encoding='utf-8-sig').splitlines()]
 seq={r['sequence']:r for r in rows}; out=[]
 for i,u in enumerate(checker['lineageUnknown'],1):
  e=u['event']; candidates=[seq[s] for s in u['candidates']]
  taps=[t for t in tap if all(t.get(k)==e.get(k) for k in ('pid','kind','nativeTime','parentPid')) and t['name'].lower()==e['name'].lower()]
  own=[r for r in rows if r['pid']==e['pid']]
  parents=[r for r in rows if r['pid']==e['parentPid']]
  details=[]
  for r in candidates:
   key=(r['pid'],r['created'])
   details.append(dict(kernel=r,native=[n for n in native if (n['pid'],n['created'])==key],retained=[h for h in handles if (h['pid'],h['created'])==key],associatedApplication=[a for a in events if a['pid']==r['pid']]))
  status='AMBIGUOUS' if len(candidates)>1 else 'UNMATCHED' if not candidates else 'UNIQUE_MATCH'
  out.append(dict(index=i,status=status,rawUnknown=u,applicationImage='UNKNOWN: notification supplies basename only',applicationCreationIdentity='UNKNOWN: nativeTime is notification TIME_CREATED',callbackAndEnqueue=taps,persistenceReceipts=[r for r in receipts if r['queueSequence']==e['queueSequence']],candidates=details,allKernelSamePid=own,allKernelSameParentPid=parents,reason='Notification has no creation/sequence identity. Independent exits prove processes ended, not which notification belongs to which reused PID.' if candidates else 'No captured kernel identity meets notification PID/name/parent/time constraints. Parent/PID reuse makes relation possible but does not prove membership.'))
 save('events-22.json',out)
 counts=collections.Counter(x['status'] for x in out)
 save('identity-summary.json',dict(counts=counts,events=len(out),kernelRows=len(rows),nativeRows=len(native),rawFailure=checker['errors'],clockFrequency=read(F/'etw-ready.json')['frequency'],distinctPidCount=len({r['pid'] for r in rows}),reusedPids={str(k):v for k,v in collections.Counter(r['pid'] for r in rows).items() if v>1}))
 lines=['# All 22 preserved application events','', 'Raw fields, callbacks, enqueue/persistence receipts and every competing kernel identity are preserved in events-22.json. FILETIME below is notification time, not creation time.','', '| # | Kind | Event ID / queue ID | PID / parent | Notification FILETIME | Receipt QPC | Candidates: sequence / creation FILETIME | Disposition |','|---|---|---|---|---|---|---|---|']
 for o in out:
  e=o['rawUnknown']['event']; cs='; '.join(str(x['kernel']['sequence'])+' / '+str(x['kernel']['created']) for x in o['candidates']) or 'none'
  lines.append(f"| {o['index']} | {e['kind']} | {e['eventIdentifier']} / {e['queueSequence']} | {e['pid']} / {e['parentPid']} | {e['nativeTime']} | {e['receivedQpc']} | {cs} | {o['status']} |")
 (R/'EVENTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print(json.dumps(counts));print('\n'.join(lines),flush=True)
elif sys.argv[1]=='capacity':
 m=read(F/'startup-events.json'); freq=read(F/'etw-ready.json')['frequency']; pts=[]; providers=collections.Counter(); identities=collections.Counter(); segments=[]; lengths=[]
 for s in m['segments']:
  p=F/s['name'];assert digest(p)==s['sha256']; qs=[];n=0
  with p.open('rb') as f:
   for line in f:
    r=json.loads(line); q=r['qpc']; pts.append((q,r['provider'],r['pid'],str(r.get('created','UNKNOWN'))));qs.append(q);lengths.append(len(line));providers[r['provider']]+=1;identities[(r['pid'],str(r.get('created','UNKNOWN')))]+=1;n+=1
  assert n==s['records'];segments.append(dict(**s,minimumEventQpc=min(qs),maximumEventQpc=max(qs),mtimeNs=p.stat().st_mtime_ns))
  print('segment',s['name'],flush=True)
 pts.sort(); windows={}
 for seconds in (1,5,10,60):
  j=0;best=(0,0,0)
  for i,p in enumerate(pts):
   while j<len(pts) and pts[j][0]<p[0]+seconds*freq:j+=1
   if j-i>best[0]:best=(j-i,i,j)
  n,i,j=best;windows[str(seconds)]=dict(records=n,perSecond=n/seconds,startQpc=pts[i][0],exclusiveEndQpc=pts[i][0]+seconds*freq,providers=collections.Counter(p[1] for p in pts[i:j]))
 dur=(pts[-1][0]-pts[0][0])/freq
 calpath=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\1c1f5d0c390b42cc9ba9f4f6221dabc6\code\calibration.json')
 cal=read(calpath)
 result=dict(definition='Exact rolling half-open [eventQpc,eventQpc+window); sorted by QPC; duplicate timestamps included; event coverage duration is not full launcher wall time.',eventSpanSeconds=dur,totalRecords=len(pts),totalBytes=m['bytes'],meanRate=len(pts)/dur,rolling=windows,providers=providers,perIdentity=[dict(pid=k[0],created=k[1],records=v) for k,v in identities.most_common()],bytesPerRecord=dict(min=min(lengths),mean=statistics.mean(lengths),max=max(lengths)),segments=segments,segmentCount=len(segments),segmentsPerEventSecond=len(segments)/dur,segmentMtimeIntervalsSeconds=[(b['mtimeNs']-a['mtimeNs'])/1e9 for a,b in zip(segments,segments[1:])],calibration=cal,calibrationSHA256=digest(calpath),sinkManifest=m)
 save('capacity-measurement.json',result)
 print(json.dumps({k:v for k,v in result.items() if k not in ('segments','perIdentity','calibration','sinkManifest')}),flush=True)
