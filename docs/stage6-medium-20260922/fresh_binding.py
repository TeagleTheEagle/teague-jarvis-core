"""Fresh-run admission and post-run binding; TEST only, no archive pre-acceptance."""
import hashlib,json,os,re
from pathlib import Path
SCHEMA='stage6-medium-declaration-v1'
def validate_declaration(d,code,root):
 expected=dict(schema=SCHEMA,runId=root.name,codeRoot=str(code),evidenceRoot=str(root),directWorkers=1,directProbes=64,cases=[dict(name='idle',groups=16,width=1),dict(name='churn',groups=16,width=1),dict(name='overlap',groups=4,width=8)],minimumSegments=8,heartbeatSeconds=10,hardDeadlineSeconds=13.6,observerSeconds=15,collectionSeconds=60,queueItems=65536,queueBytes=67108864,pendingSegments=2,segmentBytes=8192)
 if type(d) is not dict or json.dumps(d,sort_keys=True)!=json.dumps(expected,sort_keys=True):raise ValueError('DECLARATION_MISMATCH')
 if not re.fullmatch('identity-[0-9a-f]{32}',root.name) or root.parent!=code or code.name!='code' or code.parent.parent!=Path('D:/JARVIS-STAGE6-LIVE'):raise ValueError('DECLARATION_PATH')
 return d
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bound(code):
 code=Path(code);freeze=load(code/'medium-source-freeze.json');intent=load(code/'medium-intent.json');root=Path(intent['evidenceRoot'])
 for p in (code,root,*root.parents):
  if p.is_symlink() or p.is_junction():raise ValueError('REPARSE_FORBIDDEN')
 for x in freeze['files']:
  p=Path(x['path'])
  if not p.is_relative_to(code) or sha(p)!=x['sha256']:raise ValueError('CANDIDATE_HASH_DRIFT')
 if sha(code/'medium-declaration.json')!=intent['declarationSHA256']:raise ValueError('INTENT_DECLARATION_HASH')
 return root,validate_declaration(load(code/'medium-declaration.json'),code,root)
def seal_intake(code):
 root,d=bound(code);rows=[]
 for p in sorted(root.rglob('*')):
  if p.is_symlink() or p.is_junction():raise ValueError('INTAKE_REPARSE')
  if p.is_file():
   if p.name=='intake-manifest.json':raise ValueError('INTAKE_ALREADY_EXISTS')
   rows.append(dict(path=p.relative_to(root).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
 value=dict(schema='stage6-medium-intake-v1',runId=root.name,declarationSHA256=sha(Path(code)/'medium-declaration.json'),sourceFreezeSHA256=sha(Path(code)/'medium-source-freeze.json'),files=rows,acceptance=False)
 with (root/'intake-manifest.json').open('x',encoding='utf8') as f:json.dump(value,f,indent=2);f.flush();os.fsync(f.fileno())
 return value
def verify_intake(code):
 root,d=bound(code);m=load(root/'intake-manifest.json')
 if m['schema']!='stage6-medium-intake-v1' or m['runId']!=root.name or m['acceptance'] is not False or m['declarationSHA256']!=sha(Path(code)/'medium-declaration.json') or m['sourceFreezeSHA256']!=sha(Path(code)/'medium-source-freeze.json'):raise ValueError('INTAKE_BINDING')
 expected=set()
 for row in m['files']:
  rel=Path(row['path']);p=root/rel
  if rel.is_absolute() or '..' in rel.parts or ':' in str(rel) or '\\' in row['path'] or row['path'] in expected:raise ValueError('INTAKE_PATH')
  expected.add(row['path'])
  if p.is_symlink() or p.is_junction() or not p.resolve().is_relative_to(root.resolve()) or p.stat().st_size!=row['bytes'] or sha(p)!=row['sha256']:raise ValueError('INTAKE_HASH')
 actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.name!='intake-manifest.json'}
 if actual!=expected or not expected:raise ValueError('INTAKE_SET')
 return root,d,m
