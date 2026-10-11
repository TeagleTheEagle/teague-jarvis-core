"""Isolated accepted-source deployment validation; explicit verified build inputs."""
from pathlib import Path
import importlib.util,json,sys,traceback,uuid,subprocess
D=Path(__file__).resolve().parent.parent/"stage6-separated-io-20260917"
S=Path(json.loads((D/'source.json').read_text())['source'])
R=D.parents[1]
sys.path.insert(0,str(S))
spec=importlib.util.spec_from_file_location('stage6_completion',S/'tests/deployment_contract/completion.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
f=m.f
electron=(R/'desktop/node_modules/electron/dist').resolve()
expected='07b043bf9b0a0ac14a82fac0b612b7b7ed13cde727d706d74e41a45278ab51f1'
def build(version):
    if len(sys.argv)>1:
        prior=json.loads(Path(sys.argv[1]).read_text())
        item=prior['package'] if version==1 else next(r['build_b'] for r in prior['records'] if 'build_b' in r)
        root=Path(item['package'])
        assert f.contract.digest(root/'manifest.json')==item['sha256']
        for relative in f.package.APP_FILES:
            assert f.contract.digest(root/'app'/relative)==f.contract.digest(S/relative),relative
        return item
    return f.package.build(S,f.VALIDATION/('TEST-PACKAGE-'+uuid.uuid4().hex),
        node=Path(sys._base_executable).parent.parent/'node/bin/node.exe',
        native=R.parent/'stage4-toolchain/peer-build/Release/peer_identity.node',
        electron=electron,expected_electron_hash=expected,application_version=version)
c=f.InstalledCampaign();c.electron=electron/'electron.exe'
c.path=D/('deployment-'+uuid.uuid4().hex+'.json')
# Source-side comparison requires its own explicitly bound process, just as
# packaged bootstrap does. Never rebind a shared runtime or relax its root check.
def snapshot(binding):
    code="import sys,json;sys.path.insert(0,sys.argv[1]);from deployment_test.contract import Binding;import stage4_runtime as r;from deployment_test.upgrade import snapshot;b=Binding(sys.argv[2],maintenance=True);b.verify_package();r.configure_deployment(b);print(json.dumps(snapshot(b)))"
    result=subprocess.run([str(binding.release/'python/python.exe'),'-B','-c',code,str(binding.app),str(binding.descriptor)],cwd=c.cwd,env=c.env,capture_output=True,text=True,timeout=35,creationflags=0x08000000)
    if result.returncode:raise RuntimeError('Bound snapshot failed: '+result.stderr)
    return json.loads(result.stdout)
m.upgrade.snapshot=snapshot
def verify_idle(binding):
    code="import sys,json;sys.path.insert(0,sys.argv[1]);from deployment_test.contract import Binding;import stage4_runtime as r;b=Binding(sys.argv[2],maintenance=True);b.verify_package();r.configure_deployment(b);lock=r.exclusion.Lock(b.state,'core.lock');lock.__enter__();lock.__exit__(None,None,None);print(json.dumps({'core_lock_available':True}))"
    result=subprocess.run([str(binding.release/'python/python.exe'),'-B','-c',code,str(binding.app),str(binding.descriptor)],cwd=c.cwd,env=c.env,capture_output=True,text=True,timeout=35,creationflags=0x08000000)
    if result.returncode:raise RuntimeError('Bound lock check failed: '+result.stderr)
    return json.loads(result.stdout)=={'core_lock_available':True}
c.verify_idle=verify_idle

import time
OUT=Path(__file__).resolve().parent
c.path=OUT/('negative-repeat-'+uuid.uuid4().hex+'.json')
# Record identity before the original wait, without logging signed requests or credentials.
def observed_control(binding,action,args=None,request=None,expect_failure=False):
    req=request or f.enrollment.signed_request(binding,c.keys[binding.state],action,args or {})
    command=binding.python_command('--control')
    start=time.monotonic(); wall=time.time_ns()
    p=subprocess.Popen(command,cwd=c.cwd,env=c.env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,close_fds=True,creationflags=0x08000000)
    peer=c.r.transport.identity(p.pid)
    rec={'identity':peer,'action':action,'started_ns':wall,'command':command,'timeout_seconds':f.control_timeout(action),'phase':'waiting','test_state':str(binding.state)}
    c.controls.append(rec);c.save()
    try:
        stdout,stderr=p.communicate(json.dumps(req)+'\n',timeout=f.control_timeout(action))
    except subprocess.TimeoutExpired:
        rec.update(phase='TIMEOUT',elapsed=time.monotonic()-start);c.save()
        # Observe this exact existing child for cleanup only; this is NOT a retry or passing result.
        try:
            stdout,stderr=p.communicate(timeout=30)
            rec.update(cleanup_observed_exit=p.returncode,cleanup_elapsed=time.monotonic()-start,stderr=stderr)
        except subprocess.TimeoutExpired:
            rec.update(cleanup='RETAINED_FOR_REVIEW')
        c.save();raise
    rec.update(phase='exited',exit=p.returncode,elapsed=time.monotonic()-start)
    if p.returncode:
        rec['stderr']=stderr;c.save()
        if expect_failure:return {'denied':True,'stderr':stderr}
        raise RuntimeError('Installed control failed '+action+': '+stderr)
    c.save()
    if expect_failure:raise AssertionError('Expected rejection: '+action)
    return json.loads(stdout)
c.control=observed_control
failed=False
try:
    prior=json.loads((D/'final-reconciliation.json').read_text())
    for item in prior['files']:
        assert f.contract.digest(S/item['path'])==item['after'],item['path']
    c.package=build(1);second=build(2)
    c.check('frozen candidate/package source hashes unchanged',True)
    m.negatives(c,second)
except BaseException:
    failed=True;c.records.append(dict(case='bounded reproduction failure',passed=False,traceback=traceback.format_exc()));c.save();print(traceback.format_exc())
finally:c.cleanup()
print(json.dumps(dict(evidence=str(c.path),checks=len(c.records),failures=sum(not x['passed'] for x in c.records),control_timings=[{'action':x['action'],'elapsed':x.get('elapsed'),'phase':x.get('phase')} for x in c.controls])))
sys.exit(failed)
