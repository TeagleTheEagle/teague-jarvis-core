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


class RepairLoopHost:
    """Trusted TEST bootstrap owns one internal wakeup socket pair.

    No policy override or connection exception is installed. Sequential workers
    borrow the idle loop; their own executor is joined before they finish.
    """
    def __init__(self, *, mode):
        require(mode == 'STAGE4_TEST', 'TEST_ONLY')
        import asyncio
        self.loop = asyncio.new_event_loop()
        self.pid = os.getpid()
        self.lock = threading.Lock()
        self.closed = False
        self.poisoned = False

    def run(self, factory):
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        require(self.pid == os.getpid() and not self.closed and not self.poisoned, 'REPAIR_LOOP_UNAVAILABLE')
        require(self.lock.acquire(False), 'REPAIR_LOOP_BUSY')
        try:
            require(not self.loop.is_running(), 'REPAIR_LOOP_BUSY')
            # Executor shutdown belongs to the tracked worker, including when
            # cancellation or an exception leaves a thread still cleaning up.
            with ThreadPoolExecutor(max_workers=1, thread_name_prefix='STAGE4_TEST-repair') as executor:
                self.loop.set_default_executor(executor)
                try:
                    return self.loop.run_until_complete(factory())
                finally:
                    pending = asyncio.all_tasks(self.loop)
                    if pending:
                        self.poisoned = True
                        for task in pending:task.cancel()
                        self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    self.loop.run_until_complete(self.loop.shutdown_asyncgens())
                    require(not pending, 'REPAIR_UNEXPECTED_PENDING_TASKS')
        except BaseException:
            self.poisoned = True
            raise
        finally:
            self.lock.release()

    def close(self):
        require(self.pid == os.getpid(), 'REPAIR_LOOP_OWNER')
        require(self.lock.acquire(False), 'REPAIR_LOOP_BUSY')
        try:
            if not self.closed:
                require(not self.loop.is_running(), 'REPAIR_LOOP_BUSY')
                self.loop.close()
                self.closed = True
        finally:self.lock.release()


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
        self.inspection_jobs = {}
        self.inspection_runner = None
        self.inspection_finish = None  # Trusted synthetic fixture only; no capture/provider.
        self.repair_fixture = None  # Trusted synthetic outcomes; never a real repair.
        self.repair_requests = {}
        self.repair_results = {}
        self.repair_admission = threading.Lock()
        self.repair_loop = None  # Created only by trusted TEST bootstrap before audit.
        from stage4_response_history import History
        self.response_history = History(self.data/'jarvis.sqlite3')
        self.text_router = None
        self.deep_reviewer = None  # Explicit trusted TEST configuration only.
        self.allow_local_ollama = False  # Set only by trusted TEST parent configuration.
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
        self.response_bindings = {}
        self.response_fault = False
        self.owners.response_cancellations = self.seal_cancelled_responses

    def response_timeout(self):
        accepted=self.lifecycle.accepted_at
        return 1 if accepted is None else min(1,max(0,30-(self.owners.clock()-accepted)))

    def bind_response(self, run, owner, rid, wid):
        with self.owners.lock:
            require(self.owners.work[wid].family==owner.family, 'RESPONSE_OWNER')
            run.stage4_work=wid
            run.response_owner=owner
            run.response_id=rid
            run.response_record=None
            self.runs[wid]=run
            self.app.runs[run.id]=run
            self.response_bindings[wid]=run

    def settle_response(self, run, status, text=None, provenance=None):
        require(not self.response_fault,'RESPONSE_PERSISTENCE_UNCERTAIN')
        owner=run.response_owner
        def valid():
            try:self.owners.next_step(run.stage4_work)
            except Denied:return False
            return True
        final={**(provenance or {}),'run_id':run.id,'work_id':run.stage4_work}
        append=None
        if getattr(run,'request_mode','normal')=='normal' and status=='COMPLETED':
            append=lambda db:self.app.store.message(run.conversation,'assistant',text,transaction=db)
        try:
            record=self.response_history.finish(owner.client,run.response_id,status,text,final,
                session=owner.family,validate=valid if status=='COMPLETED' else None,
                append=append,timeout=self.response_timeout())
        except Exception:
            self.response_fault=True
            self.lifecycle._recovery('RESPONSE_PERSISTENCE_UNCERTAIN')
            raise
        run.response_record=record
        return record

    def publish_response(self, run, record, details=None):
        # Only a durably decided response can produce a response terminal event.
        # Cancellation after a completed commit does not rewrite that decision.
        with run.condition:
            if any(e['event'] in ('run.completed','run.cancelled','run.failed') for e in run.events):
                return 'SUCCEEDED' if record['status']=='COMPLETED' else 'FAILED'
            if record['status']=='COMPLETED':
                run.emit('response.provenance',self.response_history.get(run.response_owner.client,run.response_id))
                run.emit('assistant.completed',{'text':record['text'],'details':details})
                run.emit('run.completed',{})
            else:
                run.emit('run.cancelled' if record['status']=='CANCELLED' else 'run.failed',{'message':'Request cancelled.' if record['status']=='CANCELLED' else 'TEST request failed.'})
        return 'SUCCEEDED' if record['status']=='COMPLETED' else 'FAILED'

    def finish_response(self, run, text, provenance, details=None):
        return self.publish_response(run,self.settle_response(run,'COMPLETED',text,provenance),details)

    def fail_response(self, run, provenance=None):
        return self.publish_response(run,self.settle_response(run,'CANCELLED' if run.cancel.is_set() else 'FAILED',provenance=provenance))

    def seal_cancelled_responses(self):
        require(not self.response_fault,'RESPONSE_PERSISTENCE_UNCERTAIN')
        require(not self.owners.lock._is_owned(),'RESPONSE_LOCK_ORDER')
        # Never invoke SQLite while the global admission/ownership mutex is held.
        with self.owners.lock:
            cancelled=[run for wid,run in self.response_bindings.items() if self.owners.work[wid].cancel.is_set()]
        for run in cancelled:
            if run.response_record is None:
                self.settle_response(run,'CANCELLED')
            if self.owners.work[run.stage4_work].done.is_set():
                self.publish_response(run,run.response_record)

    def response_state(self, wid):
        run=self.response_bindings.get(wid)
        if run is None:return 'NOT_APPLICABLE'
        return self.response_history.status(run.response_owner.client,run.response_id)

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
        require(getattr(run,'request_mode','normal') not in ('text-only','deep-review'), 'TEXT_ONLY_NO_TOOLS')
        self.owners.next_step(run.stage4_work)
        if name not in ('time_now','list_items','read_conversation','search_conversations'):
            raise ValueError('STAGE4_TEST tool is outside the isolated allowlist.')

    def start_request(self, token, text):
        require(type(text) is str and 0 < len(text) <= 12000, 'TEXT')
        import server
        run = server.Run('STAGE4_TEST-conversation')
        with self.owners.lock:
            owner = self.owners._session(token,self.epoch,'request')
        rid,_=self.response_history.reserve(owner.client,owner.family,run.id,text,'normal')
        ready = threading.Event()
        def work(cancel):
            # Worker may begin before dispatch returns; wait for immutable mapping.
            ready.wait(2)
            if not ready.is_set():return 'UNKNOWN'
            run.cancel = cancel
            if cancel.is_set():return 'FAILED'
            self.app.devices.begin(run.id, 'STAGE4_TEST-'+self.owners.work[run.stage4_work].family)
            self.app.work(run, text, None)
            return 'FAILED' if any(e['event'] in ('run.failed','run.cancelled') for e in run.events) else 'SUCCEEDED'
        try:wid = self.lifecycle.dispatch(token, self.epoch, 'chat', work)
        except Exception:
            self.response_history.finish(owner.client,rid,'FAILED',None,{},session=owner.family)
            raise
        self.bind_response(run,owner,rid,wid)
        ready.set()
        return {'request_id':wid,'response_id':rid}

    def start_text_request(self, token, text, operation):
        """Explicit no-tool admission. Never enters App.work or command dispatch."""
        require(type(text) is str and 0<len(text)<=11000,'TEXT')
        require(type(operation) is str and len(operation)==32 and all(c in '0123456789abcdef' for c in operation),'OPERATION')
        require(self.text_router is not None,'TEXT_PROVIDER_UNAVAILABLE')
        import server
        from stage4_provider_fallback import Failure
        with self.owners.lock:
            owner=self.owners._session(token,self.epoch,'request')
            require(self.owners.state=='RUNNING','ADMISSION_CLOSED')
        rid,fresh=self.response_history.reserve(owner.client,owner.family,operation,text,'text-only')
        if not fresh:
            return {'response_id':rid,'duplicate':True,'status':self.response_history.status(owner.client,rid)}
        run=server.Run('STAGE4_TEST-text-only')
        run.request_mode='text-only'
        ready=threading.Event()
        def work(cancel):
            ready.wait(2)
            if not ready.is_set(): return 'UNKNOWN'
            run.cancel=cancel
            try:
                result=self.text_router.generate(rid,[{'role':'system','content':'Text-only TEST response. No tools, browsing, device actions or external actions are available. Do not claim to have performed them.'},{'role':'user','content':text}],cancel,tool_attempted=False,partial_output=False,requires_tools=False)
                return self.finish_response(run,result['content'],self.text_router.status(rid))
            except Exception as error:
                return self.fail_response(run,self.text_router.status(rid) or {})
            finally:
                with run.condition:
                    run.done=True;run.condition.notify_all()
        try:
            wid=self.lifecycle.dispatch(token,self.epoch,'chat',work)
        except Exception:
            self.response_history.finish(owner.client,rid,'FAILED',None,{},session=owner.family)
            raise
        self.bind_response(run,owner,rid,wid)
        ready.set()
        return {'request_id':wid,'response_id':rid,'request_mode':'text-only','simulated':self.text_router.local_simulated,'openai_simulated':True}

    def start_inspection(self, token, request):
        """Register the existing singleton job and archive callback as one worker."""
        from inspection_jobs import JOBS
        from interface_inspection import validate_request
        request = validate_request(request)
        require(self.inspection_runner is not None and self.inspection_finish is not None, 'TEST_INSPECTION_UNAVAILABLE')
        ready = threading.Event()
        mapping = {}
        def work(cancel):
            if not ready.wait(2):
                return 'UNKNOWN'
            wid = mapping['work']
            def registered(key):
                with self.owners.lock:
                    self.inspection_jobs[wid] = key
            try:
                result = JOBS.run_registered(request, self.inspection_runner, on_finish=self.inspection_finish,
                    cancel=cancel, before_step=lambda: self.owners.next_step(wid), registered=registered)
            except ValueError:
                # Busy/invalid job before effects; unexpected worker failures are
                # retained by Lifecycle rather than asserted to be safe cleanup.
                if wid in self.inspection_jobs:
                    raise
                return 'FAILED'
            if result['archive'].get('status') != 'archived':
                return 'UNKNOWN'  # A failed archive may have left partial writes.
            return 'SUCCEEDED' if result['status'] == 'completed' else 'FAILED'
        wid = self.lifecycle.dispatch(token, self.epoch, 'inspection', work)
        mapping['work'] = wid
        ready.set()
        return {'request_id':wid, 'mode':'STAGE4_TEST', 'capture':'UNAVAILABLE_SYNTHETIC_ONLY'}

    def inspection_status(self, token, wid):
        from inspection_jobs import JOBS
        with self.owners.lock:
            self.owners.check_owner(token, self.epoch, wid)
            require(self.owners.work[wid].kind == 'inspection', 'WORK_KIND')
            key = self.inspection_jobs.get(wid)
            done = self.owners.work[wid].done.is_set()
        return {'request_id':wid, 'done':done, 'job':JOBS.get(key) if key else None}

    def repair_dispatch(self, token, body):
        """Owner-bound fixed TEST fixture using the existing reservation runner."""
        import budgeted_repair
        require(type(body) is dict, 'REQUEST')
        with self.owners.lock:
            self.owners._session(token, self.epoch, 'request')
        require(self.repair_fixture is not None, 'TEST_REPAIR_UNAVAILABLE')
        action = body.get('action')
        if action in ('status','cancel'):
            authentication.fields(body, ('action','request_id'))
            wid = self.owners.check_owner(token, self.epoch, body['request_id'])
            require(self.owners.work[wid].kind == 'repair', 'WORK_KIND')
            if action == 'cancel':
                self.owners.cancel_request(token, self.epoch, wid)
            with self.owners.lock:
                return {'request_id':wid, 'done':self.owners.work[wid].done.is_set(),
                        'outcome':self.owners.work[wid].outcome,
                        'cancel_requested':self.owners.work[wid].cancel.is_set(),
                        'result':self.repair_results.get(wid), 'deployed':False}
        require(action == 'run', 'OPERATION_DENIED')
        authentication.fields(body, ('action','operation','project','task','confirmation'))
        operation = body['operation']
        require(type(operation) is str and len(operation)==32 and all(c in '0123456789abcdef' for c in operation), 'OPERATION')
        require(type(body['confirmation']) is str and len(body['confirmation']) <= 100, 'CONFIRMATION')
        confirmation = body['confirmation']
        fixture = self.repair_fixture
        require(body['project']==fixture['project'] and body['task']==fixture['task'], 'TEST_FIXTURE_ONLY')
        # Never hold the ownership/admission mutex during SQLite or journal IO.
        # Concurrent callers get BUSY rather than wait behind a stalled publisher.
        require(self.repair_admission.acquire(blocking=False), 'BUSY')
        try:
            with self.owners.lock:
                self.owners._session(token, self.epoch, 'request')
                require(self.owners.state == 'RUNNING', 'ADMISSION_CLOSED')
                prior = self.repair_requests.get(operation)
                if prior:
                    self.owners.check_owner(token, self.epoch, prior['request_id'])
                    require(prior['confirmation']==body['confirmation'], 'IDEMPOTENCY_CONFLICT')
                    return {'request_id':prior['request_id'], 'duplicate':True, 'deployed':False}
                require(not any(w.kind=='repair' and (not w.done.is_set() or self.lifecycle.workers[w.id].is_alive())
                                for w in self.owners.work.values()), 'BUSY')
            with self.app.store.connect() as db:
                # A historical reservation is not restored execution authority.
                # No ownership inference from a known operation ID after restart.
                require(db.execute('SELECT 1 FROM project_budget_reservations WHERE project=? AND operation=?',
                    (fixture['project'],operation)).fetchone() is None, 'REPLAY_NOT_AUTHORIZED')
                available = budgeted_repair.budgets.snapshot(db,fixture['project'])
                require(available['configured'] and all(available['remaining'][k] >= v
                        for k,v in budgeted_repair.ALLOCATION.items()), 'RESOURCE_LIMIT')
            ready = threading.Event(); mapping = {}
            def work(cancel):
                if not ready.wait(2):return 'UNKNOWN'
                wid = mapping['work']
                def checkpoint():
                    try:self.owners.next_step(wid)
                    except Denied:
                        cancel.set()
                        raise InterruptedError('TEST repair admission closed') from None
                try:
                    require(self.repair_loop is not None, 'REPAIR_LOOP_UNAVAILABLE')
                    result = self.repair_loop.run(lambda: budgeted_repair.run(self.app.store,fixture['responder'],fixture['project'],fixture['task'],
                        operation,confirmation,cancel,fixture['checker'],before_step=checkpoint,test_workflow=fixture['workflow']))
                except Exception as exc:
                    import traceback
                    diagnostic={'error_type':type(exc).__name__, 'errno':getattr(exc,'errno',None),
                        'winerror':getattr(exc,'winerror',None), 'phase':'registered TEST repair worker',
                        'frames':[{'file':f.filename,'line':f.lineno,'function':f.name} for f in traceback.extract_tb(exc.__traceback__)]}
                    with self.owners.lock:
                        self.repair_results[wid]={'status':'UNKNOWN',**diagnostic,'deployed':False,'simulated':True}
                    return 'UNKNOWN'
                with self.owners.lock:
                    self.repair_results[wid]={**result,'simulated':True,'actual_repair_executed':False}
                if result.get('budget_state') == 'recovery_required':return 'UNKNOWN'
                return 'SUCCEEDED' if result['status']=='READY_FOR_REVIEW' else 'FAILED'
            wid = self.lifecycle.dispatch(token,self.epoch,'repair',work,budget_ref=fixture['project']+':'+operation)
            mapping['work'] = wid
            self.repair_requests[operation]={'request_id':wid,'confirmation':confirmation}
            ready.set()
            return {'request_id':wid,'duplicate':False,'deployed':False,'simulated':True,'actual_repair_executed':False}
        finally:
            self.repair_admission.release()


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
            target=expected if args[0] in (expected.as_uri()+'?mode=ro',expected.as_uri()+'?mode=rw') else path(args[0])
            require(target is not None and target.is_relative_to(context.root), 'TEST_DATABASE_BOUNDARY')
        elif event == 'socket.connect':
            from stage4_ollama_transport import permitted
            require(context.allow_local_ollama and permitted(args[1],args[0].family,args[0].type),'TEST_DESTINATION_DENIED')
        elif event in ('socket.getaddrinfo','socket.gethostbyname','socket.sendto','subprocess.Popen','os.system'):
            raise Denied('TEST_EXTERNAL_EXECUTION_DENIED')
    sys.addaudithook(isolated_io)  # This disposable process only; no OS settings.
    _context = context
    import server
    def denied(*args, **kwargs):
        raise server.providers.ProviderError('STAGE4_TEST live provider access denied')
    server.providers.request = denied
    server.providers.transcribe = denied
    def chat(messages, tools, callback, cancel, vision=False):
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
        try:
            return self._operation(client,request,selected)
        finally:
            # Expiry detected during authentication also revokes pending responses.
            # No successful RPC can leave a signalled response unsealed.
            self.context.owners.flush_response_cancellations()

    def _operation(self, client, request, selected):
        # Restart admission opens only after the coordinator has independently
        # reconciled the lifetime owner and authenticated the new pipe identity.
        restart = getattr(self.context, 'restart_transaction', None)
        if restart is not None:
            verified = _start_read(self.context.root, restart, 'verified')
            require(verified['identity'] == self.identity, 'START_NOT_VERIFIED')
        authentication.fields(request, ('op','token','args'))
        op, token, args = request['op'], request['token'], request['args']
        require(type(args) is dict and client in self.enrollments, 'REQUEST')
        o = self.context.owners
        if op == 'recovery-attach':
            authentication.fields(args, ());require(token is None)
            issued=o.recover_verified(client,selected)
            return {'result':'RECOVERY_ATTACHED','token':issued,'epoch':o.epoch,'identity':self.identity}
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
            if s.recovery:
                require(op in ('lifecycle-status','shutdown','detach'), 'RECOVERY_SCOPE')
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
        if op == 'request-text-only':
            authentication.fields(args, ('text','operation'))
            return self.context.start_text_request(token,args['text'],args['operation'])
        if op == 'inspection-start':
            authentication.fields(args, ('request',))
            return self.context.start_inspection(token, args['request'])
        if op == 'inspection-status':
            authentication.fields(args, ('request_id',))
            return self.context.inspection_status(token, args['request_id'])
        if op == 'repair':
            authentication.fields(args, ('request',))
            import budgeted_repair
            return budgeted_repair.dispatch(self.context.app,None,args['request'],stage4_token=token)
        if op == 'deep-review':
            authentication.fields(args, ('review',))
            from stage4_deep_review import admit
            return admit(self.context,token,args['review'])
        if op == 'response-provider':
            authentication.fields(args, ('response_id',));require('read' in s.scopes,'SCOPE')
            from stage4_response_history import describe
            record=self.context.response_history.get(s.client,args['response_id'])
            return {'provenance':record,'answer':describe(record)}
        if op == 'last-response-provider':
            authentication.fields(args, ());require('read' in s.scopes,'SCOPE')
            from stage4_response_history import describe
            record=self.context.response_history.last(s.client)
            return {'provenance':record,'answer':describe(record)}
        if op == 'request-status':
            authentication.fields(args, ('request_id',));wid=o.check_owner(token,o.epoch,args['request_id'])
            run=self.context.runs[wid]
            self.context.seal_cancelled_responses()
            return {'done':o.work[wid].done.is_set(),'events':list(run.events),
                    'response_status':self.context.response_state(wid),'worker_outcome':o.work[wid].outcome}
        if op == 'cancel':
            authentication.fields(args, ('request_id',))
            result=o.cancel_request(token,o.epoch,args['request_id'])
            return {'result':result,'response_status':self.context.response_state(args['request_id'])}
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


def serve(root, configuration, *, inspection_setup=None, repair_setup=None, expiry_setup=None, start_observer=None):
    """Explicit isolated child entry; caller coordinates startup under supervisor.lock.

    No stdin lifetime ownership and no restart loop. Credentials arrive only from
    the trusted disposable test parent and are never written to evidence.
    """
    root=validate_root(root)
    restart = configuration.get('start_transaction')
    if restart is None:
        require(not (root/'stop').exists(), 'STOP_LATCH')
    enrollments=configuration['enrollments']
    for entry in enrollments.values():entry['key']=bytes.fromhex(entry['key'])
    key=bytes.fromhex(configuration['server_key'])
    require(len(key)==32 and all(len(e['key'])==32 for e in enrollments.values()), 'TEST_KEYS')
    with exclusion.Lock(root,'core.lock') as lock:
        exclusion.event(root,'core_acquired',identity=exclusion.process_identity(os.getpid()))
        if restart is not None:
            _claim_test_start(root, configuration)
            if start_observer:start_observer('claimed', None)
        context=Context(root,configuration['data_id'],lock,{k:v['scopes'] for k,v in enrollments.items()})
        if restart is not None:context.restart_transaction=restart
        from stage4_provider_fallback import offline_router
        context.text_router=offline_router(configuration.get('text_provider_scenario','openai'))
        if configuration.get('deep_review_fixture') is True:
            from stage4_deep_review import Engine, fixture_transport
            context.deep_reviewer=Engine(fixture_transport,mode='STAGE4_TEST',simulated=True)
        if configuration.get('real_local_ollama') is True:
            from stage4_ollama_transport import real_router
            context.allow_local_ollama=True
            context.text_router=real_router()
        if configuration.get('repair_fixture') is True:
            require(repair_setup is not None, 'TRUSTED_REPAIR_FIXTURE_REQUIRED')
            # This fixed runtime resource is created before the permanent audit
            # hook. No request callback or provider code runs during bootstrap.
            context.repair_loop = RepairLoopHost(mode='STAGE4_TEST')
        app=construct_app(context)
        if configuration.get('controller_expiry_fixture') is True:
            require(expiry_setup is not None, 'TRUSTED_EXPIRY_FIXTURE_REQUIRED')
            expiry_setup(context)
        if configuration.get('inspection_fixture') is True:
            require(inspection_setup is not None, 'TRUSTED_INSPECTION_FIXTURE_REQUIRED')
            inspection_setup(context)
        if configuration.get('repair_fixture') is True:
            require(repair_setup is not None, 'TRUSTED_REPAIR_FIXTURE_REQUIRED')
            repair_setup(context)
        metadata={**exclusion.process_identity(os.getpid()),'namespace':root.name,'mode':'TEST','epoch':context.epoch}
        exclusion.write(root/'core.json',metadata)
        identity={**transport.identity(os.getpid()),'mode':'TEST','namespace':root.name,
                  'installation_id':'STAGE4_TEST','data_id':context.data_id,'core_instance_id':context.epoch,
                  'startup_epoch':context.epoch,'runtime_build':'STAGE4_TEST-incomplete','protocol':[2,3]}
        if start_observer:start_observer('identity', identity)
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
            if context.repair_loop is not None:
                close_errors=[]
                def close_repair_loop():
                    try:context.repair_loop.close()
                    except BaseException as exc:close_errors.append(type(exc).__name__)
                closer=threading.Thread(target=close_repair_loop,daemon=True)
                closer.start()
                remaining=max(0,30-(context.owners.clock()-context.lifecycle.accepted_at))
                closer.join(min(2,remaining))
                if closer.is_alive() or close_errors or not context.repair_loop.closed:
                    context.lifecycle._recovery('REPAIR_LOOP_CLEANUP_UNCERTAIN')
                    exclusion.event(root,'RECOVERY_REQUIRED',reason='REPAIR_LOOP_CLEANUP_UNCERTAIN')
                    while True:time.sleep(1)
                exclusion.event(root,'repair_loop_closed')
            try:context.lifecycle.record_exit_ready()
            except Exception:
                exclusion.event(root,'RECOVERY_REQUIRED',reason='EXIT_READINESS_PERSISTENCE_FAILED')
                while True:time.sleep(1)
            exclusion.event(root,'stage4_drained',work=len(context.owners.work),production=False)
    # No second startup or automatic restart follows process exit.

# Explicit TEST coordinator. No App/Store/provider/voice construction here.
def _start_path(root, operation):
    root=validate_root(root)
    require(type(operation) is str and len(operation)==32 and all(c in '0123456789abcdef' for c in operation), 'START_OPERATION')
    parent=root/'STAGE4_TEST-starts'
    for p in (parent, parent/operation):
        if p.exists():
            st=p.lstat();require(p.is_dir() and not getattr(st,'st_file_attributes',0)&0x400 and not p.is_symlink(),'START_REPARSE')
    return parent/operation


def _start_read(root, operation, name):
    require(name in ('grant','intent','claimed','verified'), 'START_RECORD')
    path=_start_path(root,operation)/(name+'.json')
    st=path.lstat();require(not getattr(st,'st_file_attributes',0)&0x400 and not path.is_symlink() and st.st_size<=16384,'START_RECORD_PATH')
    return json.loads(path.read_text(encoding='utf8'))


def _start_write(root, operation, name, record):
    require(name in ('grant','intent','claimed','verified'), 'START_RECORD')
    target=_start_path(root,operation)
    target.mkdir(parents=True,exist_ok=True)
    _start_path(root,operation)
    # Immutable, exclusive, fsynced records. A partial record is never removed,
    # overwritten or interpreted as authorization to retry a launch.
    with (target/(name+'.json')).open('x',encoding='utf8') as stream:
        json.dump(record,stream,sort_keys=True);stream.flush();os.fsync(stream.fileno())


def _start_digest(value):
    return hashlib.sha256(authentication.canonical(value)).hexdigest()


def _stop_binding(root):
    stop=root/'stop'
    if not stop.exists():return None
    st=stop.lstat()
    require(not getattr(st,'st_file_attributes',0)&0x400 and not stop.is_symlink() and stop.is_file(),'STOP_PATH')
    return {'sha256':hashlib.sha256(stop.read_bytes()).hexdigest(),'size':st.st_size,'mtime_ns':st.st_mtime_ns}


def _old_core(root):
    path=root/'core.json'
    if not path.exists():return None
    metadata=exclusion.read(path)
    require(type(metadata) is dict and metadata.get('namespace')==root.name and metadata.get('mode')=='TEST','CORE_METADATA')
    require(set(metadata)=={'pid','created','namespace','mode','epoch'},'CORE_METADATA_SCHEMA')
    return metadata


def _start_history(root,data_id):
    validate_data(root,data_id)
    for prior in root.glob('STAGE4_TEST-journal-*'):
        Journal(prior,{'mode':'STAGE4_TEST','data_id':data_id}).inspect()
    starts=root/'STAGE4_TEST-starts'
    if starts.exists():
        paths=list(starts.iterdir());require(len(paths)<=1024,'START_RECORD_LIMIT')
        for path in paths:
            _start_path(root,path.name)
            if (path/'intent.json').exists():
                intent=_start_read(root,path.name,'intent')
                require((path/'verified.json').exists(),'RECOVERY_REQUIRED')
                verified=_start_read(root,path.name,'verified')
                claimed=_start_read(root,path.name,'claimed')
                require(verified['operation']==intent['operation']==path.name and
                        {k:verified['identity'][k] for k in ('pid','created','exe_digest')}==claimed['peer'], 'START_HISTORY')


def _claim_test_start(root,configuration):
    import hmac
    operation=configuration['start_transaction']
    intent=_start_read(root,operation,'intent')
    require(intent['data_id']==configuration['data_id'] and intent['namespace']==root.name,'START_IDENTITY')
    require(time.time()<intent['launch_expires'],'START_EXPIRED')
    require(_stop_binding(root)==intent['stop'] and _old_core(root)==intent['prior'],'START_PRIOR_STATE')
    nonce=configuration.get('launch_nonce')
    require(type(nonce) is str and hmac.compare_digest(hashlib.sha256(nonce.encode()).hexdigest(),intent['launch_digest']),'START_LAUNCH_AUTHORITY')
    base={k:v for k,v in configuration.items() if k not in ('start_transaction','launch_nonce')}
    require(_start_digest(base)==intent['configuration_digest'],'START_CONFIGURATION')
    _start_write(root,operation,'claimed',{'operation':operation,'peer':transport.identity(os.getpid()),'at':time.time()})


class TestRestartCoordinator:
    """One native TEST controller session; Stage 2 authenticates its exact peer.

    All mutable authority is private to this coordinator instance. Durable
    records carry hashes, never reusable grant tokens. Adoption can complete a
    consumed transaction for an existing owner, but cannot spawn its replacement.
    """
    def __init__(self,root,configuration,observer=None):
        self.root=validate_root(root);self.configuration=configuration;self.observer=observer
        self.data_id=configuration['core']['data_id'];validate_data(self.root,self.data_id)
        self.peer=transport.identity(os.getpid());self.instance=uuid.uuid4().hex
        self.identity={**self.peer,'mode':'TEST','namespace':self.root.name,
                       'installation_id':'STAGE4_TEST_COORDINATOR','data_id':self.data_id,
                       'core_instance_id':self.instance,'startup_epoch':self.instance,
                       'runtime_build':'STAGE4_TEST_COORDINATOR','protocol':[2,3]}
        self.enrollments={configuration['owner']:{'enabled':True,'key':bytes.fromhex(configuration['owner_key']),
            'exe_digest':configuration['owner_peer']['exe_digest'],'protocol':[2,3]}}
        self.session=None;self.grants={};self.thread=None;self.closed=False;self.result={'result':'IDLE'}

    def active(self):
        authentication.validate_identity(self.identity,self.identity)

    def checkpoint(self,stage):
        if self.observer:self.observer(stage)

    def _absent(self):
        with exclusion.Lock(self.root,'core.lock'):pass
        old=_old_core(self.root)
        if old:
            try:peer=transport.identity(old['pid'])
            except transport.Rejected as exc:
                require(str(exc)=='PROCESS_DEAD','PROCESS_UNCERTAIN');peer=None
            except OSError as exc:
                require(exc.errno in (87,1168),'PROCESS_UNCERTAIN');peer=None
            require(peer is None or peer['created']!=old['created'],'CORE_EXIT_UNCONFIRMED')
        return old

    def _session(self,client,token):
        require(client==self.configuration['owner'] and self.session is not None,'COORDINATOR_OWNER')
        require(type(token) is str and authentication.digest(token)==self.session['digest'] and
                time.monotonic()<self.session['expires'],'COORDINATOR_SESSION')

    def operation(self,client,request,selected):
        import secrets,hmac
        authentication.fields(request,('op','token','args'))
        op,token,args=request['op'],request['token'],request['args']
        require(type(args) is dict and client==self.configuration['owner'],'COORDINATOR_OWNER')
        if op=='attach':
            authentication.fields(args,());require(token is None and self.session is None,'COORDINATOR_ATTACH')
            token=secrets.token_hex(32);self.session={'digest':authentication.digest(token),'expires':time.monotonic()+120,'family':uuid.uuid4().hex}
            return {'result':'ATTACHED','token':token,'identity':self.identity}
        self._session(client,token)
        if op=='status':authentication.fields(args,());return dict(self.result)
        if op=='close':
            authentication.fields(args,());require(self.thread is None or not self.thread.is_alive(),'START_ACTIVE')
            self.closed=True;return {'result':'CLOSED'}
        if op=='issue':
            authentication.fields(args,('action','prior_epoch','ttl'))
            require(args['action'] in ('start','restart') and type(args['ttl']) is int and 1<=args['ttl']<=30,'START_BOUNDS')
            with exclusion.Lock(self.root,'supervisor.lock'):
                prior=self._absent();_start_history(self.root,self.data_id)
                stop=_stop_binding(self.root)
                require((args['action']=='start' and prior is None and stop is None and args['prior_epoch'] is None) or
                        (args['action']=='restart' and prior is not None and args['prior_epoch']==prior['epoch']),'START_TARGET')
                require(not (self.root/'intent.json').exists() or prior is not None,'RECOVERY_REQUIRED')
                operation=uuid.uuid4().hex;grant=secrets.token_hex(32)
                record={'operation':operation,'coordinator':self.identity,'owner':client,'owner_peer':self.configuration['owner_peer'],
                    'session':self.session['family'],'namespace':self.root.name,'data_id':self.data_id,'action':args['action'],
                    'prior':prior,'stop':stop,'grant_digest':authentication.digest(grant),'expires':time.time()+args['ttl']}
                _start_write(self.root,operation,'grant',record)
                self.grants[operation]={'record':record,'expires':time.monotonic()+args['ttl']}
            return {'result':'ISSUED','operation':operation,'authorization':grant}
        if op=='execute':
            authentication.fields(args,('operation','authorization'))
            operation=args['operation'];local=self.grants.get(operation)
            require(local is not None and time.monotonic()<local['expires'],'START_GRANT_UNKNOWN_OR_EXPIRED')
            record=_start_read(self.root,operation,'grant')
            require(record==local['record'] and record['session']==self.session['family'] and record['coordinator']==self.identity,'START_GRANT_BINDING')
            require(type(args['authorization']) is str and hmac.compare_digest(authentication.digest(args['authorization']),record['grant_digest']),'START_GRANT_INVALID')
            require(not (_start_path(self.root,operation)/'intent.json').exists(),'START_ALREADY_CONSUMED')
            lock=exclusion.Lock(self.root,'supervisor.lock')
            try:
                require(self._absent()==record['prior'] and _stop_binding(self.root)==record['stop'],'START_STALE_TARGET')
                _start_history(self.root,self.data_id)
                self.checkpoint('before-intent')
                nonce=secrets.token_hex(32)
                intent={**record,'grant_consumed':True,'launch_digest':hashlib.sha256(nonce.encode()).hexdigest(),
                        'launch_expires':time.time()+15,'configuration_digest':_start_digest(self.configuration['core'])}
                _start_write(self.root,operation,'intent',intent)
                del self.grants[operation]
                self.checkpoint('intent')
                self.result={'result':'STARTING','operation':operation}
                self.thread=threading.Thread(target=self._launch,args=(lock,operation,nonce),daemon=False)
                self.thread.start()
            except BaseException:lock.close();raise
            return {'result':'AUTHORIZATION_CONSUMED','operation':operation}
        if op=='adopt':
            authentication.fields(args,())
            with exclusion.Lock(self.root,'supervisor.lock'):
                try:
                    with exclusion.Lock(self.root,'core.lock'):pass
                except exclusion.Busy:
                    self.result=self._verify_existing()
                    return dict(self.result)
                if (self.root/'stop').exists():raise Denied('STOP_LATCH')
                raise Denied('RECOVERY_REQUIRED' if (self.root/'core.json').exists() or (self.root/'STAGE4_TEST-starts').exists() else 'EXPLICIT_START_REQUIRED')
        raise Denied('COORDINATOR_OPERATION')

    def _verify_existing(self,operation=None):
        metadata=_old_core(self.root);require(metadata is not None and exclusion.reconcile(self.root),'CORE_RECONCILIATION')
        ready=exclusion.read(self.root/'stage4-ready.json');require(type(ready) is dict,'CORE_READY')
        identity=ready['identity'];peer=transport.identity(metadata['pid'])
        require(ready['peer']==peer and identity['startup_epoch']==metadata['epoch'] and identity['data_id']==self.data_id and identity['namespace']==self.root.name,'CORE_READY_IDENTITY')
        matches=[]
        for directory in (self.root/'STAGE4_TEST-starts').glob('*'):
            if (directory/'claimed.json').exists():
                claimed=_start_read(self.root,directory.name,'claimed')
                if claimed['peer']==peer:matches.append(directory.name)
        require(len(matches)==1 and (operation is None or matches==[operation]),'START_CLAIM_IDENTITY')
        operation=matches[0];intent=_start_read(self.root,operation,'intent');claimed=_start_read(self.root,operation,'claimed')
        require(intent['data_id']==self.data_id and claimed['at']<=intent['launch_expires'] and
                (intent['prior'] is None or identity['startup_epoch']!=intent['prior']['epoch']),'START_EPOCH')
        core=self.configuration['core'];owner=self.configuration['owner']
        # Authenticate the new peer before sending client proof/request. This
        # does not restore a session or grant request authority.
        response=authentication.client(core['endpoint'],peer,identity,bytes.fromhex(core['server_key']),owner,
            bytes.fromhex(core['enrollments'][owner]['key']),{},drop=True)
        require(response['result']=='DROPPED_BEFORE_CLIENT_PROOF','CORE_AUTHENTICATION')
        target=_start_path(self.root,operation)/'verified.json'
        if not target.exists():_start_write(self.root,operation,'verified',{'operation':operation,'identity':identity,'coordinator':self.identity,'at':time.time()})
        else:require(_start_read(self.root,operation,'verified')['identity']==identity,'START_VERIFICATION')
        exclusion.event(self.root,'start_verified',operation=operation,identity=identity,coordinator=self.peer)
        return {'result':'ADOPTED' if self.result.get('operation')!=operation else 'STARTED','operation':operation,'identity':identity}

    def _launch(self,lock,operation,nonce):
        import subprocess
        try:
            core={**self.configuration['core'],'start_transaction':operation,'launch_nonce':nonce}
            env={k.upper():v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','TEMP','TMP')}
            with (self.root/(operation+'.stdout.log')).open('w') as out,(self.root/(operation+'.stderr.log')).open('w') as err:
                child=subprocess.Popen([sys.executable,'-I',str(REPO/'tests/lifecycle_stage4/fixtures.py'),'--restart-app-worker',str(self.root)],
                    env=env,stdin=subprocess.PIPE,stdout=out,stderr=err,text=True,close_fds=True,creationflags=0x08000000)
                peer=transport.identity(child.pid)
                exclusion.event(self.root,'start_spawned',operation=operation,identity=peer,coordinator=self.peer)
                child.stdin.write(json.dumps(core)+'\n');child.stdin.close()
                self.checkpoint('spawned')
                deadline=time.monotonic()+15
                while True:
                    require(child.poll() is None,'START_CHILD_EXITED')
                    ready=exclusion.read(self.root/'stage4-ready.json')
                    if ready and ready.get('peer')==peer:break
                    require(time.monotonic()<deadline,'START_READINESS_TIMEOUT');time.sleep(.02)
                self.result=self._verify_existing(operation)
        except BaseException as exc:
            import traceback
            self.result={'result':'RECOVERY_REQUIRED','operation':operation,'error':type(exc).__name__,'reason':str(exc)}
            exclusion.event(self.root,'start_recovery_required',operation=operation,error=type(exc).__name__,reason=str(exc),traceback=traceback.format_exc())
        finally:lock.close()


def serve_test_coordinator(root,configuration,observer=None):
    authority=TestRestartCoordinator(root,configuration,observer)
    require(transport.identity(configuration['owner_peer']['pid'])==configuration['owner_peer'],'CONTROLLER_PROCESS_IDENTITY')
    key=bytes.fromhex(configuration['server_key']);first=True
    deadline=time.monotonic()+120
    while not authority.closed and time.monotonic()<deadline:
        pipe=transport.listen(configuration['endpoint'])
        try:
            if first:
                exclusion.write(authority.root/('coordinator-'+configuration['name']+'.json'),{'identity':authority.identity,'peer':authority.peer,'endpoint':configuration['endpoint']})
                first=False
            pipe.io('connect')
            require(pipe.peer(server=True)==configuration['owner_peer'],'CONTROLLER_PROCESS_BINDING')
            try:authentication.serve_one(pipe,authority,key,'normal')
            except (Denied,authentication.Denied,OSError,ValueError,TypeError,KeyError,exclusion.Busy):
                try:pipe.send({'result':'DENIED'})
                except Exception:pass
        except (Denied,authentication.Denied,OSError):pass
        finally:pipe.close()
    # A coordinator exit cannot kill its Core. A worker retains supervisor
    # ownership until its bounded verification completes; never force cleanup.
    if authority.thread:authority.thread.join()
