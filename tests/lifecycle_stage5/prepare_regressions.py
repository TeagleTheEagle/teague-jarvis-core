"""Stage test dependencies without overwriting any accepted application file."""
from pathlib import Path
import hashlib,json,shutil,subprocess
R=Path(__file__).resolve().parents[2];D=R/'docs/stage5-continuation-20260917'
base=json.loads((R/'docs/stage5-accepted-baseline-20260917/baseline.json').read_text());A=Path(base['app']);rows=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
# Missing support sources come from the immutable commit, never pending runtime edits.
paths=subprocess.check_output(['git','ls-tree','-r','--name-only',base['baseline']],cwd=R,text=True).splitlines()
for name in paths:
    p=Path(name)
    if len(p.parts)>1 and p.parts[0] not in ('desktop','intelligence','static','tests'):continue
    if 'evidence' in p.parts or 'node_modules' in p.parts:continue
    if p.suffix not in ('.py','.js','.cjs','.html','.css','.png','.svg') and p.name!='package.json':continue
    target=A/name
    if target.exists():continue
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(subprocess.check_output(['git','show',base['baseline']+':'+name],cwd=R))
    rows.append({'path':name,'origin':base['baseline'],'sha256':sha(target)})
# Current test files are harness-only inputs; keep accepted runtime modules intact.
protected={str(Path(x['path']).relative_to('accepted-app')).replace('\\','/') for x in base['source']}
inputs=list(R.glob('test_*.py'))+list((R/'tests').rglob('*.py'))+list((R/'desktop/test').glob('*.cjs'))+list((R/'intelligence/test').glob('*.cjs'))
for p in inputs:
    name=p.relative_to(R).as_posix()
    if 'evidence' in p.relative_to(R).parts or name in protected or name.startswith('tests/lifecycle_stage5/'):continue
    target=A/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
    rows.append({'path':name,'origin':'test-only source','sha256':sha(target)})
# Desktop entry sources were hash-pinned in the historical accepted client records.
old=json.loads((R/'docs/lifecycle-stage5-evidence/source-final.json').read_text())
for name in ('desktop/main.cjs','intelligence/main.cjs'):
    expected=next(x['sha256'] for x in old if x['path']==name);assert sha(R/name)==expected
    shutil.copyfile(R/name,A/name);rows.append({'path':name,'origin':'accepted client source pin','sha256':expected})
for name in ('docs/lifecycle-stage4-evidence/completion-campaign-20260915/python_regression_guard.py',):
    target=A/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/name,target)
package=Path(json.loads((D/'candidate.json').read_text())['package']['package'])
electron=A/'desktop/node_modules/electron/dist'
if not electron.exists():shutil.copytree(package/'electron',electron)
for directory in ('tests/lifecycle_stage2/evidence','tests/lifecycle_stage3/evidence'):(A/directory).mkdir(parents=True,exist_ok=True)
for x in base['source']:assert sha(A/Path(x['path']).relative_to('accepted-app'))==x['sha256']
(D/'regression-inputs.json').write_text(json.dumps(rows,indent=2))
print(json.dumps({'test_support_inputs':len(rows),'accepted_application_unchanged':True}))
