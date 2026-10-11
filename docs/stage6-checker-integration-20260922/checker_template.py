"""Version 2 small TEST evidence checker. No runtime or legacy-checker dispatch.

Public acceptance: replay(). Fixture rules alone cannot produce acceptance.
All evidence is read only; no processes, traces or workloads are launched.
"""
import collections,copy,hashlib,json,math,re,stat,sys,zipfile
from pathlib import Path,PurePosixPath
import combined as adapter
from process_instances import InstanceTable
R=Path(__file__).parent
VERSION='stage6-checker-input-v2'
CONTRACT='STAGE6-TEST-KERNEL-INSTANCE-20260921-v1'
class Rejection(ValueError):pass
def need(value,reason):
 if value is not True:raise Rejection(reason)
def digest(data):return hashlib.sha256(data).hexdigest()
def pairs(items):
 result={}
 for k,v in items:
  if k in result:raise Rejection('DUPLICATE_JSON_KEY:'+k)
  result[k]=v
 return result
def decode(data):
 try:return json.loads(data,object_pairs_hook=pairs,parse_constant=lambda s:(_ for _ in ()).throw(Rejection('NONFINITE_JSON')))
 except (UnicodeError,json.JSONDecodeError) as e:raise Rejection('MALFORMED_JSON') from e
def load(p):return decode(Path(p).read_bytes().decode('utf-8-sig'))
def sha(p):return digest(Path(p).read_bytes())
def schema_check(x,s,path='$'):
 if s is False:raise Rejection('SCHEMA_FORBIDDEN_ITEM:'+path)
 if 'anyOf' in s:
  for option in s['anyOf']:
   try:schema_check(x,option,path);return
   except Rejection:pass
  raise Rejection('SCHEMA_VARIANT:'+path)
 t=s['type'];ok={'object':type(x) is dict,'array':type(x) is list,'null':x is None,'boolean':type(x) is bool,'integer':type(x) is int,'number':type(x) in (int,float) and math.isfinite(x),'string':type(x) is str}[t]
 need(ok,'SCHEMA_TYPE:'+path)
 if 'const' in s:need(type(x) is type(s['const']) and x==s['const'],'SCHEMA_VERSION_OR_CONSTANT:'+path)
 if t=='object':
  need(set(x)==set(s['required'])==set(s['properties']),'SCHEMA_FIELDS:'+path)
  for k,v in x.items():schema_check(v,s['properties'][k],path+'.'+k)
 elif t=='array':
  for i,v in enumerate(x):schema_check(v,s['items'],path+'['+str(i)+']')
 elif t=='number':need(math.isfinite(x),'NONFINITE_NUMBER:'+path)
def safe_path(p,roots):
 p=Path(p)
 need(p.is_absolute() and '..' not in p.parts and '\x00' not in str(p) and ':' not in str(p)[2:],'UNSAFE_PATH')
 need(any(p==r or p.is_relative_to(r) for r in roots),'PATH_OUTSIDE_BOUNDARY')
 for part in (p,*p.parents):
  info=part.lstat()
  need(not (getattr(info,'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT),'REPARSE_PATH')
 need(p.resolve()==p,'NONCANONICAL_PATH')
 return p
def self_verify():
 freeze=load(R/'source-freeze.json')
 for row in freeze['files']:
  p=safe_path(Path(row['path']),[R]);need(p.name==row['name'] and sha(p)==row['sha256'],'CANDIDATE_SOURCE_DRIFT')
 config=load(R/'binding.json')
 p=Path(config['reference']);need(sha(p)==config['referenceSHA256']==sha(R/'frozen_reference.py'),'FROZEN_CHECKER_PRESERVATION_FAILURE')
 return config
def archive_verify(config):
 rc=config['archive'];a=Path(rc['archive']);mp=a.parent/'manifest.json';sp=Path(config['seal'])
 for p in (a,mp,sp):safe_path(p,[a.parent,Path(config['review'])])
 need(sha(a)==rc['archiveSHA256'] and sha(mp)==rc['manifestSHA256'] and sha(sp)==config['sealSHA256'],'ARCHIVE_MANIFEST_OR_SEAL_MISMATCH')
 m=load(mp);seal=load(sp)
 need(seal['archiveSHA256']==rc['archiveSHA256'] and seal['manifestSHA256']==rc['manifestSHA256'] and seal['status']=='SMALL_COMBINED_VALIDATED' and seal['run']==config['root'],'ACCEPTANCE_BINDING')
 roots=[Path(x) for x in config['allowedRoots']];checks=[]
 with zipfile.ZipFile(a) as z:
  names=z.namelist();expected=[x['name'] for x in m['files']]+['manifest.json']
  need(len(names)==len(set(names))==rc['membersVerified'] and set(names)==set(expected),'ARCHIVE_MEMBER_SET')
  need(z.read('manifest.json')==mp.read_bytes(),'ARCHIVE_MANIFEST_BYTES')
  for row in m['files']:
   n=PurePosixPath(row['name']);need(not n.is_absolute() and '..' not in n.parts and ':' not in str(n) and '\\' not in str(n),'ARCHIVE_MEMBER_PATH')
   p=safe_path(row['source'],roots);b=z.read(row['name'])
   need(len(b)==row['bytes'] and digest(b)==row['sha256']==sha(p),'ARCHIVE_SOURCE_HASH:'+row['name']);checks.append(str(p))
  payload=decode(z.read('review/combined-interface.json').decode('utf8'))
 need(digest(json.dumps(payload).encode())==digest(json.dumps(load(Path(config['review'])/'combined-interface.json')).encode()),'INTERFACE_BYTES_DISAGREE')
 need(sha(Path(config['review'])/'combined-interface.json')==seal['interfaceSHA256'],'INTERFACE_SEAL_MISMATCH')
 need(sha(config['host'])==seal['cleanupSHA256'],'CLEANUP_SEAL_MISMATCH')
 return payload,checks
def secondary_policy(record,canonical):
 """Conditional contract predicate; true flag alone is NEVER a public replay binding."""
 need(type(record) is dict and record.get('provenContradiction',False) is False,'CIM_PROVEN_CONTRADICTION')
 status=record.get('result');need(status in ('UNIQUE_CORRELATED','AMBIGUOUS','UNMATCHED'),'CIM_STATUS')
 if status=='UNIQUE_CORRELATED':
  selected=record.get('selected');need(type(selected) is list and record.get('independentEventBoundProof') is True and tuple(selected) in canonical,'CIM_UNPROVEN_UNIQUE')
 else:need(record.get('selected') is None,'CIM_FORCED_MATCH')
 return status
def recompute_secondary(b):
 rows=copy.deepcopy(b['kernel']['rows'])
 for r in rows:
  if r.get('handleCreated')=='0':
   need(r['handleRetained'] is False and r['reason']=='OPEN_PROCESS_FAILED' and r['openError']==87 and r['stopQpc']<r['handleAttemptBeginQpc']<=r['handleAttemptQpc'] and Path(r['image']).name.lower()=='conhost.exe','INVALID_POST_EXIT_SENTINEL')
   r['handleCreated']=None
 table=InstanceTable(rows,b['kernel']['session'])
 canonical={(e['scope'],e['pid'],e['created'],e['sequence']) for e in b['events']}
 for record in b['cim']:
  secondary_policy(record,canonical)
  derived=table.correlate(record['raw']);derived['token']=Path(b['root']).name+':'+str(record['raw']['queueSequence'])
  need(derived==record,'CIM_CORRELATION_SUBSTITUTION')
def rules(envelope,compare_payload=True):
 """Offline semantic evaluation only. No archive acceptance is possible here."""
 schema_check(envelope,load(R/'schema.json'))
 need(envelope['schema']==VERSION and envelope['contract']==CONTRACT and envelope['adapter']=='stage6-small-combined-v1','UNSUPPORTED_CONTRACT')
 b=envelope['bundle'];need(bool(re.fullmatch('identity-[0-9a-f]{32}',envelope['runId'])),'RUN_ID')
 need(envelope['evidenceRoot']==b['root']==envelope['payload']['run'] and Path(b['root']).name==envelope['runId'],'RUN_BINDING')
 need(b['structural']['events']==b['events'] and b['structural']['kernel']==b['kernel'] and b['structural']['cim']==b['cim'] and b['coverage']['events']==b['events'],'RAW_INPUT_DISAGREEMENT')
 for label,values in [('identities',b['coverage']['expected']),('handles',b['coverage']['handles']),('native',b['coverage']['natives']),('segments',b['manifest']['segments']),('events',b['events']),('cim',b['cim'])]:need(len(values)>0,'EMPTY_REQUIRED_'+label)
 need(all(h['image'] for h in b['coverage']['handles'] if h['source']=='creator-owned-handle'),'EMPTY_REQUIRED_IMAGES')
 recompute_secondary(b)
 result=adapter.validate(b)
 # Coverage inputs must retain kernel attributes, not a parallel substituted identity.
 bykey={(x['pid'],x['created'],x['sequence']):x for x in b['kernel']['rows']}
 for x in b['coverage']['expected']:
  need(all(x[k]==v for k,v in bykey[(x['pid'],x['created'],x['sequence'])].items()),'COVERAGE_KERNEL_SUBSTITUTION')
 if compare_payload:need(result==envelope['payload'],'ADAPTER_PAYLOAD_DISAGREEMENT')
 classes=[];cv=result['verification']['coverage']['identities']
 for x in cv:
  if x['role'] in ('DIRECT_PROBE','DIRECT_WORKER'):kind='DIRECT_CREATOR_CAPTURE'
  elif x['role']=='OS_CONSOLE_HELPER':kind='QUALIFIED_POST_EXIT_HELPER' if x['qualifiedPostExit'] else 'TRACER_HELPER_VERIFIED'
  elif x['role']=='APPLICATION_OBSERVER':kind='APPLICATION_OBSERVER_VERIFIED'
  else:raise Rejection('UNKNOWN_PROCESS_CLASS')
  classes.append(dict(pid=x['pid'],created=x['created'],role=x['role'],evidenceClass=kind))
 return dict(status='RULES_SATISFIED_NOT_ACCEPTANCE',schema=VERSION,satisfiedRules=['DURABLE_BYTES_REOPENED_BY_REPLAY','COMPLETE_SEGMENTS','CONTIGUOUS_SEQUENCE','KERNEL_START_STOP_UNIQUE','INDEPENDENT_REQUIRED_INVENTORY','NONVACUOUS_CLASS_COVERAGE','CREATOR_TRACER_POSTEXIT_DISTINCT','NATIVE_ENTRY','CIM_SECONDARY_NOT_FORCED','HEARTBEAT_UNCHANGED','DEADLINES_UNCHANGED','QUEUES_DRAINED','MANIFEST_SEALED','CLEANUP_CLOSED'],counts=dict(collections.Counter(x['evidenceClass'] for x in classes)),identities=classes,adapter=result)
def replay():
 config=self_verify();payload,files=archive_verify(config)
 b=adapter.read_bundle(Path(config['root']),Path(config['analysis']),Path(config['host']))
 envelope=dict(schema=VERSION,contract=CONTRACT,adapter='stage6-small-combined-v1',runId=config['runId'],evidenceRoot=config['root'],payload=payload,bundle=b)
 outcome=rules(envelope)
 # Repeat verification after reading/analysis; no cached summary can substitute bytes.
 archive_verify(config);self_verify()
 return dict(status='PASS',schema=VERSION,contract=CONTRACT,runId=config['runId'],archiveMembersVerified=config['archive']['membersVerified'],originalSourcesVerified=len(files),rules=outcome,acceptanceScope='OFFLINE_SMALL_COMBINED_REPLAY_ONLY',protectedAccess=False,productionChanged=False)
def main():
 try:
  need(sys.argv[1:]==['--replay-validated-small'],'EXPLICIT_REPLAY_MODE_REQUIRED')
  print(json.dumps(replay(),allow_nan=False));return 0
 except Exception as e:
  # The command always exits nonzero on unexpected errors; no fallback or seal.
  print(json.dumps(dict(status='REJECT',errorType=type(e).__name__,reason=str(e))));return 1
if __name__=='__main__':raise SystemExit(main())
