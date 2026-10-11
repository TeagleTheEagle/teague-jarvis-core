"""TEST ONLY diagnostic publisher/reader; no App, Store, Core or providers.

Repeated publication mirrors Stage 1's 15ms loop. Once-per-challenge is an
experimental comparator only. This is not an accepted lifecycle implementation.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
import uuid

BASE = Path(__file__).resolve().parents[2] / 'docs/lifecycle-stage4-evidence'


def write(path, data):
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    temporary.write_text(json.dumps(data), encoding='utf8')
    os.replace(temporary, path)


def fault(exc, operation, path, temporary=None):
    return dict(operation=operation, path=str(path), temporary=str(temporary) if temporary else None,
                exception=type(exc).__name__, errno=getattr(exc, 'errno', None),
                winerror=getattr(exc, 'winerror', None), traceback=traceback.format_exc(),
                pid=os.getpid(), at_ns=time.perf_counter_ns())


def worker(root, role, mode, profile):
    root = root.resolve()
    if not root.is_relative_to(BASE.resolve()) or (root/'TEST_ONLY').read_text() != 'DISPOSABLE FILE IPC ONLY':
        raise ValueError('Isolated TEST directory required')
    events, errors = [], []
    (root/(role+'.ready')).touch()
    until = time.monotonic()+10
    while not (root/'go').exists():
        if time.monotonic()>until: raise TimeoutError('barrier')
        time.sleep(.002)
    end = time.monotonic()+1.2
    last = None
    reads = 0
    try:
        while time.monotonic()<end:
            if role == 'publisher':
                try: request = json.loads((root/'challenge.json').read_text(encoding='utf8'))
                except (OSError, ValueError):
                    time.sleep(.015)
                    continue
                challenge = request.get('challenge')
                if mode == 'repeated' or challenge != last:
                    path = root/'response.json'
                    temporary = path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
                    record = dict(challenge=challenge, at_ns=time.perf_counter_ns(), published=False)
                    events.append(record)
                    operation = 'temporary.write_text'
                    try:
                        temporary.write_text(json.dumps(dict(identity={'mode':'TEST', 'pid':os.getpid()}, challenge=challenge)), encoding='utf8')
                        operation = 'os.replace(temporary, response.json)'
                        os.replace(temporary, path)
                        record['published'] = True
                        last = challenge
                    except OSError as exc:
                        errors.append(fault(exc, operation, path, temporary))
                        break  # Stage 1 stops on write failure; no diagnostic retry.
                time.sleep(.015)
            else:
                if profile == 'no-reader':
                    time.sleep(.020)
                    continue
                try:
                    if profile == 'held-read':
                        with (root/'response.json').open(encoding='utf8') as stream:
                            json.loads(stream.read())
                            time.sleep(.010)  # Explicit amplification, NOT Stage 1 behavior.
                    else:
                        json.loads((root/'response.json').read_text(encoding='utf8'))
                    reads += 1
                except FileNotFoundError:
                    pass  # Initial publication has not happened yet.
                except (OSError, ValueError) as exc:
                    errors.append(fault(exc, 'response.read_text/json.loads', root/'response.json'))
                time.sleep(.020 if profile != 'fast-read' else .0005)
    finally:
        (root/(role+'.json')).write_text(json.dumps(dict(events=events, errors=errors, reads=reads), indent=2))


def run():
    source = Path(__file__).resolve().parents[1]/'lifecycle_stage1/harness.py'
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    runroot = BASE/('publication-diagnostic-'+uuid.uuid4().hex)
    runroot.mkdir(parents=True)
    results=[]
    env={k:v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','TEMP','TMP')}
    profiles = [('no-reader',10)] if '--no-reader-control' in sys.argv else [('baseline',20),('fast-read',10),('held-read',10)]
    for profile, pairs in profiles:
        for pair in range(pairs):
            for mode in (('repeated','once') if pair%2==0 else ('once','repeated')):
                root=runroot/f'{profile}-{pair:02}-{mode}'
                root.mkdir(); (root/'TEST_ONLY').write_text('DISPOSABLE FILE IPC ONLY')
                write(root/'challenge.json',{'challenge':'challenge-0'})
                processes=[]
                for role in ('publisher','reader'):
                    processes.append(subprocess.Popen([sys.executable,'-I',__file__,'--worker',str(root),role,mode,profile],env=env,stdin=subprocess.DEVNULL,close_fds=True,creationflags=0x08000000))
                until=time.monotonic()+5
                while not all((root/(role+'.ready')).exists() for role in ('publisher','reader')):
                    if time.monotonic()>until: raise TimeoutError('ready')
                    time.sleep(.005)
                (root/'go').touch()
                # Keep one challenge unchanged for the full trial to isolate redundant publication.
                for process in processes:
                    if process.wait(timeout=5): raise RuntimeError('diagnostic worker failed')
                publisher=json.loads((root/'publisher.json').read_text())
                reader=json.loads((root/'reader.json').read_text())
                counts={}
                for event in publisher['events']:
                    item=counts.setdefault(event['challenge'],{'attempts':0,'published':0})
                    item['attempts']+=1; item['published']+=int(event['published'])
                results.append(dict(profile=profile,pair=pair,mode=mode,directory=root.name,
                                    challenges=counts,publisher_errors=publisher['errors'],
                                    reader_errors=reader['errors'],reads=reader['reads']))
                (runroot/'results.json').write_text(json.dumps(dict(source_sha256=before,cases=results),indent=2))
            if pair%5==4: print(profile, 'pairs complete',pair+1,flush=True)
    summary=[]
    for profile, _ in profiles:
        for mode in ('repeated','once'):
            rows=[r for r in results if r['profile']==profile and r['mode']==mode]
            summary.append(dict(profile=profile,mode=mode,trials=len(rows),
                failed_trials=sum(bool(r['publisher_errors']) for r in rows),
                publications=sum(c['published'] for r in rows for c in r['challenges'].values()),
                attempts=sum(c['attempts'] for r in rows for c in r['challenges'].values())))
    unchanged=before==hashlib.sha256(source.read_bytes()).hexdigest()
    (runroot/'summary.json').write_text(json.dumps(dict(summary=summary,stage1_unchanged=unchanged,
        limitations=['Mechanism experiment; not accepted Stage 1 regression or historical root-cause proof.',
                     'Baseline reader polls throughout trial; actual reconcile stops on success.',
                     'Fast and held reads amplify contention and are not production behavior.',
                     'No OS-wide handle trace or antivirus causation established.']),indent=2))
    print('EVIDENCE',runroot,flush=True)
    print(json.dumps(summary),flush=True)


def native_probe():
    import threading
    repo=Path(__file__).resolve().parents[2]
    sys.path.insert(0,str(repo/'tests/lifecycle_stage2'))
    import pipe_transport as pt
    cache=repo.parent/'stage4-toolchain'
    electron=repo/'desktop/node_modules/electron/dist/electron.exe'
    native=cache/'peer-build/Release/peer_identity.node'
    report=[]
    env={k.upper():v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA')}
    env['ELECTRON_RUN_AS_NODE']='1'
    cases=('correct','wrong-pid','wrong-created','wrong-executable','wrong-namespace','missing-bridge','self',
           'core-separate','core-wrong-created','core-wrong-executable','core-dead','core-argument','core-unpinned','core-closed','core-immutable')
    for case in cases:
        name='TEAGUE-TEST-'+uuid.uuid4().hex
        observed=pt.identity(os.getpid());pin={**observed,'created':str(observed['created'])}
        if case=='wrong-pid':pin['pid']+=1
        if case=='wrong-created':pin['created']=str(observed['created']+1)
        if case=='wrong-executable':pin['exe_digest']='0'*64
        received=[];server_errors=[];pipe=None;thread=None
        core_process=None;core_pin=None
        if case.startswith('core-') and case!='core-unpinned':
            # Disposable idle process only: no App, Store, Core or production imports.
            core_process=subprocess.Popen([sys.executable,'-I','-c','import time; time.sleep(30)'],env=env,stdin=subprocess.DEVNULL,close_fds=True,creationflags=0x08000000)
            core_pin=pt.identity(core_process.pid);core_pin['created']=str(core_pin['created'])
            if case=='core-wrong-created':core_pin['created']=str(int(core_pin['created'])+1)
            if case=='core-wrong-executable':core_pin['exe_digest']='0'*64
            if case=='core-dead':core_process.terminate();core_process.wait(5)
        if case in ('correct','wrong-pid','wrong-created','wrong-executable') or case.startswith('core-'):
            pipe=pt.listen(name)
            def server():
                try:
                    pipe.io('connect');pipe.deadline=time.monotonic()+5
                    message=pipe.receive();received.append(message)
                    pipe.send({'result':'OK'})
                except Exception as exc:server_errors.append(type(exc).__name__)
                finally:pipe.close()
            thread=threading.Thread(target=server);thread.start()
        config={'nativePath':str(native) if case!='missing-bridge' else str(cache/'missing.node'),
                'endpoint':name if case!='wrong-namespace' else 'PRODUCTION', 'peer':pin,
                'action':'self' if case=='self' else 'exchange'}
        if core_pin:config['core']=core_pin
        if case.startswith('core-'):config['verify']={'core-argument':'argument','core-closed':'closed','core-immutable':'immutable'}.get(case,'normal')
        try:
            p=subprocess.run([str(electron),str(repo/'desktop/test/stage4-client.test.cjs'),'--native-case'],input=json.dumps(config),capture_output=True,text=True,env=env,timeout=12)
        finally:
            if core_process and core_process.poll() is None:core_process.terminate();core_process.wait(5)
        if thread:thread.join(7)
        value=json.loads(p.stdout)
        expected=case in ('correct','self','core-separate','core-immutable')
        passed=p.returncode==0 and value['passed']==expected and (not thread or not thread.is_alive())
        if not expected:passed=passed and not received
        report.append({'case':case,'passed':passed,'child_returncode':p.returncode,'result':value,'received_frames':len(received),'server_errors':server_errors})
        # Retain failed development evidence as well as successful cases.
    dest=BASE/('native-probe-'+uuid.uuid4().hex+'.json')
    dest.write_text(json.dumps(report,indent=2));print('EVIDENCE',dest);print('native checks',len(report),'PASS')
    if not all(row['passed'] for row in report):raise AssertionError('Native checks failed; see retained evidence')


def bootstrap_probe():
    import threading, secrets
    repo=Path(__file__).resolve().parents[2]
    sys.path.insert(0,str(repo/'tests/lifecycle_stage2'))
    import pipe_transport as pt
    import bootstrap as auth
    env={k.upper():v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA')}
    env['ELECTRON_RUN_AS_NODE']='1'
    report=[]
    for case in ('valid-separate','wrong-core-created','wrong-core-executable','dead-core','fake-server-proof','wrong-pipe-peer'):
        child=subprocess.Popen([sys.executable,'-I','-c','import time; time.sleep(30)'],env=env,stdin=subprocess.DEVNULL,close_fds=True,creationflags=0x08000000)
        identity={**pt.identity(child.pid),'mode':'TEST','protocol':[2,3]}
        if case=='wrong-core-created':identity['created']+=1
        if case=='wrong-core-executable':identity['exe_digest']='0'*64
        if case=='dead-core':child.terminate();child.wait(5)
        name='TEAGUE-TEST-'+uuid.uuid4().hex;pipe=pt.listen(name)
        pin=pt.identity(os.getpid());pin['created']=str(pin['created'])
        if case=='wrong-pipe-peer':pin['created']=str(int(pin['created'])+1)
        server_key=secrets.token_bytes(32);client_key=secrets.token_bytes(32)
        frames=[];errors=[]
        def server():
            try:
                pipe.io('connect');pipe.deadline=time.monotonic()+5
                hello=pipe.receive();frames.append('hello')
                t={'hello':hello,'server_nonce':secrets.token_hex(32),'identity':identity,'selected':3,'peer':pipe.peer(server=True)}
                proof=auth.proof(server_key,'server',t)
                pipe.send({'transcript':t,'proof':'0'*64 if case=='fake-server-proof' else proof})
                answer=pipe.receive();frames.append('client-proof')
                if answer!={'proof':auth.proof(client_key,'client',t)}:raise AssertionError('CLIENT_PROOF')
                pipe.receive();frames.append('request');pipe.send({'result':'OK'})
            except Exception as exc:errors.append(type(exc).__name__)
            finally:pipe.close()
        thread=threading.Thread(target=server);thread.start()
        config={'action':'bootstrap','nativePath':str(repo.parent/'stage4-toolchain/peer-build/Release/peer_identity.node'),
                'endpoint':name,'pinnedPeer':pin,'expectedIdentity':{**identity,'created':str(identity['created'])},
                'serverKey':server_key.hex(),'clientKey':client_key.hex(),'clientId':'STAGE4_TEST_CLIENT','request':{'op':'test'}}
        try:
            p=subprocess.run([str(repo/'desktop/node_modules/electron/dist/electron.exe'),str(repo/'desktop/test/stage4-client.test.cjs'),'--native-case'],input=json.dumps(config),capture_output=True,text=True,env=env,timeout=12)
        finally:
            if child.poll() is None:child.terminate();child.wait(5)
        thread.join(7);value=json.loads(p.stdout)
        expected=case=='valid-separate'
        passed=p.returncode==0 and value['passed']==expected and not thread.is_alive()
        passed=passed and (frames==['hello','client-proof','request'] if expected else 'client-proof' not in frames and 'request' not in frames)
        report.append({'case':case,'passed':passed,'frames':frames,'result':value,'server_errors':errors})
    dest=BASE/('core-pin-bootstrap-'+uuid.uuid4().hex+'.json');dest.write_text(json.dumps(report,indent=2))
    print('EVIDENCE',dest,flush=True)
    if not all(row['passed'] for row in report):raise AssertionError('Bootstrap checks failed; see evidence')
    print('bootstrap checks',len(report),'PASS')


def bind_inspection_fixture(context):
    """Synthetic panels, actual singleton worker/archive. No capture or provider."""
    from interface_inspection import new_evidence
    import workspaces
    h = context.__class__.__module__
    h = sys.modules[h].exclusion
    # A fresh synthetic Store has no improvement project. Use the existing API
    # and bind the existing TEST archive instance to that TEST project; do not
    # manufacture a production project ID or change Archive/Store semantics.
    with context.app.store.connect() as db:
        if db.execute('SELECT count(*) FROM workspaces').fetchone()[0] != 0:
            raise ValueError('Inspection fixture requires fresh synthetic storage')
    project = workspaces.change(context.app.store, {'action':'create','name':'STAGE4_TEST inspection archive'})['id']
    context.app.inspection_archive.project = project
    with context.app.store.connect() as db:
        if db.execute('SELECT name FROM workspaces WHERE id=?',(project,)).fetchone()[0] != 'STAGE4_TEST inspection archive':
            raise ValueError('TEST archive project verification failed')
    h.event(context.root, 'inspection_fixture_ready', project_id=project)
    def runner(request, cancel):
        h.event(context.root, 'inspection_panel_started')
        if not cancel.wait(5):
            raise TimeoutError('TEST inspection cancellation was not received')
        result = new_evidence(request)
        result['limitations'] = ['STAGE4_TEST synthetic panel; no screen/media/provider access']
        return result
    def finish(job):
        operation = 'TEST archive release wait'
        try:
            h.event(context.root, 'inspection_archive_started', status=job['status'], panels=len(job['results']))
            until = time.monotonic()+5
            while not (context.root/'inspection-release').exists():
                if time.monotonic() >= until:
                    raise TimeoutError('TEST archive release was not received')
                time.sleep(.01)
            operation = 'Archive.save synthetic inspection'
            result = context.app.inspection_archive.save(job)
            h.event(context.root, 'inspection_archive_finished', status=result['status'], job_id=job['id'])
            return result
        except Exception as exc:
            h.event(context.root, 'inspection_archive_failed', **fault(exc,operation,context.data/'inspection-archive'))
            raise  # Preserve UNKNOWN/fail-closed outcome; never retry or settle.
    context.inspection_runner = runner
    context.inspection_finish = finish


async def synthetic_repair_workflow(responder, cancel, checker):
    """Exercise metering/cancellation callbacks only; no patch or sandbox execution."""
    import asyncio
    report={'status':'RUNNING','deployed':False,'synthetic_outcome_only':True,'actual_repair_executed':False}
    try:
        for label in ('SYNTHETIC_BASELINE','SYNTHETIC_CANDIDATE'):
            if cancel.is_set():raise InterruptedError()
            result=await asyncio.to_thread(checker,label,cancel)
            if not result.get('cleanup'):
                report['status']='FAILED';return report
            if label=='SYNTHETIC_BASELINE':
                if cancel.is_set():raise InterruptedError()
                await responder.respond('STAGE4_TEST synthetic resource attempt',cancel=cancel)
        if cancel.is_set():raise InterruptedError()
        report['status']='READY_FOR_REVIEW'
    except InterruptedError:report['status']='CANCELLED'
    except Exception:report['status']='FAILED'
    return report


def provision_repair_fixture(context, responder, checker, workflow=synthetic_repair_workflow):
    import workspaces, budgeted_repair
    store=context.app.store
    project=workspaces.change(store,{'action':'create','name':'STAGE4_TEST repair accounting'})['id']
    task=store.task_put('STAGE4_TEST synthetic cleanup outcome')['id']
    workspaces.change(store,{'action':'link','project':project,'kind':'task','ref':task})
    workspaces.change(store,{'action':'budget_configure','project':project,'limits':budgeted_repair.ALLOCATION})
    context.repair_fixture={'project':project,'task':task,'responder':responder,'checker':checker,'workflow':workflow}
    return project,task


def bind_repair_fixture(context):
    """Trusted TEST parent setup; no provider, child process or real repair runner."""
    from types import SimpleNamespace
    h=sys.modules[context.__class__.__module__].exclusion
    async def respond(prompt, *, cancel):
        h.event(context.root,'repair_attempt_started')
        if not cancel.wait(15):raise TimeoutError('TEST cancellation not received')
        h.event(context.root,'repair_cleanup_started')
        until=time.monotonic()+5
        while not (context.root/'repair-release').exists():
            if time.monotonic()>=until:raise TimeoutError('TEST cleanup release not received')
            time.sleep(.01)
        h.event(context.root,'repair_cleanup_finished')
        return 'STAGE4_TEST synthetic completed attempt; no AI response or patch'
    def checker(label,cancel):
        h.event(context.root,'repair_check_attempt',fixture=label)
        return {'cleanup':True,'simulated':True}
    project,task=provision_repair_fixture(context,SimpleNamespace(respond=respond),checker)
    h.event(context.root,'repair_fixture_ready',project=project,task=task)


def controller_action(call, tokens, identity, scopes, command):
    """Explicit TEST operator actions only; never retry work or print a token."""
    if command in ('REAUTH','RECOVER'):
        recovery=command=='RECOVER'
        result=call('controller','recovery-attach' if recovery else 'attach',{} if recovery else {'scopes':scopes})
        if result.get('result')=='DENIED':return {'result':'DENIED'}
        if (result.get('result')!=('RECOVERY_ATTACHED' if recovery else 'ATTACHED') or
                result.get('identity')!=identity or result.get('epoch')!=identity['startup_epoch']):
            raise ValueError('TEST controller reattachment identity mismatch')
        tokens['controller']=result['token']
        return {'result':'RECOVERY_AUTHENTICATED' if recovery else 'REAUTHENTICATED','identity':identity}
    if command not in ('STATUS','SHUTDOWN'):raise ValueError('Unknown TEST operator action')
    return call('controller','lifecycle-status' if command=='STATUS' else 'shutdown',{} if command=='STATUS' else {'operation':uuid.uuid4().hex})


def bind_expiry_fixture(context):
    """Fixed parent-only TEST clock steps. No protocol operation can set time."""
    def clock():
        # Immutable existence latches avoid racing a read against a partial write.
        step=sum((context.root/name).exists() for name in ('TEST-expire-1','TEST-expire-2'))
        return time.monotonic()+901*step
    context.owners.clock=clock


def polling_app_worker(root, configuration):
    """TEST scheduling injection only: actual App + actual Store message commit."""
    repo=Path(__file__).resolve().parents[2];sys.path.insert(0,str(repo))
    import stage4_runtime
    original_construct=stage4_runtime.construct_app
    h=stage4_runtime.exclusion
    def construct(context):
        app=original_construct(context)
        original_message=app.store.message;used=set()
        def message(conversation, role, content):
            for case in ('control','cancel'):
                if role=='assistant' and case not in used and (root/('polling-'+case+'-arm')).exists():
                    used.add(case)
                    h.event(root,'polling_commit_paused',case=case)
                    until=time.monotonic()+5
                    while not (root/('polling-'+case+'-release')).exists():
                        if time.monotonic()>until:raise TimeoutError('TEST commit observation deadline')
                        time.sleep(.005)
                    result=original_message(conversation,role,content)
                    h.event(root,'polling_commit_returned',case=case)
                    return result
            return original_message(conversation,role,content)
        app.store.message=message
        return app
    stage4_runtime.construct_app=construct
    stage4_runtime.serve(root,configuration,inspection_setup=bind_inspection_fixture,repair_setup=bind_repair_fixture,expiry_setup=bind_expiry_fixture)


def real_app_probe(final_case='normal'):
    import secrets
    repo=Path(__file__).resolve().parents[2];sys.path.insert(0,str(repo))
    import stage4_runtime as runtime
    h=runtime.exclusion;b=runtime.authentication;pt=runtime.transport
    root=h.BASE/('TEST-STAGE4-'+uuid.uuid4().hex);root.mkdir(parents=True)
    (root/'TEST_ONLY').write_text('NO PRODUCTION SERVICES')
    data_id='TEST-'+uuid.uuid4().hex;runtime.provision(root,data_id)
    key=secrets.token_bytes(32);name='TEAGUE-TEST-'+uuid.uuid4().hex
    exe=pt.identity(os.getpid())['exe_digest']
    enrolled={client:{'enabled':True,'key':secrets.token_bytes(32).hex(),'exe_digest':exe,'protocol':[2,3],
                       'scopes':sorted(runtime.Ownership.ORDINARY|(runtime.Ownership.MANAGEMENT if client=='controller' else set()))}
              for client in ('teague','intelligence','controller')}
    config={'data_id':data_id,'server_key':key.hex(),'endpoint':name,'enrollments':enrolled}
    if final_case.startswith('inspection-'):
        config['inspection_fixture'] = True
    if final_case.startswith('repair-'):
        config['repair_fixture'] = True
    if final_case=='controller-expiry':config['controller_expiry_fixture']=True
    env={k.upper():v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','TEMP','TMP')}
    report=[];tokens={};ready=None;core=None;measurements={}
    def record(case,ok):
        report.append({'case':case,'passed':bool(ok)})
        if not ok:raise AssertionError(case)
    def call(client,op,args=None,token=None):
        return b.client(name,ready['peer'],ready['identity'],key,client,bytes.fromhex(enrolled[client]['key']),
                        {'op':op,'token':None if op in ('attach','recovery-attach') else tokens.get(client) if token is None else token,'args':args or {}})
    try:
        with h.Lock(root,'supervisor.lock'):
            with h.Lock(root,'core.lock'):pass
            h.write(root/'intent.json',{'mode':'TEST','operation':uuid.uuid4().hex})
            worker_mode='--polling-app-worker' if final_case=='event-polling' else '--app-worker'
            core=subprocess.Popen([sys.executable,'-I',__file__,worker_mode,str(root)],env=env,
                 stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,close_fds=True,creationflags=0x08000000)
            core.stdin.write(json.dumps(config)+'\n');core.stdin.close()
            until=time.monotonic()+15
            while not (root/'stage4-ready.json').exists():
                if core.poll() is not None:raise RuntimeError(core.stderr.read())
                if time.monotonic()>until:raise TimeoutError('App readiness')
                time.sleep(.02)
            ready=h.read(root/'stage4-ready.json')
            record('Stage1 reconciliation before attachment',h.reconcile(root))
        record('single App/VoiceEngine/WakeDetector',all(ready[k]==1 for k in ('app_instances','voice_instances','wake_instances')))
        record('one Store and second App refused before Store',ready['store_instances']==1 and ready['second_app_refused_before_store'])
        record('model paths isolated and source env skipped',ready['model_paths_isolated'] and not ready['source_env_loaded'])
        record('stdin EOF does not terminate TEST Core',core.poll() is None)
        for client in enrolled:
            result=call(client,'attach',{'scopes':enrolled[client]['scopes']})
            tokens[client]=result['token'];record(client+' attaches same identity',result['identity']==ready['identity'])
        record('ordinary shutdown denied',call('teague','shutdown',{'operation':uuid.uuid4().hex}).get('result')=='DENIED')
        wid=call('teague','request',{'text':'what time is it'})['request_id'];original_teague_request=wid
        until=time.monotonic()+5
        while True:
            status=call('teague','request-status',{'request_id':wid})
            if status['done']:break
            if time.monotonic()>until:raise TimeoutError('Request completion')
            time.sleep(.02)
        record('existing real App local-time path',any(e['event']=='run.completed' for e in status['events']))
        lease=call('teague','media',{'purpose':'playback','request_id':wid,'lease_id':None})
        voice=call('teague','voice-synthesize',{'request_id':wid,'lease_id':lease['id']})['request_id']
        record('duplicate speech request reuses same operation',call('teague','voice-synthesize',{'request_id':wid,'lease_id':lease['id']})['request_id']==voice)
        until=time.monotonic()+5
        while True:
            audio=call('teague','voice-status',{'request_id':voice})
            if audio['done']:break
            if time.monotonic()>until:raise TimeoutError('Core synthesis fixture')
            time.sleep(.02)
        record('one existing VoiceEngine deterministic speech path',audio.get('mode')=='SILENT_DETERMINISTIC_CORE_FIXTURE' and len(audio.get('audio',''))>100 and not audio['audibility_verified'])
        record('foreign speech result denied',call('intelligence','voice-status',{'request_id':voice}).get('result')=='DENIED')
        call('teague','stop-playback',{'lease_id':lease['id']})
        record('stopped playback cannot fetch pending audio',call('teague','voice-status',{'request_id':voice}).get('result')=='DENIED')
        record('foreign request read denied',call('intelligence','request-status',{'request_id':wid}).get('result')=='DENIED')
        record('foreign cancellation denied',call('intelligence','cancel',{'request_id':wid}).get('result')=='DENIED')
        a=call('teague','shared');bstate=call('intelligence','shared')
        record('same canonical TEST state',a['data_id']==bstate['data_id']==data_id and a['conversations']==bstate['conversations'])
        # The provider branch uses synthetic personality and an explicit deterministic callback.
        wid=call('intelligence','request',{'text':'STAGE4_TEST explain the fixture'})['request_id']
        until=time.monotonic()+5
        while True:
            status=call('intelligence','request-status',{'request_id':wid})
            if status['done']:break
            if time.monotonic()>until:raise TimeoutError('Deterministic request')
            time.sleep(.02)
        record('deterministic provider path clearly labelled',any(e['event']=='assistant.completed' and 'STAGE4_TEST deterministic' in e['data']['text'] for e in status['events']))
        call('teague','detach');record('other client works after detach',call('intelligence','shared')['data_id']==data_id)
        call('intelligence','detach');record('last ordinary client departure retains Core',core.poll() is None)
        with h.Lock(root,'supervisor.lock'):
            record('replacement coordinator reconciles existing Core',h.reconcile(root))
        old_token=tokens['teague']
        stale=b.client(name,ready['peer'],ready['identity'],key,'teague',bytes.fromhex(enrolled['teague']['key']),
                       {'op':'attach','token':old_token,'args':{'scopes':enrolled['teague']['scopes']}})
        record('historical stale-token attach mechanism reproduced as DENIED',stale.get('result')=='DENIED' and 'token' not in stale)
        record('detached token cannot read shared state',call('teague','shared').get('result')=='DENIED')
        tokens['teague']=call('teague','attach',{'scopes':enrolled['teague']['scopes']})['token']
        record('fresh attach issues new token and same canonical state',tokens['teague']!=old_token and call('teague','shared')['data_id']==data_id)
        record('fresh session cannot inherit previous request authority',call('teague','request-status',{'request_id':original_teague_request}).get('result')=='DENIED')
        record('controller authority survives ordinary reattachment denial',call('controller','lifecycle-status')['state']=='RUNNING')
        if final_case=='failure-cleanup':raise RuntimeError('EXPECTED_FAILURE_BEFORE_LIFECYCLE')
        if final_case=='event-polling':
            import sqlite3
            def assistant_rows():
                with sqlite3.connect((Path(ready['data_root'])/'jarvis.sqlite3').as_uri()+'?mode=ro',uri=True) as db:
                    return db.execute("SELECT count(*) FROM messages WHERE conversation=? AND role='assistant'",('STAGE4_TEST-conversation',)).fetchone()[0]
            for case in ('control','cancel'):
                before=assistant_rows();(root/('polling-'+case+'-arm')).touch()
                wid=call('teague','request',{'text':'STAGE4_TEST explain event polling'})['request_id']
                until=time.monotonic()+3
                while not any(h.read(p).get('case')==case for p in root.glob('*-polling_commit_paused.json')):
                    if time.monotonic()>until:raise TimeoutError('TEST commit barrier missing')
                    time.sleep(.005)
                first=call('teague','request-status',{'request_id':wid})
                record(case+' owner sees active real worker',not first['done'])
                record(case+' foreign event read denied',call('intelligence','request-status',{'request_id':wid}).get('result')=='DENIED')
                record(case+' foreign cancellation denied',call('intelligence','cancel',{'request_id':wid}).get('result')=='DENIED')
                record(case+' commit has not written while paused',assistant_rows()==before)
                if case=='cancel':
                    reply=call('teague','cancel',{'request_id':wid})
                    record('owner cancellation acknowledged before release',reply['result']=='CANCELLATION_REQUESTED')
                    record('cancel signal not represented as completed worker',not call('teague','request-status',{'request_id':wid})['done'])
                (root/('polling-'+case+'-release')).touch()
                until=time.monotonic()+3
                while True:
                    terminal=call('teague','request-status',{'request_id':wid})
                    if terminal['done']:break
                    if time.monotonic()>until:raise TimeoutError('Polling terminal result')
                    time.sleep(.005)
                repeated=call('teague','request-status',{'request_id':wid})
                after=assistant_rows()
                measurements['polling_'+case]={'assistant_rows_before':before,'assistant_rows_after':after,'event_types':[e['event'] for e in terminal['events']],'done':terminal['done'],'terminal_stable':terminal==repeated,'scheduling':'pause before actual Store.message body; no database/event mutation by observer'}
                record(case+' terminal poll deterministic',terminal==repeated)
                if case=='control':record('uncancelled control commits one final answer',after==before+1 and any(e['event']=='assistant.completed' for e in terminal['events']))
                else:record('cancelled request cannot commit late assistant message',after==before)
        if final_case=='deadline':
            wid=call('teague','request',{'text':'STAGE4_TEST uncooperative deadline'})['request_id']
            until=time.monotonic()+5
            while not list(root.glob('*-fixture_provider_wait_started.json')):
                if time.monotonic()>until:raise TimeoutError('Noninterruptible fixture started')
                time.sleep(.02)
            first_stop=uuid.uuid4().hex;started=time.monotonic();call('controller','shutdown',{'operation':first_stop})
            until=time.monotonic()+32
            while True:
                state=call('controller','lifecycle-status')
                if state['state']=='RECOVERY_REQUIRED':break
                if time.monotonic()>until:raise TimeoutError('Bounded shutdown decision')
                time.sleep(.05)
            elapsed=time.monotonic()-started
            measurements['shutdown_to_recovery_seconds']=round(elapsed,6)
            record('real wall-clock deadline reaches recovery within 32 seconds',30<=elapsed<32)
            record('uncooperative work remains unknown/active at deadline',state['active_work']>0 and not state['core_exit_verified'] and not state['budget_refunds_performed'])
            record('new work denied during recovery',call('teague','request',{'text':'what time is it'}).get('result')=='DENIED')
            record('premature owner re-evaluation denied',call('controller','shutdown',{'operation':uuid.uuid4().hex}).get('result')=='DENIED')
            held=False
            try:
                with h.Lock(root,'core.lock'):pass
            except h.Busy:held=True
            record('quarantined Core retains lifetime ownership',held and core.poll() is None)
            until=time.monotonic()+8
            while call('controller','lifecycle-status')['active_work']:
                if time.monotonic()>until:raise TimeoutError('Late worker accounting')
                time.sleep(.05)
            record('late completion does not automatically resume or exit',call('controller','lifecycle-status')['state']=='RECOVERY_REQUIRED' and core.poll() is None)
        elif final_case=='emergency':
            record('ordinary emergency authority denied',call('teague','emergency-stop',{'operation':uuid.uuid4().hex}).get('result')=='DENIED')
            state=call('controller','emergency-stop',{'operation':uuid.uuid4().hex})
            record('owner emergency suspends but does not shut down Core',state['state']=='SUSPENDED' and core.poll() is None)
            record('suspended Core refuses new work',call('teague','request',{'text':'what time is it'}).get('result')=='DENIED')
        if final_case=='controller-expiry':
            prior=tokens['controller']
            (root/'TEST-expire-1').touch()
            record('expired controller STATUS denied',call('controller','lifecycle-status').get('result')=='DENIED')
            result=controller_action(call,tokens,ready['identity'],enrolled['controller']['scopes'],'REAUTH')
            record('explicit REAUTH pins same surviving Core',result['identity']==ready['identity'] and core.poll() is None)
            record('old controller token remains denied',call('controller','lifecycle-status',token=prior).get('result')=='DENIED')
            oldwork=call('controller','request',{'text':'what time is it'})['request_id']
            until=time.monotonic()+3
            while not call('controller','request-status',{'request_id':oldwork})['done']:
                if time.monotonic()>until:raise TimeoutError('TEST controller work')
                time.sleep(.01)
            controller_before=tokens['controller']
            call('controller','emergency-stop',{'operation':uuid.uuid4().hex})
            (root/'TEST-expire-2').touch()
            record('expired suspended controller shutdown denied',call('controller','shutdown',{'operation':uuid.uuid4().hex}).get('result')=='DENIED')
            record('ordinary attach still closed while suspended',call('teague','attach',{'scopes':enrolled['teague']['scopes']}).get('result')=='DENIED')
            record('ordinary client denied recovery enrollment',call('teague','recovery-attach').get('result')=='DENIED')
            result=controller_action(call,tokens,ready['identity'],enrolled['controller']['scopes'],'RECOVER')
            record('fresh lifecycle recovery pins same Core',result['identity']==ready['identity'] and core.poll() is None)
            record('recovery STATUS sees suspension unchanged',controller_action(call,tokens,ready['identity'],enrolled['controller']['scopes'],'STATUS')['state']=='SUSPENDED')
            record('expired predecessor still denied',call('controller','lifecycle-status',token=controller_before).get('result')=='DENIED')
            for op,args in [('request',{'text':'what time is it'}),('request-status',{'request_id':oldwork}),('cancel',{'request_id':oldwork}),('shared',{}),('renew',{}),('emergency-stop',{'operation':uuid.uuid4().hex})]:
                record('recovery scope rejects '+op,call('controller',op,args).get('result')=='DENIED')
            record('recovery attach does not execute/replay repair',not list(root.glob('*-repair_attempt_started.json')))
            # Existing final branch performs the separate authorized shutdown.
        if final_case.startswith('repair-'):
            import sqlite3, budgeted_repair
            fixture=h.read(next(root.glob('*-repair_fixture_ready.json')))
            operation=uuid.uuid4().hex
            body={'action':'run','operation':operation,'project':fixture['project'],'task':fixture['task'],'confirmation':budgeted_repair.CONFIRMATION}
            def row():
                with sqlite3.connect((Path(ready['data_root'])/'jarvis.sqlite3').as_uri()+'?mode=ro',uri=True) as db:
                    db.row_factory=sqlite3.Row
                    return dict(db.execute('SELECT * FROM project_budget_reservations WHERE project=? AND operation=?',(fixture['project'],operation)).fetchone())
            started=call('teague','repair',{'request':body});repair=started['request_id']
            record('repair is explicitly synthetic and not deployed',started['simulated'] and not started['actual_repair_executed'] and not started['deployed'])
            until=time.monotonic()+3
            while not list(root.glob('*-repair_attempt_started.json')):
                status=call('teague','repair',{'request':{'action':'status','request_id':repair}})
                if status['done']:
                    report.append({'case':'repair ended before resource attempt','passed':False,'diagnostic':status['result']})
                    raise AssertionError('Repair ended before first attempt; inspect preserved diagnostic')
                if time.monotonic()>until:raise TimeoutError('Synthetic repair resource started')
                time.sleep(.01)
            record('resource attempts charged before completion',row()['state']=='started' and row()['used_core']==1 and row()['used_container']==1)
            record('same owner duplicate returns same request',call('teague','repair',{'request':body})['request_id']==repair)
            record('foreign repair result denied',call('intelligence','repair',{'request':{'action':'status','request_id':repair}}).get('result')=='DENIED')
            record('foreign repair cancellation denied',call('intelligence','repair',{'request':{'action':'cancel','request_id':repair}}).get('result')=='DENIED')
            record('foreign operation ID does not grant authority',call('intelligence','repair',{'request':body}).get('result')=='DENIED')
            if final_case=='repair-drain':
                measurements['repair_shutdown_started']=time.monotonic()
                call('controller','shutdown',{'operation':uuid.uuid4().hex})
                record('shutdown grace retains active repair',call('controller','lifecycle-status')['state']=='DRAINING' and row()['state']=='started')
            elif final_case=='repair-detach':
                call('teague','detach')
                tokens['teague']=call('teague','attach',{'scopes':enrolled['teague']['scopes']})['token']
                record('reattachment does not inherit repair ownership',call('teague','repair',{'request':{'action':'status','request_id':repair}}).get('result')=='DENIED')
            elif final_case=='repair-emergency':
                call('controller','emergency-stop',{'operation':uuid.uuid4().hex})
                record('emergency cancels repair without Core exit',core.poll() is None)
            else:
                call('teague','repair',{'request':{'action':'cancel','request_id':repair}})
            until=time.monotonic()+(13 if final_case=='repair-drain' else 3)
            while not list(root.glob('*-repair_cleanup_started.json')):
                if time.monotonic()>until:raise TimeoutError('Repair cleanup started')
                time.sleep(.01)
            record('cancellation did not settle or refund active repair',row()['state']=='started' and row()['used_core']==1 and row()['used_container']==1)
            record('cleanup remains registered active work',call('controller','lifecycle-status')['active_work']==1)
            if final_case=='repair-drain':
                measurements['repair_cancellation_after_seconds']=time.monotonic()-measurements.pop('repair_shutdown_started')
                record('repair cancellation follows ten-second grace',10<=measurements['repair_cancellation_after_seconds']<13)
            else:call('controller','shutdown',{'operation':uuid.uuid4().hex})
            record('repair admission closed during drain',call('intelligence','repair',{'request':{**body,'operation':uuid.uuid4().hex}}).get('result')=='DENIED')
            held=False
            try:
                with h.Lock(root,'core.lock'):pass
            except h.Busy:held=True
            record('repair cleanup retains lifetime ownership',held and core.poll() is None)
            (root/'repair-release').touch()
        elif final_case.startswith('inspection-'):
            record('synthetic archive prerequisite verified before request',len(list(root.glob('*-inspection_fixture_ready.json')))==1)
            started=call('teague','inspection-start',{'request':{'panel':'all'}})
            inspection=started['request_id']
            record('inspection is explicitly synthetic without capture',started['capture']=='UNAVAILABLE_SYNTHETIC_ONLY')
            until=time.monotonic()+3
            while not list(root.glob('*-inspection_panel_started.json')):
                if time.monotonic()>until:raise TimeoutError('Inspection started')
                time.sleep(.01)
            record('foreign inspection result denied',call('intelligence','inspection-status',{'request_id':inspection}).get('result')=='DENIED')
            record('foreign inspection cancel denied',call('intelligence','cancel',{'request_id':inspection}).get('result')=='DENIED')
            if final_case=='inspection-detach':
                call('teague','detach')
                tokens['teague']=call('teague','attach',{'scopes':enrolled['teague']['scopes']})['token']
                record('reattachment cannot inherit inspection authority',call('teague','inspection-status',{'request_id':inspection}).get('result')=='DENIED')
            elif final_case=='inspection-emergency':
                call('controller','emergency-stop',{'operation':uuid.uuid4().hex})
                record('emergency retains Core while cancelling inspection',core.poll() is None)
            else:
                call('teague','cancel',{'request_id':inspection})
            until=time.monotonic()+3
            while not list(root.glob('*-inspection_archive_started.json')):
                if time.monotonic()>until:raise TimeoutError('Archive started')
                time.sleep(.01)
            archive_start=h.read(next(root.glob('*-inspection_archive_started.json')))
            record('cancelled inspection still reaches archive with one panel',archive_start['status']=='cancelled' and archive_start['panels']==1)
            if final_case!='inspection-detach':
                job=call('teague','inspection-status',{'request_id':inspection})
                record('archive phase visible but worker not complete',not job['done'] and job['job']['phase']=='archiving')
            record('archive callback counted as active work',call('controller','lifecycle-status')['active_work']==1)
            call('controller','shutdown',{'operation':uuid.uuid4().hex})
            record('new inspection denied during drain',call('intelligence','inspection-start',{'request':{'panel':'all'}}).get('result')=='DENIED')
            record('Core remains alive while archive is held',core.poll() is None and call('controller','lifecycle-status')['active_work']==1)
            held=False
            try:
                with h.Lock(root,'core.lock'):pass
            except h.Busy:held=True
            record('archive drain retains lifetime lock',held)
            (root/'inspection-release').touch()
        else:
            call('controller','shutdown',{'operation':uuid.uuid4().hex})
        core.wait(8);record('authorized drained process exits',core.returncode==0)
        with h.Lock(root,'core.lock'):record('lifetime lock available only after exit',True)
        rows=[]
        for journal in root.glob('STAGE4_TEST-journal-*'):
            rows.extend(runtime.Journal(journal,{'mode':'STAGE4_TEST','data_id':data_id}).inspect())
        record('graceful drain journal contains only terminal records',bool(rows))
        if final_case.startswith('repair-'):
            result=row()
            record('TEST asyncio loop closed before Core exit',len(list(root.glob('*-repair_loop_closed.json')))==1)
            record('known cleanup settles only observed partial usage',result['state']=='settled' and result['outcome']=='failed' and result['used_core']==1 and result['used_container']==1)
            record('terminal journal keeps exact budget reference',any(r['operation']==repair and r['phase']=='FAILED' and r['budget_ref']==fixture['project']+':'+operation for r in rows))
            record('no next check or duplicate resource attempt',len(list(root.glob('*-repair_attempt_started.json')))==1 and len(list(root.glob('*-repair_check_attempt.json')))==1)
            record('cleanup completed before exit',len(list(root.glob('*-repair_cleanup_finished.json')))==1)
        if final_case.startswith('inspection-'):
            archived=h.read(next(root.glob('*-inspection_archive_finished.json')))
            # Use the actual advertised isolated Store root, not source data.
            target=Path(ready['data_root'])/'inspection-archive'/(archived['job_id']+'.md')
            record('actual archive callback completed and file preserved',archived['status']=='archived' and target.is_file())
            import sqlite3
            # Independent read-only verification after Core exit, using the same
            # canonical TEST Store and the real archive/document/project tables.
            with sqlite3.connect((Path(ready['data_root'])/'jarvis.sqlite3').as_uri()+'?mode=ro',uri=True) as db:
                record('one archive record and linked document in canonical TEST state',db.execute(
                    'SELECT count(*) FROM inspection_records i JOIN documents d ON d.id=i.document JOIN workspace_links l ON l.project=i.project AND l.ref=d.id WHERE i.id=?',
                    (archived['job_id'],)).fetchone()[0]==1)
            record('cancelled inspection journal terminal after cleanup',any(r['operation']==inspection and r['phase']=='FAILED' for r in rows))
            record('no second panel or duplicate archive',len(list(root.glob('*-inspection_panel_started.json')))==1 and len(list(root.glob('*-inspection_archive_finished.json')))==1)
        if final_case=='deadline':record('failed original shutdown remains failed in journal',any(r['operation']==first_stop and r['phase']=='FAILED' for r in rows))
    except Exception as exc:
        report.append({'case':'probe failure','passed':False,'error':type(exc).__name__,'detail':str(exc)[:20000]})
        # Use still-held controller authority for one cooperative cleanup attempt.
        # Never force-kill or treat an unresolved drain as successful cleanup.
        if core and core.poll() is None and ready:
            try:
                if not tokens.get('controller'):
                    tokens['controller']=call('controller','attach',{'scopes':enrolled['controller']['scopes']})['token']
                call('controller','shutdown',{'operation':uuid.uuid4().hex});core.wait(8)
                report.append({'case':'authenticated failure cleanup','passed':core.returncode==0})
            except Exception as cleanup_error:
                report.append({'case':'cleanup unresolved; retain TEST ownership','passed':False,'error':type(cleanup_error).__name__})
    finally:
        dest=BASE/('real-app-probe-'+uuid.uuid4().hex+'.json')
        dest.write_text(json.dumps({'cases':report,'root':str(root),'child_pid':core.pid if core else None,
            'child_exit':core.poll() if core else None,'scope':'Real isolated App + authenticated Python TEST clients; not Electron UI or actual voice',
            'production_access':False,'final_case':final_case,'controller_credentials_persisted':False,'measurements':measurements},indent=2));print('EVIDENCE',dest,flush=True)
        if core and core.poll() is None:
            # Never discard the only controller credentials on an unresolved
            # failure. Hold them in this TEST parent; no retry/forced termination.
            # An explicit operator command can request another authorized shutdown.
            print('TEST_CONTROLLER_RETAINED: unresolved TEST Core; commands STATUS, REAUTH, RECOVER or SHUTDOWN',flush=True)
            while core.poll() is None:
                line=sys.stdin.readline().strip()
                if line not in ('STATUS','SHUTDOWN','REAUTH','RECOVER'):
                    time.sleep(1);continue
                try:
                    result=controller_action(call,tokens,ready['identity'],enrolled['controller']['scopes'],line)
                    print('TEST_OPERATOR_RESULT',json.dumps(result),flush=True)
                except Exception as error:print('TEST_OPERATOR_DENIED',type(error).__name__,flush=True)
    if final_case=='failure-cleanup' and core.poll()==0 and any(r.get('detail')=='EXPECTED_FAILURE_BEFORE_LIFECYCLE' for r in report) and any(r['case']=='authenticated failure cleanup' and r['passed'] for r in report):
        print('EXPECTED_FAILURE_CLEANUP_PASS',flush=True);return
    if any(not r['passed'] for r in report):raise AssertionError('Real App probe failed; preserve evidence and inspect live fixture')
    print('real App checks',len(report),'PASS')


def electron_app_probe():
    """Actual Electron entry pages + real synthetic App; never production launchers."""
    import secrets, queue, threading, hashlib
    repo=Path(__file__).resolve().parents[2];sys.path.insert(0,str(repo))
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
    config={'data_id':data_id,'server_key':key.hex(),'endpoint':name,'enrollments':enrolled}
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
        entry=repo/('desktop' if client_id=='teague' else 'intelligence')/'main.cjs'
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
            core=subprocess.Popen([sys.executable,'-I',__file__,'--app-worker',str(root)],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,close_fds=True,creationflags=0x08000000)
            core.stdin.write(json.dumps(config)+'\n');core.stdin.close()
            until=time.monotonic()+15
            while not (root/'stage4-ready.json').exists():
                if core.poll() is not None:raise RuntimeError(core.stderr.read())
                if time.monotonic()>until:raise TimeoutError('TEST App readiness')
                time.sleep(.02)
            ready=h.read(root/'stage4-ready.json');record('Stage1 reconciliation before Electron',h.reconcile(root))
        controller=control('attach',{'scopes':enrolled['controller']['scopes']})['token']
        a=start_client('teague');c=start_client('intelligence')
        record('same authenticated Core identity in both Electron clients',a['ready']['identity']==c['ready']['identity'])
        record('independent TEST profiles',a['ready']['profile']!=c['ready']['profile'] and all(Path(x['ready']['profile']).is_relative_to(root) for x in (a,c)))
        for client in (a,c):
            send(client,'boundaries');checks=receive(client,'boundaries')['result']
            record(client['ready']['client']+' renderer network/invalid request/legacy bridge denied',checks=={'networkDenied':True,'invalidRequestDenied':True,'shutdownExposed':False,'productionBridge':False})
            send(client,'capture');capture=receive(client,'capture')
            if capture.get('failed'):
                report.append({'case':client['ready']['client']+' visual capture',
                               'passed':False,'error':capture.get('error'),
                               'window':capture.get('window')})
            else:
                screenshots.append(capture['file'])
        send(a,'submit',text='what time is it');receive(a,'submitted')
        until=time.monotonic()+8
        while True:
            view=snapshot(a)
            if view['done']=='true':break
            if time.monotonic()>until:raise TimeoutError('Electron request completion')
            time.sleep(.1)
        record('actual Teague form sends request and receives completion',bool(view['request']))
        send(c,'foreign-cancel',request_id=view['request'])
        denied=receive(c,'foreign-cancel')['result']
        record('foreign cancellation through actual renderer denied',denied['denied'])
        send(a,'renew');renewed=receive(a,'renewed')['result']
        record('authenticated renewal strips token before leaving worker',renewed['result']=='RENEWED' and 'token' not in renewed)
        send(a,'shared');statea=receive(a,'shared')['result'];send(c,'shared');statec=receive(c,'shared')['result']
        record('both read same canonical TEST conversations',statea['data_id']==statec['data_id']==data_id and statea['conversations']==statec['conversations'])
        send(a,'close');a['process'].wait(10);record('Teague closes without Core exit',core.poll() is None and a['process'].returncode==0)
        send(c,'submit',text='STAGE4_TEST deterministic check');receive(c,'submitted')
        until=time.monotonic()+8
        while snapshot(c)['done']!='true':
            if time.monotonic()>until:raise TimeoutError('Intelligence request completion')
            time.sleep(.1)
        record('Intelligence remains operational after Teague closes',True)
        send(c,'close');c['process'].wait(10);record('last client closes without Core exit',core.poll() is None and c['process'].returncode==0)
        a2=start_client('teague');record('reopen authenticates same surviving Core',a2['ready']['identity']==a['ready']['identity'])
        record('reopen does not replay old request',snapshot(a2)['request'] is None)
        c2=start_client('intelligence');record('Intelligence reopens on same surviving Core',c2['ready']['identity']==c['ready']['identity'])
        send(c2,'close');c2['process'].wait(10)
        send(a2,'shared');record('Teague still works after Intelligence closes',receive(a2,'shared')['result']['data_id']==data_id)
        c3=start_client('intelligence');send(c3,'crash-renderer');c3['process'].wait(10)
        send(a2,'shared');record('Intelligence renderer crash does not stop Core or Teague',receive(a2,'shared')['result']['data_id']==data_id and core.poll() is None)
        send(a2,'close');a2['process'].wait(10)
        control('shutdown',{'operation':uuid.uuid4().hex});core.wait(8)
        record('separately authorized shutdown drains TEST Core',core.returncode==0)
        with h.Lock(root,'core.lock'):record('Core lifetime lock released after process exit',True)
    except Exception as exc:
        report.append({'case':'Electron probe failure','passed':False,'error':type(exc).__name__,'detail':str(exc)[:5000]})
    finally:
        # Failure cleanup is scoped, cooperative client departure and authenticated
        # TEST lifecycle only. Never force-kill a Core or delete ownership files.
        for client in clients:
            if client['process'].poll() is None:
                try:client['process'].stdin.close();client['process'].wait(10)
                except Exception:pass
        if core and core.poll() is None and controller:
            try:control('shutdown',{'operation':uuid.uuid4().hex});core.wait(8)
            except Exception as exc:report.append({'case':'cleanup unresolved; retain TEST ownership','passed':False,'error':type(exc).__name__})
        dest=BASE/('electron-app-probe-'+uuid.uuid4().hex+'.json')
        dest.write_text(json.dumps({'cases':report,'root':str(root),'core_pid':core.pid if core else None,'core_exit':core.poll() if core else None,
            'clients':[{'launcher_pid':c['process'].pid,'electron_pid':c.get('ready',{}).get('pid'),'exit':c['process'].poll(),'stderr':c['stderr'],'electron_version':c.get('ready',{}).get('electron')} for c in clients],
            'screenshots':screenshots,
            'physical_voice_verified':False,'production_activation':False},indent=2));print('EVIDENCE',dest,flush=True)
    if any(not r['passed'] for r in report):raise AssertionError('Electron probe failed; retain evidence')
    print('Electron checks',len(report),'PASS')


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--worker':worker(Path(sys.argv[2]),*sys.argv[3:])
    elif '--native-probe' in sys.argv:native_probe()
    elif '--bootstrap-probe' in sys.argv:bootstrap_probe()
    elif '--real-app-probe' in sys.argv:real_app_probe()
    elif '--real-app-deadline' in sys.argv:real_app_probe('deadline')
    elif '--real-app-emergency' in sys.argv:real_app_probe('emergency')
    elif '--real-app-failure-cleanup' in sys.argv:real_app_probe('failure-cleanup')
    elif '--real-app-inspection-cleanup' in sys.argv:real_app_probe('inspection-cleanup')
    elif '--real-app-inspection-detach' in sys.argv:real_app_probe('inspection-detach')
    elif '--real-app-inspection-emergency' in sys.argv:real_app_probe('inspection-emergency')
    elif '--real-app-repair-cleanup' in sys.argv:real_app_probe('repair-cleanup')
    elif '--real-app-repair-detach' in sys.argv:real_app_probe('repair-detach')
    elif '--real-app-repair-emergency' in sys.argv:real_app_probe('repair-emergency')
    elif '--real-app-repair-drain' in sys.argv:real_app_probe('repair-drain')
    elif '--real-app-controller-expiry' in sys.argv:real_app_probe('controller-expiry')
    elif '--real-app-event-polling' in sys.argv:real_app_probe('event-polling')
    elif '--electron-app-probe' in sys.argv:electron_app_probe()
    elif '--polling-app-worker' in sys.argv:polling_app_worker(Path(sys.argv[2]),json.loads(sys.stdin.readline()))
    elif '--app-worker' in sys.argv:
        repo=Path(__file__).resolve().parents[2];sys.path.insert(0,str(repo))
        import stage4_runtime
        stage4_runtime.serve(Path(sys.argv[2]),json.loads(sys.stdin.readline()),inspection_setup=bind_inspection_fixture,repair_setup=bind_repair_fixture,expiry_setup=bind_expiry_fixture)
    else:run()
