"""TEST-only OS-helper corroboration; original tracer facts are never rewritten."""
import json,hashlib,os
from pathlib import Path
from journal import frequency
from small_coverage import identity,normalize
from support_verifier import structural

def need(ok,why):
 if not ok:raise ValueError(why)
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def binding(root,pid,created):
 from small_binding_v2 import validate
 d=validate(root,load(root/'small-declaration-v2.json'));ready=load(root/'etw-ready.json');obs=load(root/'observer-identities.json');launcher=load(root/'launcher-identity.json')
 need(ready['pid']==obs['etw']['pid'] and ready['rootPid']==launcher['pid'] and ready['rootCreated']==launcher['created'],'SESSION_LAUNCHER')
 need(ready['frequency']==frequency() and ready['session'],'CLOCK_SESSION')
 return dict(run=root.name,declarationSHA256=digest(root/'small-declaration-v2.json'),sourceManifestSHA256=d['sourceManifestSHA256'],kernelSession=ready['session'],producer=dict(pid=pid,created=created),frequency=frequency(),observerSHA256=digest(root/'observer-identities.json'))

def adapt(root,expected,handles,kernel,mapping,collector):
 doc=load(root/'tree-image-support.json');structural(doc)
 need(identity(doc['anchor'])==collector,'ANCHOR_COLLECTOR')
 need(doc['binding']==binding(root,*collector),'PRODUCER_BINDING')
 need(doc['binding']['kernelSession']==kernel['session'],'KERNEL_SESSION')
 bykey={identity(r):r for r in expected};byseq={r['sequence']:r for r in expected}
 need(len(bykey)==len(byseq)==len(expected),'KERNEL_DUPLICATE')
 need(collector in bykey and bykey[collector]['role']=='DIRECT_WORKER','COLLECTOR_REQUIRED')
 ac=doc['anchor']['capture'];ak=bykey[collector]
 need(ac['frequency']==doc['binding']['frequency'] and ak['startQpc']<=ac['acquisitionBeginQpc']<=ac['acquisitionReturnedQpc']<=ac['captureEntryQpc']<=ac['stateAfterQpc']<=doc['anchor']['closeQpc']<ak['stopQpc'],'ANCHOR_LIVE_INTERVAL')
 need(normalize(ac['image'],mapping)==normalize(ak['image'],mapping),'ANCHOR_IMAGE')
 rows={identity(r):r for r in doc['descendants']}
 for key,row in rows.items():
  need(key in bykey,'EXTRA_TRACKER_IDENTITY');k=bykey[key];c=row['capture'];parent=byseq.get(k['parentSequence'])
  need(parent is not None and parent['pid']==row['parentPid']==k['parentPid'],'EXACT_PARENT_INSTANCE')
  need(parent['startQpc']<=k['startQpc']<parent['stopQpc'],'PARENT_LIFETIME')
  need(c['frequency']==doc['binding']['frequency'],'CLOCK')
  need(k['startQpc']<=c['acquisitionBeginQpc']<=c['acquisitionReturnedQpc']<=c['captureEntryQpc']<=c['stateAfterQpc']<k['stopQpc'],'LIVE_CAPTURE_INTERVAL')
  need(normalize(c['image'],mapping)==normalize(k['image'],mapping),'TRACKER_IMAGE_CONTRADICTION')
  need(row['exitFiletime']==k['exitFiletime'] and row['exitCode']==k['exitCode'],'TRACKER_EXIT_CONTRADICTION')
 out=[]
 for h in handles:
  key=identity(h);k=bykey[key]
  if k['role']!='OS_CONSOLE_HELPER' or key not in rows or h.get('qualifiedPostExit'):
   out.append(h);continue
  c=rows[key]['capture']
  # Supplement unavailable image only. Other tracer facts must still agree.
  if h.get('imageError')==0:
   need(normalize(h['image'],mapping)==normalize(c['image'],mapping),'TRACER_IMAGE_CONTRADICTION');out.append(h);continue
  need(h.get('imageError') not in (None,0) and not h.get('image'),'UNAVAILABLE_IMAGE_REQUIRED')
  need(h['source']=='tracer-opened-handle' and h['retained'] and h['closed'] and h['exited'] and h['handleCreated']==key[1] and h['exitFiletime']==k['exitFiletime'] and h['exitCode']==k['exitCode'],'TRACER_CONTRADICTION')
  out.append(dict(h,source='independent-tree-handle-v1',image=c['image'],imageError=0,queryBeginQpc=c['queryBeginQpc'],queryEndQpc=c['queryEndQpc'],trackerVerified=True,originalTracer=dict(h),trackerEvidence=rows[key]))
 return out
