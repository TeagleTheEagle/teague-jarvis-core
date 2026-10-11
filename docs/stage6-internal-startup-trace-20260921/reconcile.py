import pathlib,json,hashlib,statistics,collections
R=pathlib.Path(__file__).parent;read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();a=read(R/'analysis.json');checks=[];identities=[]
def check(n,v):checks.append(dict(name=n,pass_=bool(v)));assert v,n
def stats(xs):return dict(n=len(xs),min=min(xs),median=statistics.median(xs),max=max(xs))
plans=[read(R/n) for n in ('plan.json','followup-plan.json','control-plan.json')]
for num,p in enumerate(plans):
 C=pathlib.Path(p['code']);F=pathlib.Path(p['root']);m=read(R/'diagnostic-hashes.json') if num==0 else p['diagnosticHashes']
 for x in m:check(f'copy{num}: '+x['name'],sha(C/x['name'])==x['sha256'])
 k=read(F/'etw-result.json');exit=read(F/'observer-exit.json');check(f'observer exit {num}',exit['exited'] and exit['exitCode']==0)
 for name in ('faults','eventsLost','realtimeBuffersLost','buffersLost','flushResult','stopResult','consumerResult'):check(f'kernel {num} {name}',k[name]==0)
 for r in k['rows']:
  ret=r['handleRetained'];post=not ret and r['reason']=='OPEN_PROCESS_FAILED' and r['openError']==87 and int(r['sequence']) and r['stopQpc'] and r['handleAttemptQpc']>=r['stopQpc'] and int(r['exitFiletime']) and r['exitCodeKnown']
  check(f'exit {num} {r["pid"]}:{r["created"]}',r['stopQpc'] and int(r['exitFiletime'])>=int(r['created']) and r['handleClosed'] and (ret and r['signalObservedQpc'] or post))
  identities.append(dict(pid=r['pid'],created=r['created'],image=r['image'],exitFiletime=r['exitFiletime'],run=num,retained=ret,qualifiedPostExit=bool(post)))
 for name in ('observer-identity.json','launcher.json'):
  q=read(F/name);identities.append(dict(pid=q['pid'],created=q['created'],image=q['image'],run=num,source=name))
for x in plans[0]['sourceHashes']:check('original '+x['name'],sha(pathlib.Path(plans[0]['source'])/x['name'])==x['sha256'])
for x in read(R/'first-failure-freeze.json'):
 f=pathlib.Path(x['path']);check('preserved failed run '+f.name,sha(f)==x['sha256'] and f.stat().st_size==x['bytes'] and f.stat().st_mtime_ns==x['mtime'])
old=read(R.parent/'stage6-preserved-probe-sampler-diagnosis-20260921'/'freeze.json')
for x in old['rawFiles']:
 f=pathlib.Path(x['path']);check('historical failure '+f.name,sha(f)==x['sha256'] and f.stat().st_mtime_ns==x['mtime_ns'])
control=read(pathlib.Path(plans[2]['root'])/'probes.json');check('40 control probes',len(control)==40)
groups={}
for c in ('idle','C-read','C-hash','D-hash'):
 xs=[(int(x['exitFiletime'])-int(x['created']))/1e7 for x in control if x['condition']==c]
 g=a['groups'][c];st=stats(xs);groups[c]=dict(processOnly=st,fullETW=g['minimal'],fullETWWithEntry=g['entry'],fullETWMedianDifference=g['minimal']['median']-st['median'],debugMarkerMedianDifference=g['entry']['median']-g['minimal']['median'])
for x in control:check('control '+str(x['index']),x['finalWait']==0 and x['observerResult']==0 and x['exitCode']==0 and not x['fault'] and not x['deadlineExceeded'])
ev=read(pathlib.Path(plans[1]['root'])/'startup-events.json')['events']
strings=[str(v) for e in ev for v in e['fields'].values() if isinstance(v,str)]
forbidden=[s for s in strings if any(t in s.lower() for t in ('jarvis-clean-win11','virtualbox vms','.vbox','.vdi','.nvram','\\.virtualbox\\'))]
check('no protected trace paths',not forbidden)
derived=dict(selfEffect=groups,traceChecks=len(a['checks']),reconciliationChecks=len(checks),probeCount=80,controlCount=40,initialFailedDiagnosticProbes=2,kernelIdentityCount=sum(1 for x in identities if 'retained' in x),retained=sum(x.get('retained',False) for x in identities),postExit=sum(x.get('qualifiedPostExit',False) for x in identities),entryMarkerCount=sum(t['T6_PEEntry'] is not None for t in a['timelines']),entryAfterCreate=stats([x['postCreateToEntry'] for x in a['timelines'] if x['postCreateToEntry'] is not None]),firstScheduleToEntry=stats([x['firstScheduledToEntry'] for x in a['timelines'] if x['firstScheduledToEntry'] is not None]),largestImageEventGap=max((x['largestImageEventGap'] for x in a['timelines'] if x['largestImageEventGap']),key=lambda x:x['seconds']),debugHandling=stats([x['debugHandlingSeconds'] for x in a['timelines'] if x['mode']=='entry']),helperCount=len(a['helpers']),helperPreEntry=sum(h['startRelativeToEntrySeconds'] is not None and h['startRelativeToEntrySeconds']<0 for h in a['helpers']),helperStartAfterParent=stats([h['startAfterParentSeconds'] for h in a['helpers']]),helperMaxLifetime=max(h['kernelLifetime'] for h in a['helpers']),fileOperationCounts=dict(collections.Counter(e['id'] for e in ev if e['provider']=='file')),protectedPathsInTrace=forbidden,checks=checks)
with (R/'reconciliation.json').open('x') as f:json.dump(derived,f,indent=2)
with (R/'recorded-identities.json').open('x') as f:json.dump(identities,f,indent=2)
print(json.dumps({k:v for k,v in derived.items() if k!='checks'}))
