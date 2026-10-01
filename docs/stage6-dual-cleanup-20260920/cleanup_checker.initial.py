"""Strict dual-evidence cleanup gate, diagnostic TEST infrastructure only.
Reads frozen evidence; never fabricates lifecycle events or edits primary failures.
"""
import pathlib,json,collections,sys
HANDLE='HANDLE_CONFIRMED_EXIT'
KERNEL='KERNEL_CONFIRMED_POST_EXIT_HANDLE_ACQUISITION'
INSUFFICIENT='INSUFFICIENT_EVIDENCE'
def load(root):
 root=pathlib.Path(root)
 def read(n):return json.loads((root/n).read_text(encoding='utf-8-sig'))
 return dict(kernel=read('etw-result.json'),ready=read('etw-ready.json'),app=read('app-result.json'),events=[json.loads(l) for l in (root/'app-events.jsonl').read_text(encoding='utf-8-sig').splitlines()],receipts=read('app-receipts.json'),tap=read('app-tap.json'),heartbeat=read('app-heartbeats.json'),handles=read('tree-handles.json'),producer=read('stress-result.json'),launcher=read('launcher.json'),launchResult=read('launcher-result.json'),appExit=read('app-exit.json'),appReady=read('app-ready.json'),observers=read('observer-identities.json'),volumeMap=read('volume-map.json')['mapping'],internal=[[json.loads(l) for l in p.read_text().splitlines()] for p in root.glob('internal-*.jsonl')])
def normalize(path,mapping):
 p=str(path).replace('/','\\').lower()
 for drive,device in mapping.items():
  prefix=device.lower().rstrip('\\')+'\\'
  if p.startswith(prefix):p=drive.lower()+'\\'+p[len(prefix):];break
 return str(pathlib.PureWindowsPath(p))
def check(d):
 errors=[];kernel=d['kernel'];rows=kernel['rows'];events=d['events'];handles=d['handles']['rows'];producer=d['producer'];mapping=d['volumeMap']
 def fail(s):errors.append(s)
 for field in ('faults','eventsLost','realtimeBuffersLost','buffersLost','flushResult','stopResult','consumerResult'):
  if kernel[field]!=0:fail('KERNEL_'+field)
 if not kernel['requestedStop']:fail('KERNEL_STOP_NOT_REQUESTED')
 app=d['app'];q=app['queue']
 if not app['success'] or not app['unsubscribed'] or not app['durableFinalization'] or app['error'] or app['tapErrors'] or app['tapOverflow'] or app['source']!='CIM_PROCESS_NOTIFICATION':fail('APPLICATION_COLLECTOR_FAILED')
 if q['failed'] or q['remaining'] or not q['enqueued']==q['selected']==q['persisted']==q['removed']==len(events):fail('QUEUE_NOT_RECONCILED')
 if any(not x['exited'] or x['exitCode']!=0 for x in (d['launchResult'],d['appExit'])):fail('OBSERVER_NOT_CLOSED')
 if d['observers']['etw']['pid']!=d['ready']['pid'] or d['observers']['app']['pid']!=d['appReady']['pid'] or d['observers']['app']['created']!=d['appReady']['created']:fail('OBSERVER_IDENTITY_MISMATCH')
 if not d['observers']['etw']['created']:fail('MISSING_ETW_OBSERVER_CREATION')
 if d['ready']['rootPid']!=d['launcher']['pid'] or d['ready']['rootCreated']!=d['launcher']['creationFiletime']:fail('KERNEL_ROOT_MISMATCH')
 if any(x['interval']>=10 or x['interval']<0 for x in d['heartbeat']) or not d['heartbeat']:fail('HEARTBEAT')
 if not d['handles']['allExited'] or not d['handles']['allHandlesClosed'] or not d['handles']['threadStopped']:fail('RETAINED_TREE_INCOMPLETE')
 # Errors with preserved handles are not silently bypassed.
 if d['handles']['errors']:fail('RETAINED_TREE_ERROR')
 seqs=collections.Counter(x['sequence'] for x in rows);keys=collections.Counter((x['pid'],x['created']) for x in rows)
 if any(n!=1 for n in seqs.values()) or any(n!=1 for n in keys.values()) or '0' in seqs:fail('DUPLICATE_KERNEL_IDENTITY')
 roots=[x for x in rows if x['pid']==producer['collectorPid']]
 if len(roots)!=1:return dict(status='FAIL',errors=errors+['AMBIGUOUS_COLLECTOR'],identities=[],total=0,handleConfirmed=0,kernelPostExit=0,insufficient=0)
 scope={roots[0]['sequence']}
 while True:
  new=scope|{x['sequence'] for x in rows if x['parentSequence'] in scope}
  if new==scope:break
  scope=new
 tracked=[x for x in rows if x['sequence'] in scope];pids={x['pid'] for x in tracked};byseq={x['sequence']:x for x in rows};bykey={(x['pid'],x['created']):x for x in rows}
 # Derive the app tree independently as well; an ETW omission must not hide a child.
 appscope={producer['collectorPid']}
 while True:
  new=appscope|{x['pid'] for x in events if x['kind']=='start' and x['parentPid'] in appscope}
  if new==appscope:break
  appscope=new
 if appscope!=pids:fail('APPLICATION_KERNEL_TREE_DISAGREEMENT')
 for x in producer['launched']:
  if (x['pid'],x['created']) not in bykey or x['pid'] not in pids:fail('MISSING_EXPLICIT_LAUNCH')
 for marker in d['internal']:
  if not marker or marker[0]['pid'] not in pids or marker[-1]['stage']!='return-main':fail('MISSING_INSTRUMENTED_CHILD')
 for h in handles:
  if (h['pid'],h['created']) not in bykey or h['pid'] not in pids:fail('RETAINED_PROCESS_MISSING_FROM_KERNEL')
 if len({(h['pid'],h['created']) for h in handles})!=len(handles):fail('DUPLICATE_RETAINED_IDENTITY')
 receipts=collections.defaultdict(list)
 for v in d['receipts']:receipts[v['queueSequence']].append(v)
 if len({v['queueSequence'] for v in events})!=len(events) or len(d['receipts'])!=len(events):fail('QUEUE_RECEIPT_IDENTITY')
 for v in events:
  rs=receipts[v['queueSequence']]
  if v['source']!='CIM_PROCESS_NOTIFICATION' or len(rs)!=1 or any(not a['removed'] or a['pid']!=v['pid'] or a['kind']!=v['kind'] or a['persistedQpc']<v['drainedQpc'] for a in rs):fail('MISSING_PERSISTENCE_RECEIPT')
  if not 0<v['receivedQpc']<=v['drainedQpc']:fail('APPLICATION_RECEIPT_TIME_CONFLICT')
  for stage in ('A-callback','A-enqueue'):
   matched=[a for a in d['tap'] if a['stage']==stage and a['pid']==v['pid'] and a['kind']==v['kind'] and a['nativeTime']==v['nativeTime'] and a['name'].lower()==v['name'].lower()]
   if len(matched)!=1:fail('MISSING_OR_AMBIGUOUS_APPLICATION_CALLBACK')
 result=[]
 for x in tracked:
  why=[];key=(x['pid'],x['created']);ks=[a for a in rows if a['pid']==x['pid']];hs=[a for a in handles if (a['pid'],a['created'])==key]
  starts=[a for a in events if a['pid']==x['pid'] and a['kind']=='start'];stops=[a for a in events if a['pid']==x['pid'] and a['kind']=='stop']
  if len(ks)!=1:why.append('PID_REUSE_AMBIGUITY')
  if not x['startQpc'] or not x['stopQpc'] or x['stopQpc']<=x['startQpc'] or int(x['created'])<=0 or int(x['exitFiletime'])<int(x['created']) or not x['exitCodeKnown']:why.append('KERNEL_LIFECYCLE_MISSING_OR_CONFLICTING')
  if len(starts)!=1 or len(stops)!=1:why.append('APPLICATION_START_STOP_INCOMPLETE')
  else:
   start,stop=starts[0],stops[0];name=pathlib.PureWindowsPath(x['image']).name.lower()
   if start['parentPid']!=x['parentPid'] or stop['parentPid'] not in (0,x['parentPid']) or start['name'].lower()!=name or stop['name'].lower()!=name:why.append('APPLICATION_PARENT_IMAGE_CONFLICT')
   if int(stop['nativeTime'])<int(start['nativeTime']):why.append('APPLICATION_EVENT_ORDER_CONFLICT')
  if x['sequence']==roots[0]['sequence']:
   if x['parentPid']!=d['launcher']['pid'] or int(x['created'])<int(d['launcher']['creationFiletime']):why.append('COLLECTOR_PARENT_CONFLICT')
  else:
   parent=byseq.get(x['parentSequence'])
   if not parent or parent['pid']!=x['parentPid'] or not int(parent['created'])<=int(x['created'])<=int(parent['exitFiletime']):why.append('KERNEL_PARENT_IDENTITY_CONFLICT')
  retained=bool(hs) or x['handleRetained']
  if hs:
   h=hs[0]
   if not h['closed'] or not h['signalObservedQpc'] or h['exitFiletime']!=x['exitFiletime'] or h['exitCode']!=x['exitCode'] or h['parentPid']!=x['parentPid'] or normalize(h['image'],mapping)!=normalize(x['image'],mapping):why.append('RETAINED_IDENTITY_EXIT_CONFLICT')
  if x['handleRetained'] and (x['reason']!='RETAINED_MATCHING_KERNEL_CREATION' or not x['signalObservedQpc'] or not x['handleClosed'] or x['metadataError'] or x['openError']):why.append('ETW_RETAINED_HANDLE_INCOMPLETE')
  classification=HANDLE if retained else KERNEL
  if not retained:
   begin=x.get('handleAttemptBeginQpc',0)
   if not (x['reason']=='OPEN_PROCESS_FAILED' and x['openError']==87 and x['metadataError']==0 and x['stopQpc']<begin<=x['handleAttemptQpc']):why.append('POST_EXIT_ACQUISITION_NOT_PROVEN')
  if why or errors:classification=INSUFFICIENT
  result.append(dict(pid=x['pid'],created=x['created'],sequence=x['sequence'],parentPid=x['parentPid'],image=x['image'],classification=classification,errors=why,appStartCount=len(starts),appStopCount=len(stops)))
 counts=collections.Counter(x['classification'] for x in result)
 return dict(status='PASS' if not errors and not counts[INSUFFICIENT] else 'FAIL',total=len(result),handleConfirmed=counts[HANDLE],kernelPostExit=counts[KERNEL],insufficient=counts[INSUFFICIENT],appStarts=sum(x['appStartCount'] for x in result),appStops=sum(x['appStopCount'] for x in result),kernelCreates=sum(bool(x['startQpc']) for x in tracked),kernelExits=sum(bool(x['stopQpc']) for x in tracked),errors=errors,identities=result,primaryFailure=producer.get('primary_failure'),producerStatus=producer['status'],acceptance=False,outsideKernel=[dict(pid=x['pid'],created=x['created'],image=x['image']) for x in rows if x['sequence'] not in scope],outsideAppEvents=[x for x in events if x['pid'] not in pids],externalEventIdentifierCollisions=len(events)-len({x['eventIdentifier'] for x in events}),queueIdentityCollisions=len(events)-len({x['queueSequence'] for x in events}))
def evaluate(root):
 try:return check(load(root))
 except (OSError,ValueError,KeyError,TypeError,IndexError) as ex:return dict(status='FAIL',errors=['MISSING_OR_INVALID_EVIDENCE: '+str(ex)],identities=[],acceptance=False)
if __name__=='__main__':
 root=pathlib.Path(sys.argv[1]);result=evaluate(root)
 with (root/'cleanup-checker-result.json').open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps({k:v for k,v in result.items() if k not in ('identities','outsideAppEvents','outsideKernel')}))
 raise SystemExit(0 if result['status']=='PASS' else 1)
