"""Disposable security-rule probes; never launch JARVIS or alter its guard."""
import ast,hashlib,json,os,subprocess,sys,uuid
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parents[1]
S=Path(json.loads((R/'docs/stage6-20260917/source.json').read_text())['source'])
if len(sys.argv)>1:
    root=Path(sys.argv[2]);mode=sys.argv[1]
    tree=ast.parse((S/'deployment_test/bootstrap.py').read_text())
    main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    node=next(n for n in main.body if isinstance(n,ast.FunctionDef) and n.name=='no_external_code')
    def need(ok,reason):
        if not ok:raise ValueError(reason)
    scope={'Path':Path,'RELEASE':root/'active','need':need}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'<exact-existing-audit-function>','exec'),scope)
    guard=scope['no_external_code'];incoming=root/'incoming/inert.py'
    def audit(event,args):
        # Deliberately proposed exact-file read-only exception, experiment only.
        # Demonstrates why this exception ALONE cannot prove execution denial.
        if mode=='read-only-exception' and event=='open' and isinstance(args[0],str) and Path(args[0]).resolve()==incoming and args[1]=='r' and not args[2] & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):return
        guard(event,args)
    if mode!='no-hook':sys.addaudithook(audit)
    result={'mode':mode}
    try:
        text=incoming.read_text();result['incoming_read']='ALLOWED'
        namespace={};exec(compile(text,str(incoming),'exec'),namespace)
        result['inert_code_executed']=namespace.get('TEST_INERT_VALUE')==73
    except Exception as exc:result['incoming_read']='DENIED';result['error']=str(exc)
    target=root/'staged/inert.py'
    try:
        with target.open('xb') as stream:stream.write(b'# synthetic staging probe\n')
        result['staging_write']='ALLOWED'
    except Exception as exc:result['staging_write']='DENIED';result['write_error']=str(exc)
    print(json.dumps(result));sys.exit(0)
results=[]
for mode in ('existing-guard','read-only-exception','no-hook'):
    root=D/('TEST-PROBE-'+uuid.uuid4().hex)
    for name in ('active','incoming','staged'):(root/name).mkdir(parents=True)
    (root/'incoming/inert.py').write_text('TEST_INERT_VALUE = 73\n')
    p=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),mode,str(root)],capture_output=True,text=True,timeout=10)
    results.append({'root':str(root),'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
record={'results':results,'source_sha256':hashlib.sha256((S/'deployment_test/bootstrap.py').read_bytes()).hexdigest(),'production_changed':False,'core_launched':False,'interpretation':'Exact-file read-only exception alone does not prevent execution. Audit hook is process-local, not Windows cross-process access control.'}
(D/'probe-results.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record,indent=2))
