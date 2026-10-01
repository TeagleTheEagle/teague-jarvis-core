"""Stage 6 TEST-only two-phase evidence predicates. No process launch authority."""
import hashlib,json,os,pathlib
SCHEMA='stage6-terminal-v3'
STATES=('PREPARED','RUN_ACTIVE','COLLECTOR_LOCAL_FINALIZING',
 'LOCAL_EVIDENCE_FINALIZED_PENDING_EXTERNAL_EXIT','COLLECTOR_EXITED',
 'TERMINAL_EVIDENCE_PENDING','TERMINAL_EVIDENCE_COMPLETE',
 'PRE_SHUTDOWN_WORKLOAD_CENSUS_COMPLETE','OBSERVER_SHUTDOWN_ALLOWED',
 'OBSERVERS_AND_LAUNCHER_EXITED','FINAL_CENSUS_PENDING','FINAL_CENSUS_COMPLETE',
 'CHECKER_FINALIZATION_ALLOWED','ACCEPTED')
OWNERS=('controller','launcher','collector','collector','launcher','launcher',
 'launcher','launcher','launcher','controller','controller','controller','checker','finalizer')
class Rejected(ValueError):pass
def need(ok,reason):
 if not ok:raise Rejected(reason)
def integer(v):
 need(type(v) is int and v>0,'INTEGER');return v
def identity(r):
 integer(r['pid']);need(type(r['created']) is str and r['created'].isdecimal() and int(r['created'])>0,'CREATION');return r['pid'],r['created']
def norm(s):
 p=pathlib.PureWindowsPath(s);need(p.is_absolute() and '..' not in p.parts and '\x00' not in s,'IMAGE');return str(p).casefold()
def digest_bytes(b):return hashlib.sha256(b).hexdigest()
def digest(p):return digest_bytes(pathlib.Path(p).read_bytes())
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def load(p):
 def pairs(xs):
  out={}
  for k,v in xs:need(k not in out,'DUPLICATE_KEY');out[k]=v
  return out
 b=pathlib.Path(p).read_bytes();need(0<len(b)<=1048576,'RECORD_SIZE');return json.loads(b,object_pairs_hook=pairs)
def write_once(p,v):
 """Fixed caller-selected run artifact: complete bytes, exclusive final publication."""
 p=pathlib.Path(p);tmp=p.with_name(p.name+'.pending')
 with tmp.open('xb') as f:f.write(canonical(v));f.flush();os.fsync(f.fileno())
 # Windows rename fails if destination exists. No overwrite/replace fallback.
 tmp.rename(p)
def bound(p):
 b=p['binding'];need(b['schema']==SCHEMA,'SCHEMA')
 for key in ('run','declarationSHA256','sourceManifestSHA256','kernelSession','observerSHA256'):
  need(isinstance(b[key],str) and bool(b[key]),'BINDING_'+key)
 for key in ('declarationSHA256','sourceManifestSHA256','observerSHA256'):
  need(len(b[key])==64 and all(c in '0123456789abcdef' for c in b[key]),'DIGEST')
 f=integer(b['frequency']);start=integer(p['cleanupEntryQpc'])
 need(p['deadlineQpc']==start+20*f,'DEADLINE_RESET')
 return b,start,p['deadlineQpc']
def before(p,now):
 _,start,end=bound(p);need(type(now) is int and start<=now<end,'ABSOLUTE_DEADLINE');return end-now
def phase_a(p):
 b,start,end=bound(p);need(p['state']==STATES[3],'PHASE_A_STATE')
 for flag in ('admissionsStopped','localDurable','trackerStopped','localHandlesClosed'):
  need(p[flag] is True,'PHASE_A_'+flag)
 need(p['cleanupPass'] is False and p['acceptance'] is False,'PREMATURE_PASS')
 c=p['collector'];identity(c);norm(c['image']);identity(p['authorityObserver'])
 rows=p['helpers'];need(type(rows) is list and len(rows)<=8192,'HELPER_BOUND')
 keys=set()
 for r in rows:
  key=identity(r);need(key not in keys,'DUPLICATE_HELPER');keys.add(key)
  need(r['role']=='OS_CONSOLE_HELPER' and identity(r['parent'])==identity(c),'HELPER_CLASS_PARENT')
  need(norm(r['image'])==r'c:\windows\system32\conhost.exe','HELPER_IMAGE')
  need(r['localClosed'] is True,'LOCAL_HANDLE_OPEN');before(p,r['localCloseQpc']);need(r['localCloseQpc']<=p['completedQpc'],'LOCAL_CLOSE_AFTER_PHASE')
  need(r['stateAtClose'] in (0,258),'LOCAL_HANDLE_STATE')
 before(p,p['completedQpc']);return p
def native(n,row,p):
 need(identity(n)==identity(row),'NATIVE_IDENTITY')
 need(n['finalWait']==0 and n['fault'] is False and n['deadlineExceeded'] is False,'NATIVE_FAILED')
 need(n['exitCode']==row['exitCode'] and n['exitFiletime']==row['exitFiletime'],'NATIVE_CONTRADICTION')
 need(row['startQpc']<=n['entryQpc']<row['stopQpc'],'NATIVE_ENTRY')
def terminal(p,r,phase_sha,observed_qpc,native_collector):
 phase_a(p);before(p,observed_qpc)
 need(r['schema']==SCHEMA and r['kind']=='workload-terminal' and r['sequence']==1,'RECEIPT_SCHEMA_SEQUENCE')
 need(r['binding']==p['binding'] and r['phaseASHA256']==phase_sha,'STALE_RECEIPT')
 need(r['cleanupEntryQpc']==p['cleanupEntryQpc'] and r['deadlineQpc']==p['deadlineQpc'],'RECEIPT_DEADLINE')
 need(identity(r['observer'])==identity(p['authorityObserver']) and norm(r['observer']['image'])==norm(p['authorityObserver']['image']),'OBSERVER_IDENTITY')
 need(r['faults']==0 and r['eventsLost']==r['buffersLost']==0,'TRACE_LOSS')
 need(r['coordinationOnly'] is True and r['acceptance'] is False,'RECEIPT_NOT_ACCEPTANCE')
 before(p,r['capturedQpc']);need(r['capturedQpc']<=observed_qpc,'FUTURE_RECEIPT')
 expected={identity(p['collector']):p['collector'],**{identity(x):x for x in p['helpers']}}
 rows={identity(x):x for x in r['rows']};need(len(rows)==len(r['rows']) and set(rows)==set(expected),'MISSING_OR_REUSED_INSTANCE')
 sequences=set()
 for k,want in expected.items():
  x=rows[k];need(x['sequence'] not in sequences and int(x['sequence'])>0,'SEQUENCE');sequences.add(x['sequence'])
  need(norm(x['handleImage'])==norm(want['image']) and x['handleCreated']==k[1],'IMAGE_CREATION')
  need(x['handleRetained'] is True and x['imageError']==0 and x['metadataError']==0,'HANDLE_REQUIRED')
  need(x['startQpc']<=x['handleAttemptQpc']<=x['signalObservedQpc']<=r['capturedQpc'],'HANDLE_CONTINUITY')
  need(x['imageBeginQpc']<=x['imageEndQpc']<x['stopQpc'],'LIVE_IMAGE')
  need(x['stopQpc']>x['startQpc'] and x['stopQpc']<=x['stopCallbackQpc']<=r['capturedQpc'] and x['stopQpc']<=x['signalObservedQpc'],'KERNEL_STOP')
  need(0<x['signalObservedQpc']<p['deadlineQpc'] and 0<x['stopQpc']<p['deadlineQpc'],'TERMINAL_LATE')
  need(x['kernelExitFiletime']==x['exitFiletime'] and x['kernelExitCode']==x['exitCode'],'HANDLE_KERNEL_CONTRADICTION')
  if k!=identity(p['collector']):
   parent=rows[identity(p['collector'])]
   need(x['parentPid']==parent['pid'] and x['parentSequence']==parent['sequence'],'PARENT_CONTRADICTION')
   need(x['handleAttemptQpc']<want['localCloseQpc'] and x['imageBeginQpc']<want['localCloseQpc'],'HANDOFF_LATE')
  else:
   need(p['completedQpc']<=x['stopQpc'] and x['exitCode']==0,'COLLECTOR_CRASH_OR_EARLY_EXIT');native(native_collector,x,p)
 return rows
def census(p,c,final=False):
 before(p,c['completedQpc']);need(c['binding']==p['binding'],'CENSUS_BINDING')
 need(c['available'] is True and c['unknown']==[],'CENSUS_UNAVAILABLE')
 need(c['workloadRemaining']==[],'WORKLOAD_REMAINS')
 if final:
  need(c['matchingProcesses']==[] and c['traceSessions']==[],'FINAL_CENSUS_REMAINS')
  need(c['launcherExitVerified'] is True and c['observerExitsVerified'] is True,'EXIT_UNPROVEN')
 else:
  need(c['kind']=='workload-only','WRONG_CENSUS')
  need(c['matchingProcesses']==c['expectedManagement'],'UNEXPECTED_PROCESS')
 return True
def closure(p,doc):
 before(p,doc['completedQpc']);need(doc['binding']==p['binding'],'CLOSURE_BINDING')
 need(doc['launcherExitVerified'] is True and doc['launcherExitCode']==0,'LAUNCHER_EXIT')
 need(set(doc['observers'])=={'application','detail','authority'},'MISSING_OBSERVER')
 last=0
 for role in ('application','detail','authority'):
  x=doc['observers'][role]
  need(x['exitVerified'] is True and x['exitCode']==0 and x['drained'] is True,'OBSERVER_'+role)
  need(last<=x['exitQpc']<p['deadlineQpc'],'SHUTDOWN_ORDER');last=x['exitQpc']
 need(doc['durableComplete'] is True and doc['authoritativeContradictions']==[],'FINAL_STREAM')
 need(doc['allRequiredHandlesClosed'] is True,'HANDLE_CLOSURE')
 return True
class Machine:
 def __init__(self,binding):self.state='PREPARED';self.binding=binding;self.records=[]
 def reject(self,reason):self.state='REJECTED';self.records.append(dict(state='REJECTED',reason=reason));raise Rejected(reason)
 def advance(self,state,owner,evidence,p=None,now=None):
  try:
   need(self.state!='REJECTED','PERMANENT_REJECTION')
   i=STATES.index(self.state)+1;need(i<len(STATES) and STATES[i]==state,'STATE_ORDER')
   need(owner==OWNERS[i] and evidence.get('binding')==self.binding,'STATE_OWNER_BINDING')
   if p is not None and state not in ('CHECKER_FINALIZATION_ALLOWED','ACCEPTED'):before(p,now)
   self.state=state;self.records.append(dict(state=state,owner=owner,evidence=evidence,qpc=now))
  except (ValueError,KeyError,TypeError) as exc:self.reject(str(exc))
