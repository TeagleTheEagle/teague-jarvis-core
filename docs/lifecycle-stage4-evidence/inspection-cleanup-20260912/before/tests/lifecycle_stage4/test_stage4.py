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


if __name__=='__main__':
    if '--ownership-tests' in sys.argv:ownership_tests()
    if len(sys.argv)>1 and sys.argv[1]=='--worker':worker(Path(sys.argv[2]),sys.argv[3],sys.argv[4],sys.argv[5]=='1')
    else:run()
