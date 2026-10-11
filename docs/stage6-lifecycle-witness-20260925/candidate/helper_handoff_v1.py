"""TEST-only pre-release coordination. No launch, duplication or acceptance authority."""
import json,os,pathlib,time,hashlib,re
from coordination_v3 import need,identity,norm,write_once,digest,load,canonical
from journal import ticks,frequency
SCHEMA='stage6-helper-handoff-v1'
NAMES=tuple('helper-handoff-'+x+'-v1.json' for x in ('obligations','acquired','observed'))
def integer(n):need(type(n) is int and n>0,'HANDOFF_INTEGER');return n
def exact(v,keys):need(type(v) is dict and set(v)==set(keys.split()),'HANDOFF_FIELDS')
def safe(root,name):
 from workspace_binding_v4 import safe as contained,CODE
 root=pathlib.Path(root);contained(root,CODE)
 need(root.parent==CODE and re.fullmatch('protected-[0-9a-f]{32}',root.name),'HANDOFF_ROOT')
 need(name in NAMES,'HANDOFF_FIXED_PATH');p=contained(root/name,root)
 if p.exists():need(p.stat().st_nlink==1,'HANDOFF_HARDLINK')
 return p
def publish(root,name,v):
 p=safe(root,name);safe_pending=p.with_name(p.name+'.pending')
 from workspace_binding_v4 import safe as contained
 contained(safe_pending,pathlib.Path(root));need(not p.exists() and not safe_pending.exists(),'HANDOFF_ALREADY_PUBLISHED')
 write_once(p,v)
def ontime(o,now):
 f=integer(o['binding']['frequency']);start=integer(o['cleanupEntryQpc']);end=integer(o['deadlineQpc'])
 need(end==start+20*f and type(now) is int and start<=now<end,'HANDOFF_ABSOLUTE_DEADLINE')
def validate_obligations(o):
 exact(o,'schema kind binding obligationSetId cleanupEntryQpc deadlineQpc collector authorityObserver helpers preparedQpc coordinationOnly cleanupPass acceptance')
 need(o['schema']==SCHEMA and o['kind']=='HELPER_OBLIGATIONS','HANDOFF_SCHEMA')
 need(o['coordinationOnly'] is True and o['cleanupPass'] is False and o['acceptance'] is False,'HANDOFF_NOT_ACCEPTANCE')
 b=o['binding'];exact(b,'run declarationSHA256 sourceManifestSHA256 kernelSession frequency observerSHA256 workspaceBindingSHA256 cleanupOriginSHA256')
 for n in ('declarationSHA256','sourceManifestSHA256','observerSHA256','workspaceBindingSHA256','cleanupOriginSHA256'):
  need(type(b[n]) is str and len(b[n])==64 and all(x in '0123456789abcdef' for x in b[n]),'HANDOFF_DIGEST')
 need(type(b['run']) is str and type(b['kernelSession']) is str and b['kernelSession'],'HANDOFF_SESSION')
 identity(o['collector']);norm(o['collector']['image']);identity(o['authorityObserver']);norm(o['authorityObserver']['image'])
 hs=o['helpers'];need(type(hs) is list and 0<len(hs)<=8192,'HANDOFF_HELPERS');ids=set();keys=set()
 for h in hs:
  exact(h,'obligationId pid created expectedSequence parent image localHandleIdentity localRetained localRetainedQpc localVerifiedQpc publicationState')
  k=identity(h);need(k not in keys and h['obligationId'] not in ids,'HANDOFF_DUPLICATE');keys.add(k);ids.add(h['obligationId'])
  need(h['obligationId']==str(k[0])+'-'+k[1],'HANDOFF_OBLIGATION_ID')
  need(h['expectedSequence'] is None or (type(h['expectedSequence']) is str and h['expectedSequence'].isdecimal() and int(h['expectedSequence'])>0),'HANDOFF_SEQUENCE')
  need(h['parent']==o['collector'] and norm(h['image'])==r'c:\windows\system32\conhost.exe','HANDOFF_PARENT_IMAGE')
  need(h['localRetained'] is True and h['publicationState']=='SEALED_CLAIM','HANDOFF_LOCAL_HANDLE')
  need(type(h['localHandleIdentity']) is str and h['localHandleIdentity'].isdecimal() and int(h['localHandleIdentity'])>0,'HANDOFF_LOCAL_HANDLE')
  need(integer(h['localRetainedQpc'])<=integer(h['localVerifiedQpc'])<=o['preparedQpc'],'HANDOFF_LOCAL_TIMING')
 need(o['obligationSetId']==hashlib.sha256(canonical(hs)).hexdigest(),'HANDOFF_SET_HASH');ontime(o,o['preparedQpc'])
 return o
def validate_receipt(o,a,obligation_sha,now):
 validate_obligations(o);ontime(o,now)
 exact(a,'schema kind receiptSequence binding obligationsSHA256 cleanupEntryQpc deadlineQpc collector authorityObserver helpers preparedQpc coordinationOnly cleanupPass acceptance')
 need(a['schema']==SCHEMA and a['kind']=='HANDOFF_ACQUIRED' and type(a['receiptSequence']) is int and a['receiptSequence']==1,'HANDOFF_RECEIPT_SCHEMA')
 need(a['binding']==o['binding'] and a['obligationsSHA256']==obligation_sha,'HANDOFF_STALE_RECEIPT')
 for k in ('cleanupEntryQpc','deadlineQpc','collector','authorityObserver'):need(a[k]==o[k],'HANDOFF_BINDING_'+k)
 need(a['coordinationOnly'] is True and a['cleanupPass'] is False and a['acceptance'] is False,'HANDOFF_NOT_ACCEPTANCE')
 ontime(o,a['preparedQpc']);need(a['preparedQpc']<=now,'HANDOFF_FUTURE_RECEIPT')
 need(type(a['helpers']) is list and len(a['helpers'])==len(o['helpers']),'HANDOFF_COUNT')
 wanted={h['obligationId']:h for h in o['helpers']};seen=set();seq=set()
 for r in a['helpers']:
  exact(r,'obligationId pid created sequence kernelSession parent kernelImage handleImage method accessMask handlePid handleCreated handleIdentity retained acquisitionBeginQpc acquisitionReturnQpc creationVerifiedQpc imageBeginQpc imageEndQpc verificationQpc')
  key=r['obligationId'];need(key in wanted and key not in seen,'HANDOFF_DUPLICATE_RECEIPT');seen.add(key);h=wanted[key]
  need(identity(r)==identity(h) and r['handlePid']==r['pid'] and type(r['handlePid']) is int and r['handleCreated']==r['created'],'HANDOFF_CREATION')
  need(r['parent']['pid']==o['collector']['pid'] and r['parent']['created']==o['collector']['created'] and norm(r['parent']['image'])==norm(o['collector']['image']),'HANDOFF_PARENT')
  for s in (r['sequence'],r['parent']['sequence']):need(type(s) is str and s.isdecimal() and int(s)>0,'HANDOFF_SEQUENCE')
  need(r['sequence'] not in seq and r['sequence']!=r['parent']['sequence'],'HANDOFF_SEQUENCE');seq.add(r['sequence'])
  need(h['expectedSequence'] in (None,r['sequence']) and r['kernelSession']==o['binding']['kernelSession'],'HANDOFF_SEQUENCE_SESSION')
  need(norm(r['handleImage'])==norm(h['image']) and type(r['kernelImage']) is str and bool(r['kernelImage']),'HANDOFF_IMAGE')
  need(r['method']=='OpenProcess' and type(r['accessMask']) is int and r['accessMask']==0x101000 and r['retained'] is True,'HANDOFF_RETENTION')
  need(type(r['handleIdentity']) is str and r['handleIdentity'].isdecimal() and int(r['handleIdentity'])>0,'HANDOFF_HANDLE')
  points=[integer(r[k]) for k in ('acquisitionBeginQpc','acquisitionReturnQpc','creationVerifiedQpc','imageBeginQpc','imageEndQpc','verificationQpc')]
  need(points==sorted(points) and points[-1]<=a['preparedQpc'],'HANDOFF_VERIFICATION_TIMING')
 return a
def perform(root,tracker,entry,end,clock=ticks,pause=time.sleep,health=None):
 """Only called after tracker join, while all local handles remain owned."""
 root=pathlib.Path(root)
 for n in NAMES:need(not safe(root,n).exists() and not safe(root,n).with_name(n+'.pending').exists(),'HANDOFF_STALE_ARTIFACT')
 from tracker_adapter_v3 import binding
 b=dict(binding(root,tracker.anchor['pid'],tracker.anchor['created']));b.pop('producer')
 b.update(workspaceBindingSHA256=digest(root/'workspace-binding-v4.json'),cleanupOriginSHA256=digest(root/'cleanup-origin-v3.json'))
 c=dict(pid=tracker.anchor['pid'],created=tracker.anchor['created'],image=tracker.anchor['capture']['image'])
 obs=load(root/'observer-identities.json')['etw'];hs=[]
 for r in tracker.snapshot():
  if not tracker.eligible(r):continue
  need(not r['closed'] and (r['pid'],r['created']) in tracker.handles,'HANDOFF_LOCAL_RELEASED')
  hs.append(dict(obligationId=str(r['pid'])+'-'+r['created'],pid=r['pid'],created=r['created'],expectedSequence=None,parent=c,image=r['image'],localHandleIdentity=r['handleIdentity'],localRetained=True,localRetainedQpc=r['handleRetainedQpc'],localVerifiedQpc=r['imageCapture']['stateAfterQpc'],publicationState='SEALED_CLAIM'))
 o=dict(schema=SCHEMA,kind='HELPER_OBLIGATIONS',binding=b,obligationSetId=hashlib.sha256(canonical(hs)).hexdigest(),cleanupEntryQpc=entry,deadlineQpc=end,collector=c,authorityObserver=obs,helpers=hs,preparedQpc=clock(),coordinationOnly=True,cleanupPass=False,acceptance=False)
 validate_obligations(o);publish(root,NAMES[0],o);ontime(o,clock());oh=digest(root/NAMES[0])
 while True:
  ontime(o,clock())
  for n in ('primary-failure.json','rejected-v3.json','terminal-failure-v3.json','etw-failure.json'):
   need(not (root/n).exists(),'HANDOFF_PRESERVED_FAILURE')
  if health:health()
  p=safe(root,NAMES[1])
  if p.exists():
   a=load(p);now=clock();validate_receipt(o,a,oh,now);rawhash=digest(p)
   v=dict(schema=SCHEMA,kind='HANDOFF_OBSERVED',binding=b,obligationsSHA256=oh,acquiredSHA256=rawhash,collector=c,cleanupEntryQpc=entry,deadlineQpc=end,observedQpc=now,helpers=[dict(obligationId=h['obligationId'],pid=h['pid'],created=h['created']) for h in hs],localReleaseEvidence='tree-handles.json:localCloseQpc/localCloseReturnedQpc/closed',coordinationOnly=True,cleanupPass=False,acceptance=False)
   publish(root,NAMES[2],v);ontime(o,clock());return v
  pause(min(.01,max(0,(end-clock())/b['frequency'])))
def verify_final(root):
 """Additional coordination verification; never replaces existing terminal checker."""
 root=pathlib.Path(root);o=load(safe(root,NAMES[0]));a=load(safe(root,NAMES[1]));v=load(safe(root,NAMES[2]));p=load(root/'phase-a-v3.json')
 need(v['schema']==SCHEMA and v['kind']=='HANDOFF_OBSERVED','HANDOFF_OBSERVED_SCHEMA')
 validate_receipt(o,a,digest(root/NAMES[0]),v['observedQpc'])
 need(v['binding']==o['binding'] and v['acquiredSHA256']==digest(root/NAMES[1]) and v['obligationsSHA256']==digest(root/NAMES[0]),'HANDOFF_OBSERVED_BINDING')
 need(v['collector']==o['collector'] and v['cleanupEntryQpc']==o['cleanupEntryQpc'] and v['deadlineQpc']==o['deadlineQpc'],'HANDOFF_OBSERVED_ORIGIN')
 need(v['coordinationOnly'] is True and v['cleanupPass'] is False and v['acceptance'] is False,'HANDOFF_NOT_ACCEPTANCE')
 need(v['helpers']==[dict(obligationId=h['obligationId'],pid=h['pid'],created=h['created']) for h in o['helpers']],'HANDOFF_OBSERVED_SET')
 b=dict(p['binding']);b.pop('schema');b.update(workspaceBindingSHA256=digest(root/'workspace-binding-v4.json'),cleanupOriginSHA256=digest(root/'cleanup-origin-v3.json'))
 need(b==o['binding'] and p['collector']==o['collector'] and p['authorityObserver']==o['authorityObserver'] and p['cleanupEntryQpc']==o['cleanupEntryQpc'] and p['deadlineQpc']==o['deadlineQpc'],'HANDOFF_FINAL_BINDING')
 etw=load(root/'etw-result.json');need(etw['session']==b['kernelSession'] and etw['faults']==etw['eventsLost']==etw['buffersLost']==etw['realtimeBuffersLost']==0,'HANDOFF_LATER_AUTHORITY_FAILURE')
 rows={(r['pid'],r['created']):r for r in etw['rows']};tree={(r['pid'],r['created']):r for r in load(root/'tree-handles.json')['rows']}
 for r in a['helpers']:
  key=identity(r);x=rows[key];t=tree[key]
  for akey,xkey in [('sequence','sequence'),('handlePid','handlePid'),('handleCreated','handleCreated'),('handleIdentity','handleIdentity'),('acquisitionBeginQpc','handleAttemptBeginQpc'),('acquisitionReturnQpc','handleAttemptQpc'),('creationVerifiedQpc','creationVerifiedQpc'),('imageBeginQpc','imageBeginQpc'),('imageEndQpc','imageEndQpc')]:need(r[akey]==x[xkey],'HANDOFF_AUTHORITY_CONTRADICTION_'+akey)
  need(r['kernelImage']==x['image'] and norm(r['handleImage'])==norm(x['handleImage']) and r['parent']['pid']==x['parentPid'] and r['parent']['sequence']==x['parentSequence'],'HANDOFF_FINAL_IMAGE_PARENT')
  parent=rows[identity(o['collector'])];need(parent['sequence']==r['parent']['sequence'],'HANDOFF_FINAL_PARENT_INSTANCE')
  need(x['handleRetained'] and x['handleClosed'] and x['imageError']==x['metadataError']==0 and x['imageStateBefore']==x['imageStateAfter']==258 and 0<x['signalObservedQpc']<o['deadlineQpc'] and x['imageEndQpc']<x['stopQpc'],'HANDOFF_FINAL_HANDLE')
  need(t['closed'] is True and v['observedQpc']<t['localCloseQpc']<=t['localCloseReturnedQpc']<o['deadlineQpc'],'HANDOFF_RELEASE_ORDER')
 return dict(status='HANDOFF_COORDINATION_VERIFIED_NOT_ACCEPTANCE',obligations=len(a['helpers']))
