"""Stage 2 isolated Windows evidence; secrets are never written to reports."""
import concurrent.futures
import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import secrets
import struct
import subprocess
import sys
import time
import unittest

import uuid
sys.path.insert(0,str(Path(__file__).absolute().parent))
sys.path.insert(0,str(Path(__file__).absolute().parent.parent/'lifecycle_stage1'))
import harness as stage1
import pipe_transport as pt
import bootstrap as b

def until(predicate,seconds=5):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if predicate():return
        time.sleep(.02)
    raise AssertionError('Fixture readiness timeout')

def child_attach(arguments,control):
    try:
        r=b.client(*arguments)
        control.send({'result':r['result'],'identity':r.get('identity'),'tool_authorized':r.get('tool_authorized')})
    except Exception as exc:control.send({'error':type(exc).__name__})
    finally:control.close()

def crash_client(arguments):b.client(*arguments,drop='crash')

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.run_folder=stage1.BASE/('TEST-STAGE2-'+uuid.uuid4().hex);cls.run_folder.mkdir(parents=True)
    def setUp(self):
        self.root=self.run_folder/('TEST-'+uuid.uuid4().hex);self.root.mkdir()
        (self.root/'TEST_ONLY').write_text('NO PRODUCTION SERVICES')
        self.ctx=mp.get_context('spawn');self.servers=[];self.cores=[]
        self.addCleanup(self.cleanup)
        self.start_core()
        exe=pt.identity(os.getpid())['exe_digest']
        self.enrolled={name:{'enabled':True,'key':secrets.token_bytes(32),'exe_digest':exe,'protocol':[2,3],
            'scopes':['attach','status','test']+extra} for name,extra in [('teague',[]),('intelligence',[]),('controller',['lifecycle']),('media',['media'])]}
        self.key=secrets.token_bytes(32);self.name='TEAGUE-TEST-'+uuid.uuid4().hex
        self.start_server()
    def start_core(self):
        old=stage1.read(self.root/'core.json')
        p=stage1.spawn(self.root,'core');self.cores.append(p)
        until(lambda:(v:=stage1.read(self.root/'core.json')) and v!=old)
        info=stage1.read(self.root/'core.json')
        self.identity={**pt.identity(info['pid']),'mode':'TEST','namespace':self.root.name,
            'installation_id':'TEST-installation','data_id':'TEST-data-'+self.root.name,
            'core_instance_id':info['epoch'],'startup_epoch':info['epoch'],'runtime_build':'TEST-fixture-1',
            'runtime_digest':hashlib.sha256(Path(stage1.__file__).read_bytes()).hexdigest(),'protocol':[2,3],'schema':1}
    def start_server(self,behavior='normal',ttl=1):
        parent,child=self.ctx.Pipe(duplex=False);stop=self.ctx.Event()
        p=self.ctx.Process(target=b.server,args=(self.name,self.identity,self.enrolled,str(self.root),self.key,child,stop,ttl,behavior))
        p.start();child.close();self.servers.append((p,stop));self.assertTrue(parent.poll(8))
        ready=parent.recv();parent.close();self.assertNotIn('failed',ready)
        self.peer=ready['peer'];self.acl=ready['acl']
    def restart_bootstrap(self,behavior='normal',ttl=1):
        p,stop=self.servers[-1];stop.set();p.join(3)
        if p.is_alive():p.terminate();p.join(3)
        self.start_server(behavior,ttl)
    def args(self,client='teague',request=None,expected=None,key=None,protocol=None):
        entry=self.enrolled.get(client,self.enrolled['teague'])
        return (self.name,self.peer,expected or self.identity,key or self.key,client,entry['key'],
                request or {'op':'attach','token':None,'args':{'scopes':['attach','status','test']}},protocol)
    def call(self,client='teague',request=None,**kwargs):return b.client(*self.args(client,request,**kwargs))
    def attach(self,client='teague',scopes=None):
        result=self.call(client,{'op':'attach','token':None,'args':{'scopes':scopes or ['attach','status','test']}})
        self.assertTrue(result.get('result')=='ATTACHED');self.assertFalse(result['tool_authorized']);return result['token']
    def op(self,token,op='status',client='teague',args=None):return self.call(client,{'op':op,'token':token,'args':args or {}})
    def denied(self,fn):
        try:r=fn()
        except (b.Denied,OSError,ValueError):return
        self.assertTrue(r.get('result')=='DENIED')
    def cleanup(self):
        for p,stop in self.servers:
            stop.set();p.join(2)
            if p.is_alive():p.terminate();p.join(3)
        (self.root/'stop').touch()
        for p in self.cores:
            try:p.wait(3)
            except Exception:p.terminate();p.wait(3)
    def test_01_approved_and_unapproved(self):
        token=self.attach();self.assertTrue(self.op(token)['result']=='ALLOWED')
        self.denied(lambda:self.call('unknown'))
    def test_02_identity_matrix(self):
        for key in ('installation_id','data_id','core_instance_id','startup_epoch','runtime_build','runtime_digest','namespace'):
            with self.subTest(field=key):self.denied(lambda:self.call(expected={**self.identity,key:'WRONG'}))
        for key in ('pid','created','schema'):
            with self.subTest(field=key):self.denied(lambda:self.call(expected={**self.identity,key:0}))
    def test_03_modes(self):
        self.denied(lambda:self.call(expected={**self.identity,'mode':'PRODUCTION'}))
        with self.assertRaises(b.Denied):b.validate_identity({**self.identity,'mode':'PRODUCTION'},self.identity)
    def test_04_scopes(self):
        token=self.attach()
        for op in ('media','start','stop','restart','maintenance','revoke_client'):
            with self.subTest(op=op):self.denied(lambda:self.op(token,op))
        admin=self.attach('controller',['attach','test','status','lifecycle'])
        for op in ('start','stop','restart','maintenance'):
            r=self.op(admin,op,'controller');self.assertFalse(r['lifecycle_executed']);self.assertFalse(r['tool_authorized'])
        media=self.attach('media',['attach','test','media']);self.assertTrue(self.op(media,'media','media')['result']=='ALLOWED')
    def test_05_expiry(self):
        token=self.attach();time.sleep(1.1);self.denied(lambda:self.op(token));self.denied(lambda:self.op(token,'renew'))
    def test_06_renew_revoke(self):
        token=self.attach();r=self.op(token,'renew');new=r['token']
        self.denied(lambda:self.op(token));self.assertTrue(self.op(new)['result']=='ALLOWED')
        self.assertTrue(self.op(new,'revoke')['result']=='REVOKED');self.denied(lambda:self.op(new))
    def test_07_wrong_client_random_malformed(self):
        token=self.attach();self.denied(lambda:self.op(token,client='intelligence'))
        for value in ('',None,5,'short','f'*64):
            with self.subTest(type=type(value).__name__):self.denied(lambda:self.op(value))
    def test_08_enrollment_revocation(self):
        token=self.attach();admin=self.attach('controller',['attach','status','test','lifecycle'])
        self.op(admin,'revoke_client','controller',{'client':'teague'})
        self.denied(lambda:self.op(token));self.denied(lambda:self.op(token,'renew'));self.denied(lambda:self.call())
    def test_09_core_and_bootstrap_restart(self):
        token=self.attach();old=self.identity.copy()
        p=self.cores[-1];p.terminate();p.wait(3)
        self.denied(lambda:self.op(token))
        self.start_core();self.assertNotEqual(old['startup_epoch'],self.identity['startup_epoch'])
        self.restart_bootstrap();self.denied(lambda:self.op(token));self.attach()
    def test_10_bootstrap_restart_invalidates(self):
        token=self.attach();self.restart_bootstrap();self.denied(lambda:self.op(token));self.attach()
    def test_11_cross_namespace_token(self):
        token=self.attach();self.identity={**self.identity,'namespace':'TEST-other','data_id':'TEST-other'}
        self.restart_bootstrap();self.denied(lambda:self.op(token))
    def test_12_protocol_ranges(self):
        self.assertEqual(b.negotiate([2,3],[2,3]),3)
        for pair in ([1,1],[4,4],[3,2],[True,3],[],['2',3],[2,4]):
            with self.subTest(range=pair):
                with self.assertRaises(b.Denied):b.negotiate(pair,[2,3])
        with self.assertRaises(b.Denied):b.negotiate([2,2],[3,3])
        self.denied(lambda:self.call(protocol=[2,2]))
    def test_13_fake_proof_replay_downgrade(self):
        for behavior in ('fake-proof','replay','downgrade','fake-health'):
            with self.subTest(behavior=behavior):
                self.restart_bootstrap(behavior);self.denied(lambda:self.call())
    def test_14_wrong_process_and_key(self):
        self.denied(lambda:b.client(self.name,{**self.peer,'created':0},self.identity,self.key,'teague',self.enrolled['teague']['key'],{'op':'status','token':None,'args':{}}))
        self.denied(lambda:self.call(key=secrets.token_bytes(32)))
        args=list(self.args());args[5]=secrets.token_bytes(32);self.denied(lambda:b.client(*args))
    def test_15_origin_redirects(self):
        expected='http://127.0.0.1:12345'
        self.assertTrue(b.origin_allowed(expected+'/api/status',expected))
        for url in ('http://127.0.0.1:123456','http://127.0.0.1.evil:12345','http://user@127.0.0.1:12345',
                    'http://127.0.0.1:12346','https://127.0.0.1:12345','http://localhost:12345','http://127.0.0.1:12345@evil',
                    'http://127.0.0.1:12345\\@evil','http://evil/redirect'):
            with self.subTest(url=url):self.assertFalse(b.origin_allowed(url,expected))
    def test_16_descriptor_hints(self):
        expected={'endpoint':self.name,'identity':self.identity}
        stage1.write(self.root/'descriptor.json',expected)
        self.assertTrue(b.descriptor_valid(stage1.read(self.root/'descriptor.json'),expected))
        for value in ({},None,{'endpoint':self.name,'identity':{}},{**expected,'token':'FORBIDDEN'},
                      {'endpoint':'TEAGUE-TEST-'+uuid.uuid4().hex,'identity':self.identity}):
            self.assertFalse(b.descriptor_valid(value,expected))
        (self.root/'descriptor.json').write_text('{');self.assertFalse(b.descriptor_valid(stage1.read(self.root/'descriptor.json'),expected))
        # Copying an accurate public hint does not supply a server key.
        self.denied(lambda:self.call(key=secrets.token_bytes(32)))
    def test_17_bad_wire_messages(self):
        for wire in (struct.pack('!I',0),struct.pack('!I',8193),struct.pack('!I',1)+b'{',
                     struct.pack('!I',1)+b'\xff',struct.pack('!I',20)+b'{}',b'\0\0'):
            with self.subTest(length=len(wire)):
                pipe=pt.connect(self.name)
                try:pipe.raw(wire)
                finally:pipe.close()
                self.attach()
    def test_18_unknown_operations_fields(self):
        token=self.attach()
        for request in ({'op':'shell','token':token,'args':{}},{'op':'status','token':token,'args':{},'extra':1},
                        {'op':'status','token':token,'args':{'path':'anything'}},
                        {'op':'attach','token':None,'args':{'scopes':['attach','test','lifecycle']}}):
            self.denied(lambda:self.call(request=request))
    def test_19_server_crash_handshake(self):
        self.restart_bootstrap('crash-handshake');self.denied(lambda:self.call())
        self.servers[-1][0].join(3);self.assertEqual(self.servers[-1][0].exitcode,81)
    def test_20_client_drop_handshake(self):
        self.assertTrue(b.client(*self.args(),drop=True)['result']=='DROPPED_BEFORE_CLIENT_PROOF')
        self.attach()
    def test_21_parallel_clients(self):
        for _ in range(3):
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                replies=list(pool.map(lambda _:self.call(),range(4)))
            self.assertTrue(all(r.get('identity')==self.identity for r in replies))
    def test_22_process_clients(self):
        for _ in range(2):
            workers=[]
            for name in ('teague','intelligence'):
                rx,tx=self.ctx.Pipe(False);p=self.ctx.Process(target=child_attach,args=(self.args(name),tx));p.start();tx.close();workers.append((p,rx))
            for p,rx in workers:
                self.assertTrue(rx.poll(8));r=rx.recv();rx.close();p.join(4)
                self.assertTrue(r.get('identity')==self.identity)
    def test_23_supervisor_composition(self):
        for _ in range(3):
            (self.root/'go').touch()
            ps=[stage1.spawn(self.root,'coordinator') for _ in range(4)]
            for p in ps:p.wait(6)
            self.attach();self.assertTrue(stage1.read(self.root/'core.json')['epoch']==self.identity['startup_epoch'])
            self.assertFalse(any(stage1.read(p).get('kind')=='spawned' for p in self.root.glob('*-spawned.json')))
    def test_24_stop_latch(self):
        token=self.attach();(self.root/'stop').touch()
        self.denied(lambda:self.call());self.denied(lambda:self.op(token));self.assertTrue((self.root/'stop').exists())
    def test_25_acl_collision_denial(self):
        self.assertIn(pt.current_sid(),self.acl)
        self.assertNotIn(';;;WD',self.acl);self.assertNotIn(';;;AN',self.acl)
        with self.assertRaises(OSError):pt.listen(self.name)
        name='TEAGUE-TEST-'+uuid.uuid4().hex;pipe=pt.listen(name,deny=True)
        try:
            with self.assertRaises(OSError) as cm:pt.connect(name)
            self.assertEqual(cm.exception.errno,5)
        finally:pipe.close()
    def test_26_remote_names_refused(self):
        for name in ('\\\\remote\\pipe\\test','production','TEAGUE-TEST-foo'):
            with self.assertRaises(b.Denied):pt.connect(name)
    @unittest.skip('Other-user/cross-session and actual remote-host denial not exercised')
    def test_27_other_user_cross_session(self):pass
    def test_28_no_secret_descriptors(self):
        token=self.attach();stage1.write(self.root/'descriptor.json',{'endpoint':self.name,'identity':self.identity})
        content=(self.root/'descriptor.json').read_text()
        self.assertFalse(any(s in content for s in (token,self.key.hex(),self.enrolled['teague']['key'].hex())))
    def test_29_client_crash_handshake(self):
        p=self.ctx.Process(target=crash_client,args=(self.args(),));p.start();p.join(5)
        self.assertEqual(p.exitcode,82);self.attach()
    def test_30_pipe_handle_not_inherited(self):
        name='TEAGUE-TEST-'+uuid.uuid4().hex;pipe=pt.listen(name)
        child=subprocess.Popen([sys.executable,'-I','-c','import time; time.sleep(2)'],
            close_fds=False,env={k:os.environ[k] for k in ('SystemRoot','WINDIR','TEMP','TMP') if k in os.environ},
            creationflags=0x08000000)
        try:
            pipe.close();self.assertIsNone(child.poll())
            replacement=pt.listen(name);replacement.close()
        finally:
            if child.poll() is None:child.terminate()
            child.wait(3)
    def test_31_unenrolled_build_digest(self):
        self.enrolled['teague']['exe_digest']='0'*64
        self.restart_bootstrap();self.denied(lambda:self.call())
    def test_32_coordinator_startup_race_composed(self):
        for _ in range(3):self.coordinator_startup_race_composed()
    def coordinator_startup_race_composed(self):
        # Separate namespace, no prior Core. Authentication never invokes startup.
        root=self.run_folder/('TEST-'+uuid.uuid4().hex);root.mkdir()
        (root/'TEST_ONLY').write_text('NO PRODUCTION SERVICES')
        ps=[stage1.spawn(root,'coordinator') for _ in range(4)]
        (root/'go').touch()
        try:
            for p in ps:p.wait(6)
            rows=[stage1.read(p) for p in root.glob('*.json')]
            self.assertEqual(sum(r.get('kind')=='core_acquired' for r in rows),1)
            self.assertEqual(sum(r.get('kind')=='spawned' for r in rows),1)
            info=stage1.read(root/'core.json')
            original=self.root
            try:
                self.root=root;self.identity={**self.identity,**pt.identity(info['pid']),
                    'namespace':root.name,'data_id':'TEST-data-'+root.name,'core_instance_id':info['epoch'],'startup_epoch':info['epoch']}
                self.restart_bootstrap();self.attach('teague');self.attach('intelligence')
            finally:self.root=original
        finally:
            (root/'stop').touch()
            for p in ps:
                if p.poll() is None:p.terminate();p.wait(3)
    def test_33_stalled_handshake_bounded(self):
        pipe=pt.connect(self.name)
        try:
            pipe.raw(b'\0');time.sleep(1.4)
        finally:pipe.close()
        self.attach()
    def test_34_enrollment_claim_without_secret(self):
        arguments=list(self.args());arguments[5]=self.enrolled['intelligence']['key']
        self.denied(lambda:b.client(*arguments))
    def test_35_no_credentials_to_fake_listener(self):
        token=self.attach();self.restart_bootstrap('fake-proof')
        shapes=[];send=pt.Pipe.send
        def observed(pipe,value):
            shapes.append(sorted(value.keys()));return send(pipe,value)
        pt.Pipe.send=observed
        try:self.denied(lambda:self.op(token))
        finally:pt.Pipe.send=send
        self.assertEqual(shapes,[['client','nonce','range']])
    def test_36_unprivileged_child_no_credential_environment(self):
        token=self.attach()
        child=subprocess.run([sys.executable,'-I','-c',
            'import os,json; print(json.dumps(sorted(os.environ)))'],capture_output=True,text=True,
            env={k:os.environ[k] for k in ('SystemRoot','WINDIR','TEMP','TMP') if k in os.environ},creationflags=0x08000000)
        self.assertEqual(child.returncode,0)
        self.assertTrue(set(json.loads(child.stdout))<={'SYSTEMROOT','WINDIR','TEMP','TMP'})
        self.assertNotIn(token,child.stdout)

class Evidence(unittest.TextTestResult):
    def startTest(self,test):self.started=time.monotonic();super().startTest(test)
    def addSuccess(self,test):
        RECORDS.append({'case':test.id(),'result':'PASS','ms':round((time.monotonic()-self.started)*1000),
                        'namespace':str(getattr(test,'root','')),'core_identity':getattr(test,'identity',None)})
        super().addSuccess(test)
    def addFailure(self,test,err):
        RECORDS.append({'case':test.id(),'result':'FAIL','reason':err[0].__name__});super().addFailure(test,err)
    def addError(self,test,err):
        RECORDS.append({'case':test.id(),'result':'ERROR','reason':err[0].__name__});super().addError(test,err)
    def addSkip(self,test,reason):
        RECORDS.append({'case':test.id(),'result':'UNVERIFIED','reason':reason});super().addSkip(test,reason)
    def addSubTest(self,test,subtest,err):
        RECORDS.append({'case':test.id(),'variant':str(subtest.params),'result':'PASS' if err is None else 'FAIL',
            'reason':None if err is None else err[0].__name__})
        super().addSubTest(test,subtest,err)

RECORDS=[]
if __name__=='__main__':
    for key in list(os.environ):
        if key.upper() not in ('SYSTEMROOT','WINDIR','TEMP','TMP'):os.environ.pop(key,None)
    mp.freeze_support()
    result=unittest.TextTestRunner(verbosity=2,resultclass=Evidence).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    dest=Path(__file__).parent/'evidence';dest.mkdir(exist_ok=True)
    output=dest/(uuid.uuid4().hex+'.json')
    output.write_text(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'records':RECORDS},indent=2))
    print('EVIDENCE',output);sys.exit(not result.wasSuccessful())
