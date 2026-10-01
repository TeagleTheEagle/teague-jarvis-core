"""File/pipe sequencing tests. No Core, provider or production data."""
import contextlib
import io
import json
from pathlib import Path
import queue
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import uuid

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import stage4_runtime as runtime
from fixtures import RestartCampaign

class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='JARVIS-TEST-publication-')
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'coordinator.json'
        self.item={'configuration':{'name':uuid.uuid4().hex},'started':time.monotonic(),
                   'publication_timeout':.3,'publication_queue':queue.Queue(),
                   'publication_state':'NOT_BEGUN','wait_polls':0}
        self.c=RestartCampaign.__new__(RestartCampaign)
    def signal(self,*args,**kwargs):self.item['publication_queue'].put(args[0]+'\n')
    def message(self,state,name=None):
        return 'STAGE4_READINESS '+json.dumps({'name':name or self.item['configuration']['name'],'state':state})+'\n'
    def test_01_in_progress_waits(self):
        reached=threading.Event();release=threading.Event();outcome=[]
        replace=runtime.os.replace
        def held(a,b):
            replace(a,b);reached.set()
            if not release.wait(2):raise TimeoutError('test handoff')
        def writer():
            try:runtime.publish_coordinator_readiness(self.path,{'ok':True},self.item['configuration']['name'])
            except BaseException as e:outcome.append(e)
        with patch('builtins.print',side_effect=self.signal),patch.object(runtime.os,'replace',side_effect=held):
            t=threading.Thread(target=writer);t.start()
            try:
                self.assertTrue(reached.wait(2));self.assertTrue(self.path.exists())
                first=self.item['publication_queue'].get_nowait()
                self.assertIn('PUBLISHING',first)
                self.assertTrue(self.item['publication_queue'].empty())
                self.item['publication_queue'].put(first);release.set()
                self.c.coordinator_publication(self.item)
                self.assertEqual(json.loads(self.path.read_text()),{'ok':True})
            finally:release.set();t.join(2)
        self.assertFalse(t.is_alive());self.assertFalse(outcome)
    def test_02_normal(self):
        with patch('builtins.print',side_effect=self.signal):
            runtime.publish_coordinator_readiness(self.path,{'ok':True},self.item['configuration']['name'])
        self.c.coordinator_publication(self.item)
        self.assertEqual(self.item['publication_state'],'COMPLETE')
        self.assertFalse(list(self.path.parent.glob('*.tmp')))
    def test_03_never_began(self):
        self.item['publication_timeout']=0
        with self.assertRaisesRegex(TimeoutError,'NOT_BEGUN'):self.c.coordinator_publication(self.item)
    def test_04_incomplete(self):
        self.item['publication_queue'].put(self.message('PUBLISHING'));self.item['publication_timeout']=0
        with self.assertRaisesRegex(TimeoutError,'PUBLISHING'):self.c.coordinator_publication(self.item)
    def test_05_original_writer_error(self):
        error=PermissionError(13,'explicit TEST publication fault');error.winerror=32
        with patch('builtins.print',side_effect=self.signal),patch.object(runtime.os,'replace',side_effect=error):
            with self.assertRaises(PermissionError) as caught:
                runtime.publish_coordinator_readiness(self.path,{},self.item['configuration']['name'])
        self.assertIs(caught.exception,error)
        with self.assertRaisesRegex(RuntimeError,'FAILED'):self.c.coordinator_publication(self.item)
        self.assertEqual(self.item['publication_failure']['winerror'],32)
        self.assertIn('PermissionError',self.item['publication_failure']['traceback'])
        self.assertFalse(list(self.path.parent.glob('*.tmp')))
    def test_06_stale_notification(self):
        self.path.write_text('{}')
        self.item['publication_queue'].put(self.message('PUBLISHING','old-instance'))
        with self.assertRaisesRegex(ValueError,'Stale'):self.c.coordinator_publication(self.item)
    def test_07_completion_without_begin_rejected(self):
        self.item['publication_queue'].put(self.message('COMPLETE'))
        with self.assertRaisesRegex(ValueError,'transition'):self.c.coordinator_publication(self.item)
    def test_08_writer_exit(self):
        self.item['publication_queue'].put('')
        with self.assertRaisesRegex(RuntimeError,'exited'):self.c.coordinator_publication(self.item)

if __name__=='__main__':
    output=Path(sys.argv[1]);stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=2,failfast=True).run(unittest.defaultTestLoader.loadTestsFromTestCase(PublicationTests))
    output.write_text(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'log':stream.getvalue()},indent=2))
    print(stream.getvalue());sys.exit(0 if result.wasSuccessful() else 1)
