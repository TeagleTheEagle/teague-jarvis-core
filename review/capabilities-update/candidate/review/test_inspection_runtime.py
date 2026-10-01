import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(ROOT/'review/inspection-deps'),str(ROOT)]
import inspection_runtime as runtime
from interface_inspection import PANELS
from store import Store
import workspaces


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.store=Store(self.temp.name)
        workspaces.setup(self.store)
        with self.store.connect() as db:
            db.execute("INSERT INTO reminders VALUES ('reminder','SECRET_TOKEN_123',0,0)")
            db.execute("INSERT INTO messages(conversation,role,content,created) VALUES ('secret-id','user','SECRET_TOKEN_123',0)")
            db.execute("INSERT INTO items(id,kind,body,created,updated) VALUES ('secret','memory','SECRET_TOKEN_123',0,0)")
        runtime.IMAGES.clear()

    def tearDown(self):
        self.temp.cleanup()

    def test_readonly_snapshot_redacts_and_preserves_reminder(self):
        before=self.store.path.read_bytes()
        data=runtime.snapshot(self.store.path)
        self.assertNotIn('SECRET_TOKEN',json.dumps(data))
        self.assertEqual(data['state']['reminders'][0]['fired'],0)
        self.assertEqual(before,self.store.path.read_bytes())

    def test_missing_database_not_created(self):
        missing=Path(self.temp.name)/'missing.sqlite'
        with self.assertRaises(sqlite3.OperationalError):runtime.snapshot(missing)
        self.assertFalse(missing.exists())

    def test_no_consent_no_analyzer(self):
        evidence=runtime.new_evidence({'panel':'command'})
        evidence['screenshots']=[{'reference':None}]
        with patch.object(runtime,'capture',return_value=(evidence,[b'png'])),patch.object(runtime,'snapshot',return_value={}),patch('builtins.print'):
            analyzer=unittest.mock.Mock()
            report=runtime.run(ROOT,self.store.path,'http://127.0.0.1:8765',{'panel':'command'},False,analyzer)
            analyzer.assert_not_called()
            self.assertEqual(report['assessment_mode'],'dom_only')

    def test_analyzer_failure_not_completion(self):
        evidence=runtime.new_evidence({'panel':'command'})
        evidence['screenshots']=[{'reference':None}]
        with patch.object(runtime,'capture',return_value=(evidence,[b'png'])):
            result=runtime.run(ROOT,self.store.path,'http://127.0.0.1:8765',{'panel':'command'},True,lambda *a: (_ for _ in ()).throw(ValueError('secret provider error')))
        self.assertEqual(result['stages']['analysis_completed'],'failed')
        self.assertNotIn('secret provider error',json.dumps(result))

    def test_actual_capture_bytes_delivered_to_analyzer(self):
        evidence=runtime.new_evidence({'panel':'command'})
        evidence['screenshots']=[{'reference':None}]
        evidence['stages']['screenshot_captured']='completed'
        pixels=b'\x89PNG\r\n\x1a\nTEST_CAPTURE'
        analyzer=unittest.mock.Mock(return_value='Image 1: observed heading spacing.')
        with patch.object(runtime,'capture',return_value=(evidence,[pixels])):
            result=runtime.run(ROOT,self.store.path,'http://127.0.0.1:8765',{'panel':'command'},True,analyzer,'TEST')
        self.assertEqual(analyzer.call_args.args[0],[pixels])
        self.assertEqual(result['stages']['analysis_completed'],'completed')
        self.assertEqual(result['assessment_mode'],'visual_analysis')

    def test_capture_failure_releases_lock(self):
        with patch.object(runtime,'capture',side_effect=TimeoutError()):
            result=runtime.run(ROOT,self.store.path,'http://127.0.0.1:8765',{'panel':'command'})
        self.assertTrue(result['errors'])
        self.assertFalse(runtime.LOCK.locked())

    def test_expired_capture_removed(self):
        runtime.IMAGES['expired']=(time.monotonic()-1,b'private')
        self.assertIsNone(runtime.image_get('expired'))
        self.assertNotIn('expired',runtime.IMAGES)

    def test_invalid_origins(self):
        for origin in ('https://example.com','http://localhost:8765','http://127.0.0.1:8765@evil.test','http://127.0.0.1:8765/path'):
            with self.subTest(origin=origin),self.assertRaises(ValueError):
                runtime.capture(ROOT,origin,{'panel':'command','scope':'viewport','focus':''},{})

    def test_parallel_job_rejected(self):
        runtime.LOCK.acquire()
        try:
            with self.assertRaises(ValueError):runtime.run(ROOT,self.store.path,'http://127.0.0.1:8765',{'panel':'command'})
        finally:runtime.LOCK.release()

    def test_bounded_long_panel_and_other_page_unchanged(self):
        if '--browser' not in sys.argv_original:self.skipTest('Real browser test')
        from playwright.sync_api import sync_playwright
        with self.store.connect() as db:
            for _ in range(130):db.execute("INSERT INTO messages(conversation,role,content,created) VALUES ('test','user','SECRET_TOKEN_123',0)")
        data=runtime.snapshot(self.store.path)
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='chrome',headless=True)
            try:
                tab=browser.new_page()
                tab.set_content('<input id="draft" value="keep this"><div style="height:3000px">Projects</div>')
                tab.evaluate('window.scrollTo(0,300)')
                before=tab.evaluate('({url:location.href,scroll:scrollY,draft:document.querySelector("input").value})')
                # A second Playwright sync context cannot nest on this thread;
                # invoke the worker on its own thread like the HTTP server does.
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    report,images=pool.submit(runtime.capture,ROOT,'http://127.0.0.1:8765',{'panel':'communications','scope':'full_panel','focus':''},data).result(timeout=50)
                after=tab.evaluate('({url:location.href,scroll:scrollY,draft:document.querySelector("input").value})')
                self.assertEqual(before,after)
                self.assertGreater(len(images),1)
                self.assertLessEqual(len(images),6)
                self.assertEqual(report['coverage'],'bounded_sections')
                self.assertTrue(report['omissions'])
                self.assertNotIn('SECRET_TOKEN',json.dumps(report))
            finally:browser.close()

    def test_real_all_panels(self):
        if '--browser' not in sys.argv_original:
            self.skipTest('Pass --browser for real isolated Chrome tests')
        data=runtime.snapshot(self.store.path)
        before=self.store.path.read_bytes()
        results=[]
        for panel in PANELS:
            with self.subTest(panel=panel):
                started=time.perf_counter()
                report, images=runtime.capture(ROOT,'http://127.0.0.1:8765',{'panel':panel,'scope':'viewport','focus':''},data)
                self.assertEqual(report['verified_panel'],panel)
                self.assertEqual(report['isolation']['side_effect_attempts'],[])
                self.assertNotIn('SECRET_TOKEN',json.dumps(report))
                self.assertTrue(images[0].startswith(b'\x89PNG'))
                (ROOT/'review'/('inspection-test-'+panel+'.png')).write_bytes(images[0])
                results.append({'panel':panel,'elapsed_ms':round((time.perf_counter()-started)*1000),'isolation':report['isolation']})
        self.assertEqual(before,self.store.path.read_bytes())
        (ROOT/'review/inspection-browser-results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')


if __name__=='__main__':
    sys.argv_original=list(sys.argv)
    sys.argv=[x for x in sys.argv if x!='--browser']
    unittest.main(verbosity=2)
