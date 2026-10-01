import json
from pathlib import Path
import sys
import time
import threading
import urllib.error
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent/'candidate'))
from test_jarvis import HTTPTests
from server import Run

class CapabilityRoutes(HTTPTests):
    def test_single_inspection_archives_actual_returned_findings(self):
        import assistant_capabilities as cap
        with self.server.app.store.connect() as db:db.execute('INSERT INTO workspaces VALUES (?,?)',(cap.PROJECT_ID,'Project Jarvis'))
        result={'requested_panel':'settings','assessment_mode':'visual_analysis','analysis':json.dumps({'review':'Readable except one label.','findings':[{'description':'A label overlaps','priority':'high','recommended_action':'Increase spacing'}]}),'stages':{'analysis_completed':'completed','screenshot_captured':'completed'}}
        with patch('providers.capabilities',return_value={'vision':True}),patch('inspection_runtime.run',return_value=result):
            with self.req('/api/interface-inspection',{'request':{'panel':'settings'},'transmit':True}) as response:data=json.load(response)
        self.assertEqual(data['archive']['status'],'archived')
        self.assertEqual(data['analysis'],'Readable except one label.')
        self.assertEqual(self.server.app.inspection_archive.findings()['findings'][0]['status'],'open')
        with self.req('/api/tool',{'name':'inspection_reports','args':{'action':'latest'}}) as response:
            self.assertIn('Readable except',json.load(response)['report'])
    def test_new_routes_keep_auth_and_origin_checks(self):
        for path in ('/api/control-result','/api/inspection-finding'):
            with self.assertRaises(urllib.error.HTTPError) as e:self.req(path,{},cookie=False)
            self.assertEqual(e.exception.code,401)
            with self.assertRaises(urllib.error.HTTPError) as e:self.req(path,{},origin='https://other.example')
            self.assertEqual(e.exception.code,403)
        with self.req('/assistant-controls.js') as response:self.assertIn(b'performAssistantControl',response.read())

    def test_ui_acknowledges_only_pending_run(self):
        run=Run('test');run.user_text='hologram status';results=[]
        thread=threading.Thread(target=lambda:results.append(self.server.app.controls.request('hologram_status',run,2)));thread.start()
        for _ in range(100):
            if run.events:break
            time.sleep(.005)
        body={'id':run.events[0]['data']['id'],'run_id':run.id,'result':{'status':'completed','active':False}}
        with self.req('/api/control-result',body) as response:self.assertTrue(json.load(response)['acknowledged'])
        thread.join(2);self.assertFalse(results[0]['active'])
        with self.assertRaises(urllib.error.HTTPError):self.req('/api/control-result',body)

if __name__=='__main__':
    import unittest
    unittest.main(verbosity=2)
