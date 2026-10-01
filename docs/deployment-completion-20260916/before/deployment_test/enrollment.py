"""Bounded TEST owner enrollment; existing Core authenticates every client."""
import hashlib
import hmac
import json
import secrets
import time
import uuid
from .contract import (Binding, canonical, digest, need, read_json, read_protected,
                       exclusive_json, write_protected, safe_path, _transport)

ORDINARY = ['attach','media','read','request']
MANAGEMENT = sorted(ORDINARY + ['emergency','lifecycle'])

def signed_request(binding, owner_key, action, args):
    """Called only by the explicit owner TEST driver; no key in evidence."""
    body = dict(binding=binding.seal, installation=binding.record['installation_id'],
                action=action, args=args, nonce=uuid.uuid4().hex, expires=time.time()+30)
    return {'body':body, 'proof':hmac.new(owner_key, canonical(body), 'sha256').hexdigest()}

def _identity(binding):
    return {k:binding.record[k] for k in ('installation_id','data_id','owner_sid','package_hash','protocol')}

def private(binding):
    result = read_protected(binding.state/'enrollment/owner.dpapi')
    need(result['binding'] == binding.seal and result['identity'] == _identity(binding), 'ENROLLMENT_INSTALLATION')
    return result

def authorize(binding, request, *, initial=False):
    need(type(request) is dict and set(request)=={'body','proof'}, 'OWNER_PROOF_REQUIRED')
    body = request['body']
    need(type(body) is dict and set(body)=={'binding','installation','action','args','nonce','expires'}, 'OWNER_REQUEST')
    need(body['binding']==binding.seal and body['installation']==binding.record['installation_id'], 'OWNER_TARGET')
    need(type(body['expires']) in (float,int) and time.time()<body['expires']<=time.time()+31, 'OWNER_EXPIRY')
    need(type(body['nonce']) is str and len(body['nonce'])==32 and all(x in '0123456789abcdef' for x in body['nonce']), 'OWNER_NONCE')
    record = read_protected(binding.install/'initial-owner.dpapi') if initial else private(binding)
    need(record['binding']==binding.seal, 'OWNER_BINDING')
    expected = hmac.new(bytes.fromhex(record['owner_key']), canonical(body), 'sha256').hexdigest()
    need(type(request['proof']) is str and hmac.compare_digest(request['proof'],expected), 'OWNER_PROOF')
    receipt = binding.state/'owner-intents'/(body['nonce']+'.json')
    exclusive_json(receipt, {'body':body, 'authorized':True, 'proof_digest':hashlib.sha256(request['proof'].encode()).hexdigest()})
    return body

def initialize(binding, request, provision):
    body = authorize(binding,request,initial=True)
    need(body['action']=='initialize' and body['args']=={'intent':read_protected(binding.install/'initial-owner.dpapi')['intent']}, 'EXPLICIT_INITIALIZATION')
    need(not (binding.state/'enrollment/owner.dpapi').exists(), 'INITIALIZATION_ALREADY_COMMITTED')
    initial = read_protected(binding.install/'initial-owner.dpapi')
    provision()
    owner = dict(binding=binding.seal, identity=_identity(binding), owner_key=initial['owner_key'],
                 server_key=secrets.token_hex(32), endpoint='TEAGUE-TEST-'+uuid.uuid4().hex)
    write_protected(binding.state/'enrollment/owner.dpapi', owner)
    entries = {}
    for client in ('teague','intelligence','controller'):
        entries[client] = dict(client=client, enabled=True, version=1, key=secrets.token_hex(32),
            exe_digest=digest(binding.release/('python/python.exe' if client=='controller' else 'electron/electron.exe')),
            scopes=MANAGEMENT if client=='controller' else ORDINARY, protocol=[2,3], identity=_identity(binding))
        if 'restored_policy' in initial:
            old=initial['restored_policy'][client]
            need(old['scopes']==entries[client]['scopes'],'RESTORE_SCOPE')
            entries[client]['version']=old['version']+1
            entries[client]['enabled']=old['enabled']
    write_protected(binding.state/'enrollment/generation-000001.dpapi',dict(version=1,entries=entries,binding=binding.seal,owner_intent=body['nonce']))
    exclusive_json(binding.state/'initialized.json',dict(intent=initial['intent'], data_id=binding.record['data_id'],owner_intent=body['nonce']))
    return {'result':'INITIALIZED','intent':initial['intent'],'identity':_identity(binding)}

def current(binding):
    private(binding)
    files = sorted((binding.state/'enrollment').glob('generation-*.dpapi'))
    need(1<=len(files)<=512,'ENROLLMENT_HISTORY')
    need([p.name for p in files]==[f'generation-{i:06d}.dpapi' for i in range(1,len(files)+1)],'ENROLLMENT_GAP')
    record = read_protected(files[-1])
    need(record['binding']==binding.seal and record['version']==len(files), 'ENROLLMENT_GENERATION')
    need(set(record['entries'])=={'teague','intelligence','controller'},'CLIENT_ALLOWLIST')
    for name, entry in record['entries'].items():
        need(entry['client']==name and entry['identity']==_identity(binding) and entry['protocol']==[2,3] and
             entry['scopes']==(MANAGEMENT if name=='controller' else ORDINARY), 'ENROLLMENT_POLICY')
        need(type(entry['enabled']) is bool and type(entry['version']) is int and entry['version']>=1 and
             len(bytes.fromhex(entry['key']))==32 and len(entry['exe_digest'])==64,'ENROLLMENT_ENTRY')
    return record

def core_configuration(binding):
    owner=private(binding); record=current(binding)
    revision=read_protected(binding.state/'reinstall-ready.dpapi')['revision'] if (binding.state/'reinstall-ready.dpapi').exists() else 1
    return dict(data_id=binding.record['data_id'],server_key=owner['server_key'],endpoint=owner['endpoint'],
                enrollments={name:{k:entry[k] for k in ('enabled','key','exe_digest','protocol','scopes')} for name,entry in record['entries'].items()},
                deep_review_fixture=True, text_provider_scenario='quota',deployment_revision=revision)

def mutate(binding, request):
    """Executed in the installed trusted owner process. No renderer route."""
    import stage4_runtime as r
    body=authorize(binding,request)
    # The control role can inspect pending maintenance. Enrollment mutation
    # additionally requires the normal operational binding; a completed,
    # authenticated reinstall is operational, an unfinished fence is not.
    Binding(binding.descriptor).check_root(binding.state)
    action,args=body['action'],body['args']
    need(action in ('revoke','replace') and type(args) is dict and set(args)=={'client','expected_version'},'ENROLLMENT_ACTION')
    need(args['client'] in ('teague','intelligence'),'ORDINARY_CLIENT_ONLY')
    with r.exclusion.Lock(binding.state,'supervisor.lock'):
        previous=current(binding); entry=previous['entries'][args['client']]
        need(entry['version']==args['expected_version'],'STALE_ENROLLMENT_UPDATE')
        guard = r.exclusion.Lock(binding.state,'core.lock') if action=='replace' else None
        try:
            if action=='replace':
                need((binding.state/'stop').exists(),'CONTROLLED_STOP_REQUIRED')
                entry.update(key=secrets.token_hex(32), enabled=True,
                             exe_digest=digest(binding.release/'electron/electron.exe'))
            else:
                need(entry['enabled'],'ALREADY_REVOKED');entry['enabled']=False
            entry['version']+=1; previous['version']+=1; previous['owner_intent']=body['nonce']
            write_protected(binding.state/'enrollment'/f"generation-{previous['version']:06d}.dpapi",previous)
        finally:
            if guard:guard.close()
    return {'result':'REPLACED' if action=='replace' else 'REVOCATION_RECORDED',
            'generation':previous['version'],'client':args['client'],'version':entry['version'],
            'live_cleanup':'Core applies through existing revoke_client before further authenticated operations'}

def refresh_revocations(binding, authority):
    record=current(binding)
    for client, entry in record['entries'].items():
        old=authority.enrollments[client]
        if not entry['enabled']:
            # Revocation is monotonic for a live epoch. Replacement requires stop.
            if old['enabled']:
                old['enabled']=False
                authority.context.owners.revoke_client(client)
        else:
            need(old['key'].hex()==entry['key'] and old['exe_digest']==entry['exe_digest'], 'LIVE_ENROLLMENT_CHANGE_DENIED')

def client_configuration(binding, owner_request, identity, client):
    body=authorize(binding,owner_request)
    need(body['action']=='client-configuration' and body['args']=={'client':client},'CLIENT_CONFIG_AUTHORITY')
    need(client in ('teague','intelligence'),'ORDINARY_CLIENT_ONLY')
    owner=private(binding); enrollment=current(binding)['entries'][client]
    need(enrollment['enabled'],'CLIENT_REVOKED')
    need(identity['data_id']==binding.record['data_id'] and identity['installation_id']==binding.record['installation_id'] and
         identity['runtime_build']==binding.record['package_hash'],'CORE_INSTALLATION_IDENTITY')
    peer={k:identity[k] for k in ('pid','created','exe_digest')}
    need(_transport().identity(peer['pid'])==peer,'LIVE_CORE_IDENTITY')
    return dict(clientId=client,endpoint=owner['endpoint'],expectedIdentity={**identity,'created':str(identity['created'])},
                pinnedPeer={**peer,'created':str(peer['created'])},serverKey=owner['server_key'],clientKey=enrollment['key'],driver=True,
                deployment={'root':str(binding.state),'app':str(binding.app),'packageHash':binding.record['package_hash'],
                            'installation':binding.record['installation_id'],'nativePath':str(binding.release/'native/peer_identity.node')})
