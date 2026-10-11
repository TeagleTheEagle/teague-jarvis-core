"""Real bounded local fallback validation; one disposable authenticated TEST Core."""
import os, sys, json, time, uuid, traceback, subprocess
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]/"docs/ollama-acceptance-diagnosis"
def run():
    """Actual Electron entry pages + real synthetic App; never production launchers."""
    import secrets, queue, threading, hashlib
    repo=Path(__file__).resolve().parents[1];sys.path.insert(0,str(repo))
    import stage4_runtime as runtime
    h=runtime.exclusion;b=runtime.authentication;pt=runtime.transport
    root=h.BASE/('TEST-STAGE4-'+uuid.uuid4().hex);root.mkdir(parents=True)
    (root/'TEST_ONLY').write_text('NO PRODUCTION SERVICES')
    data_id='TEST-'+uuid.uuid4().hex;runtime.provision(root,data_id)
    electron=repo/'desktop/node_modules/electron/dist/electron.exe'
    key=secrets.token_bytes(32);name='TEAGUE-TEST-'+uuid.uuid4().hex
    enrolled={client:{'enabled':True,'key':secrets.token_bytes(32).hex(),
              'exe_digest':pt.identity(os.getpid())['exe_digest'] if client=='controller' else hashlib.sha256(electron.read_bytes()).hexdigest(),
              'protocol':[2,3],'scopes':sorted(runtime.Ownership.ORDINARY|({'lifecycle'} if client=='controller' else set()))}
              for client in ('teague','intelligence','controller')}
    config={'data_id':data_id,'server_key':key.hex(),'endpoint':name,'enrollments':enrolled,'text_provider_scenario':'temporary'}
    env={k.upper():v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','TEMP','TMP')}
    report=[];clients=[];core=None;ready=None;controller=None;screenshots=[]
    def record(case,ok):
        report.append({'case':case,'passed':bool(ok)})
        if not ok:raise AssertionError(case)
    def control(op,args=None):
        return b.client(name,ready['peer'],ready['identity'],key,'controller',bytes.fromhex(enrolled['controller']['key']),{'op':op,'token':controller,'args':args or {}})
    def read_events(process,destination):
        for line in process.stdout:
            if line.startswith('STAGE4 '):destination.put(json.loads(line[7:]))
    def receive(client,event,timeout=15):
        until=time.monotonic()+timeout
        while time.monotonic()<until:
            try:value=client['queue'].get(timeout=.2)
            except queue.Empty:
                if client['process'].poll() is not None:raise RuntimeError('Electron exited: '+str(client['process'].returncode))
                continue
            if value['event']=='denied':raise RuntimeError('Electron driver/attachment denied')
            if value['event']==event:return value
        raise TimeoutError('Electron '+event)
    def send(client,action,**kw):
        client['process'].stdin.write(json.dumps({'action':action,**kw})+'\n');client['process'].stdin.flush()
    def snapshot(client):
        send(client,'snapshot');return receive(client,'snapshot')['result']
    def start_client(client_id):
        entry=repo/'tests/ollama_ui_diagnostic.cjs'
        errpath=root/(client_id+'-'+uuid.uuid4().hex+'-stderr.txt')
        node=Path(os.environ['USERPROFILE'])/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
        launcher="""const {fork}=require('node:child_process');
const c=fork(process.argv[2],['--stage4-test','--stage4-root='+process.argv[3]],{execPath:process.argv[1],stdio:['ignore','pipe','pipe','ipc'],windowsHide:true});
c.stdout.pipe(process.stdout);c.stderr.pipe(process.stderr);
const lines=require('node:readline').createInterface({input:process.stdin});lines.on('line',line=>c.send(JSON.parse(line)));lines.on('close',()=>{if(c.connected)c.disconnect();});
c.on('exit',code=>process.exit(code===null?1:code));"""
        client_env={k.upper():v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','TEMP','TMP','USERPROFILE','APPDATA','LOCALAPPDATA','COMSPEC','PATH')}
        process=subprocess.Popen([str(node),'-e',launcher,str(electron),str(entry),str(root)],env=client_env,
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=errpath.open('w'),text=True,close_fds=True,creationflags=0x08000000)
        client={'process':process,'queue':queue.Queue(),'stderr':str(errpath)};clients.append(client)
        threading.Thread(target=read_events,args=(process,client['queue']),daemon=True).start()
        identity={**ready['identity'],'created':str(ready['identity']['created'])}
        peer={**ready['peer'],'created':str(ready['peer']['created'])}
        settings={'clientId':client_id,'endpoint':name,'expectedIdentity':identity,'pinnedPeer':peer,'serverKey':key.hex(),
                  'clientKey':enrolled[client_id]['key'],'driver':True}
        process.stdin.write(json.dumps(settings)+'\n');process.stdin.flush()
        attached=receive(client,'ready');client['ready']=attached
        until=time.monotonic()+10
        while True:
            view=snapshot(client)
            if view.get('ready')=='true':break
            if time.monotonic()>until:raise TimeoutError('Actual renderer initialization')
            time.sleep(.1)
        record(client_id+' real renderer authenticated',view['connection']=='attached')
        record(client_id+' no renderer Node/native/management bridge',view['node']=='undefined' and set(view['bridge'])=={'connection','shared','request','requestStatus','cancelRequest','stopCapture','stopPlayback'})
        return client
    try:
        with h.Lock(root,'supervisor.lock'):
            with h.Lock(root,'core.lock'):pass
            h.write(root/'intent.json',{'mode':'TEST','operation':uuid.uuid4().hex})
            core=subprocess.Popen([sys.executable,'-I',str(repo/'tests/lifecycle_stage4/fixtures.py'),'--app-worker',str(root)],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,close_fds=True,creationflags=0x08000000)
            core.stdin.write(json.dumps(config)+'\n');core.stdin.close()
            until=time.monotonic()+15
            while not (root/'stage4-ready.json').exists():
                if core.poll() is not None:raise RuntimeError(core.stderr.read())
                if time.monotonic()>until:raise TimeoutError('TEST App readiness')
                time.sleep(.02)
            ready=h.read(root/'stage4-ready.json');record('Stage1 reconciliation before Electron',h.reconcile(root))
        controller=control('attach',{'scopes':enrolled['controller']['scopes']})['token']
        record('one TEST App/Store/Voice/Wake instance',all(ready[n]==1 for n in ('app_instances','store_instances','voice_instances','wake_instances')))
        a=start_client('teague')
        send(a,'text-fallback',text='What is 2 plus 2? Answer only with the number.',operation=uuid.uuid4().hex)
        result=receive(a,'text-fallback',timeout=30)
        report.append({'case':'offline replay transport result','passed':True,'result':result})
        send(a,'capture');screenshots.append(receive(a,'capture'))
        send(a,'diagnose-render');diagnosis=receive(a,'diagnose-render')
        report.append({'case':'DOM observation only','passed':True,'observation':diagnosis})
        send(a,'capture');screenshots.append(receive(a,'capture'))
        send(a,'close');a['process'].wait(10)
        control('shutdown',{'operation':uuid.uuid4().hex});core.wait(8)
        record('authorized TEST shutdown',core.returncode==0)
        with h.Lock(root,'core.lock'):record('Core lifetime lock released after process exit',True)
    except Exception as exc:
        report.append({'case':'Electron probe failure','passed':False,'error':type(exc).__name__,'detail':str(exc)[:5000],'traceback':traceback.format_exc(),'errno':getattr(exc,'errno',None),'winerror':getattr(exc,'winerror',None)})
    finally:
        # Failure cleanup is scoped, cooperative client departure and authenticated
        # TEST lifecycle only. Never force-kill a Core or delete ownership files.
        for client in clients:
            if client['process'].poll() is None:
                try:client['process'].stdin.close();client['process'].wait(10)
                except Exception:pass
        if core and core.poll() is None and ready:
            try:
                if not controller: controller=control('attach',{'scopes':enrolled['controller']['scopes']})['token']
                control('shutdown',{'operation':uuid.uuid4().hex});core.wait(8)
            except Exception as exc:report.append({'case':'cleanup unresolved; retain TEST ownership','passed':False,'error':type(exc).__name__})
        dest=BASE/('ui-diagnostic-'+uuid.uuid4().hex+'.json')
        dest.write_text(json.dumps({'cases':report,'root':str(root),'core_pid':core.pid if core else None,'core_exit':core.poll() if core else None,
            'clients':[{'launcher_pid':c['process'].pid,'electron_pid':c.get('ready',{}).get('pid'),'exit':c['process'].poll(),'stderr':c['stderr'],'electron_version':c.get('ready',{}).get('electron')} for c in clients],
            'screenshots':screenshots,
            'physical_voice_verified':False,'production_activation':False},indent=2));print('EVIDENCE',dest,flush=True)
    while core and core.poll() is None:
        print('TEST controller retained: STATUS or SHUTDOWN only',flush=True)
        line=sys.stdin.readline().strip().upper()
        if line in ('STATUS','SHUTDOWN'):
            try:
                result=control('lifecycle-status' if line=='STATUS' else 'shutdown',{} if line=='STATUS' else {'operation':uuid.uuid4().hex})
                print('Authenticated control returned',flush=True)
                if line=='SHUTDOWN':core.wait(8)
            except Exception as exc:print(type(exc).__name__,flush=True)
        else:time.sleep(1)
    if any(not r['passed'] for r in report):raise AssertionError('Electron probe failed; retain evidence')
    print('Electron checks',len(report),'PASS')

if __name__=="__main__":run()

