import pathlib,json,collections,statistics,hashlib
R=pathlib.Path(__file__).parent;read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));p=read(R/'followup-plan.json');F=pathlib.Path(p['root']);k=read(F/'etw-result.json');ev=read(F/'startup-events.json')['events'];probes=read(F/'probes.json');freq=probes[0]['frequency'];checks=[]
def check(name,v):checks.append(dict(name=name,pass_=bool(v)));assert v,name
check('80 probes completed',len(probes)==80 and read(F/'result.json')['failure'] is None)
for key in ('faults','eventsLost','realtimeBuffersLost','buffersLost','flushResult','stopResult','consumerResult'):check('kernel '+key,k[key]==0)
check('event buffer not overflowed',read(F/'startup-events.json')['overflow']==0)
byid={(r['pid'],r['created']):r for r in k['rows']};byevents=collections.defaultdict(list)
for e in ev:byevents[e['pid'],e['created']].append(e)
timelines=[];filepairs=[];regtimes=[];fileambiguous=[];fileunmatched=[];helpers=[];identityproof=[]
for r in k['rows']:
 key=r['pid'],r['created'];retained=r['handleRetained'];qualified=(not retained and r['reason']=='OPEN_PROCESS_FAILED' and r['openError']==87 and r['sequence']!='0' and r['stopQpc'] and r['exitFiletime']!='0' and r['exitCodeKnown'] and r['handleAttemptQpc']>=r['stopQpc'])
 check('kernel exit '+str(key),r['stopQpc'] and int(r['exitFiletime'])>=int(r['created']) and r['handleClosed'] and (retained and r['signalObservedQpc'] or qualified))
 identityproof.append(dict(pid=r['pid'],created=r['created'],sequence=r['sequence'],retained=retained,qualifiedPostExit=bool(qualified),exitFiletime=r['exitFiletime'],image=r['image']))
for x in probes:
 key=x['pid'],x['created'];r=byid[key];es=sorted(byevents[key],key=lambda e:e['qpc']);entry=x['entryQpc'];end=r['stopQpc'];start=r['startQpc'];primary=x['tid']
 check('probe completed '+str(key),not x['fault'] and not x['deadlineExceeded'] and x['finalWait']==0 and x['observerResult']==0 and x['exitCode']==0 and x['controllerExit']==0)
 check('kernel identity agrees '+str(key),r['exitFiletime']==x['exitFiletime'])
 if x['mode']=='entry':check('PE breakpoint reached '+str(key),entry>0 and sum(e['event']=='PE_ENTRY_EXECUTED' for e in x['events'])==1)
 ts=[e['qpc'] for e in es if e['provider']=='process' and e['id']==3 and e['fields'].get('ThreadID')==primary]
 scheduled=[e['qpc'] for e in ev if e['provider']=='scheduler' and e['fields'].get('newTid')==primary and start<=e['qpc']<=end]
 images=[e for e in es if e['provider']=='process' and e['id']==5];firstimage=min((e['qpc'] for e in images),default=None)
 gaps=[dict(seconds=(b['qpc']-a['qpc'])/freq,previous=a['fields'].get('ImageName'),next=b['fields'].get('ImageName')) for a,b in zip(images,images[1:])]
 t=dict(index=x['index'],condition=x['condition'],mode=x['mode'],pid=x['pid'],created=x['created'],T0_launch=x['launchQpc'],T1_createEntry=x['createBeginQpc'],T2_createReturn=x['createEndQpc'],T3_primaryThreadHandleAvailable=x['createEndQpc'],T4_kernelProcessEvent=start,T4_primaryThreadStart=min(ts) if ts else None,T5_firstImage=firstimage,T6_PEEntry=entry or None,T7_runtimeInitialized='UNKNOWN',T8_intendedWork='UNKNOWN',firstPrimaryScheduled=min(scheduled) if scheduled else None,lifetime=(int(x['exitFiletime'])-int(x['created']))/1e7,createSeconds=(x['createEndQpc']-x['createBeginQpc'])/freq,postCreateToEntry=(entry-x['createEndQpc'])/freq if entry else None,firstScheduledToEntry=(entry-min(scheduled))/freq if entry and scheduled else None,entryToKernelStop=(end-entry)/freq if entry else None,debugHandlingSeconds=x['debugHandlingTicks']/freq,imageCount=len(images),largestImageEventGap=max(gaps,key=lambda a:a['seconds']) if gaps else None)
 timelines.append(t)
 for h in k['rows']:
  if h['parentSequence']==r['sequence'] and h['parentPid']==r['pid']:
   he=byevents[h['pid'],h['created']];activity=min((e['qpc'] for e in he if e['provider']=='scheduler' and e['fields'].get('newTid')),default=None)
   helpers.append(dict(probe=x['index'],pid=h['pid'],created=h['created'],parentPid=r['pid'],parentSequence=r['sequence'],image=h['image'],startAfterParentSeconds=(h['startQpc']-start)/freq,startRelativeToEntrySeconds=(h['startQpc']-entry)/freq if entry else None,kernelLifetime=(int(h['exitFiletime'])-int(h['created']))/1e7,firstActivityQpc=activity,exitRelativeParentSeconds=(h['stopQpc']-end)/freq,creationRequest='UNKNOWN'))
# Correlate only process-qualified IRP starts/ends; unmatched or nested IRP records remain explicit.
for key,es in byevents.items():
 pending={}
 for e in sorted(es,key=lambda e:e['qpc']):
  fs=e['fields']
  if e['provider']=='file' and fs.get('Irp'):
   irp=fs['Irp']
   if e['id']==24:
    a=pending.pop(irp,None)
    if a and a.get('ambiguous') is not True:
     row=dict(pid=key[0],created=key[1],operation=a['id'],beginQpc=a['qpc'],endQpc=e['qpc'],seconds=(e['qpc']-a['qpc'])/freq,path=a['fields'].get('FileName','UNKNOWN'),status=fs.get('Status'));filepairs.append(row)
    else:fileambiguous.append(dict(pid=key[0],qpc=e['qpc'],irp=irp,reason='missing or overlapping start'))
   elif irp in pending:pending[irp]['ambiguous']=True
   else:pending[irp]=dict(e)
  if e['provider']=='registry_classic' and fs.get('InitialTime') and 0<fs['InitialTime']<=e['qpc']:
   regtimes.append(dict(pid=key[0],created=key[1],opcode=e['opcode'],beginQpc=fs['InitialTime'],endQpc=e['qpc'],seconds=(e['qpc']-fs['InitialTime'])/freq,key=fs.get('KeyName','UNKNOWN'),status=fs.get('Status')))
 fileunmatched.extend(dict(pid=key[0],qpc=a['qpc'],operation=a['id'],ambiguous=a.get('ambiguous',False)) for a in pending.values())
def stats(values):return dict(n=len(values),min=min(values) if values else None,median=statistics.median(values) if values else None,max=max(values) if values else None)
groups={c:{m:stats([x['lifetime'] for x in timelines if x['condition']==c and x['mode']==m]) for m in ('minimal','entry')} for c in ('idle','C-read','C-hash','D-hash')}
perProbe={t['pid']:t for t in timelines}
startupFiles=[e for e in filepairs if e['pid'] in perProbe and perProbe[e['pid']]['T6_PEEntry'] and e['beginQpc']>=perProbe[e['pid']]['T4_kernelProcessEvent'] and e['endQpc']<=perProbe[e['pid']]['T6_PEEntry']]
startupRegs=[e for e in regtimes if e['pid'] in perProbe and perProbe[e['pid']]['T6_PEEntry'] and e['beginQpc']>=perProbe[e['pid']]['T4_kernelProcessEvent'] and e['endQpc']<=perProbe[e['pid']]['T6_PEEntry']]
out=dict(checks=checks,timelines=timelines,groups=groups,helpers=helpers,kernelIdentities=identityproof,eventCounts=dict(collections.Counter(e['provider'] for e in ev)),totalEvents=len(ev),maxCallbackLag=max(e['callbackQpc']-e['qpc'] for e in ev)/freq,filePairs=len(filepairs),fileAmbiguous=len(fileambiguous),fileUnmatched=len(fileunmatched),fileMax=max(filepairs,key=lambda x:x['seconds']),registryPairs=len(regtimes),registryMax=max(regtimes,key=lambda x:x['seconds']),startupFileStats=stats([e['seconds'] for e in startupFiles]),startupRegistryStats=stats([e['seconds'] for e in startupRegs]),startupThresholds={str(v):dict(file=sum(e['seconds']>v for e in startupFiles),registry=sum(e['seconds']>v for e in startupRegs)) for v in (.1,.5,1)},slow5=[x for x in timelines if x['lifetime']>5],slow10=[x for x in timelines if x['lifetime']>10],slow136=[x for x in timelines if x['lifetime']>13.6])
with (R/'analysis.json').open('x') as f:json.dump(out,f,indent=2)
with (R/'operation-pairs.json').open('x') as f:json.dump(dict(file=filepairs,registry=regtimes,fileAmbiguous=fileambiguous,fileUnmatched=fileunmatched),f)
print(json.dumps({k:v for k,v in out.items() if k not in ('checks','timelines','helpers','kernelIdentities')}));print('assertions',len(checks))
