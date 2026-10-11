"""Actual installed audit logic with synthetic owner-authorized data fixtures."""
from pathlib import Path
import ctypes,hashlib,importlib.util,json,os,subprocess,sys,types,uuid
D=Path(__file__).resolve().parent;S=Path(json.loads((D/'source.json').read_text())['source']);sys.path.insert(0,str(S))
from deployment_test import contract as c,enrollment as e,update_io as u
spec=importlib.util.spec_from_file_location('policy_fixture',S/'tests/deployment_contract/test_contract.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
fixture=f.ContractTests();fixture.setUp();fixture.init();b=fixture.b
incoming=c.private_directory(fixture.parent/'TEST-PACKAGE-incoming');(incoming/'app').mkdir()
file=incoming/'app/inert.py';file.write_text('TEST_VALUE = 73\n')
manifest=dict(mode=c.MODE,version=2,application_version=2,enrollment_format=1,bootstrap_contract=2,build='b'*32,protocol=[2,3],data_schema=1,capabilities={'fixture':True},files=[{'path':'app/inert.py','sha256':c.digest(file),'bytes':file.stat().st_size}])
c.exclusive_json(incoming/'manifest.json',manifest);pin=c.digest(incoming/'manifest.json')
accepted=compile('TEST_ACCEPTED = 19',str(S/'deployment_test/update_io.py'),'exec')
unaccepted=compile(file.read_text(),str(file),'exec')
request=e.signed_request(b,fixture.key,'stage-update',{'package':str(incoming),'package_hash':pin})
target=b.install/'releases'/manifest['build'];rows=[]
def check(name,value):
    rows.append({'case':name,'passed':bool(value)})
    if not value:raise AssertionError(name)
def denied(name,fn,expected=ValueError):
    try:fn()
    except expected as exc:rows.append({'case':name,'passed':True,'denial':str(exc)});return
    raise AssertionError('Not denied: '+name)
u.install(S)
try:
    denied('unauthenticated verification',lambda:u.verification(incoming,pin).__enter__())
    denied('outside capability incoming read',lambda:file.read_bytes())
    with u.authorized(b,request):
        with u.verification(incoming,pin):
            retained_bytes=file.read_bytes()
            check('incoming bytes readable and correct hash',c.digest(file)==manifest['files'][0]['sha256'])
            denied('direct incoming execution',lambda:subprocess.Popen([str(file)]))
            denied('indirect compile even spoofed accepted filename',lambda:compile(file.read_bytes(),str(S/'deployment_test/update_io.py'),'exec'))
            denied('precompiled incoming execution',lambda:exec(unaccepted,{}))
            denied('native incoming load',lambda:ctypes.WinDLL(str(incoming/'untrusted.dll')))
            denied('incoming writes',lambda:file.open('wb'))
            denied('unrelated protected state read',lambda:(b.state/'enrollment/owner.dpapi').read_bytes())
        denied('read capability revoked',lambda:file.read_bytes())
        denied('unrelated location verification',lambda:u.verification(b.release,pin).__enter__())
        # Real protected pending intent; no Core or acceptance is synthesized.
        c.write_protected(b.state/'updates/intent-000001.dpapi',dict(binding=b.seal,sequence=1,data_id=b.record['data_id'],previous_package=b.record['package_hash'],package_hash=pin,release=str(target)))
        handle=c._transport().k.CreateFileW(str(file),0x80000000,1,None,3,0x00200080,None)
        check('source held against replacement',handle!=ctypes.c_void_p(-1).value)
        verified=types.SimpleNamespace(release=incoming,record={'package_hash':pin},manifest=manifest,handles=[handle])
        try:
            copied=list(u.stage_copy(verified,target));check('only manifest entries staged',copied==['app/inert.py','manifest.json'])
        finally:c._transport().k.CloseHandle(handle)
        with u.verification(target,pin):check('staged bytes hash verified',c.digest(target/'app/inert.py')==manifest['files'][0]['sha256'])
        denied('staged file cannot execute directly',lambda:subprocess.Popen([str(target/'app/inert.py')]))
        denied('staged unaccepted read after verification',lambda:(target/'app/inert.py').read_bytes())
        denied('staging cannot overwrite existing release',lambda:list(u.stage_copy(verified,target)))
        denied('staging cannot target rollback release',lambda:list(u.stage_copy(verified,b.release)))
        denied('traversal path rejected',lambda:u.verification(incoming/'..'/incoming.name,pin).__enter__())
    check('authority and phase revoked',u._authority.get() is None and u._phase.get() is None)
    denied('owner authorization replay',lambda:u.authorized(b,request).__enter__(),FileExistsError)
    check('accepted control function executes normally',e.signed_request(b,fixture.key,'inspect',{})['body']['action']=='inspect')
    denied('incoming execution remains denied after capability',lambda:exec(unaccepted,{}))
    escaped={}
    try:exec(compile(retained_bytes,'<string>','exec'),escaped)
    except ValueError:pass
    check('retained incoming bytes cannot execute with synthetic filename after scope',escaped.get('TEST_VALUE')!=73)
    denied('new function from incoming code object',lambda:types.FunctionType(unaccepted,{}))
    denied('native incoming load after capability',lambda:ctypes.WinDLL(str(incoming/'untrusted.dll')))
finally:
    (D/('focused-results-'+uuid.uuid4().hex+'.json')).write_text(json.dumps({'rows':rows,'fixture':str(fixture.parent),'production_changed':False,'core_launched':False},indent=2))
print(json.dumps({'checks':len(rows),'passed':sum(r['passed'] for r in rows)}))
