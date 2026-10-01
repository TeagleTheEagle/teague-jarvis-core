from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import threading
import time
import unittest
from inspection_jobs import InspectionJobs
from interface_inspection import PANELS,tool_schema
from panel_registry import NAVIGATION_PANELS

class JobsTests(unittest.TestCase):
    def wait(self,jobs,key):
        for _ in range(200):
            result=jobs.get(key)
            if result['status']!='running':return result
            time.sleep(.01)
        self.fail('Job did not finish')
    def result(self,request,event):
        return {'requested_panel':request['panel'],'analysis':'Observed spacing issue in '+request['panel'],
                'stages':{'screenshot_captured':'completed','analysis_completed':'completed'}}
    def test_all_panels_one_job_and_consolidated_review(self):
        jobs=InspectionJobs();calls=[]
        def runner(request,event):calls.append(request);return self.result(request,event)
        key=jobs.start({'panel':'all'},runner,lambda results,event:'Combined: '+', '.join(r['requested_panel'] for r in results))['job_id']
        result=self.wait(jobs,key)
        self.assertEqual(result['status'],'completed')
        self.assertEqual([r['panel'] for r in calls],list(PANELS))
        self.assertTrue(all(r['scope']=='full_panel' for r in calls))
        self.assertEqual(result['review_status'],'consolidated')
        self.assertTrue(all(r['finished_at'] for r in result['results']))
        self.assertEqual(tuple(PANELS),tuple(p for p in NAVIGATION_PANELS if p!='screen_vision'))
        self.assertIn('all',tool_schema()['function']['parameters']['properties']['panel']['enum'])
    def test_partial_failure_retains_other_panels(self):
        jobs=InspectionJobs()
        def runner(request,event):
            if request['panel']=='projects':raise RuntimeError('private error must not escape')
            return self.result(request,event)
        key=jobs.start({'panel':'all'},runner,lambda *args: (_ for _ in ()).throw(RuntimeError('offline')))['job_id']
        result=self.wait(jobs,key)
        self.assertEqual(result['status'],'partial')
        self.assertEqual(len(result['results']),len(PANELS))
        self.assertEqual(result['results'][5]['status'],'failed')
        self.assertNotIn('private error',str(result))
        self.assertEqual(result['review_status'],'combined_panel_reports')
    def test_cancellation_keeps_current_result(self):
        jobs=InspectionJobs();entered=threading.Event();release=threading.Event()
        def runner(request,event):entered.set();release.wait(2);return self.result(request,event)
        key=jobs.start({'panel':'all'},runner)['job_id']
        self.assertTrue(entered.wait(1))
        with self.assertRaises(ValueError):jobs.start({'panel':'all'},runner)
        jobs.cancel(key);release.set();result=self.wait(jobs,key)
        self.assertEqual(result['status'],'cancelled');self.assertEqual(len(result['results']),1)
    def test_timeout_does_not_claim_completion(self):
        jobs=InspectionJobs();key=jobs.start({'panel':'all'},self.result,budget=0)['job_id']
        result=self.wait(jobs,key)
        self.assertEqual(result['status'],'timed_out');self.assertEqual(result['results'],[])

if __name__=='__main__':unittest.main(verbosity=2)
