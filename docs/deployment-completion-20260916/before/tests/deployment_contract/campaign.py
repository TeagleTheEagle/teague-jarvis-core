"""Actual relocated TEST acceptance. Evidence preserves all failures."""
import importlib.util
import json
from pathlib import Path
import sys
import time
import traceback
import uuid
import concurrent.futures
import copy
import secrets

spec=importlib.util.spec_from_file_location('deployment_fixture',Path(__file__).with_name('fixtures.py'))
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)

def smoke(c):
    c.build();root,data=c.namespace();b=c.bindings[root]
    c.seed_records(root)
    core=c.core_config(data);coordinator,identity=c.start(root,core)
    c.check('Core identity bound to installed package',identity['installation_id']==b.record['installation_id'] and identity['runtime_build']==b.record['package_hash'])
    c.check('Python cannot impersonate Electron client',c.denied(lambda:c.attach(core,identity,'teague')))
    a=c.start_client(root,core,identity,'teague');other=c.start_client(root,core,identity,'intelligence')
    c.same_state(a,other,data)
    # The last opened real window is visible; do not request an animation-frame
    # acceptance capture from the window occluded by the second client.
    c.send(other,'text-fallback',text='Give a short TEST greeting.',operation=uuid.uuid4().hex)
    fallback=c.receive(other,'text-fallback',timeout=30)
    c.check('packaged fallback final answer and provider provenance',fallback['status']['done'] and bool(fallback['rendered']['text']),rendered=fallback['rendered'],provenance=fallback['provenance'])
    c.close_client(a)
    c.check('closing client preserves installed Core',c.shared(other)['data_id']==data)
    a=c.start_client(root,core,identity,'teague')
    c.close_client(a);c.close_client(other)
    old_token=c.attach(core,identity,'controller')
    c.stop(root,core,identity);c.close(coordinator)
    before=c.snapshot(root)
    newcoordinator=c.coordinator(root,core)
    c.check('ordinary startup of stopped Core denied',c.cc(newcoordinator,'adopt').get('result')=='DENIED')
    grant=c.issue(newcoordinator,identity);c.execute(newcoordinator,grant);settled=c.settle(newcoordinator)
    c.check('explicit installed restart succeeds',settled['result']=='STARTED',state=settled)
    newer=settled['identity'];c.cores.append((root,core,newer))
    c.check('new epoch with same canonical data',newer['data_id']==data and newer['startup_epoch']!=identity['startup_epoch'])
    c.check('old controller authority rejected',c.core_call(core,newer,'controller','shared',token=old_token).get('result')=='DENIED')
    c.check('restart authorization replay denied',c.execute(newcoordinator,grant).get('result')=='DENIED')
    again=c.start_client(root,core,newer,'teague')
    c.send(again,'shared');c.receive(again,'shared')
    c.close_client(again);c.stop(root,core,newer);c.close(newcoordinator)
    c.check('persistent database unchanged across idle restart',before==c.snapshot(root))
    origins=list(root.glob('deployment-runtime-*.json'))
    records=[json.loads(p.read_text()) for p in origins]
    core_records=[v for v in records if v['identity'] is not None]
    c.check('actual process import origins entirely packaged',len(core_records)==2 and all(Path(p).is_relative_to(b.release) for v in records for p in v['origins'].values()),processes=len(records),core_origins=[v['origins'] for v in core_records])
    c.check('unrelated working directory and no PATH dependency',all(v['cwd']==str(c.cwd) and 'PATH' not in v['environment_names'] for v in records))
    return root,data,core,newer

def enrollment_checks(c,root,data,core,prior):
    b=c.bindings[root]
    before=c.control(b,'inspect')
    bad=f.enrollment.signed_request(b,b'\0'*32,'inspect',{})
    c.check('incorrect owner proof rejected in actual packaged process',c.control(b,'inspect',request=bad,expect_failure=True)['denied'])
    coordinator,identity=c.start(root,core,prior)
    old_settings=c.control(b,'client-configuration',{'client':'teague'})
    a=c.start_client(root,core,identity,'teague');other=c.start_client(root,core,identity,'intelligence')
    current=before['clients']['teague']['version']
    revoke=c.control(b,'revoke',{'client':'teague','expected_version':current})
    c.check('owner-authorized revocation durably recorded',revoke['version']==current+1)
    c.send(a,'shared')
    try:c.receive(a,'shared')
    except RuntimeError:c.check('revoked active Electron session rejected',True)
    else:raise AssertionError('Revoked client remained authorized')
    c.check('revocation preserves other owner and Core',c.shared(other)['data_id']==data)
    c.close_client(a);c.close_client(other)
    c.denied_client(root,core,identity,'teague',old_settings)
    c.stop(root,core,identity);c.close(coordinator)
    rejected=c.control(b,'replace',{'client':'teague','expected_version':current},expect_failure=True)
    c.check('stale replacement intent rejected',rejected['denied'])
    replaced=c.control(b,'replace',{'client':'teague','expected_version':current+1})
    c.check('explicit stopped-client re-enrollment advances version',replaced['version']==current+2)
    newcore=c.core_config(data);coordinator,newid=c.start(root,newcore,identity)
    stale=copy.deepcopy(old_settings)
    stale['expectedIdentity']={**newid,'created':str(newid['created'])}
    stale['pinnedPeer']={k:stale['expectedIdentity'][k] for k in ('pid','created','exe_digest')}
    c.denied_client(root,newcore,newid,'teague',stale)
    fresh=c.start_client(root,newcore,newid,'teague')
    c.check('new enrollment authenticates actual executable',c.shared(fresh)['data_id']==data)
    c.close_client(fresh);c.stop(root,newcore,newid);c.close(coordinator)
    after=c.control(b,'inspect')
    c.check('persistent enrollment history survives fresh control processes',after['clients']['teague']['version']==current+2 and after['enrollment_version']==3)
    return newcore,newid

def contender_checks(c,root,core,prior):
    for round_index in range(3):
        contenders=[c.coordinator(root,core) for _ in range(4)]
        grants=[c.issue(x,prior) for x in contenders]
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            outcomes=list(pool.map(lambda pair:c.execute(*pair),zip(contenders,grants)))
        winners=[i for i,x in enumerate(outcomes) if x.get('result')=='AUTHORIZATION_CONSUMED']
        c.check('exactly one installed concurrent start transaction wins',len(winners)==1,round=round_index,outcomes=outcomes)
        winner=contenders[winners[0]];settled=c.settle(winner)
        c.check('winning contender verifies one installed Core',settled['result']=='STARTED',state=settled)
        identity=settled['identity'];c.cores.append((root,core,identity))
        c.check('contender restart changes epoch only',identity['data_id']==prior['data_id'] and identity['startup_epoch']!=prior['startup_epoch'])
        for item in contenders:
            adopted=c.cc(item,'adopt')
            c.check('losing/replacement coordinator adopts same Core',adopted.get('identity')==identity)
            c.close(item)
        # The Core survives every coordinator closing.
        token=c.attach(core,identity,'controller')
        c.check('Core independent of coordinator lifetime',c.core_call(core,identity,'controller','shared',token=token)['data_id']==identity['data_id'])
        c.stop(root,core,identity);prior=identity
    acquired=[x for x in c.events(root,'core_acquired')]
    c.check('each installed start has exactly one recorded acquisition',len(acquired)==len([x for x in c.cores if x[0]==root]),acquisitions=[x['identity'] for x in acquired])
    return prior

def restore_and_uninstall(c,root,data,core,prior):
    b=c.bindings[root]
    snapshot=c.snapshot(root)
    target='TEST-INSTALL-'+uuid.uuid4().hex
    prepared=c.control(b,'prepare-restore',{'target_parent':str(f.VALIDATION),'target_installation':target})
    c.check('synthetic backup prepared under stopped Core locks',prepared['data_id']==data)
    maint=f.contract.Binding(b.descriptor,maintenance=True)
    request=f.enrollment.signed_request(maint,c.keys[root],'finish-restore',{'operation':prepared['operation']})
    restored=f.package.finish_restore(maint,request,c.keys[root])
    c.bindings[restored.state]=restored;c.keys[restored.state]=c.keys[root];c.roots.append(restored.state)
    c.check('restore preserves data identity and renews installation binding',restored.record['data_id']==data and restored.record['installation_id']!=b.record['installation_id'])
    c.check('restored SQLite tables independently match source',c.snapshot(restored.state)==snapshot)
    initialized=c.control(restored,'initialize',{'intent':'RESTORE_SYNTHETIC_TEST'})
    c.check('explicit RESTORE never creates replacement data identity',initialized['identity']['data_id']==data and initialized['intent']=='RESTORE_SYNTHETIC_TEST')
    try:f.contract.Binding(b.descriptor)
    except ValueError as exc:c.check('old installation fenced against double activation',str(exc)=='DEPLOYMENT_FENCED')
    else:raise AssertionError('Transferred installation was not fenced')
    # A restore starts fresh authority/epoch; it does not copy old ready/stop/session files.
    c.check('restored transient Core authority not copied',not (restored.state/'stage4-ready.json').exists() and not (restored.state/'STAGE4_TEST-starts').exists())
    restored_core=c.control(restored,'configuration')
    coordinator,newid=c.start(restored.state,restored_core)
    client=c.start_client(restored.state,restored_core,newid,'teague')
    c.check('restored actual client reads same canonical memory',c.shared(client)['data_id']==data)
    c.close_client(client);c.stop(restored.state,restored_core,newid);c.close(coordinator)
    uninstall=c.control(restored,'prepare-uninstall')
    rm=f.contract.Binding(restored.descriptor,maintenance=True)
    request=f.enrollment.signed_request(rm,c.keys[root],'finish-uninstall',{'operation':uninstall['operation']})
    removed=f.package.finish_uninstall(rm,request)
    c.check('normal TEST uninstall removes only package files',removed['files']>0 and removed['data_preserved'] and not (rm.release/'python/python.exe').exists(),result=removed)
    c.check('uninstall retains database and protected enrollment',(rm.state/'STAGE4_TEST-data/jarvis.sqlite3').is_file() and (rm.state/'enrollment/owner.dpapi').is_file())
    forbidden=f.enrollment.signed_request(rm,c.keys[root],'destroy-data',{'operation':uninstall['operation']})
    try:f.package.finish_uninstall(rm,forbidden)
    except ValueError as exc:c.check('destructive-data authority not exposed',str(exc)=='MAINTENANCE_AUTHORITY')
    else:raise AssertionError('Destructive action accepted')
    request=f.enrollment.signed_request(rm,c.keys[root],'reinstall',{'operation':uninstall['operation']})
    reinstalled=f.package.reinstall(rm,Path(c.package['package']),request)
    c.check('same approved package reinstall preserves identity stopped',reinstalled['data_id']==data and not reinstalled['activation_authorized'])
    active=f.contract.Binding(rm.descriptor);c.bindings[active.state]=active
    newcore=c.control(active,'configuration')
    c.check('reinstall changes start configuration generation',newcore['deployment_revision']==2)
    coordinator=c.coordinator(active.state,newcore)
    c.check('reinstall does not authorize ordinary startup',c.cc(coordinator,'adopt').get('result')=='DENIED')
    grant=c.issue(coordinator,newid);c.execute(coordinator,grant);state=c.settle(coordinator)
    c.check('explicit restart after reinstall works',state['result']=='STARTED',state=state)
    identity=state['identity'];c.cores.append((active.state,newcore,identity))
    fresh=c.start_client(active.state,newcore,identity,'teague')
    c.check('reinstalled actual client reattaches same data',c.shared(fresh)['data_id']==data)
    c.close_client(fresh);c.stop(active.state,newcore,identity);c.close(coordinator)
    inspected=c.control(active,'inspect')
    version=inspected['clients']['teague']['version']
    result=c.control(active,'replace',{'client':'teague','expected_version':version})
    c.check('completed reinstall retains explicit enrollment management',result['version']==version+1)

def negatives(c):
    first,data=c.namespace();second,other=c.namespace()
    c.check('explicit NEW installations have distinct synthetic identities',data!=other and c.bindings[first].record['installation_id']!=c.bindings[second].record['installation_id'])
    core=c.core_config(data)
    marker=first/'STAGE4_TEST-data/STAGE4_TEST.json'
    before=f.contract.digest(marker)
    marker.write_text(json.dumps({'mode':'STAGE4_TEST','data_id':other}))
    c.check('fixture-only mismatched canonical data recorded',True,before=before,after=f.contract.digest(marker))
    c.rejected_coordinator(first,core,'DATA_IDENTITY')
    # Copy synthetic protected material only into an unrelated disposable NEW
    # installation. Its binding must fail even under the same Windows user.
    target=second/'enrollment/owner.dpapi'
    before=f.contract.digest(target);target.write_bytes((first/'enrollment/owner.dpapi').read_bytes())
    denied=c.control(c.bindings[second],'configuration',expect_failure=True)
    c.check('copied owner enrollment rejected by installed bootstrap','ENROLLMENT_INSTALLATION' in denied['stderr'],before=before,after=f.contract.digest(target))
    # Restore rejection before a destination is materialized. Preserve the
    # corrupt backup exactly as injected; never substitute a new data identity.
    root,data=c.namespace();b=c.bindings[root];core=c.core_config(data)
    coordinator,identity=c.start(root,core);c.stop(root,core,identity);c.close(coordinator)
    target='TEST-INSTALL-'+uuid.uuid4().hex
    prepared=c.control(b,'prepare-restore',{'target_parent':str(f.VALIDATION),'target_installation':target})
    backup=root/'backups'/prepared['operation']/'STAGE4_TEST.json'
    before=f.contract.digest(backup);backup.write_text('INVALID SYNTHETIC BACKUP')
    maint=f.contract.Binding(b.descriptor,maintenance=True)
    req=f.enrollment.signed_request(maint,c.keys[root],'finish-restore',{'operation':prepared['operation']})
    try:f.package.finish_restore(maint,req,c.keys[root])
    except ValueError as exc:
        c.check('corrupt restore refuses replacement identity',str(exc)=='RESTORE_ARTIFACT' and not (f.VALIDATION/target).exists(),
            error=str(exc),target=target,before=before,after=f.contract.digest(backup))
    else:raise AssertionError('Corrupt restore succeeded')

def run(c):
    root,data,core,prior=smoke(c)
    core,prior=enrollment_checks(c,root,data,core,prior)
    prior=contender_checks(c,root,core,prior)
    restore_and_uninstall(c,root,data,core,prior)
    for boundary in ('before-intent','intent','spawned'):
        c.fault_case(boundary)
    negatives(c)

if __name__=='__main__':
    campaign=f.InstalledCampaign();failed=False
    try:run(campaign)
    except BaseException as exc:
        failed=True;campaign.records.append(dict(case='campaign exception',passed=False,type=type(exc).__name__,traceback=traceback.format_exc()));campaign.save()
        print(traceback.format_exc())
    finally:campaign.cleanup()
    failed=failed or any(not r['passed'] for r in campaign.records)
    print(json.dumps(dict(evidence=str(campaign.path),records=len(campaign.records),failures=sum(not r['passed'] for r in campaign.records),passed=not failed)))
    sys.exit(failed)
