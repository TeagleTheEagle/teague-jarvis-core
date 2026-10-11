"""Prospective TEST qualifier/adapter only; never imports/changes frozen checker."""
import json,hashlib,collections,copy
from pathlib import Path
CONTRACT='STAGE6-TEST-KERNEL-INSTANCE-20260921-v1'
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(v,reason):
 if not v:raise ValueError(reason)
def stream(root,prefix):
 root=Path(root);m=load(root/(prefix+'-manifest.json'));seal=load(root/(prefix+'-seal.json'));result=load(root/(prefix+'-result.json'))
 require(not result['fault'] and result['threadsExited'] and result['remaining']==0,'SINK_INCOMPLETE')
 require(seal['manifestSHA256']==sha(root/(prefix+'-manifest.json')),'MANIFEST_HASH')
 require(m['format']=='durable-segments-v1' and len(m['segments'])==seal['segments'],'MANIFEST_FORMAT')
 expected=1;records=[];size=0
 for i,s in enumerate(m['segments']):
  require(Path(s['name']).name==s['name'] and ':' not in s['name'],'SEGMENT_PATH')
  p=root/s['name'];require(p.exists() and not p.is_symlink(),'MISSING_SEGMENT')
  require(s['number']==i and s['first']==expected and s['states']==[0,1,2,3,4],'SEGMENT_ORDER_STATE')
  require(p.stat().st_size==s['bytes'] and sha(p)==s['sha256'],'SEGMENT_HASH')
  lines=p.read_bytes().splitlines();require(len(lines)==s['records'],'SEGMENT_COUNT')
  for line in lines:
   row=json.loads(line);require(row['seq']==expected,'GLOBAL_SEQUENCE_GAP');expected+=1;records.append(row['raw'])
  require(s['last']==expected-1,'SEGMENT_RANGE');size+=s['bytes']
 require(expected-1==m['accepted']==seal['accepted']==result['written']==result['accepted']==result['attempted'],'TOTAL_COUNT')
 require(size==m['bytes'],'TOTAL_BYTES')
 require(all(s['states']==[0,1,2,3,4,5] for s in result['segments']),'NOT_MANIFESTED')
 return records,m,result
def qualify(events,kernel,handles,natives,cim):
 require(events and kernel['session'],'NO_KERNEL_EVIDENCE')
 for field in ('faults','eventsLost','realtimeBuffersLost','buffersLost','flushResult','stopResult','consumerResult'):
  require(kernel[field]==0,'KERNEL_'+field)
 require(kernel['requestedStop'],'KERNEL_NOT_CLOSED')
 instances=collections.defaultdict(list);sequences={};creation={}
 for e in events:
  require(e['source']=='Microsoft-Windows-Kernel-Process' and e['scope']==kernel['session'],'KERNEL_SCOPE')
  key=(e['scope'],e['pid'],e['created'],e['sequence'])
  require(e['pid']>0 and int(e['created'])>0 and int(e['sequence'])>0,'IDENTITY_MISSING')
  require(e['kind'] in ('start','stop'),'INVALID_EDGE');instances[key].append(e)
  ck=(e['scope'],e['pid'],e['created']);sk=(e['scope'],e['sequence'])
  require(creation.get(ck,key)==key and sequences.get(sk,key)==key,'AUTHORITATIVE_IDENTITY_AMBIGUITY');creation[ck]=key;sequences[sk]=key
 table={};summary={}
 for r in kernel['rows']:
  key=(kernel['session'],r['pid'],r['created'],r['sequence']);require(key not in summary,'DUPLICATE_SUMMARY');summary[key]=r
 require(set(instances)==set(summary),'PERSISTED_SUMMARY_DISAGREEMENT')
 for key,edges in instances.items():
  starts=[e for e in edges if e['kind']=='start'];stops=[e for e in edges if e['kind']=='stop']
  require(len(starts)==len(stops)==1,'KERNEL_START_STOP_MISSING_OR_DUPLICATE');a,b=starts[0],stops[0];r=summary[key]
  require(a['eventQpc']<b['eventQpc'] and int(b['exitFiletime'])>=int(a['created']),'LIFECYCLE_TIME')
  for f in ('parentPid','parentSequence','image'):require(a[f]==b[f]==r[f],'KERNEL_METADATA_CONFLICT')
  require(a['eventQpc']==r['startQpc'] and b['eventQpc']==r['stopQpc'] and b['exitFiletime']==r['exitFiletime'] and b['exitCode']==r['exitCode'] and r['exitCodeKnown'],'KERNEL_SUMMARY_CONFLICT')
  require(r['handleClosed'] and r['metadataError']==0,'HANDLE_CLEANUP_OR_METADATA')
  if r['handleRetained']:
   require(r['reason']=='RETAINED_MATCHING_KERNEL_CREATION' and r['signalObservedQpc']>=r['handleAttemptQpc']>0 and r['openError']==0,'KERNEL_HANDLE_CONTRADICTION')
  else:
   require(r['reason']=='OPEN_PROCESS_FAILED' and r['openError']==87 and r['stopQpc']<r['handleAttemptBeginQpc']<=r['handleAttemptQpc'],'UNQUALIFIED_NO_HANDLE')
  table[key]={'pid':a['pid'],'created':a['created'],'sequence':a['sequence'],'scope':a['scope'],'image':a['image'],'startQpc':a['eventQpc'],'stopQpc':b['eventQpc'],'exitFiletime':b['exitFiletime'],'exitCode':b['exitCode'],'parentPid':a['parentPid'],'parentSequence':a['parentSequence']}
 for h in handles:
  found=[r for r in table.values() if (r['pid'],r['created'])==(h['pid'],h['created'])];require(len(found)==1,'RETAINED_IDENTITY_MISSING')
  r=found[0];require(h['exited'] and h['closed'] and h['exitFiletime']==r['exitFiletime'] and h['exitCode']==r['exitCode'] and Path(h['image']).name.lower()==Path(r['image']).name.lower(),'RETAINED_HANDLE_CONTRADICTION')
  native=[n for n in natives if (n['pid'],n['created'])==(h['pid'],h['created'])];require(len(native)==1,'NATIVE_ENTRY_MISSING')
  n=native[0];require(not n['fault'] and not n['deadlineExceeded'] and n['finalWait']==0 and r['startQpc']<=n['entryQpc']<=r['stopQpc'],'NATIVE_ENTRY_CONTRADICTION')
 for e in cim:
  require(e['result'] in ('UNIQUE_CORRELATED','AMBIGUOUS','UNMATCHED'),'CIM_STATUS')
  require(not e.get('provenContradiction',False),'CIM_PROVEN_CONTRADICTION')
  if e['result']!='UNIQUE_CORRELATED':require(e.get('selected') is None,'CIM_FORCED_MATCH')
  else:require(e.get('independentEventBoundProof') is True and tuple(e['selected']) in table,'CIM_UNPROVEN_UNIQUE')
 return dict(contract=CONTRACT,status='PASS',identities=list(table.values()),unique=len(table),starts=len(table),stops=len(table),falseUnique=0,authoritativeAmbiguous=0,cim=dict(collections.Counter(x['result'] for x in cim)),kernelPIDReuse=len(table)-len({x['pid'] for x in table.values()}))
