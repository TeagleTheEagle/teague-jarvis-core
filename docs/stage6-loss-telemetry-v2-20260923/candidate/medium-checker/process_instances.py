"""Strict future instance correlation, with no event identity invented from lookup.

Independent observations of a process are not evidence binding a CIM event to it.
"""
import pathlib,copy
class InstanceTable:
 def __init__(self,rows,boot_scope):
  if not boot_scope:raise ValueError('BOOT_SCOPE_REQUIRED')
  self.scope=boot_scope;self.rows=copy.deepcopy(rows);seen=set();creation_keys=set()
  for r in self.rows:
   k=(r['pid'],str(r['created']),str(r['sequence']))
   if k in seen or int(r['created'])<=0 or not r['sequence'] or int(r['exitFiletime'])<int(r['created']) or r['stopQpc']<r['startQpc']:raise ValueError('INVALID_INSTANCE')
   if k[:2] in creation_keys:raise ValueError('CREATION_IDENTITY_COLLISION')
   seen.add(k);creation_keys.add(k[:2])
  byseq={r['sequence']:r for r in self.rows}
  if len(byseq)!=len(self.rows):raise ValueError('SEQUENCE_COLLISION')
  for r in self.rows:
   if r.get('parentRequired'):
    p=byseq.get(r['parentSequence'])
    if not p or p['pid']!=r['parentPid'] or not int(p['created'])<=int(r['created'])<=int(p['exitFiletime']):raise ValueError('PARENT_INSTANCE_CONFLICT')
   if r.get('handleCreated') is not None and str(r['handleCreated'])!=str(r['created']):raise ValueError('HANDLE_CREATION_CONFLICT')
   if r.get('nativeEntryQpc') is not None and not r['startQpc']<=r['nativeEntryQpc']<=r['stopQpc']:raise ValueError('NATIVE_ENTRY_CONFLICT')
 def key(self,r):return dict(bootScope=self.scope,pid=r['pid'],created=str(r['created']),kernelSequence=str(r['sequence']))
 def correlate(self,raw):
  # No timestamp upper-bound is inferred from CIM event generation/arrival time.
  # Old incarnations remain possible after exit/reuse because notifications may delay.
  candidates=[]
  for r in self.rows:
   if raw['pid']!=r['pid'] or int(raw['nativeTime'])<int(r['created']):continue
   if raw['receivedQpc']<r['startQpc'] or (raw['kind']=='stop' and raw['receivedQpc']<r['stopQpc']):continue
   if raw['name'].lower()!=pathlib.PureWindowsPath(r['image']).name.lower():continue
   if raw['parentPid'] not in ((r['parentPid'],) if raw['kind']=='start' else (0,r['parentPid'])):continue
   candidates.append(r)
  # The real CIM schema supplies no independently event-bound creation key.
  # A synthetic/raw caller field, current PID query or nearest time is never trusted.
  return dict(raw=copy.deepcopy(raw),candidates=[self.key(r) for r in candidates],selected=None,result='AMBIGUOUS' if candidates else 'UNMATCHED',reason='MISSING_INDEPENDENT_EVENT_INSTANCE_DISCRIMINATOR' if candidates else 'NO_COMPATIBLE_INSTANCE',observationsNotEventProof=True)
