"""Isolated correction validation against actual Stage 1 core(); NOT Stage 4 acceptance."""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
import uuid

REPO=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(REPO/'tests/lifecycle_stage1'))
import harness as h


def worker(root, role, profile, injection):
    root=h.validate(root)
    if not (root/'CORRECTION_DIAGNOSTIC').exists():raise ValueError('Diagnostic marker required')
    events=[];errors=[];reads=0;exception_state=[]
    original_write=h.write;original_read=h.read
    def traced_write(path,data):
        if path.name!='response.json':return original_write(path,data)
        event={'challenge':data['challenge'],'at_ns':time.perf_counter_ns(),'published':False}
        events.append(event);handle=None
        try:
            if injection and data['challenge']=='fail-B':
                # Deliberately prevent replacement of this TEST response for failure-state validation.
                handle=h.k.CreateFileW(str(path),0x80000000,1,None,3,0,None)
                if handle==ctypes.c_void_p(-1).value:raise RuntimeError('injection handle unavailable')
            result=original_write(path,data)
            event['published']=True
            return result
        except Exception as exc:
            frames=traceback.extract_tb(exc.__traceback__)
            errors.append({'exception':type(exc).__name__,'errno':getattr(exc,'errno',None),
                           'winerror':getattr(exc,'winerror',None),'traceback':traceback.format_exc(),
                           'operation':frames[-1].line,'source_line':frames[-1].lineno,
                           'source_file':frames[-1].filename,'path':str(path),
                           'pid':os.getpid(),'at_ns':time.perf_counter_ns()})
            raise
        finally:
            if handle is not None and handle!=ctypes.c_void_p(-1).value:h.k.CloseHandle(handle)
    def traced_read(path):
        if path.name=='challenge.json':
            until=time.monotonic()+5
            while not (root/'go').exists():
                if time.monotonic()>until:raise TimeoutError('go')
                time.sleep(.002)
        return original_read(path)
    def trace(frame,event,arg):
        if frame.f_code is h.core.__code__ and event=='exception':
            value=frame.f_locals.get('last_answered')
            exception_state.append({'last_answered':value if isinstance(value,(str,int,float,bool)) or value is None else 'UNANSWERED'})
        return trace
    (root/(role+'.ready')).touch()
    if role=='publisher':
        h.write=traced_write;h.read=traced_read;sys.settrace(trace)
        try:h.core(root,'normal')
        except Exception as exc:h.event(root,'FAILED_CLOSED',error=type(exc).__name__,code=getattr(exc,'errno',None))
        finally:
            sys.settrace(None)
            (root/'publisher-result.json').write_text(json.dumps({'events':events,'errors':errors,'exception_state':exception_state},indent=2))
    else:
        until=time.monotonic()+5
        while not (root/'go').exists():
            if time.monotonic()>until:raise TimeoutError('go')
            time.sleep(.002)
        end=time.monotonic()+1.2
        while time.monotonic()<end:
            try:
                if profile=='no-reader':time.sleep(.020);continue
                if profile=='held-read':
                    with (root/'response.json').open(encoding='utf8') as stream:json.loads(stream.read());time.sleep(.010)
                else:json.loads((root/'response.json').read_text(encoding='utf8'))
                reads+=1
            except FileNotFoundError:pass
            except (OSError,ValueError) as exc:errors.append({'error':type(exc).__name__,'errno':getattr(exc,'errno',None),'winerror':getattr(exc,'winerror',None)})
            time.sleep(.0005 if profile=='fast-read' else .020)
        (root/'reader-result.json').write_text(json.dumps({'reads':reads,'errors':errors}))


def until(predicate, timeout=5):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if predicate():return
        time.sleep(.010)
    raise AssertionError('Timed out')


def run():
    runroot=h.BASE/('TEST-'+uuid.uuid4().hex);runroot.mkdir(parents=True)
    evidence=REPO/'docs/lifecycle-stage4-evidence'/('correction-'+runroot.name)
    evidence.mkdir(parents=True)
    env={k:v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','TEMP','TMP')}
    results=[];checks=[]
    def root(name):
        p=runroot/name;p.mkdir();(p/'TEST_ONLY').write_text('NO PRODUCTION SERVICES');(p/'CORRECTION_DIAGNOSTIC').touch();return p
    def spawn(p,role,profile='',injection=False):
        return subprocess.Popen([sys.executable,'-I',__file__,'--worker',str(p),role,profile,str(int(injection))],env=env,stdin=subprocess.DEVNULL,close_fds=True,creationflags=0x08000000)
    def finish(p,process):
        (p/'stop').touch();assert process.wait(5)==0
        return json.loads((p/'publisher-result.json').read_text())
    def valid(p,challenge):
        metadata=h.read(p/'core.json');response=h.read(p/'response.json')
        return bool(metadata and response=={'identity':metadata,'challenge':challenge}
                    and h.process_identity(metadata['pid'])=={k:metadata[k] for k in ('pid','created')})
    for profile,count in [('baseline',20),('fast-read',10),('held-read',10),('no-reader',10)]:
        for trial in range(count):
            p=root(f'{profile}-{trial:02}');h.write(p/'challenge.json',{'challenge':'challenge-0'})
            publisher=spawn(p,'publisher');reader=spawn(p,'reader',profile)
            until(lambda: (p/'publisher.ready').exists() and (p/'reader.ready').exists());(p/'go').touch()
            assert reader.wait(5)==0
            result=finish(p,publisher)
            results.append({'profile':profile,'trial':trial,'root':str(p),**result})
            (evidence/'comparison.json').write_text(json.dumps(results,indent=2))
        print('corrected profile complete',profile,flush=True)
    # Actual Core fresh/duplicate challenge behavior; no substitute implementation.
    p=root('fresh-identical');h.write(p/'challenge.json',{'challenge':'A'});publisher=spawn(p,'publisher');(p/'go').touch()
    until(lambda:valid(p,'A'));time.sleep(.100)
    h.write(p/'challenge.json',{'challenge':'B'});until(lambda:valid(p,'B'));time.sleep(.100)
    h.write(p/'challenge.json',{'challenge':'B'});time.sleep(.100)
    assert not valid(p,'C')
    result=finish(p,publisher)
    assert [e['challenge'] for e in result['events']]==['A','B'] and all(e['published'] for e in result['events'])
    checks.append({'case':'fresh-and-identical','passed':True,'stale_C_rejected':True,'events':result})
    # Failure after a success must retain A as last answered, never fail-B.
    p=root('failed-publication');h.write(p/'challenge.json',{'challenge':'A'});publisher=spawn(p,'publisher',injection=True);(p/'go').touch()
    until(lambda:valid(p,'A'));h.write(p/'challenge.json',{'challenge':'fail-B'})
    assert publisher.wait(5)==0
    result=json.loads((p/'publisher-result.json').read_text())
    assert len(result['errors'])==1 and result['events'][-1]['published'] is False
    assert result['exception_state'][-1]['last_answered']=='A'
    assert h.read(p/'response.json')['challenge']=='A'
    assert not list(p.glob('*-spawned.json'))
    checks.append({'case':'failed-publication-not-answered','passed':True,'result':result})
    (evidence/'semantics.json').write_text(json.dumps(checks,indent=2))
    summary=[]
    for profile in ('baseline','fast-read','held-read','no-reader'):
        rows=[r for r in results if r['profile']==profile]
        summary.append({'profile':profile,'trials':len(rows),'failed_trials':sum(bool(r['errors']) for r in rows),
                        'publications':sum(e['published'] for r in rows for e in r['events'])})
    (evidence/'summary.json').write_text(json.dumps({'summary':summary,'semantic_checks':len(checks),
        'source_sha256':hashlib.sha256(Path(h.__file__).read_bytes()).hexdigest(),'raw_root':str(runroot),
        'scope':'Actual corrected credential-free Stage 1 Core fixture; no production App or data. Not Stage 4 acceptance.'},indent=2))
    print('EVIDENCE',evidence,flush=True);print(json.dumps(summary),flush=True)
    if any(r['errors'] for r in results):raise SystemExit(1)


def ownership_tests():
    import concurrent.futures
    import threading
    import unittest
    sys.path.insert(0, str(REPO))
    from stage4_sessions import Ownership, Denied
    from stage4_lifecycle import Lifecycle, Journal

    class MemoryJournal:
        def __init__(self):self.rows=[];self.fail=False
        def write(self, *args, **kwargs):
            if self.fail:raise OSError('TEST injected persistence failure')
            self.rows.append((args, kwargs))

    class Tests(unittest.TestCase):
        def setUp(self):
            self.now=0.0
            self.o=Ownership(mode='STAGE4_TEST',epoch='TEST-epoch',clock=lambda:self.now,
                enrollments={'a':Ownership.ORDINARY,'b':Ownership.ORDINARY,
                             'owner':Ownership.ORDINARY|Ownership.MANAGEMENT})
            self.a=self.o.attach_verified('a',Ownership.ORDINARY,3)
            self.b=self.o.attach_verified('b',Ownership.ORDINARY,3)
            self.owner=self.o.attach_verified('owner',Ownership.ORDINARY|Ownership.MANAGEMENT,3)
            self.e=self.o.epoch;self.j=MemoryJournal();self.life=Lifecycle(self.o,self.j)
            self.release=threading.Event();self.addCleanup(self.clean)
        def clean(self):
            self.release.set()
            for t in self.life.workers.values():
                if t.ident:t.join(2)
                self.assertFalse(t.is_alive())
        def stop(self,action='shutdown',operation=None):
            operation=operation or uuid.uuid4().hex
            cap=self.o.management_capability(self.owner,self.e,action,operation)
            return self.life.request(self.owner,self.e,cap,action,operation)
        def wait_workers(self):
            for t in self.life.workers.values():t.join(2);self.assertFalse(t.is_alive())
        def test_01_test_only(self):
            with self.assertRaises(Denied):Ownership(mode='PRODUCTION',epoch='x',enrollments={})
        def test_02_foreign_request_and_unknown_same_denial(self):
            w=self.o.admit(self.a,self.e,'chat')
            for wid in (w,'unknown'):
                with self.assertRaisesRegex(Denied,'^DENIED$'):self.o.cancel_request(self.b,self.e,wid)
            self.assertEqual(self.o.cancel_request(self.a,self.e,w),'CANCELLATION_REQUESTED')
            self.assertFalse(self.o.work[w].done.is_set())
        def test_03_renewal_preserves_family(self):
            w=self.o.admit(self.a,self.e,'local');old=self.a
            self.a=self.o.renew_verified(self.a,self.e,'a')
            self.assertEqual(self.o.check_owner(self.a,self.e,w),w)
            with self.assertRaises(Denied):self.o.check_owner(old,self.e,w)
        def test_04_new_attachment_cannot_inherit(self):
            w=self.o.admit(self.a,self.e,'local');new=self.o.attach_verified('a',Ownership.ORDINARY,3)
            with self.assertRaises(Denied):self.o.check_owner(new,self.e,w)
        def test_05_wrong_client_cannot_renew(self):
            with self.assertRaises(Denied):self.o.renew_verified(self.a,self.e,'b')
        def test_06_expiry_cancels_no_completion(self):
            w=self.o.admit(self.a,self.e,'chat');self.o.begin(w)
            self.now=901;self.o.snapshot()
            self.assertTrue(self.o.work[w].cancel.is_set());self.assertFalse(self.o.work[w].done.is_set())
            with self.assertRaises(Denied):self.o.next_step(w)
        def test_07_detach_is_local(self):
            a=self.o.admit(self.a,self.e,'local');b=self.o.admit(self.b,self.e,'local')
            self.o.detach(self.a,self.e)
            self.assertTrue(self.o.work[a].cancel.is_set());self.assertFalse(self.o.work[b].cancel.is_set())
            self.assertEqual(self.o.state,'RUNNING')
        def test_08_revoke_old_epoch(self):
            with self.assertRaises(Denied):self.o.admit(self.a,'OLD','local')
            self.o.revoke_client('a')
            with self.assertRaises(Denied):self.o.admit(self.a,self.e,'local')
        def test_09_single_chat_concurrent(self):
            barrier=threading.Barrier(8)
            def attempt(i):
                barrier.wait()
                try:return self.o.admit(self.a if i%2 else self.b,self.e,'chat')
                except Denied:return None
            with concurrent.futures.ThreadPoolExecutor(8) as pool:results=list(pool.map(attempt,range(8)))
            self.assertEqual(sum(r is not None for r in results),1)
        def test_10_capture_busy_and_expiry(self):
            a=self.o.media(self.a,self.e,'capture')
            with self.assertRaises(Denied):self.o.media(self.b,self.e,'capture')
            with self.assertRaises(Denied):self.o.stop_media(self.b,self.e,'capture',a['id'])
            self.now=11;self.assertEqual(self.o.snapshot()['media'],[])
            b=self.o.media(self.b,self.e,'capture')
            with self.assertRaises(Denied):self.o.media(self.a,self.e,'capture',lease_id=a['id'])
            self.assertTrue(b['id'])
        def test_11_playback_owner_and_idempotency(self):
            w=self.o.admit(self.a,self.e,'local');p=self.o.media(self.a,self.e,'playback',request_id=w)
            with self.assertRaises(Denied):self.o.media(self.b,self.e,'playback',request_id=w)
            self.o.stop_media(self.a,self.e,'playback',p['id'])
            with self.assertRaises(Denied):self.o.media(self.a,self.e,'playback',request_id=w)
            self.assertFalse(self.o.work[w].cancel.is_set())
        def test_12_ordinary_denied_lifecycle(self):
            for action in ('shutdown','emergency-stop'):
                with self.assertRaises(Denied):self.o.management_capability(self.a,self.e,action,uuid.uuid4().hex)
            self.assertEqual(self.o.state,'RUNNING')
        def test_13_capability_bound_action_and_expiry(self):
            op=uuid.uuid4().hex;c=self.o.management_capability(self.owner,self.e,'shutdown',op)
            with self.assertRaises(Denied):self.o.consume_management(self.owner,self.e,c,'emergency-stop',op)
            self.now=31
            with self.assertRaises(Denied):self.o.consume_management(self.owner,self.e,c,'shutdown',op)
        def test_14_capability_single_use(self):
            op=uuid.uuid4().hex;c=self.o.management_capability(self.owner,self.e,'shutdown',op)
            self.o.consume_management(self.owner,self.e,c,'shutdown',op)
            with self.assertRaises(Denied):self.o.consume_management(self.owner,self.e,c,'shutdown',op)
        def test_15_shutdown_admission_and_idempotency(self):
            op=uuid.uuid4().hex;self.stop(operation=op);at=self.life.accepted_at;rows=len(self.j.rows)
            self.now=4;self.life.request(self.owner,self.e,'not-a-capability','shutdown',op)
            self.assertEqual(self.life.accepted_at,at);self.assertEqual(len(self.j.rows),rows)
            with self.assertRaises(Denied):self.o.admit(self.a,self.e,'chat')
            self.assertEqual(self.life.tick()['state'],'FINALIZING')
            self.assertFalse(self.life.status()['core_exit_verified'])
        def test_16_emergency_distinct(self):
            w=self.o.admit(self.a,self.e,'local');self.o.begin(w)
            self.stop('emergency-stop')
            self.assertTrue(self.o.work[w].cancel.is_set());self.assertEqual(self.life.tick()['state'],'SUSPENDED')
            self.assertFalse(self.life.status()['core_exit_verified'])
        def test_17_uncooperative_deadline(self):
            started=threading.Event()
            def work(cancel):started.set();self.release.wait(2);return 'SUCCEEDED'
            w=self.life.dispatch(self.a,self.e,'local',work);self.assertTrue(started.wait(1))
            self.stop();self.now=10;self.assertEqual(self.life.tick()['state'],'CANCELLING')
            self.assertTrue(self.o.work[w].cancel.is_set());self.assertFalse(self.o.work[w].done.is_set())
            self.now=30;self.assertEqual(self.life.tick()['state'],'RECOVERY_REQUIRED')
            self.release.set();self.wait_workers();self.assertEqual(self.life.tick()['state'],'RECOVERY_REQUIRED')
        def test_18_stop_intent_failure(self):
            self.j.fail=True;self.stop()
            self.assertEqual(self.o.state,'RECOVERY_REQUIRED');self.assertFalse(self.life.status()['intent_persisted'])
        def test_19_acceptance_failure_no_execution(self):
            called=[];self.j.fail=True
            with self.assertRaises(OSError):self.life.dispatch(self.a,self.e,'local',lambda c:called.append(1))
            self.assertFalse(called);self.assertEqual(self.o.state,'RECOVERY_REQUIRED')
        def test_20_unknown_consumption_preserved(self):
            w=self.life.dispatch(self.a,self.e,'repair',lambda c:'UNKNOWN',budget_ref='TEST-held-reservation')
            self.wait_workers();self.stop();self.now=30
            self.assertEqual(self.life.tick()['state'],'RECOVERY_REQUIRED')
            self.assertEqual(self.o.work[w].budget_ref,'TEST-held-reservation')
            self.assertFalse(self.life.status()['budget_refunds_performed'])
        def test_21_cleanup_blocks_finalization(self):
            started=threading.Event()
            def work(cancel):started.set();self.release.wait(2);return 'SUCCEEDED'
            self.life.dispatch(self.a,self.e,'inspection',work);self.assertTrue(started.wait(1))
            self.stop();self.assertEqual(self.life.tick()['state'],'DRAINING')
            self.release.set();self.wait_workers();self.assertEqual(self.life.tick()['state'],'FINALIZING')
        def test_22_not_started_cancel_blocks_dispatch(self):
            w=self.o.admit(self.a,self.e,'local');self.o.cancel_request(self.a,self.e,w)
            with self.assertRaises(Denied):self.o.begin(w)
            self.o.complete(w,'NEVER_STARTED');self.assertTrue(self.o.work[w].done.is_set())
        def test_23_stop_start_barrier(self):
            barrier=threading.Barrier(9);calls=[]
            def submit(i):
                barrier.wait()
                try:return self.life.dispatch(self.a,self.e,'local',lambda c:(calls.append(i) or 'SUCCEEDED'))
                except Denied:return None
            with concurrent.futures.ThreadPoolExecutor(8) as pool:
                futures=[pool.submit(submit,i) for i in range(8)]
                barrier.wait();self.stop();[f.result() for f in futures]
            self.wait_workers()
            self.assertEqual(self.life.tick()['state'],'FINALIZING')
            with self.assertRaises(Denied):self.life.dispatch(self.a,self.e,'local',lambda c:'SUCCEEDED')
        def test_24_journal_recovery_and_identity(self):
            root=REPO/'tests/lifecycle_stage4/evidence'/('STAGE4_TEST-'+uuid.uuid4().hex);root.mkdir(parents=True)
            identity={'mode':'STAGE4_TEST','data_id':'TEST-data'}
            (root/'STAGE4_TEST.json').write_text(json.dumps(identity,sort_keys=True))
            j=Journal(root,identity);op=uuid.uuid4().hex;j.write(op,'RUNNING',kind='local')
            with self.assertRaises(Denied):j.inspect()
            j.write(op,'SUCCEEDED',kind='local');self.assertEqual(len(j.inspect()),1)
            (root/(op+'.json')).write_text('{')
            with self.assertRaises(Denied):j.inspect()
            with self.assertRaises(Denied):Journal(root,{**identity,'data_id':'WRONG'})

        def test_25_deadline_requires_fresh_owner_reevaluation(self):
            started=threading.Event()
            def work(cancel):started.set();self.release.wait(2);return 'SUCCEEDED'
            self.life.dispatch(self.a,self.e,'local',work);self.assertTrue(started.wait(1))
            self.stop();self.now=30;self.life.tick()
            with self.assertRaises(Denied):self.stop()
            self.release.set();self.wait_workers()
            self.assertEqual(self.life.tick()['state'],'RECOVERY_REQUIRED')
            self.stop();self.assertEqual(self.life.tick()['state'],'FINALIZING')
            self.life.record_exit_ready()
            terminal=[args[1] for args,kwargs in self.j.rows if kwargs.get('kind')=='shutdown' and args[1]!='STOP_INTENT']
            self.assertEqual(terminal,['FAILED','SUCCEEDED'])
        def test_26_emergency_requires_separate_shutdown(self):
            self.stop('emergency-stop');self.assertEqual(self.life.tick()['state'],'SUSPENDED')
            self.stop();self.assertEqual(self.life.tick()['state'],'FINALIZING')
        def test_27_final_journal_failure_retains_recovery(self):
            self.stop();self.life.tick();self.j.fail=True
            with self.assertRaises(OSError):self.life.record_exit_ready()
            self.assertEqual(self.o.state,'RECOVERY_REQUIRED')
            with self.assertRaises(Denied):self.stop()

    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    dest=REPO/'docs/lifecycle-stage4-evidence'/('ownership-model-'+uuid.uuid4().hex+'.json')
    dest.write_text(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
        'details':[s for _,s in result.failures+result.errors],
        'scope':'Pure ownership/drain model; real Python worker threads and isolated journal; not App/Electron/voice integration',
        'deadline_clock':'injected monotonic clock; no claim of real runtime wall-clock shutdown guarantee'},indent=2))
    print('EVIDENCE',dest)
    raise SystemExit(not result.wasSuccessful())


def inspection_tests():
    """Actual singleton job + real tracked threads, with synthetic panel/archive IO."""
    import threading, unittest
    from unittest.mock import patch
    sys.path.insert(0,str(REPO))
    from inspection_jobs import JOBS
    from stage4_runtime import Context
    from stage4_sessions import Ownership, Denied
    from stage4_lifecycle import Lifecycle
    from interface_inspection import PANELS

    class MemoryJournal:
        def __init__(self):self.rows=[];self.before_running=None
        def write(self, operation, phase, **kw):
            if phase=='RUNNING' and self.before_running:self.before_running()
            self.rows.append((operation,phase,kw))

    class Tests(unittest.TestCase):
        def setUp(self):
            self.now=0.;self.release=threading.Event();self.panel=threading.Event();self.archiving=threading.Event()
            self.block_panel=False;self.block_archive=False;self.fail_archive=False;self.calls=[];self.archives=[]
            self.o=Ownership(mode='STAGE4_TEST',epoch='TEST-inspection',clock=lambda:self.now,
                enrollments={'a':Ownership.ORDINARY,'b':Ownership.ORDINARY,'owner':Ownership.ORDINARY|Ownership.MANAGEMENT})
            self.a=self.o.attach_verified('a',Ownership.ORDINARY,3);self.b=self.o.attach_verified('b',Ownership.ORDINARY,3)
            self.owner=self.o.attach_verified('owner',Ownership.ORDINARY|Ownership.MANAGEMENT,3)
            self.j=MemoryJournal();self.life=Lifecycle(self.o,self.j)
            self.ctx=Context.__new__(Context)
            self.ctx.owners=self.o;self.ctx.lifecycle=self.life;self.ctx.epoch=self.o.epoch;self.ctx.inspection_jobs={}
            self.ctx.inspection_runner=self.runner;self.ctx.inspection_finish=self.archive
            JOBS.jobs.clear()  # This no-App unit-test process owns its singleton.
            self.addCleanup(self.clean)
        def clean(self):
            self.release.set()
            for w in self.o.work.values():w.cancel.set()
            for t in self.life.workers.values():
                if t.ident:t.join(3)
                self.assertFalse(t.is_alive())
            JOBS.jobs.clear()
        def runner(self, request, cancel):
            self.calls.append(request['panel']);self.panel.set()
            if self.block_panel:cancel.wait(3)
            return {'requested_panel':request['panel'],'stages':{'analysis_completed':'completed'},'analysis':'Synthetic TEST finding'}
        def archive(self, job):
            self.archiving.set()
            if self.block_archive:self.release.wait(3)
            if self.fail_archive:raise OSError('TEST partial archive failure')
            self.archives.append(job)
            return {'status':'archived','inspection_id':job['id']}
        def start(self):return self.ctx.start_inspection(self.a,{'panel':'all'})['request_id']
        def wait(self):
            for t in self.life.workers.values():t.join(3);self.assertFalse(t.is_alive())
        def stop(self, action='shutdown'):
            op=uuid.uuid4().hex;cap=self.o.management_capability(self.owner,self.o.epoch,action,op)
            return self.life.request(self.owner,self.o.epoch,cap,action,op)
        def test_01_success_actual_job_no_nested_timer(self):
            with patch('inspection_jobs.threading.Timer',side_effect=AssertionError('Untracked TEST timer')):
                wid=self.start();self.wait()
            result=self.ctx.inspection_status(self.a,wid)
            self.assertTrue(result['done']);self.assertEqual(result['job']['status'],'completed')
            self.assertEqual(self.calls,list(PANELS));self.assertEqual(len(self.archives),1)
            self.assertEqual(self.o.work[wid].outcome,'SUCCEEDED')
            self.assertFalse(any(k.startswith('_') for k in result['job']))
        def test_02_foreign_status_and_cancel_denied(self):
            self.block_panel=True;wid=self.start();self.assertTrue(self.panel.wait(1))
            with self.assertRaises(Denied):self.ctx.inspection_status(self.b,wid)
            with self.assertRaises(Denied):self.o.cancel_request(self.b,self.o.epoch,wid)
            self.assertFalse(self.o.work[wid].cancel.is_set())
            self.o.cancel_request(self.a,self.o.epoch,wid);self.wait()
        def test_03_cancel_waits_for_archive(self):
            self.block_panel=True;self.block_archive=True;wid=self.start();self.assertTrue(self.panel.wait(1))
            self.o.cancel_request(self.a,self.o.epoch,wid);self.assertTrue(self.archiving.wait(1))
            status=self.ctx.inspection_status(self.a,wid)
            self.assertFalse(status['done']);self.assertEqual(status['job']['phase'],'archiving')
            self.stop();self.assertEqual(self.life.tick()['state'],'DRAINING')
            self.release.set();self.wait();self.assertEqual(self.life.tick()['state'],'FINALIZING')
            self.assertEqual(len(self.calls),1);self.assertEqual(self.archives[0]['status'],'cancelled')
        def test_04_detach_and_reattach_no_inherited_authority(self):
            self.block_panel=True;wid=self.start();self.assertTrue(self.panel.wait(1))
            self.o.detach(self.a,self.o.epoch);self.a=self.o.attach_verified('a',Ownership.ORDINARY,3)
            self.wait()
            with self.assertRaises(Denied):self.ctx.inspection_status(self.a,wid)
            self.assertEqual(len(self.calls),1);self.assertEqual(len(self.archives),1)
        def test_05_archive_failure_is_unknown_not_success(self):
            self.fail_archive=True;wid=self.start();self.wait()
            self.assertEqual(self.o.work[wid].outcome,'UNKNOWN')
            self.assertEqual(self.ctx.inspection_status(self.a,wid)['job']['archive']['status'],'failed')
            self.stop();self.now=30;self.assertEqual(self.life.tick()['state'],'RECOVERY_REQUIRED')
            self.assertFalse(self.life.status()['budget_refunds_performed'])
        def test_06_archive_liveness_survives_deadline(self):
            self.block_archive=True;wid=self.start();self.assertTrue(self.archiving.wait(1))
            self.stop();self.now=30;self.assertEqual(self.life.tick()['state'],'RECOVERY_REQUIRED')
            self.assertFalse(self.o.work[wid].done.is_set())
            self.release.set();self.wait();self.assertEqual(self.life.tick()['state'],'RECOVERY_REQUIRED')
        def test_07_expiry_cannot_remove_active_archive(self):
            self.block_archive=True;wid=self.start();self.assertTrue(self.archiving.wait(1))
            key=self.ctx.inspection_jobs[wid];JOBS.jobs[key]['expires']=0
            JOBS._expire(key);self.assertEqual(self.ctx.inspection_status(self.a,wid)['job']['phase'],'archiving')
            self.release.set();self.wait();JOBS.jobs[key]['expires']=0
            with self.assertRaises(ValueError):JOBS.get(key)
        def test_08_no_inspection_after_shutdown(self):
            self.stop()
            with self.assertRaises(Denied):self.start()
            self.assertFalse(JOBS.jobs);self.assertFalse(self.calls)
        def test_09_cancel_before_begin_creates_no_job(self):
            entered=threading.Event()
            self.j.before_running=lambda:(entered.set(),self.release.wait(3))
            wid=self.start();self.assertTrue(entered.wait(1));self.o.cancel_request(self.a,self.o.epoch,wid)
            self.release.set();self.wait()
            self.assertEqual(self.o.work[wid].outcome,'NEVER_STARTED');self.assertFalse(JOBS.jobs);self.assertFalse(self.archives)
        def test_10_drain_prevents_next_panel_and_summary(self):
            calls=[];summaries=[]
            def panel(request,cancel):
                calls.append(request['panel']);self.stop()
                return {'requested_panel':request['panel'],'stages':{'analysis_completed':'completed'}}
            # Same optional job hook with real lifecycle step checks, including summary admission.
            gate=threading.Event();mapping={}
            def work(cancel):
                gate.wait(1)
                JOBS.run_registered({'panel':'all'},panel,lambda *a:summaries.append(1),on_finish=self.archive,
                    cancel=cancel,before_step=lambda:self.o.next_step(mapping['id']),registered=lambda key:None)
                return 'FAILED'
            mapping['id']=self.life.dispatch(self.a,self.o.epoch,'inspection',work);gate.set();self.wait()
            self.assertEqual(len(calls),1);self.assertFalse(summaries);self.assertEqual(len(self.archives),1)
        def test_11_emergency_cancels_without_shutdown(self):
            self.block_panel=True;wid=self.start();self.assertTrue(self.panel.wait(1))
            self.stop('emergency-stop');self.wait()
            self.assertEqual(self.life.tick()['state'],'SUSPENDED');self.assertTrue(self.o.work[wid].done.is_set())
            self.assertEqual(self.archives[0]['status'],'cancelled')
        def test_12_concurrent_jobs_use_existing_singleton(self):
            self.block_panel=True;wid=self.start();self.assertTrue(self.panel.wait(1))
            other=self.ctx.start_inspection(self.b,{'panel':'all'})['request_id']
            self.life.workers[other].join(2);self.assertEqual(self.o.work[other].outcome,'FAILED')
            self.assertEqual(len(JOBS.jobs),1);self.o.cancel_request(self.a,self.o.epoch,wid);self.wait()
        def test_13_legacy_start_still_background_and_timer(self):
            timer_started=threading.Event()
            with patch('inspection_jobs.threading.Timer') as timer:
                timer.return_value.start.side_effect=timer_started.set
                result=JOBS.start({'panel':PANELS[0]},self.runner,on_finish=self.archive)
                self.assertTrue(timer_started.wait(2));self.assertEqual(JOBS.get(result['job_id'])['status'],'completed')
                self.assertEqual(timer.call_args.args[0],301)
            self.assertFalse(self.life.workers)

    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    dest=REPO/'docs/lifecycle-stage4-evidence'/('inspection-workers-'+uuid.uuid4().hex+'.json')
    dest.write_text(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
        'details':[s for _,s in result.failures+result.errors],
        'scope':'Actual InspectionJobs singleton/worker + TEST ownership/lifecycle; synthetic IO; injected deadline clock; no App/Core/provider/media',
        'production_access':False},indent=2));print('EVIDENCE',dest)
    raise SystemExit(not result.wasSuccessful())


def controller_recovery_tests():
    from types import SimpleNamespace
    sys.path.insert(0,str(REPO));sys.path.insert(0,str(Path(__file__).parent))
    from stage4_sessions import Ownership,Denied
    from stage4_lifecycle import Lifecycle
    from stage4_runtime import Authority, authentication
    from fixtures import controller_action
    records=[]
    root=REPO/'tests/lifecycle_stage4/evidence'/('STAGE4_TEST-recovery-'+uuid.uuid4().hex);root.mkdir(parents=True)
    class Journal:
        def __init__(self):self.rows=[]
        def write(self,*a,**k):self.rows.append((a,k))
    def fixture():
        now=[0.];enroll={'controller':Ownership.ORDINARY|Ownership.MANAGEMENT,'client':Ownership.ORDINARY,'emergency':Ownership.ORDINARY|{'emergency'}}
        o=Ownership(mode='STAGE4_TEST',epoch='TEST-recovery',clock=lambda:now[0],enrollments=enroll);life=Lifecycle(o,Journal())
        identity={'mode':'TEST','namespace':'TEST-STAGE4-recovery','startup_epoch':o.epoch,'core_instance_id':'no-Core-fixture'}
        ctx=SimpleNamespace(owners=o,lifecycle=life,root=root,app=SimpleNamespace(devices=SimpleNamespace(register=lambda *a,**k:None,disconnect=lambda *a,**k:None)))
        auth=Authority(ctx,identity,enroll);tokens={};calls=[]
        def call(client,op,args=None,token=None):
            calls.append(op)
            return auth.operation(client,{'op':op,'args':args or {},'token':None if op in ('attach','recovery-attach') else token or tokens.get(client)},3)
        tokens['controller']=call('controller','attach',{'scopes':sorted(enroll['controller'])})['token']
        return now,o,life,identity,auth,tokens,calls,call,enroll
    def check(name,ok):
        records.append({'case':name,'passed':bool(ok)})
        if not ok:raise AssertionError(name)
    def denied(fn):
        try:fn()
        except (Denied,authentication.Denied):return True
        return False
    try:
        for state in ('SUSPENDED','DRAINING','CANCELLING','RECOVERY_REQUIRED'):
            now,o,life,ident,auth,tokens,calls,call,enroll=fixture();o.state=state;life.accepted_at=7
            issued=call('controller','recovery-attach')['token'];s=o._session(issued,o.epoch)
            check('restricted recovery in '+state,s.recovery and s.scopes=={'attach','lifecycle'} and o.state==state and life.accepted_at==7)
            check('ordinary recovery denied '+state,denied(lambda:call('client','recovery-attach')))
            check('ordinary attach remains denied '+state,denied(lambda:call('client','attach',{'scopes':sorted(Ownership.ORDINARY)})))
        for state in ('RUNNING','FINALIZING'):
            now,o,life,ident,auth,tokens,calls,call,enroll=fixture();o.state=state
            check('recovery refused '+state,denied(lambda:call('controller','recovery-attach')))
        now,o,life,ident,auth,tokens,calls,call,enroll=fixture();old=tokens['controller'];oldfamily=o._session(old,o.epoch).family
        wid=o.admit(old,o.epoch,'repair');now[0]=901
        check('expired controller denied',denied(lambda:call('controller','lifecycle-status')))
        result=controller_action(call,tokens,ident,sorted(enroll['controller']),'REAUTH')
        check('explicit REAUTH same identity new family',result['identity']==ident and o._session(tokens['controller'],o.epoch).family!=oldfamily)
        check('old repair authority not inherited',denied(lambda:o.check_owner(tokens['controller'],o.epoch,wid)))
        check('old repair cancelled before start',o.work[wid].cancel.is_set() and denied(lambda:o.begin(wid)))
        o.complete(wid,'NEVER_STARTED')
        call('controller','emergency-stop',{'operation':uuid.uuid4().hex});now[0]=1802
        result=controller_action(call,tokens,ident,sorted(enroll['controller']),'RECOVER')
        check('explicit RECOVER restricted',result['result']=='RECOVERY_AUTHENTICATED' and o._session(tokens['controller'],o.epoch).recovery)
        check('recovery status allowed',controller_action(call,tokens,ident,[], 'STATUS')['state']=='SUSPENDED')
        for op in ('request','request-text-only','repair','cancel','request-status','shared','renew','voice','voice-status','capture','deep-review','inspection-start','inspection-status','response-provider','last-response-provider','emergency-stop'):
            check('recovery operation denied '+op,denied(lambda:call('controller',op)))
        check('recovery separate known shutdown allowed',controller_action(call,tokens,ident,[],'SHUTDOWN')['state']=='DRAINING')
        check('known work may finalize without replay',life.tick()['state']=='FINALIZING' and len(o.work)==1)
        now,o,life,ident,auth,tokens,calls,call,enroll=fixture();old=tokens['controller'];w=o.admit(old,o.epoch,'repair');o.begin(w);o.complete(w,'UNKNOWN')
        o.state='RECOVERY_REQUIRED';life.failure='SHUTDOWN_DEADLINE_OR_UNKNOWN_OUTCOME';life.accepted_at=5;now[0]=901
        tokens['controller']=call('controller','recovery-attach')['token']
        check('unknown outcome still blocks shutdown',denied(lambda:call('controller','shutdown',{'operation':uuid.uuid4().hex})) and o.state=='RECOVERY_REQUIRED' and life.accepted_at==5)
        for state in ('DRAINING','CANCELLING'):
            o.state=state;before=life.accepted_at
            check('recovery does not restart deadline '+state,denied(lambda:call('controller','shutdown',{'operation':uuid.uuid4().hex})) and life.accepted_at==before)
        o.state='SUSPENDED'
        check('emergency-only enrollment cannot recover',denied(lambda:call('emergency','recovery-attach')))
        check('recovery rejects supplied scopes',denied(lambda:call('controller','recovery-attach',{'scopes':['request']})))
        check('recovery requires absent old token',denied(lambda:auth.operation('controller',{'op':'recovery-attach','token':old,'args':{}},3)))
        check('wrong protocol rejected',denied(lambda:auth.operation('controller',{'op':'recovery-attach','token':None,'args':{}},1)))
        check('fresh family cannot use old request',denied(lambda:o.check_owner(tokens['controller'],o.epoch,w)))
        o.revoke_client('controller')
        check('revoked enrollment cannot recover',denied(lambda:call('controller','recovery-attach')))
        check('revocation invalidates recovery token',denied(lambda:call('controller','lifecycle-status')))
        now,o,life,ident,auth,tokens,calls,call,enroll=fixture();o.state='SUSPENDED';tokens['controller']=call('controller','recovery-attach')['token'];now[0]=901
        check('recovery expiry unchanged',denied(lambda:call('controller','lifecycle-status')))
        o.state='RUNNING';fresh=call('controller','attach',{'scopes':sorted(enroll['controller'])})['token'];tokens['controller']=fresh
        prior_calls=len(calls)
        controller_action(call,tokens,ident,sorted(enroll['controller']),'REAUTH')
        check('REAUTH performs only one attach not retry',calls[prior_calls:]==['attach'])
        old=tokens['controller']
        def fake(*a,**kw):return {'result':'ATTACHED','token':'0'*64,'identity':{**ident,'core_instance_id':'WRONG'},'epoch':ident['startup_epoch']}
        try:controller_action(fake,tokens,ident,[],'REAUTH');bad=False
        except ValueError:bad=True
        check('identity mismatch never replaces token',bad and tokens['controller']==old)
        check('denied reauth does not alter token',controller_action(lambda *a,**k:{'result':'DENIED'},tokens,ident,[],'REAUTH')=={'result':'DENIED'} and tokens['controller']==old)
    finally:
        dest=REPO/'docs/lifecycle-stage4-evidence'/('controller-recovery-'+uuid.uuid4().hex+'.json')
        dest.write_text(json.dumps({'cases':records,'scope':'No Core/App/Store: actual TEST ownership/lifecycle/dispatcher; injected clock; post-authentication only'},indent=2));print('EVIDENCE',dest)
    print('controller recovery checks',len(records),'PASS')


def repair_loop_audit():
    """No App/Core: run the exact runtime audit function with synthetic context."""
    import ast, asyncio, socket, threading
    from types import SimpleNamespace
    sys.path.insert(0,str(REPO))
    import stage4_runtime as runtime
    root=REPO/'tests/lifecycle_stage4/evidence'/('STAGE4_TEST-loop-'+uuid.uuid4().hex);root.mkdir(parents=True)
    host=runtime.RepairLoopHost(mode='STAGE4_TEST');poison=runtime.RepairLoopHost(mode='STAGE4_TEST')
    context=SimpleNamespace(root=root,data=root/'data',allow_local_ollama=False)
    tree=ast.parse(Path(runtime.__file__).read_text(encoding='utf8'))
    audit=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='isolated_io')
    namespace={**vars(runtime),'context':context}
    exec(compile(ast.Module(body=[audit],type_ignores=[]),str(runtime.__file__),'exec'),namespace)
    sys.addaudithook(namespace['isolated_io'])
    records=[]
    def check(label,ok):
        records.append({'case':label,'passed':bool(ok)})
        if not ok:raise AssertionError(label)
    try:
        for address in (('127.0.0.1',1),('127.0.0.1',11434),('192.168.1.1',80),('198.51.100.1',443)):
            denied=False
            with socket.socket() as sock:
                try:sock.connect(address)
                except runtime.Denied:denied=True
            check('network denied '+str(address),denied)
        denied=False
        try:socket.getaddrinfo('stage4-test.invalid',443)
        except runtime.Denied:denied=True
        check('DNS denied',denied)
        results=[]
        async def request():return await asyncio.to_thread(lambda:'synthetic response')
        for _ in range(2):
            t=threading.Thread(target=lambda:results.append(host.run(request)));t.start();t.join(3)
            check('registered sequential worker exits',not t.is_alive())
        check('sequential requests complete under unchanged audit',results==['synthetic response']*2)
        check('executor threads joined',not any(t.name.startswith('STAGE4_TEST-repair') for t in threading.enumerate()))
        entered=threading.Event();release=threading.Event()
        async def blocking():await asyncio.to_thread(lambda:(entered.set(),release.wait(3)))
        t=threading.Thread(target=lambda:host.run(blocking));t.start();check('blocking worker entered',entered.wait(2))
        try:
            denied=False
            try:host.run(request)
            except runtime.Denied:denied=True
            check('simultaneous loop borrow denied',denied)
            denied=False
            try:host.close()
            except runtime.Denied:denied=True
            check('close active loop denied',denied)
        finally:release.set();t.join(3)
        check('blocked executor cleanup joined',not t.is_alive())
        async def leak():
            asyncio.create_task(asyncio.sleep(60))
            return 'not a clean outcome'
        denied=False
        try:poison.run(leak)
        except runtime.Denied:denied=True
        check('unexpected pending task fails closed',denied and poison.poisoned and not asyncio.all_tasks(poison.loop))
        host.close();poison.close()
        check('idle loop resources closed',host.closed and poison.closed)
        denied=False
        try:host.run(request)
        except runtime.Denied:denied=True
        check('closed loop cannot be reused',denied)
    except Exception as exc:
        records.append({'case':'probe failure','passed':False,'error':type(exc).__name__,'traceback':traceback.format_exc()})
        raise
    finally:
        for owner in (host,poison):
            if not owner.closed and not owner.lock.locked():owner.close()
        dest=root/'result.json';dest.write_text(json.dumps({'cases':records,'scope':'No App/Core, exact extracted runtime audit; internal socketpairs created before hook; no permitted external connections'},indent=2))
        print('EVIDENCE',dest)
    print('loop audit checks',len(records),'PASS')


def repair_tests():
    import concurrent.futures
    import threading
    import unittest
    from unittest.mock import patch
    from types import SimpleNamespace
    sys.path.insert(0,str(REPO));sys.path.insert(0,str(Path(__file__).parent))
    import budgeted_repair, project_budgets as budgets, workspaces
    from store import Store
    from stage4_sessions import Ownership, Denied
    from stage4_lifecycle import Lifecycle, Journal
    from stage4_runtime import Context, RepairLoopHost
    from fixtures import provision_repair_fixture
    runroot=REPO/'tests/lifecycle_stage4/evidence'/('STAGE4_TEST-repair-'+uuid.uuid4().hex)
    runroot.mkdir(parents=True);records=[]

    class Tests(unittest.TestCase):
        def setUp(self):
            self.root=runroot/self._testMethodName;self.root.mkdir()
            self.now=0.;self.release=threading.Event();self.entered=threading.Event();self.cleaning=threading.Event()
            self.block=False;self.fail=False;self.bad_cleanup=False;self.calls=[]
            self.o=Ownership(mode='STAGE4_TEST',epoch='TEST-repair',clock=lambda:self.now,
                enrollments={'a':Ownership.ORDINARY,'b':Ownership.ORDINARY,'owner':Ownership.ORDINARY|Ownership.MANAGEMENT})
            self.a=self.o.attach_verified('a',Ownership.ORDINARY,3);self.b=self.o.attach_verified('b',Ownership.ORDINARY,3)
            self.owner=self.o.attach_verified('owner',Ownership.ORDINARY|Ownership.MANAGEMENT,3)
            identity={'mode':'STAGE4_TEST','case':self._testMethodName}
            jr=self.root/'STAGE4_TEST-journal';jr.mkdir();(jr/'STAGE4_TEST.json').write_text(json.dumps(identity,sort_keys=True))
            self.j=Journal(jr,identity);self.life=Lifecycle(self.o,self.j)
            self.ctx=Context.__new__(Context);self.ctx.owners=self.o;self.ctx.lifecycle=self.life;self.ctx.epoch=self.o.epoch
            self.ctx.repair_fixture=None;self.ctx.repair_requests={};self.ctx.repair_results={};self.ctx.repair_admission=threading.Lock()
            self.ctx.repair_loop=RepairLoopHost(mode='STAGE4_TEST')
            self.s=Store(self.root/'data');self.ctx.app=SimpleNamespace(store=self.s,stage4=self.ctx)
            workspaces.setup(self.s)
            self.project,self.task=provision_repair_fixture(self.ctx,SimpleNamespace(respond=self.respond),self.checker)
            self.body={'action':'run','operation':uuid.uuid4().hex,'project':self.project,'task':self.task,'confirmation':budgeted_repair.CONFIRMATION}
            self.addCleanup(self.clean)
            for target in ('budgeted_repair.repair_workflow.run','budgeted_repair.check_candidate','budgeted_repair.ExistingServiceCore'):
                p=patch(target,side_effect=AssertionError('Real repair path forbidden'));p.start();self.addCleanup(p.stop)
        async def respond(self,*args,**kwargs):
            self.calls.append('core');self.entered.set()
            if self.block:
                if not kwargs['cancel'].wait(3):raise TimeoutError('TEST cancel absent')
                self.cleaning.set()
                if not self.release.wait(3):raise TimeoutError('TEST cleanup absent')
            if self.fail:raise OSError('TEST uncertain synthetic consumption')
            return 'Synthetic completed attempt'
        def checker(self,label,cancel):
            self.calls.append(label);return {'cleanup':not self.bad_cleanup,'simulated':True}
        def clean(self):
            self.release.set()
            for w in self.o.work.values():w.cancel.set()
            self.join()
            self.ctx.repair_loop.close()
            with self.s.connect() as db:rows=[dict(r) for r in db.execute('SELECT * FROM project_budget_reservations')]
            records.append({'case':self._testMethodName,'root':str(self.root),'calls':self.calls,'reservations':rows,
                'work':[{'id':w.id,'phase':w.phase,'outcome':w.outcome,'done':w.done.is_set()} for w in self.o.work.values()],
                'state':self.o.state,'failure':self.life.failure})
        def join(self):
            for t in list(self.life.workers.values()):
                if t.ident:t.join(4)
                self.assertFalse(t.is_alive())
        def start(self,token=None,body=None):
            return budgeted_repair.dispatch(self.ctx.app,None,body or self.body,stage4_token=token or self.a)['request_id']
        def status(self,w,action='status',token=None):
            return self.ctx.repair_dispatch(token or self.a,{'action':action,'request_id':w})
        def row(self):
            with self.s.connect() as db:
                row=db.execute('SELECT * FROM project_budget_reservations WHERE operation=?',(self.body['operation'],)).fetchone()
                return dict(row) if row else None
        def stop(self,action='shutdown'):
            op=uuid.uuid4().hex;cap=self.o.management_capability(self.owner,self.o.epoch,action,op)
            return self.life.request(self.owner,self.o.epoch,cap,action,op)
        def test_01_success_settles_actual_units(self):
            w=self.start();self.join();r=self.row()
            self.assertEqual((r['state'],r['used_core'],r['used_container']),('settled',1,2))
            self.assertEqual(self.o.work[w].outcome,'SUCCEEDED');self.assertFalse(self.status(w)['result']['actual_repair_executed'])
            self.assertEqual(self.j.inspect()[0]['budget_ref'],self.project+':'+self.body['operation'])
        def test_02_duplicate_never_executes_twice(self):
            w=self.start();self.join();self.assertEqual(self.start(),w)
            self.assertEqual(self.calls.count('core'),1);self.assertEqual(len(self.life.workers),1)
        def test_03_foreign_owner_denied(self):
            w=self.start();self.join()
            for action in ('status','cancel'):
                with self.assertRaises(Denied):self.status(w,action,self.b)
            with self.assertRaises(Denied):self.start(self.b)
        def test_04_confirmation_is_not_budget_permission(self):
            self.body['confirmation']='';w=self.start();self.join()
            self.assertEqual(self.row()['state'],'released');self.assertEqual(self.calls,[])
            self.assertEqual(self.status(w)['result']['status'],'NOT_AUTHORIZED')
            with self.assertRaisesRegex(Denied,'IDEMPOTENCY_CONFLICT'):
                self.start(body={**self.body,'confirmation':budgeted_repair.CONFIRMATION})
        def test_05_cancel_retains_hold_until_cleanup(self):
            self.block=True;w=self.start();self.assertTrue(self.entered.wait(2));self.status(w,'cancel')
            self.assertTrue(self.cleaning.wait(2));self.assertFalse(self.status(w)['done'])
            self.assertEqual(self.row()['state'],'started');self.assertEqual(self.row()['used_core'],1)
            self.release.set();self.join()
            self.assertEqual((self.row()['state'],self.row()['used_container']),('settled',1))
            self.assertEqual(self.o.work[w].outcome,'FAILED');self.assertNotIn('SYNTHETIC_CANDIDATE',self.calls)
        def test_06_detach_cancels_without_inheriting(self):
            self.block=True;w=self.start();self.assertTrue(self.entered.wait(2));self.o.detach(self.a,self.o.epoch)
            new=self.o.attach_verified('a',Ownership.ORDINARY,3)
            with self.assertRaises(Denied):self.status(w,token=new)
            with self.assertRaises(Denied):self.start(new)
            self.assertTrue(self.cleaning.wait(2));self.assertEqual(self.row()['state'],'started')
            self.release.set();self.join();self.assertEqual(self.row()['state'],'settled')
        def test_07_unknown_provider_attempt_is_not_refunded(self):
            self.fail=True;w=self.start();self.join();self.assertEqual(self.o.work[w].outcome,'UNKNOWN')
            r=self.row();self.assertEqual(r['state'],'recovery_required');self.assertEqual(r['used_core'],1)
            with self.s.connect() as db:self.assertEqual(budgets.snapshot(db,self.project)['remaining'],{'core_requests':0,'container_checks':0})
            self.stop();self.now=31;self.life.tick();self.assertEqual(self.o.state,'RECOVERY_REQUIRED')
            with self.assertRaises(Denied):self.j.inspect()
        def test_08_unknown_checker_cleanup_retains_full_hold(self):
            self.bad_cleanup=True;w=self.start();self.join()
            self.assertEqual(self.row()['state'],'recovery_required');self.assertEqual(self.row()['used_container'],1)
            self.assertEqual(self.o.work[w].outcome,'UNKNOWN');self.assertNotIn('core',self.calls)
        def test_09_deadline_does_not_detach_live_cleanup(self):
            self.block=True;w=self.start();self.assertTrue(self.entered.wait(2));self.stop()
            self.now=11;self.life.tick();self.assertTrue(self.cleaning.wait(2));self.now=31;self.life.tick()
            self.assertEqual(self.o.state,'RECOVERY_REQUIRED');self.assertTrue(self.life.workers[w].is_alive())
            self.assertEqual(self.row()['state'],'started');self.release.set();self.join()
            self.assertEqual(self.row()['state'],'settled');self.assertEqual(self.o.state,'RECOVERY_REQUIRED')
        def test_10_cancel_before_begin_has_no_reservation(self):
            entered=threading.Event();go=threading.Event();original=self.j.write
            def write(operation,phase,**kw):
                if phase=='RUNNING':entered.set();go.wait(3)
                return original(operation,phase,**kw)
            with patch.object(self.j,'write',write):
                w=self.start();self.assertTrue(entered.wait(2));self.status(w,'cancel');go.set();self.join()
            self.assertEqual(self.o.work[w].outcome,'NEVER_STARTED');self.assertIsNone(self.row());self.assertEqual(self.calls,[])
        def test_11_drain_closes_admission_before_reservation(self):
            self.stop()
            with self.assertRaisesRegex(Denied,'ADMISSION_CLOSED'):self.start()
            self.assertIsNone(self.row());self.assertEqual(self.calls,[])
        def test_12_settlement_is_inside_registered_worker(self):
            settling=threading.Event();original=budgets.lifecycle
            def lifecycle(*args,**kwargs):
                if args[3]=='settle':settling.set();self.release.wait(3)
                return original(*args,**kwargs)
            with patch.object(budgets,'lifecycle',lifecycle):
                w=self.start();self.assertTrue(settling.wait(2));self.stop();self.life.tick()
                self.assertFalse(self.o.work[w].done.is_set());self.assertEqual(self.row()['state'],'started')
                self.assertEqual(self.o.state,'DRAINING');self.release.set();self.join()
            self.assertEqual(self.row()['state'],'settled');self.life.tick();self.assertEqual(self.o.state,'FINALIZING')
        def test_13_over_budget_rejected_without_worker(self):
            self.start();self.join()
            with self.assertRaisesRegex(Denied,'RESOURCE_LIMIT'):self.start(body={**self.body,'operation':uuid.uuid4().hex})
            self.assertEqual(len(self.life.workers),1)
        def test_14_restart_reservation_is_not_authority(self):
            self.fail=True;self.start();self.join();self.ctx.repair_requests.clear()
            new=self.o.attach_verified('a',Ownership.ORDINARY,3)
            with self.assertRaisesRegex(Denied,'REPLAY_NOT_AUTHORIZED'):self.start(new)
            script="import sqlite3,json,sys; d=sqlite3.connect('file:'+sys.argv[1]+'?mode=ro',uri=True); d.row_factory=sqlite3.Row; print(json.dumps([dict(r) for r in d.execute('SELECT state,used_core,used_container FROM project_budget_reservations')]))"
            result=subprocess.run([sys.executable,'-I','-B','-c',script,str(self.s.path)],capture_output=True,text=True,check=True)
            self.assertEqual(json.loads(result.stdout)[0],{'state':'recovery_required','used_core':1,'used_container':1})
        def test_15_expired_started_reservation_is_not_released(self):
            self.fail=True;self.start();self.join();r=self.row()
            with self.s.connect() as db:db.execute('UPDATE project_budget_reservations SET expires=0')
            with self.assertRaises(ValueError):budgets.lifecycle(self.s,self.project,self.body['operation'],'release',r['revision'])
            with self.s.connect() as db:
                snap=budgets.snapshot(db,self.project);self.assertIn(self.body['operation'],snap['recovery_required'])
                self.assertEqual(snap['remaining']['core_requests'],0)
        def test_16_corrupt_reservation_fails_closed(self):
            self.start();self.join()
            with self.s.connect() as db:db.execute("UPDATE project_budget_reservations SET state='CORRUPT_TEST'")
            with self.assertRaisesRegex(ValueError,'Corrupted'):self.start(body={**self.body,'operation':uuid.uuid4().hex})
            self.assertEqual(len(self.life.workers),1)
        def test_17_concurrent_duplicate_admission(self):
            barrier=threading.Barrier(8)
            def attempt(_):
                barrier.wait()
                try:return self.start()
                except Denied as e:self.assertEqual(str(e),'BUSY');return None
            with concurrent.futures.ThreadPoolExecutor(8) as pool:values=list(pool.map(attempt,range(8)))
            self.join();self.assertEqual(len(set(v for v in values if v)),1)
            self.assertEqual(self.calls.count('core'),1);self.assertEqual(len(self.life.workers),1)
        def test_18_disabled_or_unauthenticated_cannot_fall_through(self):
            with self.assertRaises(Denied):budgeted_repair.dispatch(self.ctx.app,None,self.body)
            self.ctx.repair_fixture=None
            with self.assertRaisesRegex(Denied,'TEST_REPAIR_UNAVAILABLE'):self.start()
            self.assertIsNone(self.row());self.assertFalse(self.life.workers)
        def test_19_emergency_is_separate_from_shutdown(self):
            self.block=True;w=self.start();self.assertTrue(self.entered.wait(2));self.stop('emergency-stop')
            self.assertTrue(self.cleaning.wait(2));self.assertEqual(self.o.state,'SUSPENDED')
            self.assertFalse(self.o.work[w].done.is_set());self.release.set();self.join()
            self.assertEqual(self.row()['state'],'settled');self.assertEqual(self.o.state,'SUSPENDED')
        def test_20_late_journal_failure_does_not_refund(self):
            original=self.j.write
            def write(operation,phase,**kw):
                if phase=='SUCCEEDED':raise OSError('TEST injected final journal failure')
                return original(operation,phase,**kw)
            with patch.object(self.j,'write',write):self.start();self.join()
            self.assertEqual(self.o.state,'RECOVERY_REQUIRED');self.assertEqual(self.row()['state'],'settled')
            self.assertEqual(self.row()['used_core'],1)
            with self.assertRaises(Denied):self.j.inspect()
        def test_21_sequential_repairs_reuse_only_idle_loop(self):
            budgets.change(self.s,{'action':'budget_configure','project':self.project,'limits':{'core_requests':2,'container_checks':4}})
            first=self.start();self.join()
            second=self.start(body={**self.body,'operation':uuid.uuid4().hex});self.join()
            self.assertNotEqual(first,second);self.assertEqual(self.calls.count('core'),2)
            self.assertFalse(self.ctx.repair_loop.loop.is_running());self.assertFalse(self.ctx.repair_loop.closed)
            self.assertTrue(all(w.outcome=='SUCCEEDED' for w in self.o.work.values()))
        def test_22_missing_loop_records_phase_without_reserving(self):
            host=self.ctx.repair_loop;self.ctx.repair_loop=None
            try:
                w=self.start();self.join();self.assertIsNone(self.row())
                self.assertEqual(self.status(w)['result']['error_type'],'Denied')
                self.assertTrue(self.status(w)['result']['frames']);self.assertEqual(self.o.work[w].outcome,'UNKNOWN')
            finally:self.ctx.repair_loop=host

    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    dest=REPO/'docs/lifecycle-stage4-evidence'/('repair-workers-'+uuid.uuid4().hex+'.json')
    dest.write_text(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
        'details':[s for _,s in result.failures+result.errors],'cases':records,
        'scope':'Actual reservation runner/Store + TEST ownership/lifecycle/journal; synthetic outcomes; injected deadline clock; no App/Core/provider/Podman/media',
        'production_access':False},indent=2));print('EVIDENCE',dest)
    raise SystemExit(not result.wasSuccessful())


if __name__=='__main__':
    if '--controller-recovery-tests' in sys.argv:controller_recovery_tests();raise SystemExit(0)
    if '--repair-loop-audit' in sys.argv:repair_loop_audit();raise SystemExit(0)
    if '--repair-tests' in sys.argv:repair_tests()
    if '--inspection-tests' in sys.argv:inspection_tests()
    if '--ownership-tests' in sys.argv:ownership_tests()
    if len(sys.argv)>1 and sys.argv[1]=='--worker':worker(Path(sys.argv[2]),sys.argv[3],sys.argv[4],sys.argv[5]=='1')
    else:run()
