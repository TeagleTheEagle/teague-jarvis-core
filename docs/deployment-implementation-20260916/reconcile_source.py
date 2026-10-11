"""Read-only source reconciliation plus nonsecret evidence outputs."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
changed=['tests/lifecycle_stage1/harness.py','stage4_runtime.py','stage4_client.cjs']
new=['deployment_test/'+x+'.py' for x in ('contract','package','bootstrap','enrollment')]+['tests/deployment_contract/'+x+'.py' for x in ('test_contract','fixtures','campaign')]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
for name in changed+new:
    p=ROOT/name;old=OUT/'before'/name
    records.append(dict(path=name,before_sha256=sha(old) if old.exists() else None,after_sha256=sha(p),prior_acceptance_boundary=name in changed))
    if old.exists():
        diff=''.join(difflib.unified_diff(old.read_text().splitlines(True),p.read_text().splitlines(True),fromfile='before/'+name,tofile='current/'+name))
        (OUT/(name.replace('/','__')+'.diff')).write_text(diff,encoding='utf8')
prior=json.loads((OUT/'historical-accepted-hashes.json').read_text(encoding='utf-8-sig'))
continuity=[dict(path=x['path'],historical=x['sha256'],current=sha(ROOT/x['path']),intentionally_changed=x['path'] in changed) for x in prior]
assert all(x['historical']==x['current'] or x['intentionally_changed'] for x in continuity),'UNEXPECTED_ACCEPTED_SOURCE_DRIFT'
functions=[]
for name in changed[:2]:
    def nodes(p):
        tree=ast.parse(p.read_text(encoding='utf8'))
        return {x.name:ast.dump(x,include_attributes=False) for x in tree.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
    a=nodes(OUT/'before'/name);b=nodes(ROOT/name)
    functions.append(dict(path=name,modified=[k for k in a if a[k]!=b.get(k)],added=sorted(set(b)-set(a)),removed=sorted(set(a)-set(b))))
syntax=[]
for name in changed+new:
    if name.endswith('.py'):
        ast.parse((ROOT/name).read_text(encoding='utf8'),filename=name)
        syntax.append(dict(path=name,method='ast.parse UTF-8 final source; no import/execution',passed=True,sha256=sha(ROOT/name)))
node=Path(sys._base_executable).parent.parent/'node/bin/node.exe'
result=subprocess.run([str(node),'--check',str(ROOT/'stage4_client.cjs')],capture_output=True,text=True)
syntax.append(dict(path='stage4_client.cjs',command=result.args,exit=result.returncode,output=result.stdout+result.stderr,passed=result.returncode==0))
tree=ast.parse((ROOT/'deployment_test/package.py').read_text())
for statement in tree.body:
    if isinstance(statement,ast.Assign) and isinstance(statement.targets[0],ast.Name) and statement.targets[0].id in ('ELECTRON_ENTRY','NODE_LAUNCHER'):
        code=ast.literal_eval(statement.value)
        result=subprocess.run([str(node),'--check','-'],input=code,capture_output=True,text=True)
        syntax.append(dict(path=statement.targets[0].id,source='deployment_test/package.py',sha256=hashlib.sha256(code.encode()).hexdigest(),command=result.args,exit=result.returncode,output=result.stdout+result.stderr,passed=result.returncode==0))
assert all(x['passed'] for x in syntax)
report=dict(source=records,accepted_continuity=continuity,ast_boundary_comparison=functions,syntax=syntax,production_data_opened=False)
target=OUT/'source-final.json'
if target.exists():
    old=json.loads(target.read_text());assert old==report,'FROZEN_SOURCE_CHANGED'
else:target.write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(dict(files=len(records),prior_paths=len(continuity),intentional_changes=sum(x['historical']!=x['current'] for x in continuity),syntax_checks=len(syntax),boundaries=functions)))
