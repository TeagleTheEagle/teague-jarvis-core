"""Allowlisted nonsecret evidence package; no recursive runtime copying."""
import difflib,hashlib,json,pathlib,re,shutil
OUT=pathlib.Path(__file__).resolve().parent;ROOT=OUT.parents[2];BASE=OUT.parent
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,obj):path.write_text(json.dumps(obj,indent=2),encoding='utf-8')
node='C:/Users/jonny/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
py=str(ROOT/'.venv/Scripts/python.exe')
commands=json.loads((OUT/'direct-regressions.json').read_text())
commands.extend([
 {'name':'actual-denial','command':[py,'-B','tests/lifecycle_stage4/fixtures.py','--human-denial-probe'],'exit':0,'context':'approved host context','log':'actual-denial-01.log'},
 {'name':'electron-lifecycle','command':[py,'-B','tests/lifecycle_stage4/fixtures.py','--electron-app-probe'],'exit':0,'context':'approved host context','log':'electron-lifecycle.log'},
 {'name':'desktop','command':[node,'--test',*[str(p) for d in ('desktop','intelligence') for p in sorted((ROOT/d/'test').glob('*.test.cjs'))]],'exit':0,'log':'desktop.log'}])
write(OUT/'commands.json',commands)
selected=set()
for item in json.loads((OUT/'before-hashes.json').read_text())['changed_files']:
 path=ROOT/item['path'];before=OUT/'before'/item['path']
 assert sha(before)==item['sha256']
 target=OUT/'after'/item['path'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
 patch=OUT/('diff-'+item['path'].replace('/','_')+'.patch')
 patch.write_text(''.join(difflib.unified_diff(before.read_text(encoding='utf-8').splitlines(keepends=True),path.read_text(encoding='utf-8').splitlines(keepends=True),fromfile='before/'+item['path'],tofile='after/'+item['path'])),encoding='utf-8')
 selected.add(path)
for path in OUT.rglob('*'):
 if path.is_file() and 'selected-records' not in path.parts and path.name not in ('manifest.json','archive-verification.json'):
  selected.add(path)
for name in ['human-lifecycle-7cc0db70a76149c9954eb82fc4c0c5b5.json','human-denial-probe-975dc5ebc14240ba9a3ff8839f604b92.json',
             'electron-app-probe-993086388f7546c2b0865e27c9eb2863.json','ownership-model-0176998ba48048499144d46eab5a4a6b.json',
             'controller-recovery-3638ef51e6484bdcaa9033a20104a50c.json']:
 selected.add(BASE/name)
selected.add(ROOT/'tests/lifecycle_stage2/evidence/f280991edb9c4496ad5f2d628fe98713.json')
for name in ['CORE-COMPLETION-CHECKLIST.md','STAGE4-REMAINING-REQUIREMENTS-20260915.md','STAGE4-HUMAN-LIFECYCLE-CHECK.md']:
 selected.add(ROOT/'docs'/name)
run=ROOT/'tests/lifecycle_stage1/evidence/TEST-STAGE4-b310564de96f4625a256345f28b88cb9'
selected.update(run.glob('*-ordinary_shutdown_policy.json'))
selected.update(run.glob('*-stage4_drained.json'))
secret_fields={'api_key','access_token','refresh_token','server_key','client_key','secret','password','credential','token'}
def inspect(obj):
 if isinstance(obj,dict):
  for key,value in obj.items():
   assert key.lower() not in secret_fields or value in (None,'',False,'REDACTED','[REDACTED]'),'secret field requires review'
   inspect(value)
 elif isinstance(obj,list):
  for value in obj:inspect(value)
entries=[]
for path in sorted(selected):
 relative=path.relative_to(ROOT)
 assert path.is_file() and not path.is_symlink()
 assert path.suffix.lower() in {'.py','.cjs','.md','.json','.log','.patch','.ps1'}
 text=path.read_text(encoding='utf-8-sig')
 assert not re.search(r'sk-(?:proj-)?[A-Za-z0-9_-]{24,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',text)
 if path.suffix=='.json':inspect(json.loads(text))
 target=OUT/'selected-records'/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
 assert sha(path)==sha(target)
 entries.append({'path':relative.as_posix(),'sha256':sha(path),'bytes':path.stat().st_size})
write(OUT/'manifest.json',{'purpose':'narrow TEST denial-driver correction; not human acceptance','files':entries,
 'excluded':['credentials, grants and private handshakes','databases','profiles/caches','unrelated source','runtime binaries']})
print(json.dumps({'files':len(entries),'bytes':sum(x['bytes'] for x in entries),'manifest_sha256':sha(OUT/'manifest.json')}))
