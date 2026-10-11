"""Conservative association of independent application events to kernel identities.
Delayed delivery is not process creation. Unresolvable reuse remains UNKNOWN.
"""
import pathlib,collections
def associate(rows,events,tracked_sequences):
 bypid=collections.defaultdict(list)
 for r in rows:bypid[r['pid']].append(r)
 for group in bypid.values():group.sort(key=lambda r:int(r['created']))
 bound=collections.defaultdict(list);unknown=[];outside=[]
 for e in events:
  candidates=[];stamp=int(e['nativeTime']);q=e['receivedQpc']
  group=bypid[e['pid']]
  if len({r['created'] for r in group})!=len(group):
   unknown.append(dict(event=e,status='UNKNOWN',reason='DUPLICATE_CREATION_IDENTITY',candidates=[r['sequence'] for r in group]));continue
  for i,r in enumerate(group):
   upper=int(group[i+1]['created']) if i+1<len(group) else None
   # A notification predating this creation cannot describe this incarnation.
   if stamp<int(r['created']) or (upper is not None and stamp>=upper):continue
   if q<r['startQpc'] or (e['kind']=='stop' and q<r['stopQpc']):continue
   if e['name'].lower()!=pathlib.PureWindowsPath(r['image']).name.lower():continue
   if e['parentPid'] not in ((r['parentPid'],) if e['kind']=='start' else (0,r['parentPid'])):continue
   candidates.append(r)
  if len(candidates)==1:
   bound[candidates[0]['sequence']].append(e);continue
  possible_parents=[r for r in rows if r['sequence'] in tracked_sequences and r['pid']==e['parentPid'] and int(r['created'])<=stamp]
  own_possible=[r for r in group if r['sequence'] in tracked_sequences and int(r['created'])<=stamp]
  if candidates or possible_parents or own_possible:
   unknown.append(dict(event=e,status='UNKNOWN',reason='NO_UNIQUE_TIME_IMAGE_PARENT_BOUND_IDENTITY',candidates=[r['sequence'] for r in candidates]))
  else:outside.append(dict(event=e,reason='NO_TIME_POSSIBLE_TRACKED_IDENTITY_OR_PARENT'))
 return dict(bound=dict(bound),unknown=unknown,outside=outside)

def parent_valid(child,parent):
 return child['parentPid']==parent['pid'] and child['parentSequence']==parent['sequence'] and int(parent['created'])<=int(child['created'])<=int(parent['exitFiletime']) and parent['startQpc']<=child['startQpc']<=parent['stopQpc']
