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


def _native_ready_handoff(line, deadline, start_server):
    if line != 'STAGE4_NATIVE_READY\n':raise ValueError('NATIVE_CLIENT_READINESS')
    if time.monotonic() >= deadline:raise TimeoutError('NATIVE_CLIENT_STARTUP_DEADLINE')
    start_server()


def _run_native_case(command, config, env, start_server):
    """Bound Electron startup separately from the existing short pipe operation."""
    import queue,threading
    import pipe_transport as pt
    started=time.monotonic();deadline=started+12;observed=None;process=None;reader=None
    evidence={'command':command+['--native-ready'],'started':started,'cwd':os.getcwd()}
    try:
        process=subprocess.Popen(evidence['command'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            text=True,env=env,close_fds=True,creationflags=0x08000000)
        lines=queue.Queue()
        reader=threading.Thread(target=lambda:lines.put(process.stdout.readline()),daemon=True);reader.start()
        observed=pt.identity(process.pid);evidence['identity']=observed
        remaining=deadline-time.monotonic()
        if remaining<=0:raise TimeoutError('NATIVE_CLIENT_STARTUP_DEADLINE')
        try:line=lines.get(timeout=remaining)
        except queue.Empty:raise TimeoutError('NATIVE_CLIENT_STARTUP_DEADLINE') from None
        reader.join();evidence['ready_at']=time.monotonic();evidence['ready_line']=line
        _native_ready_handoff(line,deadline,start_server)
        evidence['config_sent_at']=time.monotonic()
        stdout,stderr=process.communicate(json.dumps(config),timeout=max(0,deadline-time.monotonic()))
        evidence.update(completed_at=time.monotonic(),returncode=process.returncode,stdout=stdout,stderr=stderr)
        result=subprocess.CompletedProcess(evidence['command'],process.returncode,stdout,stderr)
        result.native_evidence=evidence
        return result
    except BaseException as exc:
        evidence.update(error=type(exc).__name__,reason=str(exc),traceback=traceback.format_exc())
        try:
            if process and process.poll() is None:
                if observed is None or pt.identity(process.pid)!=observed:raise RuntimeError('NATIVE_CLEANUP_IDENTITY_UNCERTAIN')
                process.terminate();process.wait(timeout=5);evidence['identity_verified_cleanup']=True
            if process:
                stdout,stderr=process.communicate(timeout=5)
                evidence.update(stdout=stdout,stderr=stderr,returncode=process.returncode)
            if reader:reader.join(timeout=5)
        except BaseException as cleanup:
            evidence['cleanup_error']={'error':type(cleanup).__name__,'reason':str(cleanup)}
        path=BASE/('native-startup-failure-'+uuid.uuid4().hex+'.json')
        path.write_text(json.dumps(evidence,indent=2));print('EVIDENCE',path,flush=True)
        raise


def native_probe(cases=None):
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
    cases=cases or ('correct','wrong-pid','wrong-created','wrong-executable','wrong-namespace','missing-bridge','self',
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
                except Exception as exc:server_errors.append({'error':type(exc).__name__,'reason':str(exc),'traceback':traceback.format_exc()})
                finally:pipe.close()
            thread=threading.Thread(target=server)
        config={'nativePath':str(native) if case!='missing-bridge' else str(cache/'missing.node'),
                'endpoint':name if case!='wrong-namespace' else 'PRODUCTION', 'peer':pin,
                'action':'self' if case=='self' else 'exchange'}
        if core_pin:config['core']=core_pin
        if case.startswith('core-'):config['verify']={'core-argument':'argument','core-closed':'closed','core-immutable':'immutable'}.get(case,'normal')
        try:
            def start_server():
                if thread:
                    # Start the existing five-second pipe lifetime only after Electron is ready.
                    pipe.deadline=time.monotonic()+5
                    thread.start()
            p=_run_native_case([str(electron),str(repo/'desktop/test/stage4-client.test.cjs'),'--native-case'],config,env,start_server)
        finally:
            if core_process and core_process.poll() is None:core_process.terminate();core_process.wait(5)
            if pipe and (not thread or thread.ident is None):pipe.close()
        if thread:thread.join(7)
        value=json.loads(p.stdout)
        expected=case in ('correct','self','core-separate','core-immutable')
        passed=p.returncode==0 and value['passed']==expected and (not thread or not thread.is_alive())
        if not expected:passed=passed and not received
        report.append({'case':case,'passed':passed,'child_returncode':p.returncode,'result':value,'received_frames':len(received),'server_errors':server_errors,'client':p.native_evidence})
        # Retain failed development evidence as well as successful cases.
    dest=BASE/('native-probe-'+uuid.uuid4().hex+'.json')
    dest.write_text(json.dumps(report,indent=2));print('EVIDENCE',dest);print('native checks',len(report),'PASS' if all(row['passed'] for row in report) else 'FAIL')
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
        original_finish=context.finish_response;used=set()
        # The caller now opens the response transaction before Store.message.
        # Hold before that transaction, retaining the original cancel-before-write
        # assertion; holding Store inside it instead would test commit-first.
        def finish(run, content, provenance, details=None):
            for case in ('control','cancel'):
                if case not in used and (root/('polling-'+case+'-arm')).exists():
                    used.add(case)
                    h.event(root,'polling_commit_paused',case=case)
                    until=time.monotonic()+5
                    while not (root/('polling-'+case+'-release')).exists():
                        if time.monotonic()>until:raise TimeoutError('TEST commit observation deadline')
                        time.sleep(.005)
                    result=original_finish(run,content,provenance,details)
                    h.event(root,'polling_commit_returned',case=case)
                    return result
            return original_finish(run,content,provenance,details)
        context.finish_response=finish
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
                measurements['polling_'+case]={'assistant_rows_before':before,'assistant_rows_after':after,'event_types':[e['event'] for e in terminal['events']],'done':terminal['done'],'terminal_stable':terminal==repeated,'response_status':terminal['response_status'],'scheduling':'pause before shared response transaction; actual Store INSERT participates; no database/event mutation by observer'}
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



def restart_app_worker(root,configuration):
    repo=Path(__file__).resolve().parents[2];sys.path.insert(0,str(repo))
    import threading
    import stage4_runtime as r
    if configuration.get('TEST_observe_shutdown_denial') is True:
        observe_shutdown_denial(r,root)
    def observe(stage,identity):
        if stage=='claimed' and configuration.get('TEST_crash_stage')=='claimed':
            r.exclusion.event(root,'expected_fixture_crash',stage=stage,identity=r.transport.identity(os.getpid()))
            os._exit(91)
        if stage=='identity':
            r.exclusion.event(root,'restart_transient_observation',identity=identity,ownership=r._context.owners.snapshot(),devices=r._context.app.devices.snapshot())
            def crash_watch():
                marker=root/('TEST-crash-'+identity['startup_epoch']+'.json')
                while True:
                    if marker.exists():
                        command=json.loads(marker.read_text())
                        expected={'identity':identity,'namespace':root.name,'fixture':'EXPLICIT_TEST_CRASH'}
                        if command!=expected or r.transport.identity(os.getpid())!={k:identity[k] for k in ('pid','created','exe_digest')}:
                            r.exclusion.event(root,'crash_request_denied');return
                        r.exclusion.event(root,'expected_fixture_crash',stage='running',identity=identity)
                        os._exit(92)
                    time.sleep(.02)
            threading.Thread(target=crash_watch,daemon=True).start()
    r.serve(root,configuration,start_observer=observe)


def observe_shutdown_denial(r,root):
    """TEST-fixture observer only: delegate unchanged authentication and policy.

    Record no tokens, proofs or enrollment material. A handshake failure never
    reaches Authority.operation and therefore cannot produce a policy receipt.
    """
    original_serve=r.authentication.serve_one
    def serve_observed(pipe,authority,key,behavior):
        peer=pipe.peer(server=True)
        original_operation=authority.operation
        def operation_observed(client,request,selected):
            try:return original_operation(client,request,selected)
            except r.Denied as exc:
                if (client in ('teague','intelligence') and type(request) is dict and
                    request.get('op')=='shutdown' and type(request.get('args')) is dict):
                    operation=request['args'].get('operation');token=request.get('token')
                    if (type(operation) is str and len(operation)==32 and all(c in '0123456789abcdef' for c in operation)
                        and type(token) is str):
                        with authority.context.owners.lock:
                            session=authority.context.owners.sessions.get(hashlib.sha256(token.encode('ascii')).hexdigest())
                            scopes=sorted(session.scopes) if session else None
                        r.exclusion.event(root,'ordinary_shutdown_policy',operation=operation,
                            authenticated_client=client,peer=peer,core_identity=authority.identity,
                            protocol=selected,session_client=session.client if session else None,scopes=scopes,
                            reason=str(exc),policy_reached=any(f.name=='management_capability' for f in traceback.extract_tb(exc.__traceback__)),
                            state=authority.context.owners.state)
                raise
        authority.operation=operation_observed
        try:return original_serve(pipe,authority,key,behavior)
        finally:authority.operation=original_operation
    r.authentication.serve_one=serve_observed


def restart_coordinator_worker(root,configuration):
    repo=Path(__file__).resolve().parents[2];sys.path.insert(0,str(repo))
    import stage4_runtime as r
    profile=configuration.get('TEST_crash_stage')
    def observer(stage):
        if stage==profile:
            r.exclusion.event(root,'expected_coordinator_crash',stage=stage,identity=r.transport.identity(os.getpid()))
            os._exit(93)
    r.serve_test_coordinator(root,configuration,observer)


class RestartCampaign:
    def __init__(self):
        import secrets
        repo=Path(__file__).resolve().parents[2];sys.path.insert(0,str(repo))
        import stage4_runtime as r
        self.r=r;self.secrets=secrets;self.records=[];self.coordinators=[];self.cores=[]
        self.path=BASE/('restart-campaign-'+uuid.uuid4().hex+'.json')
        self.env={k.upper():v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','TEMP','TMP')}
        self.peer=r.transport.identity(os.getpid());self.roots=[]
    def save(self):
        self.path.write_text(json.dumps({'records':self.records,'roots':[str(x) for x in self.roots],
            'production_changed':False,'paid_calls':0,'physical_media':False,'test_only':True},indent=2))
    def check(self,case,ok,**fields):
        self.records.append({'case':case,'passed':bool(ok),**fields});self.save()
        if not ok:raise AssertionError(case)
    def namespace(self):
        r=self.r;root=r.exclusion.BASE/('TEST-STAGE4-'+uuid.uuid4().hex);root.mkdir()
        (root/'TEST_ONLY').write_text('NO PRODUCTION SERVICES')
        data='TEST-'+uuid.uuid4().hex;r.provision(root,data);self.roots.append(root)
        return root,data
    def core_config(self,data,crash=None):
        r=self.r
        config={'data_id':data,'server_key':self.secrets.token_hex(32),'endpoint':'TEAGUE-TEST-'+uuid.uuid4().hex,
            'enrollments':{name:{'enabled':True,'key':self.secrets.token_hex(32),'exe_digest':self.peer['exe_digest'],'protocol':[2,3],
              'scopes':sorted(r.Ownership.ORDINARY|(r.Ownership.MANAGEMENT if name=='controller' else set()))}
              for name in ('teague','intelligence','controller')}}
        if crash:config['TEST_crash_stage']=crash
        return config
    def coordinator(self,root,core,crash=None):
        r=self.r;name=uuid.uuid4().hex
        config={'name':name,'owner':'controller','owner_peer':self.peer,'owner_key':self.secrets.token_hex(32),
                'server_key':self.secrets.token_hex(32),'endpoint':'TEAGUE-TEST-'+uuid.uuid4().hex,'core':core}
        if crash:config['TEST_crash_stage']=crash
        proc=subprocess.Popen(r.test_child_command('--restart-coordinator-worker',root),env=self.env,
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,close_fds=True,creationflags=0x08000000)
        item={'process':proc,'configuration':config,'root':root,'token':None,'ready':None,
              'spawn_peer':None,'attach_started':False,'started':time.monotonic(),
              'readiness_path':root/('coordinator-'+name+'.json'),'read_attempts':0,'wait_polls':0}
        self.coordinators.append(item)
        try:
            item['operation']='record spawned process identity'
            item['spawn_peer']=r.transport.identity(proc.pid)
            item['operation']='send private TEST bootstrap configuration'
            proc.stdin.write(json.dumps(config)+'\n');proc.stdin.close()
            item['ready']=self.coordinator_readiness(item,wait=True)
            self.check('coordinator exact live identity',True,identity=item['ready']['identity'])
            self.coordinator_attach(item)
            return item
        except BaseException as exc:
            item['startup_failure']=self.coordinator_diagnostic(item,exc,'startup')
            self.records.append({'case':'coordinator startup failed','passed':False,**item['startup_failure']});self.save()
            raise
    def coordinator_state(self,item):
        # The existing installed TEST fixture records this same independent pin
        # as initial_peer. Do not derive a trusted pin from readiness-file content.
        item.setdefault('spawn_peer',item.get('initial_peer'))
        item.setdefault('ready',None)
        item.setdefault('attach_started',item.get('token') is not None)
        item.setdefault('started',time.monotonic())
        item.setdefault('read_attempts',0);item.setdefault('wait_polls',0)
        item.setdefault('readiness_path',item['root']/('coordinator-'+item['configuration']['name']+'.json'))
    def coordinator_diagnostic(self,item,exc,phase):
        self.coordinator_state(item)
        # Whitelist metadata: never serialize configuration, credentials or tokens.
        return {'phase':phase,'operation':item.get('operation'),'path':str(item['readiness_path']),
                'pid':item['process'].pid,'spawn_peer':item.get('spawn_peer'),'namespace':item['root'].name,
                'exception':type(exc).__name__,'message':str(exc),'errno':getattr(exc,'errno',None),
                'winerror':getattr(exc,'winerror',None),'traceback':''.join(traceback.format_exception(type(exc),exc,exc.__traceback__)),
                'read_attempts':item['read_attempts'],'wait_polls':item['wait_polls'],
                'elapsed':time.monotonic()-item['started'],'at':time.time()}
    def coordinator_ready_identity(self,item,ready):
        self.coordinator_state(item)
        if type(ready) is not dict or not {'peer','identity','endpoint'}<=ready.keys():
            raise ValueError('Coordinator readiness requires peer, identity and endpoint')
        peer,identity=ready['peer'],ready['identity']
        keys={'pid','created','exe_digest','mode','namespace','installation_id','data_id',
              'core_instance_id','startup_epoch','runtime_build','protocol'}
        if type(peer) is not dict or set(peer)!={'pid','created','exe_digest'} or type(identity) is not dict or not keys<=identity.keys():
            raise ValueError('Coordinator readiness has incomplete peer or identity fields')
        if type(peer['pid']) is not int or type(peer['created']) is not int or type(peer['exe_digest']) is not str:
            raise ValueError('Coordinator readiness has invalid peer types')
        r=self.r;c=item['configuration'];pin=item.get('spawn_peer')
        r.require(pin is not None and peer==pin and r.transport.identity(item['process'].pid)==pin,'COORDINATOR_PROCESS_IDENTITY')
        r.require({k:identity[k] for k in peer}==peer and ready['endpoint']==c['endpoint'] and
                  identity['mode']=='TEST' and identity['namespace']==item['root'].name and identity['data_id']==c['core']['data_id'] and
                  identity['installation_id']==identity['runtime_build']=='STAGE4_TEST_COORDINATOR','COORDINATOR_READY_IDENTITY')
        r.require(type(identity['startup_epoch']) is str and len(identity['startup_epoch'])==32 and
                  identity['startup_epoch']==identity['core_instance_id'],'COORDINATOR_READY_EPOCH')
        uuid.UUID(hex=identity['startup_epoch'])
        r.authentication.negotiate(identity['protocol'],[2,3])
        return ready
    def coordinator_publication(self,item):
        import queue,threading
        if item.get('publication_state')=='COMPLETE':return
        if item.get('publication_error'):raise item['publication_error']
        if 'publication_queue' not in item:
            item['publication_queue']=queue.Queue();item['publication_state']='NOT_BEGUN'
            def receive():
                try:
                    for _ in range(2):
                        line=item['process'].stdout.readline()
                        item['publication_queue'].put(line)
                        if not line:break
                except BaseException as exc:item['publication_queue'].put(exc)
            threading.Thread(target=receive,daemon=True).start()
        until=item['started']+item.get('publication_timeout',8)
        while item['publication_state']!='COMPLETE':
            item['operation']='wait for coordinator publication '+item['publication_state']
            item['wait_polls']+=1
            try:line=item['publication_queue'].get(timeout=max(0,until-time.monotonic()))
            except queue.Empty:raise TimeoutError('Coordinator publication '+item['publication_state']+' deadline') from None
            if isinstance(line,BaseException):raise line
            if not line:raise RuntimeError('Coordinator exited before readiness publication: '+item['publication_state'])
            if not line.startswith('STAGE4_READINESS '):raise ValueError('Invalid publication notification')
            message=json.loads(line[17:])
            if message.get('name')!=item['configuration']['name']:raise ValueError('Stale publication notification')
            state=message.get('state')
            if state=='FAILED':
                item['publication_state']='FAILED';item['publication_failure']=message['error']
                error=RuntimeError('Coordinator publication FAILED: '+json.dumps(message['error']))
                item['publication_error']=error;raise error
            if (item['publication_state'],state) not in (('NOT_BEGUN','PUBLISHING'),('PUBLISHING','COMPLETE')):
                raise ValueError('Invalid publication transition')
            item['publication_state']=state

    def coordinator_readiness(self,item,wait=False):
        path=item['readiness_path']
        self.coordinator_publication(item)
        # Exactly one strict read. No shared sentinel helper and no read-error retry.
        item['read_attempts']+=1;item['operation']='read coordinator readiness UTF-8 file'
        content=path.read_text(encoding='utf8')
        item['operation']='parse coordinator readiness JSON';ready=json.loads(content)
        item['operation']='validate coordinator readiness and live identity'
        return self.coordinator_ready_identity(item,ready)
    def coordinator_attach(self,item):
        item['operation']='authenticate coordinator attachment';item['attach_started']=True
        result=self.cc(item,'attach')
        if type(result) is not dict or result.get('result')!='ATTACHED' or type(result.get('token')) is not str or result.get('identity')!=item['ready']['identity']:
            raise ValueError('Coordinator attachment did not establish a known session')
        item['token']=result['token']
    def cc(self,item,op,args=None,token=None):
        c=item['configuration'];ready=self.coordinator_ready_identity(item,item.get('ready'));r=self.r
        if op=='attach':item['attach_started']=True
        return r.authentication.client(c['endpoint'],ready['peer'],ready['identity'],bytes.fromhex(c['server_key']),
            'controller',bytes.fromhex(c['owner_key']),{'op':op,'token':None if op=='attach' else item['token'] if token is None else token,'args':args or {}})
    def issue(self,item,prior=None,ttl=30):
        grant=self.cc(item,'issue',{'action':'restart' if prior else 'start','prior_epoch':prior['startup_epoch'] if prior else None,'ttl':ttl})
        self.check('explicit start grant issued',grant.get('result')=='ISSUED')
        return grant
    def execute(self,item,grant):return self.cc(item,'execute',{'operation':grant['operation'],'authorization':grant['authorization']})
    def settle(self,item):
        until=time.monotonic()+18
        while True:
            state=self.cc(item,'status')
            if state['result']!='STARTING':return state
            if time.monotonic()>until:raise TimeoutError('Coordinator transaction')
            time.sleep(.03)
    def start(self,root,core,prior=None):
        c=self.coordinator(root,core);g=self.issue(c,prior)
        self.check('authorization durably consumed',self.execute(c,g)['result']=='AUTHORIZATION_CONSUMED')
        state=self.settle(c);self.check('actual TEST Core started',state['result']=='STARTED',state=state)
        self.check('replayed authorization denied',self.execute(c,g).get('result')=='DENIED')
        identity=state['identity'];self.cores.append((root,core,identity))
        ready=self.r.exclusion.read(root/'stage4-ready.json')
        self.check('exactly one App Store VoiceEngine WakeDetector',all(ready[k]==1 for k in ('app_instances','store_instances','voice_instances','wake_instances')))
        return c,identity
    def core_call(self,core,identity,owner,op,args=None,token=None):
        r=self.r
        return r.authentication.client(core['endpoint'],{k:identity[k] for k in ('pid','created','exe_digest')},identity,
            bytes.fromhex(core['server_key']),owner,bytes.fromhex(core['enrollments'][owner]['key']),
            {'op':op,'token':token,'args':args or {}})
    def attach(self,core,identity,owner):
        result=self.core_call(core,identity,owner,'attach',{'scopes':core['enrollments'][owner]['scopes']})
        self.check('fresh client authentication '+owner,result.get('identity')==identity)
        return result['token']
    def stop(self,root,core,identity):
        token=self.attach(core,identity,'controller')
        result=self.core_call(core,identity,'controller','shutdown',{'operation':uuid.uuid4().hex},token)
        self.check('authorized stop acknowledged',result['state'] in ('DRAINING','FINALIZING'))
        self.wait_dead(root,identity)
        self.check('durable stop latch retained',(root/'stop').is_file())
    def wait_dead(self,root,identity):
        r=self.r;until=time.monotonic()+8
        while r.exclusion.process_identity(identity['pid'])=={'pid':identity['pid'],'created':identity['created']}:
            if time.monotonic()>until:raise TimeoutError('TEST Core exit; retained for review')
            time.sleep(.03)
        with r.exclusion.Lock(root,'core.lock'):
            self.check('verified TEST exit and lifetime-lock release',True,identity=identity)
    def cleanup_coordinator_readiness(self,item):
        # Only after this owned child has exited; never remove another instance.
        if item['process'].poll() is None:raise RuntimeError('Readiness cleanup requires exited child')
        path=item['root']/('coordinator-'+item['configuration']['name']+'.json')
        if path.exists():
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            path.unlink()
            self.records[-1]['readiness_artifact_cleanup']={'path':str(path),'sha256':digest,'removed':True}
            self.save()
        if list(item['root'].glob(path.name+'.*.tmp')):
            raise RuntimeError('Coordinator temporary publication artifact retained for review')

    def close(self,item):
        self.coordinator_state(item)
        proc=item['process'];outcome='NOT_ATTEMPTED_IDENTITY_UNESTABLISHED'
        try:
            if proc.poll() is not None:
                ready=item.get('ready')
                self.check('coordinator exit recorded',proc.returncode in (0,93),
                           identity=ready.get('identity') if type(ready) is dict else None,
                           spawn_peer=item.get('spawn_peer'),exit=proc.returncode,cleanup_result='PROCESS_ALREADY_EXITED')
                self.cleanup_coordinator_readiness(item)
                return
            item['operation']='verify spawned coordinator for cleanup'
            self.r.require(item.get('spawn_peer') is not None and self.r.transport.identity(proc.pid)==item['spawn_peer'],'COORDINATOR_CLEANUP_IDENTITY')
            if item.get('ready') is None:
                # Independent, single cleanup-only load. Never resume failed startup.
                item['ready']=self.coordinator_readiness(item)
            else:self.coordinator_ready_identity(item,item['ready'])
            outcome='NOT_ATTEMPTED_SESSION_UNESTABLISHED'
            if item['token'] is None:
                if item['attach_started']:raise RuntimeError('Coordinator attachment outcome unknown; cleanup retained')
                self.coordinator_attach(item)
            outcome='AUTHENTICATED_CLOSE_FAILED';item['operation']='authenticated coordinator close'
            result=self.cc(item,'close')
            self.check('explicit coordinator close',type(result) is dict and result.get('result')=='CLOSED')
            outcome='AUTHENTICATED_CLOSE_ACKNOWLEDGED_EXIT_UNCONFIRMED';item['operation']='wait for authenticated coordinator exit'
            proc.wait(5)
            self.check('coordinator exit recorded',proc.returncode==0,identity=item['ready']['identity'],
                       spawn_peer=item['spawn_peer'],exit=proc.returncode,cleanup_result='AUTHENTICATED_CLOSE_SUCCEEDED')
            self.cleanup_coordinator_readiness(item)
        except BaseException as exc:
            self.records.append({'case':'coordinator cleanup failed','passed':False,'cleanup_result':outcome,
                                 **self.coordinator_diagnostic(item,exc,'cleanup')});self.save()
            raise
    def snapshot(self,root):
        import sqlite3
        path=root/'STAGE4_TEST-data/jarvis.sqlite3'
        with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as db:
            self.check('TEST SQLite integrity',db.execute('PRAGMA quick_check').fetchone()[0]=='ok')
            result={}
            for table, in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
                rows=db.execute('SELECT * FROM "'+table+'"').fetchall()
                encoded=json.dumps(sorted(rows,key=repr),default=lambda x:x.hex() if isinstance(x,bytes) else str(x),sort_keys=True)
                result[table]={'rows':len(rows),'sha256':hashlib.sha256(encoded.encode()).hexdigest()}
        return result
    def smoke(self):
        root,data=self.namespace();core=self.core_config(data);c,identity=self.start(root,core)
        token=self.attach(core,identity,'teague')
        self.check('actual shared TEST state',self.core_call(core,identity,'teague','shared',token=token)['data_id']==data)
        self.stop(root,core,identity);self.close(c)
        before=self.snapshot(root)
        self.check('ordinary stopped namespace rejected',self.r._stop_binding(root) is not None)
        core2=self.core_config(data);c2,new=self.start(root,core2,identity)
        self.check('new epoch and process',new['startup_epoch']!=identity['startup_epoch'] and new['created']!=identity['created'])
        self.check('stale session denied',self.core_call(core2,new,'teague','shared',token=token).get('result')=='DENIED')
        self.attach(core2,new,'teague')
        self.stop(root,core2,new);self.close(c2)
        self.check('all persistent tables unchanged on idle restart',before==self.snapshot(root),before=before,after=self.snapshot(root))
    def denied(self,fn):
        try:return fn().get('result')=='DENIED'
        except (self.r.authentication.Denied,self.r.Denied,OSError,ValueError,KeyError):return True
    def ordinary(self,root,core):
        p=subprocess.Popen(self.r.test_child_command('--restart-app-worker',root),env=self.env,stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,close_fds=True,creationflags=0x08000000)
        stdout,stderr=p.communicate(json.dumps(core)+'\n',timeout=8)
        self.check('actual ordinary startup refuses durable stop',p.returncode!=0 and 'STOP_LATCH' in stderr,exit=p.returncode)
    def events(self,root,kind):
        return [self.r.exclusion.read(x) for x in sorted(root.glob('*-'+kind+'.json'))]
    def seed_records(self,root):
        import sqlite3
        with sqlite3.connect(root/'STAGE4_TEST-data/jarvis.sqlite3') as db:
            db.execute("INSERT INTO items(id,kind,body,created,updated) VALUES ('TEST-memory','memory','Synthetic preserved record',1,1)")
            db.execute("INSERT INTO items(id,kind,body,created,updated) VALUES ('TEST-task','task','Synthetic preserved task',1,1)")
            db.execute("INSERT INTO task_meta(item_id,priority) VALUES ('TEST-task','normal')")
            db.execute("INSERT INTO workspaces VALUES ('TEST-project','Synthetic project')")
            db.execute("INSERT INTO workspace_links VALUES ('TEST-project','task','TEST-task','Synthetic task','')")
            db.execute("INSERT INTO project_budget_limits VALUES ('TEST-project',100,100)")
            db.execute("INSERT INTO project_budget_reservations(project,operation,task,core_requests,container_checks,created,state,started,used_core,used_container,expires,revision,outcome,evidence) VALUES ('TEST-project','TEST-unresolved-resource','TEST-task',2,2,1,'recovery_required',1,1,0,2,1,'unknown','')")
            db.execute("INSERT INTO settings VALUES ('STAGE4_TEST-fixture','preserve')")
            db.execute("INSERT INTO messages(conversation,role,content,created) VALUES ('TEST-preserved','user','Synthetic conversation',1)")
    def fresh_state(self,root,core,identity,old_token=None,old_work=None,old_lease=None):
        observations=[x for x in self.events(root,'restart_transient_observation') if x['identity']==identity]
        self.check('new epoch begins with no sessions work or grants',len(observations)==1 and observations[0]['ownership']['sessions']==0 and observations[0]['ownership']['active_work']==0 and observations[0]['ownership']['media']==[],ownership=observations[0]['ownership'] if observations else None)
        self.check('old client device presence not restored',not any(d['device_id'].startswith('STAGE4_TEST-') for d in observations[0]['devices']))
        if old_token:
            self.check('old epoch session cannot read',self.denied(lambda:self.core_call(core,identity,'teague','shared',token=old_token)))
        a=self.attach(core,identity,'teague');b=self.attach(core,identity,'intelligence')
        av=self.core_call(core,identity,'teague','shared',token=a);bv=self.core_call(core,identity,'intelligence','shared',token=b)
        self.check('both authenticated clients same canonical state',av['data_id']==bv['data_id'] and av['conversations']==bv['conversations'] and av['memory']==bv['memory'])
        if old_work:
            self.check('fresh session cannot inspect old work',self.denied(lambda:self.core_call(core,identity,'teague','request-status',{'request_id':old_work},a)))
            self.check('fresh session cannot cancel old work',self.denied(lambda:self.core_call(core,identity,'teague','cancel',{'request_id':old_work},a)))
        if old_lease:
            self.check('old lease cannot renew',self.denied(lambda:self.core_call(core,identity,'teague','media',{'purpose':'capture','request_id':None,'lease_id':old_lease},a)))
        return a,b
    def authorization_cases(self):
        root,data=self.namespace();core=self.core_config(data);c,prior=self.start(root,core);self.stop(root,core,prior);self.close(c)
        new=self.core_config(data);c=self.coordinator(root,new);c2=self.coordinator(root,new)
        stop=self.r._stop_binding(root);self.ordinary(root,new)
        self.check('ordinary coordinator cannot start stopped Core',self.denied(lambda:self.cc(c,'adopt')))
        self.check('wrong prior epoch denied',self.denied(lambda:self.cc(c,'issue',{'action':'restart','prior_epoch':'wrong','ttl':10})))
        g=self.issue(c,prior)
        self.check('wrong session denied',self.denied(lambda:self.cc(c,'execute',{'operation':g['operation'],'authorization':g['authorization']},token='f'*64)))
        self.check('grant nontransferable between coordinators',self.denied(lambda:self.execute(c2,g)))
        self.check('malformed authorization denied',self.denied(lambda:self.cc(c,'execute',{'operation':g['operation'],'authorization':{'bad':True}})))
        self.check('wrong authorization denied',self.denied(lambda:self.cc(c,'execute',{'operation':g['operation'],'authorization':'f'*64})))
        self.check('unexpected owner fields denied',self.denied(lambda:self.cc(c,'issue',{'action':'restart','prior_epoch':prior['startup_epoch'],'ttl':10,'owner':'other'})))
        expired=self.issue(c,prior,1);time.sleep(1.1)
        self.check('expired authorization denied',self.denied(lambda:self.execute(c,expired)))
        self.check('invalid requests preserve stop and no intent',self.r._stop_binding(root)==stop and not (self.r._start_path(root,g['operation'])/'intent.json').exists())
        self.check('valid grant still consumes once',self.execute(c,g)['result']=='AUTHORIZATION_CONSUMED')
        state=self.settle(c);self.check('valid grant starts new Core',state['result']=='STARTED',state=state)
        self.cores.append((root,new,state['identity']))
        self.check('replay fails after completion',self.denied(lambda:self.execute(c,g)))
        self.stop(root,new,state['identity']);self.close(c);self.close(c2)
    def race_round(self,round_):
        from concurrent.futures import ThreadPoolExecutor
        import threading
        root,data=self.namespace();self.seed_records(root);core=self.core_config(data);c,old=self.start(root,core)
        a=self.attach(core,old,'teague')
        wid=self.core_call(core,old,'teague','request',{'text':'what time is it'},a)['request_id']
        until=time.monotonic()+5
        while not self.core_call(core,old,'teague','request-status',{'request_id':wid},a)['done']:
            if time.monotonic()>until:raise TimeoutError('Seed request')
            time.sleep(.02)
        lease=self.core_call(core,old,'teague','media',{'purpose':'capture','request_id':None,'lease_id':None},a)['id']
        self.stop(root,core,old);self.close(c);before=self.snapshot(root)
        fresh=self.core_config(data);contenders=[self.coordinator(root,fresh) for _ in range(8)]
        grants=[self.issue(x,old) for x in contenders];barrier=threading.Barrier(8)
        def attempt(i):barrier.wait();return self.execute(contenders[i],grants[i])
        with ThreadPoolExecutor(max_workers=8) as pool:results=list(pool.map(attempt,range(8)))
        winners=[i for i,v in enumerate(results) if v.get('result')=='AUTHORIZATION_CONSUMED']
        self.check('one winner among eight actual contenders',len(winners)==1,round=round_,outcomes=[x['result'] for x in results],coordinators=[x['ready']['identity'] for x in contenders])
        winner=contenders[winners[0]];state=self.settle(winner);self.check('winning start verified',state['result']=='STARTED',state=state)
        new=state['identity'];self.cores.append((root,fresh,new))
        self.check('epoch advances retaining data identity',new['startup_epoch']!=old['startup_epoch'] and new['data_id']==old['data_id'])
        self.check('exactly two sequential Core claims',len(self.events(root,'core_acquired'))==2)
        self.check('retained stop marker not removed',(root/'stop').exists())
        self.fresh_state(root,fresh,new,a,wid,lease)
        old_client={**fresh,'enrollments':core['enrollments']}
        self.check('old enrollment credential rejected by new Core',self.denied(lambda:self.core_call(old_client,new,'teague','attach',{'scopes':core['enrollments']['teague']['scopes']})))
        for loser in contenders:
            result=self.cc(loser,'adopt');self.check('contender adopts same surviving Core',result.get('identity')==new)
        self.stop(root,fresh,new)
        for x in contenders:self.close(x)
        self.check('canonical records survive full stop/restart',before==self.snapshot(root),round=round_,before=before,after=self.snapshot(root))
    def fault_case(self,stage,round_=0):
        root,data=self.namespace();core=self.core_config(data);c,old=self.start(root,core);self.stop(root,core,old);self.close(c)
        fresh=self.core_config(data,'claimed' if stage=='claimed' else None)
        c=self.coordinator(root,fresh,stage if stage!='claimed' else None);grant=self.issue(c,old)
        if stage!='claimed':
            try:self.execute(c,grant)
            except (self.r.authentication.Denied,OSError,ValueError,KeyError):pass
            c['process'].wait(6)
            self.check('expected coordinator boundary crash',c['process'].returncode==93,stage=stage,identity=c['ready']['identity'])
            self.close(c)
        else:
            self.execute(c,grant);state=self.settle(c)
            self.check('claimed-before-App crash fails closed',state['result']=='RECOVERY_REQUIRED',state=state)
            self.close(c)
        replacement=self.coordinator(root,fresh)
        if stage=='spawned':
            until=time.monotonic()+8
            spawned=self.events(root,'start_spawned')[-1]['identity']
            while True:
                ready=self.r.exclusion.read(root/'stage4-ready.json')
                if ready and ready['peer']==spawned:break
                if time.monotonic()>until:raise TimeoutError('Surviving Core readiness')
                time.sleep(.02)
            result=self.cc(replacement,'adopt');self.check('replacement adopts surviving unverified Core',result['result']=='ADOPTED' and result['identity']['pid']==spawned['pid'],round=round_,identity=result.get('identity'))
            identity=result['identity'];self.cores.append((root,fresh,identity));self.stop(root,fresh,identity)
            self.check('adoption did not spawn replacement',len(self.events(root,'start_spawned'))==2)
        else:
            self.check('interrupted transaction has no automatic recovery start',self.denied(lambda:self.cc(replacement,'adopt')))
            self.check('old authorization unusable after coordinator death',self.denied(lambda:self.execute(replacement,grant)))
            self.check('durable stop remains',(root/'stop').exists())
            if stage in ('intent','claimed'):
                self.check('unresolved consumed intent blocks new authorization',self.denied(lambda:self.cc(replacement,'issue',{'action':'restart','prior_epoch':old['startup_epoch'],'ttl':10})))
        self.close(replacement)
    def crash_round(self,round_):
        root,data=self.namespace();self.seed_records(root);core=self.core_config(data);c,identity=self.start(root,core)
        a=self.attach(core,identity,'teague')
        lease=self.core_call(core,identity,'teague','media',{'purpose':'capture','request_id':None,'lease_id':None},a)['id']
        before=self.snapshot(root)
        self.check('reverify exact fixture before requested crash',self.r.transport.identity(identity['pid'])=={k:identity[k] for k in ('pid','created','exe_digest')})
        self.r.exclusion.write(root/('TEST-crash-'+identity['startup_epoch']+'.json'),{'identity':identity,'namespace':root.name,'fixture':'EXPLICIT_TEST_CRASH'})
        self.wait_dead(root,identity);self.close(c)
        self.check('crash fixture recorded exact identity',self.events(root,'expected_fixture_crash')[-1]['identity']==identity)
        fresh=self.core_config(data);c,new=self.start(root,fresh,identity)
        self.fresh_state(root,fresh,new,a,old_lease=lease)
        self.check('unexpected crash preserves all canonical records',before==self.snapshot(root),round=round_,before=before,after=self.snapshot(root))
        self.stop(root,fresh,new);self.close(c)
    def unknown(self):
        root,data=self.namespace();core=self.core_config(data);c,identity=self.start(root,core);self.stop(root,core,identity);self.close(c)
        journal=root/('STAGE4_TEST-journal-'+uuid.uuid4().hex);journal.mkdir()
        binding={'mode':'STAGE4_TEST','data_id':data};(journal/'STAGE4_TEST.json').write_text(json.dumps(binding,sort_keys=True))
        self.r.Journal(journal,binding).write(uuid.uuid4().hex,'UNKNOWN',kind='chat')
        c=self.coordinator(root,self.core_config(data))
        self.check('UNKNOWN prior work blocks restart authorization',self.denied(lambda:self.cc(c,'issue',{'action':'restart','prior_epoch':identity['startup_epoch'],'ttl':10})))
        self.check('UNKNOWN history no additional Core owner',len(self.events(root,'core_acquired'))==1)
        self.close(c)
    def full(self):
        self.authorization_cases()
        for i in range(4):self.race_round(i+1)
        for stage in ('before-intent','intent','claimed'):self.fault_case(stage)
        for i in range(3):self.fault_case('spawned',i+1)
        for i in range(3):self.crash_round(i+1)
        self.unknown()

    def run(self,mode):
        try:
            self.smoke()
            if mode!='smoke':self.full()
        except BaseException as exc:
            self.records.append({'case':'campaign failure','passed':False,'error':type(exc).__name__,'traceback':traceback.format_exc()});self.save()
            # Only authenticated graceful cleanup of the exact Core created by
            # this fixture. Unknown/pending-start Core remains for owner review.
            for root,core,identity in self.cores:
                if self.r.exclusion.process_identity(identity['pid'])=={'pid':identity['pid'],'created':identity['created']}:
                    try:self.stop(root,core,identity)
                    except Exception as error:self.records.append({'case':'TEST cleanup retained','passed':False,'identity':identity,'error':str(error)})
            for c in self.coordinators:
                try:self.close(c)
                except Exception as error:self.records.append({'case':'coordinator cleanup retained','passed':False,'pid':c['process'].pid,'error':str(error)})
            self.save();print('EVIDENCE',self.path);raise
        self.save();print('EVIDENCE',self.path);print('Restart checks',len(self.records),'PASS')


class ClientCampaign(RestartCampaign):
    """Actual authenticated Electron adapters, modeled media; no hardware."""
    def __init__(self):
        super().__init__();self.clients=[]
        self.path=BASE/('client-state-media-'+uuid.uuid4().hex+'.json')
        self.electron=Path(__file__).resolve().parents[2]/'desktop/node_modules/electron/dist/electron.exe'
    def electron_config(self,data):
        cfg=self.core_config(data)
        for owner in ('teague','intelligence'):cfg['enrollments'][owner]['exe_digest']=hashlib.sha256(self.electron.read_bytes()).hexdigest()
        return cfg
    def receive(self,client,event,timeout=15):
        import queue
        until=time.monotonic()+timeout
        while time.monotonic()<until:
            try:value=client['queue'].get(timeout=.2)
            except queue.Empty:
                if client['process'].poll() is not None:raise RuntimeError('Electron exit '+str(client['process'].returncode))
                continue
            if value['event']=='denied':raise RuntimeError('Electron driver denied; inspect preserved stderr')
            if value['event']==event:return value
        raise TimeoutError('Electron '+event)
    def send(self,client,action,**args):
        client['process'].stdin.write(json.dumps({'action':action,**args})+'\n');client['process'].stdin.flush()
    def view(self,client):
        self.send(client,'snapshot');return self.receive(client,'snapshot')['result']
    def shared(self,client):
        self.send(client,'shared');return self.receive(client,'shared')['result']
    def shutdown_denial(self,client,core,identity):
        operation=uuid.uuid4().hex
        self.send(client,'shutdown-denial',operation=operation)
        reply=self.receive(client,'shutdown-denial')
        self.check('ordinary Electron transport rejected shutdown',reply=={'event':'shutdown-denial','operation':operation,'rejected':True})
        receipts=[x for x in self.events(client['root'],'ordinary_shutdown_policy') if x.get('operation')==operation]
        self.check('exactly one authenticated shutdown policy receipt',len(receipts)==1,operation=operation)
        receipt=receipts[0];owner=client['ready']['client']
        self.check('shutdown reached authority through actual enrolled Electron',
            receipt['peer']==client['identity'] and receipt['peer']['exe_digest']==core['enrollments'][owner]['exe_digest'] and
            receipt['authenticated_client']==receipt['session_client']==owner and receipt['core_identity']==identity,receipt=receipt)
        self.check('shutdown denied for missing lifecycle authority',receipt['policy_reached'] and receipt['reason']=='SCOPE' and
            set(receipt['scopes'])==self.r.Ownership.ORDINARY and receipt['state']=='RUNNING')
        self.check('ordinary denial leaves Core and client operational',self.shared(client)['data_id']==identity['data_id'] and
            self.r.transport.identity(identity['pid'])=={k:identity[k] for k in ('pid','created','exe_digest')} and
            not (client['root']/'stop').exists())
        return receipt
    def model(self,client,control,**args):
        self.send(client,'modeled-media',control=control,**args);return self.receive(client,'modeled-media')
    def start_client(self,root,core,identity,owner):
        import queue,threading
        repo=Path(__file__).resolve().parents[2];entry=repo/('desktop' if owner=='teague' else 'intelligence')/'main.cjs'
        node=Path(os.environ['USERPROFILE'])/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
        launcher="""const {fork}=require('node:child_process');
const c=fork(process.argv[2],['--stage4-test','--stage4-root='+process.argv[3]],{execPath:process.argv[1],stdio:['ignore','pipe','pipe','ipc'],windowsHide:true});
c.stdout.pipe(process.stdout);c.stderr.pipe(process.stderr);
const lines=require('node:readline').createInterface({input:process.stdin});lines.on('line',line=>c.send(JSON.parse(line)));lines.on('close',()=>{if(c.connected)c.disconnect();});
c.on('exit',code=>process.exit(code===null?1:code));"""
        env={k.upper():v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','TEMP','TMP','USERPROFILE','APPDATA','LOCALAPPDATA','COMSPEC','PATH')}
        stderr=root/(owner+'-'+uuid.uuid4().hex+'-stderr.txt')
        with stderr.open('w') as err:
            process=subprocess.Popen([str(node),'-e',launcher,str(self.electron),str(entry),str(root)],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,close_fds=True,creationflags=0x08000000)
        client={'process':process,'queue':queue.Queue(),'stderr':str(stderr),'root':root};self.clients.append(client)
        def reader():
            for line in process.stdout:
                if line.startswith('STAGE4 '):client['queue'].put(json.loads(line[7:]))
        threading.Thread(target=reader,daemon=True).start()
        peer={k:identity[k] for k in ('pid','created','exe_digest')}
        settings={'clientId':owner,'endpoint':core['endpoint'],'expectedIdentity':{**identity,'created':str(identity['created'])},
                  'pinnedPeer':{**peer,'created':str(peer['created'])},'serverKey':core['server_key'],'clientKey':core['enrollments'][owner]['key'],'driver':True}
        process.stdin.write(json.dumps(settings)+'\n');process.stdin.flush()
        ready=self.receive(client,'ready');client['ready']=ready
        actual=self.r.transport.identity(ready['pid']);client['identity']=actual
        self.check('actual Electron verified identity',actual['exe_digest']==core['enrollments'][owner]['exe_digest'],identity=actual,owner=owner,version=ready['electron'])
        until=time.monotonic()+10
        while self.view(client).get('ready')!='true':
            if time.monotonic()>until:raise TimeoutError('Renderer ready')
            time.sleep(.05)
        self.check('actual renderer attached to target epoch',self.view(client)['connection']=='attached' and ready['identity']['startup_epoch']==identity['startup_epoch'],owner=owner,epoch=identity['startup_epoch'])
        self.check('fresh client has no stale request or media',self.view(client)['request'] is None and self.model(client,'snapshot')['state']['active']==[])
        return client
    def close_client(self,client,crash=False):
        if client['process'].poll() is None:self.send(client,'crash-renderer' if crash else 'close');client['process'].wait(10)
        self.check('Electron controlled client exit',client['process'].returncode==0,identity=client.get('identity'),exit=client['process'].returncode,renderer_crash=crash)
    def same_state(self,a,b,data):
        left=self.shared(a);right=self.shared(b)
        fields=('memory','conversations','projects','tasks')
        self.check('actual clients same canonical records',left['data_id']==right['data_id']==data and all(left[k]==right[k] for k in fields),fields=list(fields),digest=hashlib.sha256(json.dumps({k:left[k] for k in fields},sort_keys=True).encode()).hexdigest())
        self.check('project task and conservative budget visible',len(left['tasks'])==1 and len(left['projects'])==1 and left['projects'][0]['budget']['reserved']=={'core_requests':2,'container_checks':2} and left['projects'][0]['budget']['recovery_required']==['TEST-unresolved-resource'])
        return left
    def client_checks(self):
        root,data=self.namespace();self.seed_records(root);core=self.electron_config(data);c,old=self.start(root,core)
        a=self.start_client(root,core,old,'teague');b=self.start_client(root,core,old,'intelligence')
        state=self.same_state(a,b,data);settings_before=self.snapshot(root)['settings']
        first=self.model(a,'start',purpose='capture');self.check('actual Teague modeled capture begins',not first['error'] and len(first['state']['active'])==1)
        generation=first['state']['active'][0]['generation']
        self.check('Intelligence cannot take active capture',self.model(b,'start',purpose='capture')['error'] is not None)
        self.send(b,'submit',text='what time is it');self.receive(b,'submitted');until=time.monotonic()+8
        while self.view(b)['done']!='true':
            if time.monotonic()>until:raise TimeoutError('Intelligence completion')
            time.sleep(.05)
        wid=self.view(b)['request'];play=self.model(b,'start',purpose='playback',request_id=wid)
        self.check('other client remains operational and owns its playback',play['error'] is None)
        self.send(b,'foreign-cancel',request_id=wid)
        self.check('own request cancel allowed without cancelling other capture',self.receive(b,'foreign-cancel')['result']['denied'] is False and self.model(a,'snapshot')['state']['active'][0]['purpose']=='capture')
        self.model(a,'stop',purpose='capture')
        self.check('capture stop leaves other playback active',self.model(b,'snapshot')['state']['active'][0]['purpose']=='playback')
        self.check('stale capture callback rejected',self.model(a,'callback',purpose='capture',generation=generation)['accepted'] is False)
        self.model(a,'start',purpose='capture');self.model(a,'partition',enabled=True)
        expiry=self.model(a,'advance',ms=11000)
        self.check('local expiry stops without a working Core transport',expiry['state']['active']==[] and any(x.get('reason')=='LEASE_EXPIRED' for x in expiry['trace']))
        self.model(a,'partition',enabled=False);presence_before={d['device_id'] for d in self.shared(b)['presence'] if d['connected']}
        self.close_client(a)
        presence_after={d['device_id'] for d in self.shared(b)['presence'] if d['connected']}
        self.check('disconnect removes only that client presence',len(presence_before-presence_after)==1 and presence_after<presence_before)
        self.model(b,'stop',purpose='playback')
        capture=self.model(b,'start',purpose='capture');self.check('other client capture after revoked owner detach',capture['error'] is None)
        a=self.start_client(root,core,old,'teague')
        self.close_client(b,crash=True)
        self.check('renderer crash does not stop surviving Core or client',self.shared(a)['data_id']==data)
        b=self.start_client(root,core,old,'intelligence');self.same_state(a,b,data)
        for client in (a,b):
            self.send(client,'capture');shot=self.receive(client,'capture');self.check('actual client screenshot captured',not shot.get('failed'),file=shot.get('file'),owner=client['ready']['client'])
            self.close_client(client)
        self.stop(root,core,old);self.close(c);before=self.snapshot(root)
        self.check('local media controls preserve shared settings',settings_before==before['settings'])
        fresh=self.electron_config(data);c2,new=self.start(root,fresh,old)
        self.check('actual client campaign new Core epoch',new['startup_epoch']!=old['startup_epoch'])
        a=self.start_client(root,fresh,new,'teague');b=self.start_client(root,fresh,new,'intelligence');self.same_state(a,b,data)
        grant=self.model(a,'start',purpose='capture');self.check('new epoch explicit capture only',grant['error'] is None)
        token=self.attach(fresh,new,'controller')
        suspended=self.core_call(fresh,new,'controller','emergency-stop',{'operation':uuid.uuid4().hex},token)
        self.check('owner emergency suspends actual Core',suspended['state']=='SUSPENDED')
        self.model(a,'advance',ms=3000);until=time.monotonic()+8
        while self.model(a,'snapshot')['state']['active']:
            if time.monotonic()>until:raise TimeoutError('Emergency modeled media revocation')
            time.sleep(.05)
        self.check('actual adapter stops after emergency revokes Core grant',True)
        for client in (a,b):self.close_client(client)
        stopped=self.core_call(fresh,new,'controller','shutdown',{'operation':uuid.uuid4().hex},token)
        self.check('owner shutdown after emergency acknowledged',stopped['state'] in ('DRAINING','FINALIZING'))
        self.wait_dead(root,new);self.close(c2)
        after=self.snapshot(root);self.check('persistent state including settings and budgets unchanged across Electron restart',before==after,before=before,after=after)
    def run_clients(self):
        try:self.client_checks()
        except BaseException as exc:self.records.append({'case':'actual client campaign failure','passed':False,'error':type(exc).__name__,'traceback':traceback.format_exc()})
        finally:
            for client in self.clients:
                if client['process'].poll() is None:
                    try:client['process'].stdin.close();client['process'].wait(10)
                    except Exception as exc:self.records.append({'case':'client cleanup incomplete','passed':False,'error':type(exc).__name__})
            for root,core,identity in self.cores:
                if self.r.exclusion.process_identity(identity['pid'])=={'pid':identity['pid'],'created':identity['created']}:
                    try:self.stop(root,core,identity)
                    except Exception as exc:self.records.append({'case':'Core cleanup incomplete','passed':False,'error':type(exc).__name__})
            for item in self.coordinators:
                if item['process'].poll() is None:
                    try:self.close(item)
                    except Exception as exc:self.records.append({'case':'coordinator cleanup incomplete','passed':False,'error':type(exc).__name__})
            self.save();print('EVIDENCE',self.path,flush=True)
        failed=sum(not x['passed'] for x in self.records);print('actual client checks',len(self.records),'failures',failed,flush=True)
        if failed:raise AssertionError('Actual client acceptance failure preserved')


def human_lifecycle_acceptance():
    """User-operated console for the already approved TEST lifecycle control."""
    if not sys.stdin.isatty():raise RuntimeError('Human acceptance requires an interactive operator console')
    campaign=ClientCampaign();campaign.path=BASE/('human-lifecycle-'+uuid.uuid4().hex+'.json')
    core=None;identity=None;root=None
    try:
        root,data=campaign.namespace();core=campaign.electron_config(data);core['TEST_observe_shutdown_denial']=True
        coordinator,identity=campaign.start(root,core)
        campaign.close(coordinator)
        token=campaign.attach(core,identity,'controller')
        a=campaign.start_client(root,core,identity,'teague');b=campaign.start_client(root,core,identity,'intelligence')
        print('\nISOLATED STAGE4_TEST ONLY. No microphone, paid provider or production access.')
        print('Target namespace:',root.name,'\nData:',data,'\nEpoch:',identity['startup_epoch'])
        print('Verify BOTH windows visibly say STAGE4_TEST / authenticated. Physical voice is unavailable.')
        selection=input('Type SELECT '+data+' to select this exact TEST identity: ').strip()
        campaign.check('human selected exact TEST identity',selection=='SELECT '+data,operator_input=True,identity=identity)
        def step(command,explanation):
            print(explanation)
            value=input('Type '+command+' (or anything else to stop this session): ').strip()
            campaign.check('human explicit '+command,value==command,operator_input=True,timestamp=time.time())
        step('DENIAL','Check an ordinary TEST client has no Core shutdown authority.')
        campaign.shutdown_denial(a,core,identity)
        campaign.check('human ordinary shutdown denial observed',True);print('Ordinary shutdown: DENIED (authenticated Electron; Core policy SCOPE)')
        step('CRASH','Crash only this disposable Intelligence TEST renderer. Core and Teague must continue.')
        campaign.close_client(b,crash=True)
        status=campaign.core_call(core,identity,'controller','lifecycle-status',token=token)
        campaign.check('human controller reachable after renderer crash',status['state']=='RUNNING' and campaign.shared(a)['data_id']==data)
        print('Controller remains reachable; Core state:',status['state'])
        step('EMERGENCY','Authorize owner emergency stop of this TEST Core only. This suspends admission and retains Core ownership.')
        result=campaign.core_call(core,identity,'controller','emergency-stop',{'operation':uuid.uuid4().hex},token)
        campaign.check('human owner emergency acknowledged',result['state']=='SUSPENDED')
        campaign.check('human emergency retains exact Core',campaign.r.transport.identity(identity['pid'])=={k:identity[k] for k in ('pid','created','exe_digest')})
        print('Emergency state:',result['state'])
        step('SHUTDOWN','Authorize shutdown of this selected TEST Core only. Production is not a target.')
        result=campaign.core_call(core,identity,'controller','shutdown',{'operation':uuid.uuid4().hex},token)
        campaign.check('human owner shutdown acknowledged',result['state'] in ('DRAINING','FINALIZING'))
        campaign.wait_dead(root,identity);campaign.close_client(a)
        campaign.check('human session completed',True,operator_input=True)
    except BaseException as exc:
        campaign.records.append({'case':'human session incomplete','passed':False,'error':type(exc).__name__,'traceback':traceback.format_exc()})
    finally:
        for client in campaign.clients:
            if client['process'].poll() is None:
                try:client['process'].stdin.close();client['process'].wait(10)
                except Exception as exc:campaign.records.append({'case':'human client cleanup incomplete','passed':False,'error':type(exc).__name__})
        if identity and campaign.r.exclusion.process_identity(identity['pid'])=={'pid':identity['pid'],'created':identity['created']}:
            try:campaign.stop(root,core,identity)
            except Exception as exc:campaign.records.append({'case':'human Core cleanup incomplete','passed':False,'error':type(exc).__name__})
        for item in campaign.coordinators:
            if item['process'].poll() is None:
                try:campaign.close(item)
                except Exception as exc:campaign.records.append({'case':'human coordinator cleanup incomplete','passed':False,'error':type(exc).__name__})
        campaign.save();print('Evidence:',campaign.path)
    if any(not x['passed'] for x in campaign.records):raise RuntimeError('Human acceptance incomplete; evidence preserved')
    print('HUMAN TEST LIFECYCLE PASS; all TEST clients and Core exited.')


def human_denial_probe():
    """Automated actual-Electron validation; never supplies human confirmations."""
    campaign=ClientCampaign();campaign.path=BASE/('human-denial-probe-'+uuid.uuid4().hex+'.json')
    root=core=identity=None
    try:
        root,data=campaign.namespace();core=campaign.electron_config(data);core['TEST_observe_shutdown_denial']=True
        coordinator,identity=campaign.start(root,core);campaign.close(coordinator)
        controller=campaign.attach(core,identity,'controller')
        a=campaign.start_client(root,core,identity,'teague');b=campaign.start_client(root,core,identity,'intelligence')
        # Negative control: the old Python/Electron mismatch stays rejected and
        # cannot be mistaken for an authenticated shutdown policy result.
        invalid_operation=uuid.uuid4().hex
        try:campaign.core_call(core,identity,'teague','shutdown',{'operation':invalid_operation})
        except campaign.r.authentication.Denied:handshake_rejected=True
        else:handshake_rejected=False
        campaign.check('Python cannot impersonate Electron enrollment',handshake_rejected)
        campaign.check('handshake rejection produces no shutdown policy receipt',
            not any(x.get('operation')==invalid_operation for x in campaign.events(root,'ordinary_shutdown_policy')))
        for client in (a,b):
            campaign.shutdown_denial(client,core,identity)
            campaign.send(client,'boundaries');boundaries=campaign.receive(client,'boundaries')['result']
            campaign.check('renderer gains no lifecycle or production bridge',boundaries['shutdownExposed'] is False and boundaries['productionBridge'] is False)
        status=campaign.core_call(core,identity,'controller','lifecycle-status',token=controller)
        campaign.check('separate owner controller remains authorized',status['state']=='RUNNING')
        campaign.close_client(b,crash=True)
        campaign.check('controller and Teague survive TEST renderer crash',campaign.shared(a)['data_id']==data and
            campaign.core_call(core,identity,'controller','lifecycle-status',token=controller)['state']=='RUNNING')
        result=campaign.core_call(core,identity,'controller','emergency-stop',{'operation':uuid.uuid4().hex},controller)
        campaign.check('separate owner emergency authority remains intact',result['state']=='SUSPENDED')
        campaign.check('owner emergency retains exact Core identity',campaign.r.transport.identity(identity['pid'])==
            {k:identity[k] for k in ('pid','created','exe_digest')})
        result=campaign.core_call(core,identity,'controller','shutdown',{'operation':uuid.uuid4().hex},controller)
        campaign.check('separate owner shutdown authority remains intact',result['state'] in ('DRAINING','FINALIZING'))
        campaign.wait_dead(root,identity);campaign.close_client(a)
    except BaseException as exc:
        campaign.records.append({'case':'automated human-denial probe incomplete','passed':False,'error':type(exc).__name__,'traceback':traceback.format_exc()})
    finally:
        for client in campaign.clients:
            if client['process'].poll() is None:
                try:client['process'].stdin.close();client['process'].wait(10)
                except Exception as exc:campaign.records.append({'case':'probe client cleanup incomplete','passed':False,'error':type(exc).__name__})
        if identity and campaign.r.exclusion.process_identity(identity['pid'])=={'pid':identity['pid'],'created':identity['created']}:
            try:campaign.stop(root,core,identity)
            except Exception as exc:campaign.records.append({'case':'probe Core cleanup incomplete','passed':False,'error':type(exc).__name__})
        for item in campaign.coordinators:
            if item['process'].poll() is None:
                try:campaign.close(item)
                except Exception as exc:campaign.records.append({'case':'probe coordinator cleanup incomplete','passed':False,'error':type(exc).__name__})
        campaign.records.append({'case':'automated probe is not human acceptance','passed':True,'human_actions_supplied':False})
        campaign.save();print('EVIDENCE',campaign.path)
    if any(not x['passed'] for x in campaign.records):raise RuntimeError('Human denial probe failed; evidence preserved')
    print('Automated human-denial checks',len(campaign.records),'PASS')

if __name__=='__main__':
    if '--human-denial-probe' in sys.argv:human_denial_probe();raise SystemExit(0)
    if '--human-lifecycle' in sys.argv:human_lifecycle_acceptance();raise SystemExit(0)
    if '--client-state-media' in sys.argv:ClientCampaign().run_clients();raise SystemExit(0)
    if '--restart-smoke' in sys.argv:RestartCampaign().run('smoke')
    elif '--restart-campaign' in sys.argv:RestartCampaign().run('full')
    elif len(sys.argv)>1 and sys.argv[1]=='--restart-app-worker':restart_app_worker(Path(sys.argv[2]),json.loads(sys.stdin.readline()))
    elif len(sys.argv)>1 and sys.argv[1]=='--restart-coordinator-worker':restart_coordinator_worker(Path(sys.argv[2]),json.loads(sys.stdin.readline()))
    elif len(sys.argv)>1 and sys.argv[1]=='--worker':worker(Path(sys.argv[2]),*sys.argv[3:])
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
