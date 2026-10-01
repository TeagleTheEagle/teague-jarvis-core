import mimetypes
from pathlib import Path
import sys
import tempfile
import unittest
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'review'/'inspection-deps')]
import inspection_runtime as runtime
from store import Store
import workspaces
from playwright.sync_api import sync_playwright

class HistoryBrowserTest(unittest.TestCase):
    def test_history_ui(self):
        import hashlib
        with tempfile.TemporaryDirectory() as tmp,sync_playwright() as p:
            store=Store(tmp);workspaces.setup(store);data=runtime.snapshot(store.path)
            browser=p.chromium.launch(channel='chrome',headless=True)
            try:
                page=browser.new_page(viewport={'width':1366,'height':900},reduced_motion='reduce')
                init=runtime.INIT.replace("Object.defineProperty(window,'JARVIS_INSPECTION',{value:true});",'')
                init=init.replace("'AudioContext','webkitAudioContext',",'')+"Object.defineProperty(window,'AudioContext',{value:undefined});Object.defineProperty(window,'webkitAudioContext',{value:undefined});"
                page.add_init_script(init)
                errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                assets={('/' if name=='index.html' else '/'+name):ROOT/'static'/name for name in runtime.STATIC}
                hashes={'static/'+name:hashlib.sha256((ROOT/'static'/name).read_bytes()).hexdigest() for name in ['app.js','assistant-controls.js']}
                def route(r):
                    path=urlsplit(r.request.url).path
                    if path in assets:
                        raw=assets[path].read_bytes()
                        if path in ['/app.js','/assistant-controls.js']:
                            import json
                            raw+= (';window.JARVIS_LOADED_ASSETS='+json.dumps(hashes)+';').encode()
                        return r.fulfill(body=raw,content_type=mimetypes.guess_type(str(assets[path]))[0] or 'text/plain')
                    if path=='/api/tool':
                        return r.fulfill(json={'changes':[],'updates':{'source_revision':'test123','backend_start_revision':'test123','source_changed_since_backend_start':False,'frontend_files':hashes,'releases':[{'date':'2026-09-09','title':'Recorded update','summary':'<script>untrusted</script> is plain text','validation':'Mock UI test only'}],'observations':[{'observed_at':1,'revision':'test123','kind':'initial_baseline','changed_files':['server.py'],'verification':'Not runtime verification'}]}})
                    payload={'/api/state':data['state'],'/api/history':{'messages':[]},'/api/workspaces':{'projects':[]},'/api/maps/config':{'available':False}}.get(path)
                    r.fulfill(json=payload or {},status=200 if payload is not None else 403)
                page.route('**/*',route);page.goto('http://127.0.0.1:8765')
                page.wait_for_function("typeof state!=='undefined' && state.data")
                page.get_by_role('button',name='CHANGE HISTORY',exact=True).click()
                page.get_by_text('Loaded main interface scripts match the latest source.',exact=False).wait_for()
                self.assertIn('<script>untrusted</script>',page.locator('#changesView').inner_text())
                self.assertEqual(page.locator('#changesView script').count(),0)
                page.screenshot(path=str(Path(__file__).with_name('history-preview.png')))
                self.assertEqual(errors,[])
            finally:browser.close()

if __name__=='__main__':unittest.main()
