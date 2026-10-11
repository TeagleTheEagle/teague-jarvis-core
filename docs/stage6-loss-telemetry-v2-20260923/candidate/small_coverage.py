"""TEST qualification coverage; requirements never inferred from evidence lists."""
from collections import Counter
from pathlib import PureWindowsPath

FIELDS=('handle','creation','image','native','start','stop','exit','parent','source','capture')
def identity(x):return (int(x['pid']),str(x['created']))
def normalize(path,mapping):
 p=path.replace('/','\\').lower()
 if p.startswith('\\\\?\\'):p=p[4:]
 for drive,device in mapping.items():
  if p.startswith(device.lower()+'\\'):p=drive.lower()+p[len(device):];break
 return str(PureWindowsPath(p))

def coverage(expected,events,handles,natives,mapping):
 errors=[];rows=[];counts={f:Counter() for f in FIELDS}
 if not expected:errors.append('MISSING_REQUIRED_IDENTITY_INVENTORY')
 keys=[identity(x) for x in expected]
 if len(keys)!=len(set(keys)):errors.append('DUPLICATE_REQUIRED_IDENTITY')
 for x in expected:
  key=identity(x);role=x['role'];states={};reasons=[]
  if role not in ('DIRECT_PROBE','DIRECT_WORKER','OS_CONSOLE_HELPER','APPLICATION_OBSERVER','DETAIL_OBSERVER'):errors.append('UNKNOWN_REQUIRED_CLASS')
  hs=[h for h in handles if identity(h)==key];ns=[n for n in natives if identity(n)==key]
  h=hs[0] if len(hs)==1 else {};n=ns[0] if len(ns)==1 else {}
  edges=[e for e in events if identity(e)==key and str(e['sequence'])==str(x['sequence'])]
  # The reviewed post-exit exception requires a positive recorded acquisition attempt,
  # not a missing handle list. It never applies to controlled worker/probe identities.
  qualified=(role=='OS_CONSOLE_HELPER' and h.get('qualifiedPostExit') is True
    and h.get('reason')=='OPEN_PROCESS_FAILED' and h.get('openError')==87
    and x['stopQpc']<h.get('attemptBegin',0)<=h.get('attemptEnd',0))
  def check(f,present,valid,na=False):
   state='NOT_APPLICABLE' if na else ('MISSING_AND_REQUIRED' if not present else ('PRESENT_AND_VALID' if valid else 'PRESENT_BUT_CONTRADICTORY'))
   states[f]=state;counts[f][state]+=1
   if state in ('MISSING_AND_REQUIRED','PRESENT_BUT_CONTRADICTORY'):
    reason=('MISSING_REQUIRED_' if not present else 'CONTRADICTORY_')+f.upper()+'_EVIDENCE';reasons.append(reason);errors.append(reason)
  starts=[e for e in edges if e['kind']=='start'];stops=[e for e in edges if e['kind']=='stop']
  check('start',bool(starts),len(starts)==1)
  check('stop',bool(stops),len(stops)==1)
  check('handle',bool(hs),len(hs)==1 and (qualified or (h.get('retained') and h.get('exited') and h.get('closed'))))
  check('creation',bool(h.get('handleCreated')),str(h.get('handleCreated'))==key[1],qualified)
  check('image',bool(h.get('image')),h.get('imageError')==0 and normalize(h.get('image',''),mapping)==normalize(x['image'],mapping),qualified)
  direct=role in ('DIRECT_PROBE','DIRECT_WORKER')
  source='creator-owned-handle' if direct else 'tracer-opened-handle'
  check('source',bool(h.get('source')),h.get('source')==source)
  absolute=bool(h.get('image')) and PureWindowsPath(h['image']).is_absolute() and '\x00' not in h['image'] and '..' not in PureWindowsPath(h['image']).parts
  if direct:
   good=h.get('handlePid')==key[0] and h.get('creatorPid')==x.get('parentPid') and h.get('processState')==258 and h.get('success') is True and bool(h.get('handleIdentity'))
   good=good and x['startQpc']<=h.get('handleAcquiredQpc',0)<=h.get('queryBeginQpc',0)<=h.get('queryEndQpc',0)<h.get('identityPersistedQpc',0)<n.get('entryQpc',0)<=x['stopQpc'] and absolute
  else:
   good=qualified or (absolute and x['startQpc']<=h.get('queryBeginQpc',0)<=h.get('queryEndQpc',0)<x['stopQpc'])
  check('capture',bool(hs),good)
  need_native=role in ('DIRECT_PROBE','DIRECT_WORKER')
  check('native',bool(ns),len(ns)==1 and not n.get('fault',True) and not n.get('deadlineExceeded',True)
    and n.get('finalWait')==0 and x['startQpc']<=n.get('entryQpc',0)<=x['stopQpc']
    and str(n.get('exitFiletime'))==str(x['exitFiletime']) and n.get('exitCode')==x['exitCode']
    and len([e for e in n.get('events',[]) if e.get('event')=='PE_ENTRY_EXECUTED'])==1,not need_native)
  check('exit',bool(hs),qualified or (h.get('exited') and str(h.get('exitFiletime'))==str(x['exitFiletime']) and h.get('exitCode')==x['exitCode']))
  check('parent',x.get('parentVerified') is not None,x.get('parentVerified') is True)
  # Supporting annotation is explicitly optional; not a replacement for any above field.
  states['annotation']='PRESENT_AND_VALID' if x.get('annotation') else 'MISSING_BUT_OPTIONAL'
  rows.append(dict(pid=key[0],created=key[1],role=role,states=states,qualifiedPostExit=qualified,reasons=reasons,verified=not reasons))
 # Extra/reused identities cannot satisfy an expected identity; duplicate evidence also fails.
 for name,collection in [('HANDLE',handles),('NATIVE',natives)]:
  seen=Counter(identity(v) for v in collection)
  if any(v>1 for v in seen.values()):errors.append('DUPLICATE_'+name+'_EVIDENCE')
  if set(seen)-set(keys):errors.append('UNEXPECTED_'+name+'_IDENTITY')
 missing=sum(c['MISSING_AND_REQUIRED'] for c in counts.values());contradictory=sum(c['PRESENT_BUT_CONTRADICTORY'] for c in counts.values())
 return dict(status='PASS' if expected and not errors and all(r['verified'] for r in rows) else 'FAIL',
  requiredIdentities=len(expected),verifiedIdentities=sum(r['verified'] for r in rows),missingRequired=missing,
  contradictory=contradictory,notApplicableIdentities=sum(any(s=='NOT_APPLICABLE' for s in r['states'].values()) for r in rows),
  evidenceTypes={f:dict(c) for f,c in counts.items()},errors=errors,identities=rows)
