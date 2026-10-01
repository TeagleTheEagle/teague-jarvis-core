"""Explicit TEST file inventory; no installer, production paths or downloads."""
import json
import hashlib
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import time
import uuid
from .contract import (Binding, MODE, canonical, current_sid, digest, exclusive_json,
                       need, private_directory, safe_path, write_protected, read_protected, read_json, SCHEMA, compatible_manifest)

APP_MODULES = '''actions answer_evidence assistant_capabilities budgeted_repair computer_tools
connection_checks conversation_context development device_registry inspection_jobs inspection_runtime
interface_inspection local_stt maps memory ollama_provider ollama_shadow panel_registry project_budgets
providers recovery repair_sandbox repair_workflow server stage4_deep_review stage4_lifecycle
stage4_ollama_transport stage4_provider_fallback stage4_response_history stage4_runtime stage4_sessions
store update_history verified_status voice_engine wake workspaces'''.split()
APP_FILES = [name+'.py' for name in APP_MODULES] + [
    'stage4_client.cjs','desktop/preload.cjs','static/index.html','intelligence/index.html',
    'intelligence/style.css','intelligence/stage4-renderer.js',
    *['static/'+name+'.css' for name in ('style','gallery','pro','teague')],
    'static/assets/branding/teague/teague-mark.svg','static/assets/branding/teague/command-background.png',
    'tests/lifecycle_stage1/harness.py','tests/lifecycle_stage2/bootstrap.py','tests/lifecycle_stage2/pipe_transport.py',
    *['deployment_test/'+name+'.py' for name in ('contract','enrollment','bootstrap','package','native','upgrade','update_io')]]

ELECTRON_ENTRY = ''''use strict';
// Fixed packaged TEST client entry. Never loads the legacy backend branches.
if(typeof process.send!=='function')throw Error('TRUSTED_TEST_LAUNCHER_REQUIRED');
// Only nonsecret identity/path metadata crosses argv. Establish the existing
// TEST profile/rendering policy synchronously, before Electron readiness.
const args=process.argv.filter(a=>a.startsWith('--stage4-bootstrap='));
if(args.length!==1||args[0].length>16384)throw Error('DEPLOYMENT_BOOTSTRAP');
const cfg=JSON.parse(Buffer.from(args[0].slice('--stage4-bootstrap='.length),'base64url').toString('utf8'));
if(!cfg||Object.keys(cfg).sort().join(',')!=='clientId,deployment'||!cfg.deployment||!['teague','intelligence'].includes(cfg.clientId))throw Error('DEPLOYMENT_CONFIG');
require('./stage4_client.cjs').launchTestClient(cfg.clientId,cfg.deployment);
// launchTestClient retains the private IPC listener and validates/authenticates
// the full configuration before attachment and BrowserWindow creation.
'''

NODE_LAUNCHER = ''''use strict';
const path=require('node:path'),fs=require('node:fs'),{fork}=require('node:child_process');
const release=path.resolve(__dirname,'..');
if(process.argv.length!==3||!/^TEST-STAGE4-[a-f0-9]{32}$/.test(path.basename(process.argv[2])))throw Error('EXPLICIT_TEST_ROOT');
let c=null;
const lines=require('node:readline').createInterface({input:process.stdin});
lines.on('line',line=>{
 const cfg=JSON.parse(line);
 if(!c){
  const fields=['root','app','packageHash','installation','nativePath'];
  if(!cfg||!['teague','intelligence'].includes(cfg.clientId)||!cfg.deployment||
   Object.keys(cfg.deployment).sort().join(',')!==fields.slice().sort().join(',')||
   fields.some(k=>typeof cfg.deployment[k]!=='string'))throw Error('DEPLOYMENT_CONFIG');
  const boot=Buffer.from(JSON.stringify({clientId:cfg.clientId,deployment:cfg.deployment}),'utf8').toString('base64url');
  if(boot.length>16300)throw Error('DEPLOYMENT_BOOTSTRAP');
  c=fork(path.join(__dirname,'deployment-entry.cjs'),['--stage4-test','--stage4-root='+process.argv[2],'--stage4-bootstrap='+boot],{
   execPath:path.join(release,'electron/electron.exe'),stdio:['ignore','pipe','pipe','ipc'],windowsHide:true,
   cwd:release,env:Object.fromEntries(Object.entries(process.env).filter(([k])=>['SYSTEMROOT','WINDIR','TEMP','TMP','USERPROFILE','APPDATA','LOCALAPPDATA','COMSPEC'].includes(k.toUpperCase())))});
  c.stdout.pipe(process.stdout);c.stderr.pipe(process.stderr);
  c.on('exit',code=>process.exit(code===null?1:code));
 }
 c.send(cfg);
});
lines.on('close',()=>{if(c?.connected)c.disconnect();});
'''

def _copy(source, target):
    safe_path(source, directory=False)
    need(not target.exists(),'PACKAGE_OVERWRITE')
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,target)

def build(source, destination, *, node, native, electron, expected_electron_hash, application_version=1):
    source=safe_path(source,directory=True);destination=Path(destination)
    safe_path(destination.parent,directory=True)
    need(not destination.exists() and destination.name.startswith('TEST-PACKAGE-'),'NEW_TEST_PACKAGE_REQUIRED')
    destination.mkdir()
    for relative in APP_FILES:
        _copy(source/relative,destination/'app'/relative)
    (destination/'app/deployment-entry.cjs').write_text(ELECTRON_ENTRY,encoding='utf8')
    (destination/'app/client-launcher.cjs').write_text(NODE_LAUNCHER,encoding='utf8')
    python=Path(sys._base_executable).resolve().parent
    for name in ('python.exe','python3.dll','python312.dll','LICENSE.txt'):
        _copy(python/name,destination/'python'/name)
    for directory in ('Lib','DLLs'):
        for file in sorted((python/directory).rglob('*')):
            if file.is_dir():continue
            relative=file.relative_to(python)
            if any(part in ('site-packages','__pycache__','test','tests','idlelib','tkinter','turtledemo','ensurepip') for part in relative.parts):continue
            if file.suffix in ('.pyc','.pyo'):continue
            _copy(file,destination/'python'/relative)
    (destination/'python/python312._pth').write_text('.\nLib\nDLLs\n',encoding='ascii')
    electron=safe_path(electron,directory=True)
    need(digest(electron/'electron.exe')==expected_electron_hash,'ACCEPTED_ELECTRON_IDENTITY')
    for file in sorted(electron.rglob('*')):
        if file.is_file():_copy(file,destination/'electron'/file.relative_to(electron))
    _copy(Path(node),destination/'node/node.exe')
    _copy(Path(native),destination/'native/peer_identity.node')
    from . import native as nd
    for component in ('python','electron','node','native'):
        for name in nd.CRT:
            need(nd.version(nd.REDIST/name)==nd.CRT_VERSION,'BUILD_CRT_VERSION')
            _copy(nd.REDIST/name,destination/component/name)
    if application_version > 1:nd.mark_test_build(destination/'electron/electron.exe',application_version)
    exclusive_json(destination/'app/deployment-build.json',dict(mode=MODE,application_version=application_version,
        electron_base_sha256=expected_electron_hash,electron_test_resource=application_version>1))
    sources={}
    for file in destination.rglob('*'):
        if file.suffix.lower() not in ('.dll','.exe','.node','.pyd'):continue
        rel=file.relative_to(destination);component=rel.parts[0]
        if file.name in nd.CRT:origin=nd.REDIST/file.name
        elif component=='python':origin=python/Path(*rel.parts[1:])
        elif component=='electron':origin=electron/Path(*rel.parts[1:])
        elif component=='node':origin=Path(node)
        else:origin=Path(native)
        sources[rel.as_posix()]=str(origin)+(' [TEST resource marker added to copy]' if application_version>1 and file.name=='electron.exe' else '')
    nd.build_manifest(destination,sources)
    files=[dict(path=p.relative_to(destination).as_posix(),sha256=digest(p),bytes=p.stat().st_size)
           for p in sorted(destination.rglob('*')) if p.is_file()]
    manifest=dict(mode=MODE,version=2,application_version=application_version,enrollment_format=1,bootstrap_contract=2,
        build=uuid.uuid4().hex,protocol=[2,3],data_schema=1,files=files,
        capabilities={'provider':'offline deterministic only','voice':'silent TEST only',
            'physical_media':False,'repair_execution':False,'third_party_python_packages':[],
            'optional_dependencies_not_in_active_test_surface':['pypdf','python-docx','reportlab','Pillow','openwakeword','playwright','numpy','local speech models','Ollama'],
            'python':'3.12.14 standard library and native DLLs','electron':'44.2.0','node':'explicit bundled binary',
            'assets':'fixed authenticated Stage 4 static route inventory','production_launchers_bundled':False})
    exclusive_json(destination/'manifest.json',manifest)
    return dict(package=str(destination),files=len(files),bytes=sum(x['bytes'] for x in files),sha256=digest(destination/'manifest.json'))

def install(package, parent, owner_key, *, expected_package_hash, intent='NEW_SYNTHETIC_TEST', data_id=None):
    """Prepare files only. Owner-authorized initialization is a separate action."""
    need(intent=='NEW_SYNTHETIC_TEST' and data_id is None,'RESTORE_REQUIRES_EXPLICIT_TRANSFER')
    return _materialize(package,parent,owner_key,expected_package_hash,intent,'TEST-'+uuid.uuid4().hex,'TEST-INSTALL-'+uuid.uuid4().hex)

def _materialize(package,parent,owner_key,expected_package_hash,intent,data_id,installation_id,restored_policy=None):
    package=safe_path(package,directory=True);parent=safe_path(parent,directory=True)
    need(isinstance(owner_key,bytes) and len(owner_key)==32,'SYNTHETIC_OWNER_KEY')
    need(digest(package/'manifest.json')==expected_package_hash,'OWNER_APPROVED_PACKAGE_REQUIRED')
    need('onedrive' not in str(parent).lower() and not str(parent).lower().startswith(str(Path(os.environ.get('LOCALAPPDATA','C:/nonexistent'))/'Teague Industries/JARVIS').lower()),'PRODUCTION_LOCATION_DENIED')
    install_root=private_directory(parent/installation_id)
    private_directory(install_root/'state');private_directory(install_root/'releases')
    private_directory(install_root/'client-state')
    state=private_directory(install_root/'state'/('TEST-STAGE4-'+uuid.uuid4().hex))
    for name in ('enrollment','owner-intents','backups','updates'):private_directory(state/name)
    (state/'TEST_ONLY').write_text('NO PRODUCTION SERVICES',encoding='ascii')
    manifest=read_manifest(package)
    release=install_root/'releases'/manifest['build']
    # Explicit inventory copy; unmanifested files are never copied.
    for entry in manifest['files']:
        relative=entry['path'];file=package/relative
        need(digest(file)==entry['sha256'] and file.stat().st_size==entry['bytes'],'PACKAGE_INPUT_DRIFT')
        _copy(file,release/relative)
    _copy(package/'manifest.json',release/'manifest.json')
    record=dict(schema=SCHEMA,mode=MODE,installation_id=install_root.name,data_id=data_id,
        owner_sid=current_sid(),install_root=str(install_root),state_root=str(state),release_root=str(release),
        package_hash=digest(release/'manifest.json'),protocol=[2,3],data_schema=1)
    write_protected(install_root/'binding.dpapi',record)
    binding=Binding(install_root/'binding.dpapi');binding.verify_package()
    initial=dict(binding=binding.seal,owner_key=owner_key.hex(),intent=intent)
    if restored_policy is not None:initial['restored_policy']=restored_policy
    write_protected(install_root/'initial-owner.dpapi',initial)
    exclusive_json(install_root/'installation.json',dict(action=intent,identity=binding.audit_identity(),initialized=False))
    return binding

def read_manifest(package):
    from .contract import read_json
    value=read_json(package/'manifest.json',4194304)
    compatible_manifest(value)
    need(len(value['files'])<=8000 and len(value['build'])==32,'PACKAGE_LIMIT')
    names=set()
    for item in value['files']:
        p=Path(item['path'])
        need(not p.is_absolute() and '..' not in p.parts and ':' not in str(p) and p.as_posix() not in names,'PACKAGE_ENTRY')
        names.add(p.as_posix());safe_path(package/p,directory=False)
    return value

def logical_database(path):
    safe_path(path,directory=False)
    with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as db:
        need(db.execute('PRAGMA application_id').fetchone()[0]==0x544934 and
             db.execute('PRAGMA user_version').fetchone()[0]==1 and db.execute('PRAGMA quick_check').fetchone()[0]=='ok','RESTORE_DATABASE_IDENTITY')
        result={}
        for table,sql in db.execute("SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
            rows=db.execute('SELECT * FROM "'+table.replace('"','""')+'"').fetchall()
            result[table]={'schema':sql,'rows':sorted(rows,key=repr)}
        return hashlib.sha256(json.dumps(result,sort_keys=True,default=lambda x:x.hex() if isinstance(x,bytes) else str(x)).encode()).hexdigest()

def prepare_maintenance(binding, request):
    """Owner intent + existing locks + stopped state, then immutable fence."""
    import stage4_runtime as r
    from . import enrollment as e
    body=e.authorize(binding,request);action,args=body['action'],body['args']
    need(action in ('prepare-restore','prepare-uninstall'),'MAINTENANCE_ACTION')
    if action=='prepare-restore':
        import re
        need(set(args)=={'target_parent','target_installation'} and re.fullmatch(r'TEST-INSTALL-[a-f0-9]{32}',args['target_installation']),'RESTORE_TARGET')
        safe_path(args['target_parent'],directory=True)
    else:need(args=={},'UNINSTALL_ARGUMENTS')
    with r.exclusion.Lock(binding.state,'supervisor.lock'),r.exclusion.Lock(binding.state,'core.lock'):
        need((binding.state/'stop').exists(),'AUTHORIZED_STOP_REQUIRED')
        need(not (binding.state/'deployment-fence.json').exists(),'MAINTENANCE_ALREADY_PENDING')
        r._start_history(binding.state,binding.record['data_id'])
        data=r.validate_data(binding.state,binding.record['data_id'])
        ticket=dict(binding=binding.seal,action=action,operation=body['nonce'],args=args,expires=time.time()+600,
            data_id=binding.record['data_id'],package_hash=binding.record['package_hash'],database_digest=logical_database(data/'jarvis.sqlite3'))
        if action=='prepare-restore':
            backup=private_directory(binding.state/'backups'/body['nonce'])
            with sqlite3.connect((data/'jarvis.sqlite3').as_uri()+'?mode=ro',uri=True) as source,sqlite3.connect(backup/'jarvis.sqlite3') as target:
                source.backup(target)
            for file in data.rglob('*'):
                if not file.is_file() or file.name in ('jarvis.sqlite3','jarvis.sqlite3-wal','jarvis.sqlite3-shm'):continue
                need(file.name!='.env' and file.suffix!='.dpapi','SECRET_BACKUP_DENIED')
                _copy(file,backup/file.relative_to(data))
            need(logical_database(backup/'jarvis.sqlite3')==ticket['database_digest'],'BACKUP_LOGICAL_MISMATCH')
            files=[dict(path=p.relative_to(backup).as_posix(),sha256=digest(p),bytes=p.stat().st_size) for p in sorted(backup.rglob('*')) if p.is_file()]
            exclusive_json(backup/'backup-manifest.json',dict(data_id=ticket['data_id'],database_digest=ticket['database_digest'],files=files))
            ticket['backup_manifest_sha256']=digest(backup/'backup-manifest.json')
            ticket['policy']={k:{f:v[f] for f in ('enabled','version','scopes')} for k,v in e.current(binding)['entries'].items()}
        write_protected(binding.state/(body['nonce']+'.maintenance.dpapi'),ticket)
        exclusive_json(binding.state/'deployment-fence.json',dict(binding=binding.seal,action=action,operation=body['nonce']))
    return {'result':'MAINTENANCE_PREPARED','operation':body['nonce'],'action':action,'data_id':ticket['data_id'],'database_digest':ticket['database_digest']}

def _ticket(binding,request,action):
    from . import enrollment as e
    body=e.authorize(binding,request)
    need(body['action']==action and set(body['args'])=={'operation'},'MAINTENANCE_AUTHORITY')
    operation=body['args']['operation']
    need(type(operation)is str and len(operation)==32 and all(x in '0123456789abcdef' for x in operation),'MAINTENANCE_OPERATION')
    ticket=read_protected(binding.state/(operation+'.maintenance.dpapi'))
    need(ticket['binding']==binding.seal and ticket['package_hash']==binding.record['package_hash'] and
         ticket['data_id']==binding.record['data_id'] and time.time()<ticket['expires'],'MAINTENANCE_BINDING_OR_EXPIRY')
    need(read_json(binding.state/'deployment-fence.json')==dict(binding=binding.seal,action=ticket['action'],operation=operation),'MAINTENANCE_FENCE')
    return ticket,body

def finish_restore(binding,request,owner_key):
    ticket,body=_ticket(binding,request,'finish-restore')
    need(ticket['action']=='prepare-restore','RESTORE_INTENT')
    backup=binding.state/'backups'/ticket['operation']
    need(digest(backup/'backup-manifest.json')==ticket['backup_manifest_sha256'],'RESTORE_MANIFEST')
    manifest=read_json(backup/'backup-manifest.json')
    need(manifest['data_id']==binding.record['data_id'] and logical_database(backup/'jarvis.sqlite3')==ticket['database_digest'],'RESTORE_DATA')
    for entry in manifest['files']:
        p=safe_path(backup/entry['path'],directory=False)
        need(p.is_relative_to(backup) and digest(p)==entry['sha256'] and p.stat().st_size==entry['bytes'],'RESTORE_ARTIFACT')
    exclusive_json(binding.state/'restore-consumed.json',dict(operation=ticket['operation'],owner_intent=body['nonce']))
    restored=_materialize(binding.release,Path(ticket['args']['target_parent']),owner_key,ticket['package_hash'],
        'RESTORE_SYNTHETIC_TEST',ticket['data_id'],ticket['args']['target_installation'],ticket['policy'])
    data=private_directory(restored.state/'STAGE4_TEST-data')
    for entry in manifest['files']:_copy(backup/entry['path'],data/entry['path'])
    need(logical_database(data/'jarvis.sqlite3')==ticket['database_digest'],'RESTORE_POST_COPY')
    exclusive_json(restored.state/'restored.json',dict(source_installation=binding.record['installation_id'],data_id=ticket['data_id'],
        source_binding=binding.seal,backup_manifest_sha256=ticket['backup_manifest_sha256'],database_digest=ticket['database_digest']))
    return restored

def finish_uninstall(binding,request):
    ticket,body=_ticket(binding,request,'finish-uninstall')
    need(ticket['action']=='prepare-uninstall','UNINSTALL_INTENT')
    binding.verify_package()
    need(logical_database(binding.state/'STAGE4_TEST-data/jarvis.sqlite3')==ticket['database_digest'],'UNINSTALL_DATA_CHANGED')
    exclusive_json(binding.state/'uninstall-consumed.json',dict(operation=ticket['operation'],owner_intent=body['nonce']))
    targets=[]
    for entry in binding.manifest['files']:
        target=safe_path(binding.release/entry['path'],directory=False)
        need(target.is_relative_to(binding.release) and digest(target)==entry['sha256'],'UNINSTALL_TARGET')
        targets.append(target)
    # Only named, verified application files. No recursive directory deletion,
    # no data/secrets/identity removal, no process termination, no ACL changes.
    for target in targets:target.unlink()
    (binding.release/'manifest.json').unlink()
    need(logical_database(binding.state/'STAGE4_TEST-data/jarvis.sqlite3')==ticket['database_digest'],'UNINSTALL_DATA_PRESERVATION')
    return dict(result='TEST_APPLICATION_FILES_REMOVED',files=len(targets)+1,data_preserved=True,identity_preserved=True,destructive_data_authority=False)

def reinstall(binding,source_package,request):
    ticket,body=_ticket(binding,request,'reinstall')
    need(ticket['action']=='prepare-uninstall' and (binding.state/'uninstall-consumed.json').exists(),'REINSTALL_STATE')
    need(digest(source_package/'manifest.json')==binding.record['package_hash'],'SAME_APPROVED_PACKAGE_REQUIRED')
    manifest=read_manifest(source_package)
    need(not any(p.is_file() for p in binding.release.rglob('*')),'REINSTALL_PARTIAL_FILES')
    for entry in manifest['files']:
        need(digest(source_package/entry['path'])==entry['sha256'],'REINSTALL_PACKAGE')
        _copy(source_package/entry['path'],binding.release/entry['path'])
    _copy(source_package/'manifest.json',binding.release/'manifest.json')
    binding.verify_package()
    exclusive_json(binding.state/'reinstalled.json',dict(operation=ticket['operation'],owner_intent=body['nonce'],package_hash=binding.record['package_hash']))
    write_protected(binding.state/'reinstall-ready.dpapi',dict(binding=binding.seal,operation=ticket['operation'],
        owner_intent=body['nonce'],package_hash=binding.record['package_hash'],revision=2))
    # The maintenance fence is durably completed, not deleted. The existing
    # stop latch still requires a fresh authenticated start transaction.
    return dict(result='SAME_PACKAGE_REINSTALLED_STOPPED',data_id=binding.record['data_id'],identity_preserved=True,activation_authorized=False)
