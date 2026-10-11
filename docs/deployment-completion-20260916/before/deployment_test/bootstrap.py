"""Fixed-role, TEST-only packaged entry. No generic shell or Python command API."""
import json
import os
from pathlib import Path
import sys
import uuid

APP = Path(__file__).resolve().parents[1]
RELEASE = APP.parent
sys.dont_write_bytecode = True
sys.path.insert(0,str(APP))
from deployment_test.contract import Binding, need, digest, exclusive_json, safe_path
from deployment_test import enrollment

def provenance(binding, identity=None):
    origins={name:str(Path(m.__file__).resolve()) for name,m in list(sys.modules.items())
             if getattr(m,'__file__',None) and Path(m.__file__).is_absolute()}
    need(all(Path(p).is_relative_to(RELEASE) for p in origins.values()),'EXTERNAL_APPLICATION_IMPORT')
    need(all(Path(p).is_relative_to(RELEASE) for p in sys.path if p),'EXTERNAL_IMPORT_PATH')
    exclusive_json(binding.state/('deployment-runtime-'+str(os.getpid())+'-'+uuid.uuid4().hex+'.json'),
        dict(mode='STAGE4_TEST_DEPLOYMENT',pid=os.getpid(),identity=identity,executable=sys.executable,
             executable_sha256=digest(sys.executable),origins=origins,sys_path=sys.path,
             cwd=os.getcwd(),environment_names=sorted(os.environ),package_hash=binding.record['package_hash'],
             source_tree_execution=False,live_providers=False))

def main():
    need(len(sys.argv)==3 and sys.argv[1] in ('--core','--coordinator','--control'),'FIXED_BOOTSTRAP_ROLE')
    role=sys.argv[1];binding=Binding(sys.argv[2],maintenance=role=='--control')
    need(binding.app==APP and Path(sys.executable).resolve()==RELEASE/'python/python.exe','PACKAGE_RUNTIME_IDENTITY')
    binding.verify_package(hold=True)
    # Restrict this process's code reads to the explicit release. System DLLs
    # remain OS dependencies; data access is further restricted by Stage 4.
    def no_external_code(event,args):
        if event=='open' and isinstance(args[0],str):
            target=Path(args[0]).resolve()
            if target.suffix.lower() in ('.py','.pyc','.pyd'):
                need(target.is_relative_to(RELEASE),'SOURCE_TREE_EXECUTION_DENIED')
    sys.addaudithook(no_external_code)
    import stage4_runtime as r
    r.configure_deployment(binding)
    raw=sys.stdin.readline(262145)
    need(0<len(raw)<=262144,'BOOTSTRAP_INPUT_LIMIT')
    request=json.loads(raw)
    try:
        if role=='--control':
            action=request.get('body',{}).get('action')
            if action=='initialize':
                initial=enrollment.read_protected(binding.install/'initial-owner.dpapi')
                initialize_data=(lambda:r.validate_data(binding.state,binding.record['data_id'])) if initial['intent']=='RESTORE_SYNTHETIC_TEST' else (lambda:r.provision(binding.state,binding.record['data_id']))
                result=enrollment.initialize(binding,request,initialize_data)
            elif action in ('revoke','replace'):
                result=enrollment.mutate(binding,request)
            elif action=='client-configuration':
                # Identity comes only from the existing ready record, then live peer validation.
                ready=r.exclusion.read(binding.state/'stage4-ready.json')
                need(type(ready)is dict,'CORE_UNAVAILABLE')
                result=enrollment.client_configuration(binding,request,ready['identity'],request['body']['args']['client'])
            elif action=='configuration':
                body=enrollment.authorize(binding,request)
                need(body['args']=={},'CONFIGURATION_ARGUMENTS')
                result=enrollment.core_configuration(binding)
            elif action=='inspect':
                body=enrollment.authorize(binding,request);need(body['args']=={},'INSPECT_ARGUMENTS')
                result=dict(identity=binding.audit_identity(),enrollment_version=enrollment.current(binding)['version'],
                            clients={k:{f:v[f] for f in ('client','enabled','version','exe_digest','scopes','identity')} for k,v in enrollment.current(binding)['entries'].items()})
            elif action in ('prepare-restore','prepare-uninstall'):
                from deployment_test.package import prepare_maintenance
                result=prepare_maintenance(binding,request)
            else:
                raise ValueError('CONTROL_ACTION_DENIED')
            provenance(binding)
            # Private owner pipe, never an evidence log; contains keys only for
            # the two explicitly authorized configuration actions above.
            sys.stdout.write(json.dumps(result)+'\n');sys.stdout.flush()
        elif role=='--core':
            expected=enrollment.core_configuration(binding)
            need({k:v for k,v in request.items() if k not in ('start_transaction','launch_nonce')}==expected,'PERSISTENT_CORE_CONFIGURATION')
            need('start_transaction' in request and 'launch_nonce' in request,'EXPLICIT_START_TRANSACTION_REQUIRED')
            def observed(stage,identity):
                if stage=='identity':provenance(binding,identity)
            r.serve(binding.state,request,start_observer=observed)
        else:
            authorization=request.pop('_deployment_authorization',None)
            body=enrollment.authorize(binding,authorization)
            need(body['action']=='coordinator' and body['args']=={'configuration_sha256':r._start_digest(request)},'OWNER_COORDINATOR_INTENT')
            diagnostic=request.pop('_test_interruption',None)
            need(diagnostic in (None,'before-intent','intent','spawned'),'TEST_INTERRUPTION_BOUNDARY')
            need(request['owner']=='controller' and request['core']==enrollment.core_configuration(binding),'PERSISTENT_COORDINATOR_CONFIGURATION')
            need(request['owner_peer']['exe_digest']==digest(RELEASE/'python/python.exe'),'OWNER_EXECUTABLE')
            # Existing coordinator still binds the live PID + creation time and
            # authenticates the controller before any start/restart transaction.
            provenance(binding)
            def observed(stage):
                if diagnostic==stage:
                    # Explicitly owner-authorized disposable TEST self-exit,
                    # reusing the accepted coordinator observer boundaries.
                    # No process ID, command or executable can be supplied.
                    exclusive_json(binding.state/('bootstrap-interrupted-'+uuid.uuid4().hex+'.json'),
                        dict(stage=stage,identity=r.transport.identity(os.getpid()),
                             installation=binding.record['installation_id'],data_id=binding.record['data_id']))
                    os._exit(93)
            r.serve_test_coordinator(binding.state,request,observer=observed if diagnostic else None)
    finally:
        binding.close()

if __name__=='__main__':
    main()
