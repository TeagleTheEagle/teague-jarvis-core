"""Actual installed TEST process/client driver; no production access or forced cleanup."""
import hashlib
import json
import os
from pathlib import Path
import queue
import secrets
import subprocess
import sys
import threading
import time
import traceback
import uuid

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests/lifecycle_stage4'))
from fixtures import ClientCampaign
from deployment_test import contract, enrollment, package

OUT=ROOT/'docs/deployment-completion-20260916'
VALIDATION=ROOT.parent/'deployment-test-releases'

def control_timeout(action):
    # Observed verified staging: 37.110s; 20% headroom rounded up. TEST only.
    return 45 if action == 'stage-update' else 35

class InstalledCampaign(ClientCampaign):
    def __init__(self):
        super().__init__()
        self.path=OUT/('installed-'+uuid.uuid4().hex+'.json')
        self.bindings={};self.keys={};self.package=None;self.controls=[]
        VALIDATION.mkdir(exist_ok=True)
        self.cwd=VALIDATION/('TEST-WORKING-'+uuid.uuid4().hex);self.cwd.mkdir()
        self.env={k.upper():v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','TEMP','TMP','USERPROFILE','APPDATA','LOCALAPPDATA','COMSPEC')}
    def save(self):
        self.path.write_text(json.dumps(dict(records=self.records,roots=[str(p) for p in self.roots],
            mode=contract.MODE,production_changed=False,paid_calls=0,physical_media=False,
            clean_machine=False,package=self.package,control_processes=self.controls),indent=2),encoding='utf8')
    def build(self):
        node=Path(sys._base_executable).parent.parent/'node/bin/node.exe'
        native=ROOT.parent/'stage4-toolchain/peer-build/Release/peer_identity.node'
        accepted=json.loads((ROOT/'docs/lifecycle-stage5-evidence/source-final.json').read_text(encoding='utf-8-sig'))
        expected=next(x['sha256'] for x in accepted if x['path']=='desktop/node_modules/electron/dist/electron.exe')
        electron=(ROOT/'desktop/node_modules/electron/dist').resolve()
        self.check('explicit materialized Electron build input',contract.digest(electron/'electron.exe')==expected,resolved_build_input=str(electron),sha256=expected)
        self.package=package.build(ROOT,VALIDATION/('TEST-PACKAGE-'+uuid.uuid4().hex),node=node,native=native,electron=electron,expected_electron_hash=expected)
        self.check('explicit self-contained TEST inventory built',True,files=self.package['files'],bytes=self.package['bytes'],manifest_sha256=self.package['sha256'])
    def control(self,binding,action,args=None,request=None,expect_failure=False):
        command=binding.python_command('--control')
        req=request or enrollment.signed_request(binding,self.keys[binding.state],action,args or {})
        p=subprocess.Popen(command,cwd=self.cwd,env=self.env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                           text=True,close_fds=True,creationflags=0x08000000)
        peer=self.r.transport.identity(p.pid)
        stdout,stderr=p.communicate(json.dumps(req)+'\n',timeout=control_timeout(action))
        record={'identity':peer,'exit':p.returncode,'action':action}
        self.controls.append(record)
        if p.returncode:
            record['stderr']=stderr;self.save()
            if expect_failure:return {'denied':True,'stderr':stderr}
            raise RuntimeError('Installed control failed; preserved '+action+' stderr: '+stderr)
        self.save()
        if expect_failure:raise AssertionError('Expected rejection: '+action)
        return json.loads(stdout)
    def namespace(self):
        key=secrets.token_bytes(32)
        b=package.install(Path(self.package['package']),VALIDATION,key,expected_package_hash=self.package['sha256'])
        self.bindings[b.state]=b;self.keys[b.state]=key;self.roots.append(b.state)
        initialized=self.control(b,'initialize',{'intent':'NEW_SYNTHETIC_TEST'})
        self.check('new TEST identity explicitly initialized in fresh packaged process',initialized['identity']['data_id']==b.record['data_id'],identity=initialized['identity'])
        return b.state,b.record['data_id']
    def core_config(self,data,crash=None):
        b=next(b for b in self.bindings.values() if b.record['data_id']==data)
        return self.control(b,'configuration')
    def rejected_coordinator(self,root,core,reason):
        b=self.bindings[root]
        cfg={'name':uuid.uuid4().hex,'owner':'controller','owner_peer':self.peer,'owner_key':secrets.token_hex(32),
             'server_key':secrets.token_hex(32),'endpoint':'TEAGUE-TEST-'+uuid.uuid4().hex,'core':core}
        cfg['_deployment_authorization']=enrollment.signed_request(b,self.keys[root],'coordinator',{'configuration_sha256':self.r._start_digest(cfg)})
        p=subprocess.Popen(b.python_command('--coordinator'),cwd=self.cwd,env=self.env,stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,close_fds=True,creationflags=0x08000000)
        peer=self.r.transport.identity(p.pid)
        _,stderr=p.communicate(json.dumps(cfg)+'\n',timeout=35)
        self.check('incompatible bootstrap rejected before Core start',p.returncode!=0 and reason in stderr and not self.events(root,'start_spawned'),
            identity=peer,exit=p.returncode,stderr=stderr,expected=reason)
    def coordinator(self,root,core,crash=None):
        need=contract.need;need(crash in (None,'before-intent','intent','spawned'),'TEST_INTERRUPTION_BOUNDARY')
        b=self.bindings[root];name=uuid.uuid4().hex
        cfg={'name':name,'owner':'controller','owner_peer':self.peer,'owner_key':secrets.token_hex(32),
             'server_key':secrets.token_hex(32),'endpoint':'TEAGUE-TEST-'+uuid.uuid4().hex,'core':core}
        if crash:cfg['_test_interruption']=crash
        cfg['_deployment_authorization']=enrollment.signed_request(b,self.keys[root],'coordinator',{'configuration_sha256':self.r._start_digest(cfg)})
        errpath=root/('deployment-coordinator-'+name+'.stderr.log')
        with errpath.open('w') as err:
            p=subprocess.Popen(b.python_command('--coordinator'),cwd=self.cwd,env=self.env,stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,stderr=err,text=True,close_fds=True,creationflags=0x08000000)
        peer=self.r.transport.identity(p.pid)
        item={'process':p,'configuration':cfg,'root':root,'token':None,'initial_peer':peer};self.coordinators.append(item)
        p.stdin.write(json.dumps(cfg)+'\n');p.stdin.close()
        self.coordinator_state(item)
        item['publication_timeout']=25
        item['ready']=self.coordinator_readiness(item,wait=True)
        self.check('installed coordinator exact live identity',self.r.transport.identity(p.pid)==item['ready']['peer'],identity=item['ready']['identity'])
        result=self.cc(item,'attach');item['token']=result['token']
        return item
    def wait_dead(self,root,identity):
        deadline=time.monotonic()+12
        while self.r.exclusion.process_identity(identity['pid'])=={'pid':identity['pid'],'created':identity['created']}:
            if time.monotonic()>deadline:raise TimeoutError('TEST Core retained for review; no forced cleanup')
            time.sleep(.025)
        self.check('installed Core exited with identity recheck',True,identity=identity)
    def start_client(self,root,core,identity,owner,settings_override=None):
        b=self.bindings[root]
        cfg=settings_override or self.control(b,'client-configuration',{'client':owner})
        stderr=root/(owner+'-'+uuid.uuid4().hex+'-stderr.log')
        with stderr.open('w') as err:
            p=subprocess.Popen([str(b.release/'node/node.exe'),str(b.app/'client-launcher.cjs'),str(root)],
                cwd=self.cwd,env=self.env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,close_fds=True,creationflags=0x08000000)
        client={'process':p,'queue':queue.Queue(),'stderr':str(stderr),'root':root};self.clients.append(client)
        def reader():
            for line in p.stdout:
                if line.startswith('STAGE4 '):client['queue'].put(json.loads(line[7:]))
        threading.Thread(target=reader,daemon=True).start()
        p.stdin.write(json.dumps(cfg)+'\n');p.stdin.flush()
        ready=self.receive(client,'ready',timeout=30);client['ready']=ready
        peer=self.r.transport.identity(ready['pid']);client['identity']=peer
        self.check('actual relocated Electron identity authenticated',peer['exe_digest']==core['enrollments'][owner]['exe_digest'],owner=owner,identity=peer,version=ready['electron'])
        deadline=time.monotonic()+12
        while self.view(client).get('ready')!='true':
            if time.monotonic()>deadline:raise TimeoutError('Packaged renderer readiness')
            time.sleep(.05)
        self.check('actual relocated renderer attached',self.view(client)['connection']=='attached' and ready['identity']=={**identity,'created':str(identity['created'])},owner=owner)
        return client
    def cleanup(self):
        # Only supported authenticated cleanup of this driver's exact objects.
        for client in self.clients:
            if client['process'].poll() is None:
                try:self.close_client(client)
                except Exception as exc:self.records.append(dict(case='TEST client cleanup',passed=False,error=str(exc)))
        for root,core,identity in self.cores:
            if self.r.exclusion.process_identity(identity['pid'])=={'pid':identity['pid'],'created':identity['created']}:
                try:self.stop(root,core,identity)
                except Exception as exc:self.records.append(dict(case='TEST Core cleanup retained',passed=False,identity=identity,error=str(exc)))
        for item in self.coordinators:
            try:self.close(item)
            except Exception as exc:self.records.append(dict(case='TEST coordinator cleanup retained',passed=False,error=str(exc)))
        self.save()
    def denied_client(self,root,core,identity,owner,settings):
        start=len(self.clients)
        try:
            self.start_client(root,core,identity,owner,settings_override=settings)
        except Exception as exc:
            self.check('stale or revoked actual Electron authentication denied',len(self.clients)==start+1,error=str(exc))
            client=self.clients[-1]
            # Closing the driver's pipe invokes the existing client disconnect
            # handler even when authentication failed before a window existed.
            client['process'].stdin.close();client['process'].wait(12)
            self.check('rejected Electron exits through supported disconnect',client['process'].returncode==0)
            return
        raise AssertionError('Stale Electron enrollment unexpectedly accepted')
