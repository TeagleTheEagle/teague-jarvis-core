"""Isolated STAGE4_TEST runtime composition; no production startup entry point.

Explicit synthetic provisioning is separate from open-existing App construction.
This module must never read production .env, data, discovery or personality.
"""
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import sqlite3
import sys
import threading
import time
import uuid
import wave

from stage4_sessions import Ownership, Denied, require
from stage4_lifecycle import Journal, Lifecycle

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO/'tests/lifecycle_stage1'))
sys.path.insert(0, str(REPO/'tests/lifecycle_stage2'))
import harness as exclusion
import bootstrap as authentication
import pipe_transport as transport

_context = None
TEST_DB_ID = 0x544934


def validate_root(root):
    root = exclusion.validate(root)
    require(root.name.startswith('TEST-STAGE4-'), 'STAGE4_NAMESPACE')
    return root


def validate_data(root, data_id):
    root = validate_root(root)
    data = root/'STAGE4_TEST-data'
    for p in (data, data/'jarvis.sqlite3', data/'STAGE4_TEST.json', data/'personality.txt'):
        st = p.lstat()
        require(not getattr(st, 'st_file_attributes', 0) & 0x400 and not p.is_symlink(), 'TEST_REPARSE')
    require(json.loads((data/'STAGE4_TEST.json').read_text()) == {'mode':'STAGE4_TEST','data_id':data_id}, 'DATA_IDENTITY')
    with sqlite3.connect((data/'jarvis.sqlite3').as_uri()+'?mode=ro', uri=True) as db:
        require(db.execute('PRAGMA application_id').fetchone()[0] == TEST_DB_ID, 'DATABASE_IDENTITY')
        require(db.execute('PRAGMA user_version').fetchone()[0] == 1, 'DATABASE_SCHEMA')
        require(db.execute('PRAGMA quick_check').fetchone()[0] == 'ok', 'DATABASE_CORRUPT')
    return data


def provision(root, data_id):
    """Synthetic fixture creation only; never migrates or copies production data."""
    root = validate_root(root)
    require(type(data_id) is str and data_id.startswith('TEST-'), 'TEST_DATA_ID')
    data = root/'STAGE4_TEST-data'
    require(not data.exists(), 'EXISTING_DATA_REFUSED')
    data.mkdir()
    (data/'STAGE4_TEST.json').write_text(json.dumps({'mode':'STAGE4_TEST','data_id':data_id},sort_keys=True))
    (data/'personality.txt').write_text('STAGE4_TEST synthetic fixture. Deterministic test responses only.')
    from store import Store
    import workspaces
    store = Store(data)
    workspaces.setup(store)
    with store.connect() as db:
        db.execute('PRAGMA application_id='+str(TEST_DB_ID))
    return validate_data(root, data_id)


def context_for_import():
    require(_context is not None, 'TEST_CONTEXT_REQUIRED')
    _context.check_lock()
    return _context


class Context:
    def __init__(self, root, data_id, lock, enrollments):
        self.root = validate_root(root)
        self.data = validate_data(root, data_id)
        self.data_id = data_id
        self.lock = lock
        self.pid = os.getpid()
        self.claimed = False
        self.app = None
        self.runs = {}
        self.audio_results = {}
        self.voice_requests = {}
        self.voice_leases = {}
        self.provider_router = None  # Trusted offline TEST setup only.
        self.provider_slot = threading.local()
        self.epoch = uuid.uuid4().hex
        self.owners = Ownership(mode='STAGE4_TEST', epoch=self.epoch, enrollments=enrollments)
        ident = {'mode':'STAGE4_TEST','data_id':data_id}
        # Historical journals are recovery evidence, never runnable jobs. Refuse
        # unresolved attempts before constructing any App/Store on a reused root.
        for prior in self.root.glob('STAGE4_TEST-journal-*'):
            Journal(prior, ident).inspect()
        journal_root = self.root/('STAGE4_TEST-journal-'+self.epoch)
        journal_root.mkdir()
        (journal_root/'STAGE4_TEST.json').write_text(json.dumps(ident,sort_keys=True))
        self.lifecycle = Lifecycle(self.owners, Journal(journal_root, ident))

    def check_lock(self):
        require(os.getpid() == self.pid and self.lock.handle is not None, 'LIFETIME_OWNERSHIP')
        try:
            with exclusion.Lock(self.root, 'core.lock'):
                raise Denied('LIFETIME_OWNERSHIP')
        except exclusion.Busy:
            pass

    def claim_app(self, root):
        self.check_lock()
        require(not self.claimed and Path(root).resolve() == self.data, 'ONE_TEST_APP')
        validate_data(self.root, self.data_id)
        self.claimed = True  # Failure stays failed; no fallback second construction.

    def bind_app(self, app):
        require(self.app is None, 'ONE_TEST_APP')
        self.app = app
        app.devices.disconnect('pc')  # Presence must be established by attachment.

    def shared_state(self):
        require(self.app is not None)
        return {'mode':'STAGE4_TEST','data_id':self.data_id,'epoch':self.epoch,
                'memory':self.app.store.items('memory'),
                'conversations':self.app.store.conversations(),
                'voice':'DETERMINISTIC_CORE_AUDIO_ONLY','wake':'UNAVAILABLE_NO_TEST_MODEL',
                'ownership':self.owners.snapshot()}

    def check_tool(self, name, run):
        require(run is not None and getattr(run,'stage4_work',None) in self.owners.work, 'OWNER_REQUIRED')
        self.owners.next_step(run.stage4_work)
        if name not in ('time_now','list_items','read_conversation','search_conversations'):
            raise ValueError('STAGE4_TEST tool is outside the isolated allowlist.')

    def start_request(self, token, text):
        require(type(text) is str and 0 < len(text) <= 12000, 'TEXT')
        import server
        run = server.Run('STAGE4_TEST-conversation')
        ready = threading.Event()
        def work(cancel):
            # Worker may begin before dispatch returns; wait for immutable mapping.
            ready.wait(2)
            if not ready.is_set():return 'UNKNOWN'
            run.cancel = cancel
            if cancel.is_set():return 'FAILED'
            self.app.devices.begin(run.id, 'STAGE4_TEST-'+self.owners.work[run.stage4_work].family)
            self.provider_slot.run = run
            try:
                self.app.work(run, text, None)
                if self.provider_router is not None:
                    provenance = self.provider_router.status(wid)
                    if provenance is None:
                        provenance = {'request_id':wid,'mode':'STAGE4_TEST',
                            'simulated':True,'actual_final_provider':'Core deterministic',
                            'actual_final_model':None,'fallback':False,'attempts':[]}
                    completed = any(e['event']=='assistant.completed' for e in run.events)
                    provenance['response_status'] = 'COMPLETED' if completed else 'FAILED'
                    # Write only in verified synthetic TEST namespace. No schema change.
                    target = self.root/('STAGE4_TEST-response-'+wid+'.json')
                    with target.open('x',encoding='utf-8') as output:
                        json.dump(provenance,output,sort_keys=True)
                    run.emit('response.provenance',provenance)
            finally:
                self.provider_slot.run = None
            return 'FAILED' if any(e['event'] in ('run.failed','run.cancelled') for e in run.events) else 'SUCCEEDED'
        wid = self.lifecycle.dispatch(token, self.epoch, 'chat', work)
        run.stage4_work = wid
        self.runs[wid] = run
        self.app.runs[run.id] = run
        ready.set()
        return {'request_id':wid}


def construct_app(context):
    global _context
    require('server' not in sys.modules and _context is None, 'FRESH_TEST_PROCESS_REQUIRED')
    context.check_lock()
    # Sanitize only this disposable child's environment; never production settings.
    for key in list(os.environ):
        if key.upper() not in ('SYSTEMROOT','WINDIR','TEMP','TMP'):
            os.environ.pop(key, None)
    os.environ['JARVIS_STAGE4_TEST'] = '1'
    os.environ['JARVIS_OLLAMA_SHADOW'] = '0'
    sys.dont_write_bytecode = True
    def isolated_io(event, args):
        def path(value):
            return Path(value).resolve() if isinstance(value,(str,bytes,os.PathLike)) and not isinstance(value,bytes) else None
        if event == 'open':
            target=path(args[0])
            if target:
                require(target.name!='.env' and target!=REPO/'personality.txt' and not target.is_relative_to(REPO/'data'), 'PRODUCTION_FILE_DENIED')
                mode=args[1] or '';flags=args[2] or 0
                writing=any(c in mode for c in 'wax+') or flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)
                require(not writing or target.is_relative_to(context.root), 'TEST_WRITE_BOUNDARY')
        elif event == 'sqlite3.connect':
            expected=context.data/'jarvis.sqlite3'
            target=expected if args[0]==expected.as_uri()+'?mode=ro' else path(args[0])
            require(target is not None and target.is_relative_to(context.root), 'TEST_DATABASE_BOUNDARY')
        elif event in ('socket.connect','subprocess.Popen','os.system'):
            raise Denied('TEST_EXTERNAL_EXECUTION_DENIED')
    sys.addaudithook(isolated_io)  # This disposable process only; no OS settings.
    _context = context
    import server
    def denied(*args, **kwargs):
        raise server.providers.ProviderError('STAGE4_TEST live provider access denied')
    server.providers.request = denied
    server.providers.transcribe = denied
    def chat(messages, tools, callback, cancel, vision=False):
        if context.provider_router is not None:
            from stage4_provider_fallback import Failure
            run = getattr(context.provider_slot,'run',None)
            if run is None:
                raise server.providers.ProviderError('TEST_PROVIDER_REQUEST_OWNER_REQUIRED')
            try:
                return context.provider_router.generate(run.stage4_work,messages,cancel,
                    tool_attempted=any(e['event'].startswith('tool.') for e in run.events),
                    partial_output=any(e['event']=='assistant.delta' for e in run.events),
                    vision=vision,requires_tools=bool(tools))
            except Failure as error:
                raise server.providers.ProviderError(str(error)) from None
        # Fixed synthetic markers exercise cancellation/deadline boundaries only.
        # No model/tool/resource execution or arbitrary client-selected duration.
        last=next((m.get('content','') for m in reversed(messages) if m.get('role')=='user'),'')
        if last == 'STAGE4_TEST cooperative wait':cancel.wait(2)
        if last == 'STAGE4_TEST uncooperative deadline':
            exclusion.event(context.root,'fixture_provider_wait_started')
            time.sleep(33)
        return {'role':'assistant','content':'STAGE4_TEST deterministic response; no live provider used.'}
    server.providers.chat = chat
    def speech(text, profile='auto'):
        output = io.BytesIO()
        with wave.open(output, 'wb') as audio:
            audio.setnchannels(1);audio.setsampwidth(2);audio.setframerate(16000)
            audio.writeframes(b'\0\0'*1600)
        return output.getvalue()  # Explicit silent fixture, never real voice parity.
    server.providers.speech = speech
    counts={'App':0,'VoiceEngine':0,'WakeDetector':0,'Store':0}
    for name in ('VoiceEngine','WakeDetector','Store'):
        original=getattr(server,name)
        def counted(*args,_name=name,_original=original,**kwargs):
            counts[_name]+=1
            return _original(*args,**kwargs)
        setattr(server,name,counted)
    app=server.App(context.data);counts['App']+=1
    context.construction_counts=counts
    # Negative construction must be refused before a second Store is opened.
    try:server.App(context.data)
    except Denied:context.second_app_refused=True
    else:raise Denied('DUPLICATE_APP_NOT_REFUSED')
    return app


class Authority:
    """Stage 2 serve_one authenticates before calling this Core-owned dispatcher."""
    def __init__(self, context, identity, enrollments):
        self.context, self.identity, self.enrollments = context, identity, enrollments

    def active(self):
        self.context.check_lock()
        authentication.validate_identity(self.identity, self.identity)

    def operation(self, client, request, selected):
        authentication.fields(request, ('op','token','args'))
        op, token, args = request['op'], request['token'], request['args']
        require(type(args) is dict and client in self.enrollments, 'REQUEST')
        o = self.context.owners
        if op == 'attach':
            authentication.fields(args, ('scopes',));require(token is None)
            require(type(args['scopes']) is list and all(type(s) is str for s in args['scopes']), 'SCOPES')
            issued = o.attach_verified(client, args['scopes'], selected)
            with o.lock:
                s = o._session(issued, o.epoch)
                self.context.app.devices.register('STAGE4_TEST-'+s.family, {'display'}, ready={'display'}, ttl=900, simulated=True)
            return {'result':'ATTACHED','token':issued,'epoch':o.epoch,'identity':self.identity}
        with o.lock:
            s = o._session(token, o.epoch)
            require(s.client == client and s.protocol == selected, 'CLIENT_BINDING')
        if op == 'renew':
            authentication.fields(args, ())
            issued=o.renew_verified(token,o.epoch,client)
            self.context.app.devices.register('STAGE4_TEST-'+s.family, {'display'}, ready={'display'}, ttl=900, simulated=True)
            return {'result':'RENEWED','token':issued,'epoch':o.epoch}
        if op == 'shared':
            authentication.fields(args, ());require('read' in s.scopes, 'SCOPE')
            return self.context.shared_state()
        if op == 'request':
            authentication.fields(args, ('text',))
            return self.context.start_request(token, args['text'])
        if op == 'request-status':
            authentication.fields(args, ('request_id',));wid=o.check_owner(token,o.epoch,args['request_id'])
            run=self.context.runs[wid]
            return {'done':o.work[wid].done.is_set(),'events':list(run.events)}
        if op == 'cancel':
            authentication.fields(args, ('request_id',))
            return {'result':o.cancel_request(token,o.epoch,args['request_id'])}
        if op == 'media':
            authentication.fields(args, ('purpose','request_id','lease_id'))
            return o.media(token,o.epoch,args['purpose'],request_id=args['request_id'],lease_id=args['lease_id'])
        if op in ('stop-capture','stop-playback'):
            authentication.fields(args, ('lease_id',))
            o.stop_media(token,o.epoch,'capture' if op=='stop-capture' else 'playback',args['lease_id'])
            return {'result':'LEASE_RELEASED','hardware_control_verified':False}
        if op == 'voice-synthesize':
            authentication.fields(args, ('request_id','lease_id'))
            wid=o.check_owner(token,o.epoch,args['request_id'])
            require(o.work[wid].done.is_set(), 'RESPONSE_NOT_READY')
            o.media(token,o.epoch,'playback',request_id=wid,lease_id=args['lease_id'])
            if wid in self.context.voice_requests:
                return {'request_id':self.context.voice_requests[wid]}
            run=self.context.runs[wid]
            completed=[e['data']['text'] for e in run.events if e['event']=='assistant.completed']
            require(bool(completed),'NO_RESPONSE')
            output={}
            def synthesize(cancel):
                if cancel.is_set():return 'FAILED'
                audio=self.context.app.voice_engine.synthesize(completed[-1])
                output.update(audio=base64.b64encode(audio).decode(),mode='SILENT_DETERMINISTIC_CORE_FIXTURE',audibility_verified=False)
                return 'SUCCEEDED'
            voice_id=self.context.lifecycle.dispatch(token,o.epoch,'tts',synthesize)
            self.context.audio_results[voice_id]=output
            self.context.voice_requests[wid]=voice_id
            self.context.voice_leases[voice_id]=(wid,args['lease_id'])
            return {'request_id':voice_id}
        if op == 'voice-status':
            authentication.fields(args, ('request_id',));wid=o.check_owner(token,o.epoch,args['request_id'])
            with o.lock:
                o._expire();lease=o.leases.get('playback')
                require(lease is not None and lease['family']==s.family and
                        self.context.voice_leases.get(wid)==(lease['request'],lease['id']), 'PLAYBACK_LEASE_EXPIRED')
            return {'done':o.work[wid].done.is_set(),**self.context.audio_results.get(wid,{})}
        if op == 'lifecycle-status':
            authentication.fields(args, ());require(bool(s.scopes & o.MANAGEMENT),'SCOPE')
            return self.context.lifecycle.status()
        if op == 'detach':
            authentication.fields(args, ());o.detach(token,o.epoch)
            self.context.app.devices.disconnect('STAGE4_TEST-'+s.family)
            return {'result':'DETACHED','core_stopped':False}
        if op in ('shutdown','emergency-stop'):
            authentication.fields(args, ('operation',))
            cap=o.management_capability(token,o.epoch,op,args['operation'])
            result = self.context.lifecycle.request(token,o.epoch,cap,op,args['operation'])
            try:
                with (self.context.root/'stop').open('a') as f:
                    f.flush();os.fsync(f.fileno())
            except OSError:
                self.context.lifecycle._recovery('STOP_LATCH_PERSISTENCE_FAILED')
                return self.context.lifecycle.status()
            return result
        raise Denied('OPERATION_DENIED')


def serve(root, configuration):
    """Explicit isolated child entry; caller coordinates startup under supervisor.lock.

    No stdin lifetime ownership and no restart loop. Credentials arrive only from
    the trusted disposable test parent and are never written to evidence.
    """
    root=validate_root(root)
    require(not (root/'stop').exists(), 'STOP_LATCH')
    enrollments=configuration['enrollments']
    for entry in enrollments.values():entry['key']=bytes.fromhex(entry['key'])
    key=bytes.fromhex(configuration['server_key'])
    require(len(key)==32 and all(len(e['key'])==32 for e in enrollments.values()), 'TEST_KEYS')
    with exclusion.Lock(root,'core.lock') as lock:
        exclusion.event(root,'core_acquired',identity=exclusion.process_identity(os.getpid()))
        context=Context(root,configuration['data_id'],lock,{k:v['scopes'] for k,v in enrollments.items()})
        app=construct_app(context)
        metadata={**exclusion.process_identity(os.getpid()),'namespace':root.name,'mode':'TEST','epoch':context.epoch}
        exclusion.write(root/'core.json',metadata)
        identity={**transport.identity(os.getpid()),'mode':'TEST','namespace':root.name,
                  'installation_id':'STAGE4_TEST','data_id':context.data_id,'core_instance_id':context.epoch,
                  'startup_epoch':context.epoch,'runtime_build':'STAGE4_TEST-incomplete','protocol':[2,3]}
        authority=Authority(context,identity,enrollments)
        stopping=threading.Event()
        def control_loop():
            answered=object()
            while not stopping.wait(.015):
                try:
                    request=exclusion.read(root/'challenge.json')
                    if request and request.get('challenge') != answered:
                        challenge=request.get('challenge')
                        exclusion.write(root/'response.json',{'identity':metadata,'challenge':challenge})
                        answered=challenge
                    context.lifecycle.tick()
                    with context.owners.lock:
                        families={s.family for s in context.owners.sessions.values()}
                    for device in app.devices.snapshot():
                        if device['device_id'].startswith('STAGE4_TEST-') and device['device_id'][12:] not in families:
                            app.devices.disconnect(device['device_id'])
                except Exception as exc:
                    import traceback
                    exclusion.event(root,'FAILED_CLOSED',error=type(exc).__name__,code=getattr(exc,'errno',None),winerror=getattr(exc,'winerror',None),operation='Stage4 control loop',traceback=traceback.format_exc())
                    context.lifecycle._recovery('CONTROL_LOOP_FAILURE')
        controller=threading.Thread(target=control_loop,daemon=True);controller.start()
        ready=False
        try:
            while context.owners.state!='FINALIZING':
                pipe=transport.listen(configuration['endpoint'])
                try:
                    if not ready:
                        exclusion.write(root/'stage4-ready.json',{'identity':identity,'peer':transport.identity(os.getpid()),
                            'endpoint':configuration['endpoint'],'app_instances':context.construction_counts['App'],
                            'voice_instances':context.construction_counts['VoiceEngine'],'wake_instances':context.construction_counts['WakeDetector'],
                            'store_instances':context.construction_counts['Store'],
                            'second_app_refused_before_store':context.second_app_refused,
                            'data_root':str(app.store.root),'model_paths_isolated':app.wake.directory.is_relative_to(context.data) and app.local_stt.directory.is_relative_to(context.data),
                            'source_env_loaded':False,'live_providers':False})
                        ready=True
                    pipe.io('connect');pipe.deadline=time.monotonic()+5
                    authentication.serve_one(pipe,authority,key,'normal')
                except (Denied, authentication.Denied, OSError, ValueError, TypeError, KeyError):
                    try:pipe.send({'result':'DENIED'})
                    except Exception:pass
                finally:pipe.close()
        finally:
            # Only verified drained state is a graceful exit. Runtime faults while
            # work remains must quarantine instead of releasing lifetime ownership.
            if context.owners.state!='FINALIZING':
                context.lifecycle._recovery('RUNTIME_LISTENER_FAILURE')
                exclusion.event(root,'RECOVERY_REQUIRED')
                while True:time.sleep(1)
            stopping.set();controller.join(2)
            if controller.is_alive():
                context.lifecycle._recovery('CONTROL_THREAD_STILL_ACTIVE')
                while True:time.sleep(1)
            try:context.lifecycle.record_exit_ready()
            except Exception:
                exclusion.event(root,'RECOVERY_REQUIRED',reason='EXIT_READINESS_PERSISTENCE_FAILED')
                while True:time.sleep(1)
            exclusion.event(root,'stage4_drained',work=len(context.owners.work),production=False)
    # No second startup or automatic restart follows process exit.
