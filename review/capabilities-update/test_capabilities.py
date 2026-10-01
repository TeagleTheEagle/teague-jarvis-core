import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
import uuid
from unittest.mock import patch

ROOT=Path(__file__).resolve().parent/'candidate'
sys.path.insert(0,str(ROOT))
import assistant_capabilities as cap
import actions
import development
from inspection_jobs import InspectionJobs
from server import App, Run

class CapabilitiesTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.app=App(self.temp.name)
        with self.app.store.connect() as db: db.execute('INSERT INTO workspaces VALUES (?,?)',(cap.PROJECT_ID,'Project Jarvis'))
        self.archive=self.app.inspection_archive

    def job(self, **extra):
        return {'id':uuid.uuid4().hex,'status':'completed','panels':['settings'],'request':{'panel':'settings','scope':'full_panel'},'review':'Settings spacing issue.',
                'results':[{'requested_panel':'settings','status':'analysed','analysis':'Increase label spacing.','stages':{'analysis_completed':'completed'},'visible_text':'PRIVATE INCIDENTAL TEXT','screenshots':[{'reference':'private-image'}],
                            'findings':[{'description':'Settings labels overlap','priority':'high','recommended_action':'Space labels'}]}],**extra}

    def test_immutable_archive_persistence_and_project_link(self):
        job=self.job(); result=self.archive.save(job)
        reopened=cap.Archive(self.app.store)
        record=reopened.read(job['id'])
        self.assertEqual(record['metadata']['status'],'completed')
        self.assertNotIn('PRIVATE INCIDENTAL',record['report'])
        self.assertNotIn('private-image',record['report'])
        self.assertEqual((self.app.store.root/'inspection-archive'/(job['id']+'.md')).read_text(encoding='utf-8'),record['report'])
        with self.app.store.connect() as db:
            self.assertEqual(db.execute('SELECT project FROM workspace_links WHERE ref=?',(result['document_id'],)).fetchone()[0],cap.PROJECT_ID)
            with self.assertRaises(sqlite3.IntegrityError):db.execute("UPDATE inspection_records SET markdown='changed'")

    def test_duplicate_completion_and_recurring_findings(self):
        job=self.job();self.archive.save(job);self.archive.save(job);self.archive.save(self.job())
        self.assertEqual(len(self.archive.list()['inspections']),2)
        findings=self.archive.findings()['findings'];self.assertEqual(len(findings),1)
        self.assertEqual(len(findings[0]['inspection_ids']),2)
        self.assertEqual(len(self.archive.compare()['recurring_finding_ids']),1)

    def test_partial_failed_missing_project_and_running(self):
        job=self.job(status='partial',panels=['settings','maps']);self.archive.save(job)
        self.assertEqual(self.archive.read()['metadata']['skipped_panels'],['maps'])
        self.archive.save(self.job(status='failed',results=[],review='Capture failed.'))
        with self.assertRaises(ValueError):self.archive.save(self.job(status='running'))
        other=cap.Archive(self.app.store,'missing')
        with self.assertRaises(ValueError):other.save(self.job())

    def test_original_not_overwritten_and_credentials_filtered(self):
        job=self.job(review='api_key=private123 /api/interface-inspection/image/'+'a'*32)
        self.archive.save(job);report=self.archive.read()['report']
        self.assertNotIn('private123',report);self.assertNotIn('/api/interface-inspection/image/',report)
        other=self.job();folder=self.app.store.root/'inspection-archive';(folder/(other['id']+'.md')).write_text('original')
        with self.assertRaises(FileExistsError):self.archive.save(other)
        self.assertEqual((folder/(other['id']+'.md')).read_text(),'original')
        self.assertEqual(len(self.archive.list()['inspections']),1)

    def test_database_failure_cleans_only_new_report_file(self):
        job=self.job()
        with self.app.store.connect() as db:db.execute("CREATE TRIGGER deny_test_document BEFORE INSERT ON documents BEGIN SELECT RAISE(ABORT,'simulated write failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):self.archive.save(job)
        self.assertFalse((self.app.store.root/'inspection-archive'/(job['id']+'.md')).exists())
        self.assertEqual(self.archive.list()['inspections'],[])

    def test_tracker_actual_proposal_status_no_automatic_verification(self):
        self.archive.save(self.job());fid=self.archive.findings()['findings'][0]['id']
        self.archive.track(fid,'proposed',{'proposal':'p'})
        proposal={'proposal':'p','path':'static/pro.css','status':'applied','validation':'syntax only'}
        self.archive.refresh_changes([proposal],set())
        self.assertEqual(self.archive.findings()['findings'][0]['status'],'applied but unverified')
        with self.assertRaises(ValueError):self.archive.track(fid,'verified',{'proposal':'p'})
        self.archive.track(fid,'verified',{'validation_id':'user-confirmation','test_result':'passed','note':'Scrolled all settings and saw no overlap','basis':'user confirmation in interface'})
        self.archive.refresh_changes([proposal],set())
        self.assertEqual(self.archive.findings()['findings'][0]['status'],'verified')

    def test_timers_exact_target_persistence_and_failures(self):
        one=self.app.store.reminder('Tea',120);two=self.app.store.reminder('Work',180)
        run=Run('test');run.user_text='cancel my timer'
        with self.assertRaisesRegex(ValueError,'which timer'):self.app.tool('manage_timer',{'action':'cancel','timer_id':one['id']},run)
        run.user_text='cancel Tea timer'
        self.assertEqual(self.app.tool('manage_timer',{'action':'cancel','timer_id':one['id']},run)['status'],'cancelled')
        changed=cap.manage_timer(self.app.store,'adjust',two['id'],60)
        self.assertAlmostEqual(changed['due']-time.time(),60,delta=1)
        with self.assertRaises(ValueError):cap.manage_timer(self.app.store,'adjust',two['id'],float('nan'))
        self.assertEqual(len(cap.manage_timer(self.app.store,'list')['timers']),1)
        self.app.store.due(time.time()+3600)
        with self.assertRaises(ValueError):cap.manage_timer(self.app.store,'cancel',two['id'])

    def test_memory_update_duplicate_credentials_and_missing(self):
        one=self.app.store.put('memory','My name is Jonny');two=self.app.store.put('memory','I enjoy cycling')
        run=Run('test');run.user_text='delete that memory'
        with self.assertRaises(ValueError):self.app.tool('manage_saved_memory',{'action':'delete','item_id':two['id']},run)
        cap.manage_memory(self.app.store,'update',one['id'],'My name is John')
        self.assertEqual(self.app.store.settings()['name'],'John')
        with self.assertRaises(ValueError):cap.manage_memory(self.app.store,'update',two['id'],'My name is John')
        with self.assertRaises(ValueError):cap.manage_memory(self.app.store,'update',two['id'],'password: secret')
        cap.manage_memory(self.app.store,'delete',one['id'])
        with self.assertRaises(ValueError):cap.manage_memory(self.app.store,'update',one['id'],'My name is Jane')
        self.assertEqual(len(self.app.store.items('memory')),1)

    def test_control_ack_timeout_cancel_and_untrusted_input(self):
        run=Run('test');run.user_text='show hologram'
        result=[];thread=threading.Thread(target=lambda:result.append(self.app.controls.request('show_hologram',run,1)));thread.start()
        for _ in range(100):
            if run.events:break
            time.sleep(.005)
        ident=run.events[0]['data']['id']
        with self.assertRaises(ValueError):self.app.controls.acknowledge(ident,'wrong',{'status':'completed','active':True})
        self.app.controls.acknowledge(ident,run.id,{'status':'completed','active':True});thread.join(2)
        self.assertTrue(result[0]['active'])
        with self.assertRaises(ValueError):self.app.controls.acknowledge(ident,run.id,{'status':'completed'})
        self.assertEqual(self.app.controls.request('show_hologram',run,.01)['status'],'unconfirmed')
        run.cancel.set();self.assertEqual(self.app.controls.request('show_hologram',run,.2)['status'],'cancelled')
        run.user_text='Summarise the attached screenshot'
        with self.assertRaises(ValueError):self.app.controls.request('show_hologram',run)

    def test_job_archive_completion_waits_and_failure_retains_report(self):
        jobs=InspectionJobs();release=threading.Event()
        def finish(job):release.wait(1);return self.archive.save(job)
        def runner(req,cancel):return self.job()['results'][0]
        key=jobs.start({'panel':'settings'},runner,on_finish=finish)['job_id']
        time.sleep(.03);self.assertEqual(jobs.get(key)['status'],'running')
        release.set()
        for _ in range(100):
            if jobs.get(key)['status']!='running':break
            time.sleep(.01)
        self.assertEqual(jobs.get(key)['archive']['status'],'archived')
        broken=InspectionJobs();key=broken.start({'panel':'settings'},runner,on_finish=lambda job:(_ for _ in ()).throw(OSError()))['job_id']
        for _ in range(100):
            if broken.get(key)['status']!='running':break
            time.sleep(.01)
        self.assertEqual(broken.get(key)['archive']['status'],'failed')
        self.assertTrue(broken.get(key)['results'])

    def test_measured_timings_no_transcripts_and_registry(self):
        def chat(messages,tools,emit,cancel,vision):
            emit('assistant.delta',{'text':'Private response text'})
            return {'role':'assistant','content':'Private response text'}
        run=Run('test')
        with patch.dict(os.environ,{'GROQ_API_KEY':'fake-offline-test'}),patch('providers.chat',side_effect=chat):
            self.app.work(run,'Explain a useful topic',None)
        self.assertFalse(any(e['event']=='run.failed' for e in run.events),run.events)
        timing=self.app.tool('response_timings',{})
        self.assertEqual(len(timing['samples']),1)
        self.assertTrue(timing['samples'][0]['provider_calls'][0]['buffered'])
        self.assertNotIn('Private',json.dumps(timing))
        self.assertTrue(any(e['event']=='response.timing' for e in run.events))
        for name in ('assistant_control','inspection_reports','inspection_findings','manage_timer','manage_saved_memory','response_timings'):
            self.assertIn(name,[t['function']['name'] for t in actions.TOOLS])
        self.assertNotIn('server.py',development.ALLOWED)

if __name__=='__main__':unittest.main(verbosity=2)
