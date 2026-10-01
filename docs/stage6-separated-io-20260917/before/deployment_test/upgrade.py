"""Owner-authorized TEST package activation. Never starts/stops a Core or edits data."""
import hashlib
import os
from pathlib import Path
import secrets
import time
import uuid
from .contract import (Binding, canonical, digest, need, safe_path, read_json, read_protected,
                       write_protected, private_directory, exclusive_json)
from . import enrollment as e
from . import package as p

def verify_release(release,package_hash,hold=False):
    # Package verification is not an installation binding or authority grant.
    verifier=object.__new__(Binding)
    verifier.release=safe_path(release,directory=True)
    verifier.record={'package_hash':package_hash,'data_schema':1};verifier.handles=[]
    try:verifier.verify_package(hold=hold)
    except BaseException:verifier.close();raise
    return verifier

def snapshot(binding):
    import stage4_runtime as r
    data=r.validate_data(binding.state,binding.record['data_id'])
    artifacts={}
    for file in sorted(data.rglob('*')):
        if not file.is_file() or file.name in ('jarvis.sqlite3','jarvis.sqlite3-wal','jarvis.sqlite3-shm'):continue
        safe_path(file,directory=False)
        artifacts[file.relative_to(data).as_posix()]=digest(file)
    return dict(database=p.logical_database(data/'jarvis.sqlite3'),artifacts=artifacts)

def _observe(binding,boundary,requested):
    if boundary!=requested:return
    from .contract import _transport
    exclusive_json(binding.state/('update-interrupted-'+uuid.uuid4().hex+'.json'),
        dict(boundary=boundary,identity=_transport().identity(os.getpid()),data_id=binding.record['data_id']))
    os._exit(94)  # Explicit bounded TEST self-exit; never accepts another PID.

def _pending(binding):
    need(binding.pending_update is not None,'NO_PENDING_UPDATE')
    index=binding.pending_update;directory=binding.state/'updates'
    path=directory/f'intent-{index:06d}.dpapi';intent=read_protected(path)
    need(intent['binding']==binding.seal and intent['previous_package']==binding.record['package_hash'],'STALE_UPDATE')
    return directory,index,path,intent

def operate(binding,request):
    import stage4_runtime as r
    body=e.authorize(binding,request);action,args=body['action'],body['args']
    need(action in ('stage-update','stage-rollback','enroll-update','commit-update','abort-update'),'UPDATE_ACTION')
    need(type(args)is dict,'UPDATE_ARGUMENTS')
    with r.exclusion.Lock(binding.state,'supervisor.lock'),r.exclusion.Lock(binding.state,'core.lock'):
        fresh=Binding(binding.descriptor,maintenance=True)
        need(fresh.record==binding.record and fresh.activation==binding.activation,'STALE_UPDATE_CALLER')
        binding=fresh
        need((binding.state/'stop').exists(),'AUTHORIZED_STOP_REQUIRED')
        need(not (binding.state/'deployment-fence.json').exists(),'OTHER_MAINTENANCE_PENDING')
        r._start_history(binding.state,binding.record['data_id'])
        if action in ('stage-update','stage-rollback'):
            need(binding.pending_update is None,'UPDATE_ALREADY_PENDING')
            fields={'package','package_hash','expected_package','expected_enrollment','interruption'}
            need(set(args)==fields and args['expected_package']==binding.record['package_hash'],'UPDATE_TARGET')
            need(args['interruption'] in (None,'before-intent','after-intent','during-staging','after-staging'),'UPDATE_INTERRUPTION')
            previous=e.current(binding)
            need(hashlib.sha256(canonical(previous)).hexdigest()==args['expected_enrollment'],'STALE_UPDATE_ENROLLMENT')
            source=safe_path(args['package'],directory=True)
            verified=verify_release(source,args['package_hash'],hold=True)
            try:
                old=binding.verify_package();new=verified.manifest
                need(args['package_hash']!=binding.record['package_hash'],'CHANGED_BUILD_REQUIRED')
                before=snapshot(binding)
                if action=='stage-rollback':
                    need(binding.activation>0,'NO_ROLLBACK_HISTORY')
                    current=read_protected(binding.state/'updates'/f'intent-{binding.activation:06d}.dpapi')
                    need(args['package_hash']==current['previous_package'] and before==current['snapshot'],'ROLLBACK_NEWER_DATA_REFUSED')
                else:need(new['application_version']>old['application_version'],'APPLICATION_VERSION_ORDER')
                directory=binding.state/'updates';index=len(list(directory.glob('intent-*.dpapi')))+1
                need(index<=128,'UPDATE_HISTORY_LIMIT')
                target=binding.install/'releases'/new['build']
                need(target.parent==binding.install/'releases','UPDATE_RELEASE_PATH')
                _observe(binding,'before-intent',args['interruption'])
                intent=dict(binding=binding.seal,sequence=index,data_id=binding.record['data_id'],previous_package=binding.record['package_hash'],
                    package_hash=args['package_hash'],release=str(target),snapshot=before,enrollment_before=args['expected_enrollment'],
                    expires=time.time()+600,owner_intent=body['nonce'],rollback=action=='stage-rollback',application_version=new['application_version'])
                write_protected(directory/f'intent-{index:06d}.dpapi',intent)
                _observe(binding,'after-intent',args['interruption'])
                if target.exists():
                    existing=verify_release(target,args['package_hash']);existing.close()
                else:
                    for item in new['files']:
                        p._copy(source/item['path'],target/item['path'])
                        _observe(binding,'during-staging',args['interruption'])
                    p._copy(source/'manifest.json',target/'manifest.json')
                complete=verify_release(target,args['package_hash']);complete.close()
                _observe(binding,'after-staging',args['interruption'])
                return dict(result='STAGED_STOPPED_REQUIRES_ENROLLMENT_AND_COMMIT',sequence=index,package_hash=args['package_hash'],
                    identity=binding.record['data_id'],snapshot=before)
            finally:verified.close()
        directory,index,intent_path,intent=_pending(binding)
        need(set(args)==({'sequence','interruption'} if action=='commit-update' else {'sequence'}) and args['sequence']==index,'UPDATE_SEQUENCE')
        intent_hash=digest(intent_path)
        if action=='abort-update':
            write_protected(directory/f'abort-{index:06d}.dpapi',dict(binding=binding.seal,intent_hash=intent_hash,owner_intent=body['nonce']))
            return dict(result='ABORTED_STOPPED',sequence=index,files_preserved=True)
        need(time.time()<intent['expires'],'UPDATE_EXPIRED')
        need(snapshot(binding)==intent['snapshot'],'UPDATE_DATA_CHANGED')
        need(hashlib.sha256(canonical(e.current(binding))).hexdigest()==intent['enrollment_before'],'UPDATE_ENROLLMENT_CHANGED')
        target=verify_release(Path(intent['release']),intent['package_hash'],hold=True)
        try:
            enroll=directory/f'enrollment-{index:06d}'
            ready=directory/f'enrolled-{index:06d}.dpapi'
            if action=='enroll-update':
                # Separately signed, one-use enrollment operation. Update authorization alone cannot create this record.
                private_directory(enroll);old=e.current(binding);entries={}
                identity={**e._identity(binding),'package_hash':intent['package_hash']}
                for client,entry in old['entries'].items():
                    entries[client]={**entry,'key':secrets.token_hex(32),'version':entry['version']+1,'identity':identity,
                        'exe_digest':digest(target.release/('python/python.exe' if client=='controller' else 'electron/electron.exe'))}
                write_protected(enroll/'generation-000001.dpapi',dict(binding=binding.seal,version=1,entries=entries,owner_intent=body['nonce']))
                write_protected(ready,dict(binding=binding.seal,intent_hash=intent_hash,owner_intent=body['nonce'],
                    enrollment_hash=digest(enroll/'generation-000001.dpapi')))
                return dict(result='UPDATE_ENROLLMENT_PREPARED',sequence=index,enabled={k:v['enabled'] for k,v in entries.items()})
            need(args['interruption'] in (None,'before-commit','after-commit'),'COMMIT_INTERRUPTION')
            registered=read_protected(ready)
            need(registered['binding']==binding.seal and registered['intent_hash']==intent_hash and
                 registered['enrollment_hash']==digest(enroll/'generation-000001.dpapi'),'UPDATE_ENROLLMENT_REQUIRED')
            _observe(binding,'before-commit',args['interruption'])
            write_protected(directory/f'commit-{index:06d}.dpapi',dict(binding=binding.seal,intent_hash=intent_hash,
                enrollment_hash=registered['enrollment_hash'],enrollment_authority_hash=digest(ready),owner_intent=body['nonce']))
            _observe(binding,'after-commit',args['interruption'])
            return dict(result='ACTIVATED_STOPPED',sequence=index,package_hash=intent['package_hash'],data_id=intent['data_id'],
                automatic_start=False,stop_state_preserved=(binding.state/'stop').exists())
        finally:target.close()
