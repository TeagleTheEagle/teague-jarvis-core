"""Isolated multi-process Windows evidence. Run directly with -I."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest
import uuid

sys.path.insert(0,str(Path(__file__).absolute().parent))
import harness as h

RUN=h.BASE/('TEST-'+uuid.uuid4().hex)
RUN.mkdir(parents=True)
RESULTS=[]

def events(root,kind=None):
    rows=[h.read(p) for p in root.glob('*.json')]
    return [r for r in rows if r and 'kind' in r and (kind is None or r['kind']==kind)]

def until(predicate,seconds=5):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if predicate():return
        time.sleep(.02)
    raise AssertionError('Condition timed out')

class Tests(unittest.TestCase):
    def setUp(self):self.roots=[];self.children=[]
    def root(self):
        root=RUN/('TEST-'+uuid.uuid4().hex);root.mkdir()
        (root/'TEST_ONLY').write_text('NO PRODUCTION SERVICES')
        self.roots.append(root);return root
    def spawn(self,root,role,phase='normal'):
        p=h.spawn(root,role,phase);self.children.append(p);return p
    def ready_core(self,root):
        p=self.spawn(root,'core');until(lambda:events(root,'core_ready'));return p
    def coord(self,root,phase='normal'):
        (root/'go').touch();p=self.spawn(root,'coordinator',phase);p.wait(6);return p
    def tearDown(self):
        for root in self.roots:(root/'stop').touch()
        for p in self.children:
            if p.poll() is None:p.terminate()
            p.wait(5)
        for root in self.roots:
            # Unmanaged fixture children self-stop; wait for the actual recorded identity to exit.
            for row in events(root,'core_acquired'):
                identity=row['identity']
                until(lambda:h.process_identity(identity['pid'])!=identity,5)
            rows=events(root)
            RESULTS.append({'test':self.id(),'namespace':str(root),'events':rows})
            # Each acquisition is real CreateFile success. No later owner can acquire while held.
            self.assertLessEqual(len(events(root,'core_acquired')),1)
    def race(self,count):
        for _ in range(4):
            root=self.root();ps=[self.spawn(root,'coordinator') for _ in range(count)]
            time.sleep(.2);(root/'go').touch()
            for p in ps:self.assertEqual(p.wait(8),0)
            self.assertEqual(len(events(root,'startup_owner')),1)
            self.assertEqual(len(events(root,'waiter')),count-1)
            self.assertEqual(len(events(root,'core_acquired')),1)
            self.assertEqual(len(events(root,'handshake')),1)
    def test_01_two_coordinators(self):self.race(2)
    def test_02_many_coordinators(self):self.race(8)
    def test_03_core_independent(self):
        root=self.root();self.ready_core(root)
        with h.Lock(root,'supervisor.lock'):pass
        with self.assertRaises(h.Busy):h.Lock(root,'core.lock')
    def test_04_supervisor_exit_adopts(self):
        for _ in range(3):
            root=self.root();self.coord(root)
            old=h.read(root/'core.json');self.coord(root)
            self.assertEqual(old,h.read(root/'core.json'))
            self.assertEqual(len(events(root,'adopted')),1)
            self.assertEqual(len(events(root,'spawned')),1)
    def test_05_crash_before_spawn(self):
        for _ in range(3):
            root=self.root();self.assertEqual(self.coord(root,'crash-before-spawn').returncode,73)
            self.coord(root);self.assertEqual(len(events(root,'spawned')),1)
    def test_06_crash_after_spawn(self):
        for _ in range(3):
            root=self.root();self.assertEqual(self.coord(root,'crash-after-spawn').returncode,75)
            self.coord(root) # Must not spawn even if metadata is still missing.
            until(lambda:events(root,'core_ready'))
            self.coord(root)
            self.assertTrue(events(root,'adopted'))
            self.assertEqual(len(events(root,'spawned')),1)
    def test_07_core_crash_releases(self):
        for phase in ('crash-locked','crash-ready'):
            root=self.root();p=self.spawn(root,'core',phase);p.wait(5)
            self.assertIn(p.returncode,(71,72))
            with h.Lock(root,'core.lock'):pass
    def test_08_stale_metadata_not_identity(self):
        root=self.root();h.write(root/'core.json',{'pid':os.getpid(),'created':0,'mode':'TEST'})
        self.assertFalse(h.reconcile(root))
        self.coord(root);self.assertFalse(events(root,'adopted'))
        self.assertTrue(events(root,'spawned'))
    def test_09_uncertain_locked_core(self):
        root=self.root();p=self.spawn(root,'hold','core.lock')
        until(lambda:events(root,'holding'));self.coord(root)
        self.assertTrue(events(root,'RECOVERY_REQUIRED'));self.assertFalse(events(root,'spawned'))
    def test_10_stop_start_races(self):
        for _ in range(4):
            root=self.root();self.ready_core(root);(root/'go').touch()
            ps=[self.spawn(root,'coordinator',phase) for phase in ('stop','normal','normal','stop')]
            for p in ps:p.wait(6)
            self.assertFalse(events(root,'spawned'))
    def test_11_no_handle_inheritance(self):
        for name in ('supervisor.lock','core.lock'):
            root=self.root();p=self.spawn(root,'inherit',name)
            until(lambda:events(root,'child'));pid=events(root,'child')[0]['child']
            p.wait(4);self.assertIsNotNone(h.process_identity(pid))
            with h.Lock(root,name):pass
    def test_12_same_user_core_contention(self):
        for _ in range(4):
            root=self.root();ps=[self.spawn(root,'core') for _ in range(8)]
            until(lambda:len(events(root,'busy'))==7)
            self.assertEqual(len(events(root,'core_acquired')),1)
    @unittest.skip('No second Windows session or fast-user-switching action authorized/performed')
    def test_13_cross_session(self):pass
    def test_14_invalid_denied_reparse(self):
        root=self.root()
        with self.assertRaises(ValueError):h.Lock(root/'missing','core.lock')
        (root/'core.lock').mkdir()
        with self.assertRaises(ValueError):h.Lock(root,'core.lock')
        other=self.root();target=other/'core.lock';target.touch()
        h.k.SetFileAttributesW.argtypes=[h.w.LPCWSTR,h.w.DWORD]
        self.assertTrue(h.k.SetFileAttributesW(str(target),1))
        try:
            with self.assertRaises(OSError) as cm:h.Lock(other,'core.lock')
            self.assertEqual(cm.exception.errno,5)
        finally:h.k.SetFileAttributesW(str(target),128)
        link=other/'junction'
        result=subprocess.run(['cmd.exe','/d','/c','mklink','/J',str(link),str(root)],capture_output=True)
        self.assertEqual(result.returncode,0)
        with self.assertRaises(ValueError):h.Lock(link,'supervisor.lock')
    def test_15_more_crash_boundaries(self):
        for phase in ('crash-intent','crash-handshake'):
            for _ in range(3):
                root=self.root();p=self.coord(root,phase)
                self.assertIn(p.returncode,(74,76));self.coord(root)
                if phase=='crash-intent':
                    self.assertFalse(events(root,'spawned'));self.assertTrue(events(root,'RECOVERY_REQUIRED'))
                else:self.assertEqual(len(events(root,'spawned')),1);self.assertTrue(events(root,'adopted'))
    def test_16_foreign_namespace_rejected(self):
        with self.assertRaises(ValueError):h.Lock(Path(__file__).parent,'core.lock')
    def test_17_terminateprocess_releases(self):
        root=self.root();p=self.ready_core(root);p.terminate();p.wait(5)
        with h.Lock(root,'core.lock'):pass
    def test_18_stop_latch_prevents_restart(self):
        root=self.root();p=self.ready_core(root)
        self.coord(root,'stop');p.wait(5)
        self.coord(root)
        self.assertFalse(events(root,'spawned'))
    def test_19_live_pid_wrong_creation_rejected(self):
        root=self.root();p=self.ready_core(root)
        metadata=h.read(root/'core.json');metadata['created']+=1
        h.write(root/'core.json',metadata);self.coord(root)
        self.assertTrue(events(root,'RECOVERY_REQUIRED'))
        self.assertFalse(events(root,'spawned'))
    def test_20_locked_missing_identity_repeated(self):
        for _ in range(3):
            root=self.root();p=self.spawn(root,'hold','core.lock')
            until(lambda:events(root,'holding'))
            h.write(root/'core.json',{'mode':'TEST','namespace':root.name,'pid':os.getpid(),'created':0})
            self.coord(root);self.assertFalse(events(root,'spawned'))
            self.assertTrue(events(root,'RECOVERY_REQUIRED'))

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    h.write(RUN/'results.json',{'run':str(RUN),'tests':result.testsRun,'failures':len(result.failures),
        'errors':len(result.errors),'skipped':[str(x[1]) for x in result.skipped],
        'failure_details':[detail for _,detail in result.failures+result.errors],
        'cases':RESULTS,'platform':sys.getwindowsversion().platform_version,
        'scope':'TEST ONLY cooperative processes; not production authentication'})
    print('EVIDENCE',RUN/'results.json')
    sys.exit(not result.wasSuccessful())
