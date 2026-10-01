"""Actual TEST packages, processes, enrollment, native load paths and update transactions."""
import concurrent.futures
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import secrets
import shutil
import sys
import time
import traceback
import uuid

spec=importlib.util.spec_from_file_location('completion_fixture',Path(__file__).with_name('fixtures.py'))
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
from deployment_test import native, upgrade

def refresh(c,b,maintenance=False):
    new=f.contract.Binding(b.descriptor,maintenance=maintenance);c.bindings[b.state]=new
    return new

def args(c,b,package,interruption=None):
    return dict(package=package['package'],package_hash=package['sha256'],expected_package=b.record['package_hash'],
        expected_enrollment=hashlib.sha256(f.contract.canonical(f.enrollment.current(b))).hexdigest(),interruption=interruption)

def prepared(c,b,package,interruption=None,rollback=False):
    request=args(c,b,package,interruption)
    action='stage-rollback' if rollback else 'stage-update'
    answer=c.control(b,action,request,expect_failure=interruption is not None)
    if interruption is not None:
        records=[f.contract.read_json(p) for p in b.state.glob('update-interrupted-*.json')]
        c.check('real TEST updater self-exit preserved at '+interruption,any(x['boundary']==interruption for x in records),events=records)
    b=refresh(c,b,True)
    return b,answer

def activation(c,b,interruption=None):
    index=b.pending_update
    c.check('pending update rejects ordinary binding',c.denied(lambda:f.contract.Binding(b.descriptor)))
    denied=c.control(b,'commit-update',{'sequence':index,'interruption':None},expect_failure=True)
    c.check('update authorization cannot substitute for enrollment',denied['denied'])
    enrollment=c.control(b,'enroll-update',{'sequence':index})
    c.check('separate owner enrollment prepared',enrollment['result']=='UPDATE_ENROLLMENT_PREPARED')
    signed=f.enrollment.signed_request(b,c.keys[b.state],'commit-update',{'sequence':index,'interruption':interruption})
    result=c.control(b,'commit-update',request=signed,expect_failure=interruption is not None)
    if interruption=='before-commit':
        c.check('interrupted activation remains fenced',c.denied(lambda:f.contract.Binding(b.descriptor)))
        result=c.control(b,'commit-update',{'sequence':index,'interruption':None})
    new=refresh(c,b)
    c.check('activation preserves installation/data identity stopped',new.record['installation_id']==b.record['installation_id'] and
        new.record['data_id']==b.record['data_id'] and new.seal==b.seal and (new.state/'stop').exists() and
        new.record['package_hash']!=b.record['package_hash'],identity=new.audit_identity())
    c.check('activation request cannot replay',c.control(new,'commit-update',request=signed,expect_failure=True)['denied'])
    c.check('stale launcher refuses active release mismatch','PACKAGE_RUNTIME_IDENTITY' in c.control(b,'inspect',expect_failure=True)['stderr'])
    return new

def modules(c,b,identity,client):
    peer={k:identity[k] for k in ('pid','created','exe_digest')}
    records=[native.loaded_modules(identity['pid'],peer,b.release),native.loaded_modules(client['identity']['pid'],client['identity'],b.release)]
    node_peer=c.r.transport.identity(client['process'].pid)
    records.append(native.loaded_modules(node_peer['pid'],node_peer,b.release))
    c.check('actual Python Electron Node native libraries load from package',all(x['packaged_modules_external']==0 for x in records),processes=records)
    electron=records[1]['modules']
    c.check('actual bridge and MSVC libraries observed app-local',any(Path(x['path']).name=='peer_identity.node' for x in electron) and
        all(any(Path(x['path']).name.lower()==name for x in electron) for name in native.CRT))

def changed_build(c,second):
    root,data=c.namespace();b=c.bindings[root];c.seed_records(root)
    original=f.contract.digest(b.descriptor);core=c.core_config(data)
    coordinator,first=c.start(root,core)
    a=c.start_client(root,core,first,'teague');other=c.start_client(root,core,first,'intelligence')
    c.same_state(a,other,data);modules(c,b,first,other)
    oldsettings=c.control(b,'client-configuration',{'client':'teague'})
    before_policy=c.control(b,'inspect');oldentry=before_policy['clients']['teague']
    c.control(b,'revoke',{'client':'teague','expected_version':oldentry['version']})
    c.close_client(a);c.close_client(other);c.stop(root,core,first);c.close(coordinator)
    before=upgrade.snapshot(b)
    b,_=prepared(c,b,second)
    new=activation(c,b)
    c.check('canonical data unchanged by update transaction',upgrade.snapshot(new)==before and f.contract.digest(new.descriptor)==original,snapshot=before)
    policy=c.control(new,'inspect')
    c.check('revoked client stays revoked through re-enrollment',not policy['clients']['teague']['enabled'])
    c.check('actual executable identity changed',policy['clients']['intelligence']['exe_digest']!=before_policy['clients']['intelligence']['exe_digest'],
        before=before_policy['clients']['intelligence']['exe_digest'],after=policy['clients']['intelligence']['exe_digest'])
    newcore=c.core_config(data);controller=c.coordinator(root,newcore)
    c.check('new package ordinary startup remains denied',c.cc(controller,'adopt')['result']=='DENIED')
    grant=c.issue(controller,first);c.execute(controller,grant);state=c.settle(controller)
    c.check('explicit B restart succeeds',state['result']=='STARTED',state=state)
    second_id=state['identity'];c.cores.append((root,newcore,second_id))
    c.check('new epoch same canonical identity',second_id['startup_epoch']!=first['startup_epoch'] and second_id['data_id']==data)
    c.check('old controller credentials rejected',c.denied(lambda:c.attach(core,second_id,'controller')))
    stale=copy.deepcopy(oldsettings);stale['expectedIdentity']={**second_id,'created':str(second_id['created'])}
    stale['pinnedPeer']={k:stale['expectedIdentity'][k] for k in ('pid','created','exe_digest')}
    stale['deployment']['app']=str(new.app);stale['deployment']['packageHash']=new.record['package_hash'];stale['deployment']['nativePath']=str(new.release/'native/peer_identity.node')
    c.denied_client(root,newcore,second_id,'teague',stale)
    client=c.start_client(root,newcore,second_id,'intelligence');modules(c,new,second_id,client)
    c.check('B reads same canonical TEST records',c.shared(client)['data_id']==data)
    c.close_client(client);c.stop(root,newcore,second_id);c.close(controller)
    c.check('idle upgrade/restart preserved all persistent records',upgrade.snapshot(new)==before)
    # Explicit rollback without new data writes, with another distinct enrollment intent.
    b,_=prepared(c,new,c.package,rollback=True);rolled=activation(c,b)
    rolledcore=c.core_config(data);ctl,third=c.start(root,rolledcore,second_id)
    c.check('rollback does not restore old revoked authority',not c.control(rolled,'inspect')['clients']['teague']['enabled'])
    client=c.start_client(root,rolledcore,third,'intelligence')
    c.check('rollback uses previous package with same data',third['runtime_build']==c.package['sha256'] and c.shared(client)['data_id']==data)
    c.close_client(client);c.stop(root,rolledcore,third);c.close(ctl)
    c.check('rollback preserves persistent state',upgrade.snapshot(rolled)==before)
    # Upgrade again, write a real response, then refuse rollback over newer data.
    b,_=prepared(c,rolled,second);new=activation(c,b);newcore=c.core_config(data);ctl,fourth=c.start(root,newcore,third)
    client=c.start_client(root,newcore,fourth,'intelligence')
    c.send(client,'text-fallback',text='Return a brief TEST upgrade confirmation.',operation=uuid.uuid4().hex)
    answer=c.receive(client,'text-fallback',timeout=30)
    c.check('B response visibly rendered with persisted provenance',answer['status']['done'] and bool(answer['rendered']['text']),rendered=answer['rendered'],provenance=answer['provenance'])
    c.close_client(client);c.stop(root,newcore,fourth);c.close(ctl)
    rejected=c.control(new,'stage-rollback',args(c,new,c.package),expect_failure=True)
    c.check('rollback refuses newer canonical response data','ROLLBACK_NEWER_DATA_REFUSED' in rejected['stderr'] and upgrade.snapshot(new)!=before)
    c.check('failed rollback preserves B and stop state',f.contract.Binding(new.descriptor).record['package_hash']==second['sha256'] and (root/'stop').exists())

def interruption_checks(c,second):
    for boundary in ('before-intent','after-intent','during-staging','after-staging','before-commit','after-commit'):
        root,data=c.namespace();b=c.bindings[root];core=c.core_config(data);ctl,identity=c.start(root,core)
        c.stop(root,core,identity);c.close(ctl);before=upgrade.snapshot(b)
        if boundary in ('before-commit','after-commit'):
            b,_=prepared(c,b,second);b=activation(c,b,boundary)
            c.check('committed interrupted update resolves exactly B',b.record['package_hash']==second['sha256'],boundary=boundary)
        else:
            b,_=prepared(c,b,second,boundary)
            if boundary=='before-intent':c.check('before-intent interruption keeps A valid',b.pending_update is None)
            else:
                c.check('uncommitted interruption blocks startup',c.denied(lambda:f.contract.Binding(b.descriptor)))
                result=c.control(b,'abort-update',{'sequence':b.pending_update})
                c.check('explicit abort preserves failed staging files',result['result']=='ABORTED_STOPPED' and result['files_preserved'])
            b=refresh(c,b)
        c.check('interruption preserves data and lifetime lock',upgrade.snapshot(b)==before,boundary=boundary)
        with c.r.exclusion.Lock(root,'core.lock'):c.check('no unintended Core after update interruption',True,boundary=boundary)
        restarted=c.core_config(data);controller,newid=c.start(root,restarted,identity)
        c.check('recovered package requires explicit fresh epoch',newid['startup_epoch']!=identity['startup_epoch'])
        c.stop(root,restarted,newid);c.close(controller)

def repin(folder):
    manifest=f.contract.read_json(folder/'manifest.json',4194304)
    for entry in manifest['files']:
        file=folder/entry['path']
        if file.exists():entry.update(sha256=f.contract.digest(file),bytes=file.stat().st_size)
    (folder/'manifest.json').write_bytes(f.contract.canonical(manifest))
    return dict(package=str(folder),sha256=f.contract.digest(folder/'manifest.json'))

def negatives(c,second):
    root,data=c.namespace();b=c.bindings[root];core=c.core_config(data);ctl,identity=c.start(root,core)
    c.stop(root,core,identity);c.close(ctl)
    for case in ('omitted-dll','modified-dll','wrong-dll','native-version','protocol','schema','hash','incomplete'):
        folder=f.VALIDATION/('TEST-PACKAGE-'+uuid.uuid4().hex);shutil.copytree(second['package'],folder)
        dll=folder/'electron/msvcp140.dll'
        if case in ('omitted-dll','incomplete'):dll.rename(dll.with_suffix('.preserved'))
        elif case=='modified-dll':
            with dll.open('r+b') as stream:stream.seek(100);stream.write(b'TEST_CORRUPTION')
        elif case=='wrong-dll':shutil.copyfile(folder/'electron/vcruntime140.dll',dll)
        elif case=='native-version':
            n=f.contract.read_json(folder/'native-manifest.json',4194304)
            next(x for x in n['entries'] if x['path']=='electron/msvcp140.dll')['version']='0.0.0.0'
            (folder/'native-manifest.json').write_bytes(f.contract.canonical(n))
        elif case in ('protocol','schema'):
            m=f.contract.read_json(folder/'manifest.json',4194304);m['protocol' if case=='protocol' else 'data_schema']=([99,99] if case=='protocol' else 99)
            (folder/'manifest.json').write_bytes(f.contract.canonical(m))
        package=repin(folder) if case=='native-version' else dict(package=str(folder),sha256=f.contract.digest(folder/'manifest.json'))
        if case=='hash':package['sha256']='0'*64
        result=c.control(b,'stage-update',args(c,b,package),expect_failure=True)
        c.check('invalid package rejected: '+case,result['denied'] and f.contract.Binding(b.descriptor).pending_update is None,
            package=str(folder),expected_package_hash=package['sha256'],error=result['stderr'])
    # Current owner proof is distinct from lifecycle/client credentials.
    request=f.enrollment.signed_request(b,bytes.fromhex(core['enrollments']['controller']['key']),'stage-update',args(c,b,second))
    c.check('lifecycle credential cannot authorize updater',c.control(b,'stage-update',request=request,expect_failure=True)['denied'])
    pending,_=prepared(c,b,second)
    intent_path=pending.state/'updates'/f'intent-{pending.pending_update:06d}.dpapi'
    # Deliberate TEST-only protected-record expiry fixture, retained as injected.
    intent=f.contract.read_protected(intent_path);oldhash=f.contract.digest(intent_path)
    preserved=intent_path.with_suffix('.original');intent_path.rename(preserved)
    intent['expires']=0;f.contract.write_protected(intent_path,intent)
    result=c.control(pending,'enroll-update',{'sequence':pending.pending_update},expect_failure=True)
    c.check('expired durable update cannot enroll or activate','UPDATE_EXPIRED' in result['stderr'],before=oldhash,after=f.contract.digest(intent_path))
    c.control(pending,'abort-update',{'sequence':pending.pending_update});refresh(c,pending)

def run(c):
    c.build()
    second=f.package.build(f.ROOT,f.VALIDATION/('TEST-PACKAGE-'+uuid.uuid4().hex),
        node=Path(sys._base_executable).parent.parent/'node/bin/node.exe',native=f.ROOT.parent/'stage4-toolchain/peer-build/Release/peer_identity.node',
        electron=(f.ROOT/'desktop/node_modules/electron/dist').resolve(),
        expected_electron_hash='07b043bf9b0a0ac14a82fac0b612b7b7ed13cde727d706d74e41a45278ab51f1',application_version=2)
    c.check('distinct A/B package and executable versions',second['sha256']!=c.package['sha256'] and
        f.contract.digest(Path(second['package'])/'electron/electron.exe')!=f.contract.digest(Path(c.package['package'])/'electron/electron.exe'),build_b=second)
    for build in (c.package,second):
        inventory=native.verify_native(Path(build['package']))
        c.check('complete explicit native inventory verified',len(inventory['entries'])>50,package=build,manifest=inventory)
    changed_build(c,second);interruption_checks(c,second);negatives(c,second)

if __name__=='__main__':
    campaign=f.InstalledCampaign();campaign.path=f.OUT/('completion-'+uuid.uuid4().hex+'.json');failed=False
    try:run(campaign)
    except BaseException:
        failed=True;campaign.records.append(dict(case='completion exception',passed=False,traceback=traceback.format_exc()));campaign.save();print(traceback.format_exc())
    finally:campaign.cleanup()
    failed=failed or any(not x['passed'] for x in campaign.records)
    print(json.dumps(dict(evidence=str(campaign.path),checks=len(campaign.records),failures=sum(not x['passed'] for x in campaign.records))))
    sys.exit(failed)
