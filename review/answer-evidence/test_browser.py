import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'review'/'update-history'))
from test_history_browser import mimetypes,tempfile,unittest,urlsplit,runtime,sync_playwright
from unittest.mock import patch
from server import App,Run
import providers

class EvidenceBrowserTest(unittest.TestCase):
    def test_real_fixture_events(self):
        with tempfile.TemporaryDirectory() as tmp,sync_playwright() as p:
            app=App(tmp);app.store.task_put('<script>test</script> task')
            run=Run('fixture')
            with patch('actions.news_search',side_effect=providers.ProviderError('offline')):
                app.work(run,'Give me my daily briefing',None)
            data=runtime.snapshot(app.store.path)
            browser=p.chromium.launch(channel='chrome',headless=True)
            try:
                page=browser.new_page(viewport={'width':1366,'height':900})
                init=runtime.INIT.replace("Object.defineProperty(window,'JARVIS_INSPECTION',{value:true});",'')
                init=init.replace("'AudioContext','webkitAudioContext',",'')+"Object.defineProperty(window,'AudioContext',{value:undefined});Object.defineProperty(window,'webkitAudioContext',{value:undefined});"
                page.add_init_script(init);errors=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                assets={('/' if n=='index.html' else '/'+n):ROOT/'static'/n for n in runtime.STATIC}
                def route(r):
                    path=urlsplit(r.request.url).path
                    if path in assets:return r.fulfill(body=assets[path].read_bytes(),content_type=mimetypes.guess_type(str(assets[path]))[0] or 'text/plain')
                    payload={'/api/state':data['state'],'/api/history':{'messages':[]},'/api/workspaces':{'projects':[]},'/api/maps/config':{'available':False},'/api/chat':{'run_id':run.id},'/api/runs/'+run.id+'/events':{'events':run.events,'done':True}}.get(path)
                    r.fulfill(json=payload or {},status=200 if payload is not None else 403)
                page.route('**/*',route);page.goto('http://127.0.0.1:8765')
                page.wait_for_function("typeof state!=='undefined' && state.data")
                page.get_by_role('button',name='COMMUNICATIONS',exact=True).click()
                page.evaluate("send('Give me my daily briefing',null,{quiet:true})")
                note=page.locator('.reply-evidence');note.wait_for()
                self.assertIn('partial',note.inner_text());self.assertIn('checked',note.inner_text())
                self.assertIn("I couldn't get the news",page.locator('body').inner_text())
                page.get_by_text('Briefing sources and check times',exact=True).click()
                self.assertIn('News: could not check',page.locator('body').inner_text())
                self.assertIn('<script>test</script> task',page.locator('body').inner_text())
                self.assertEqual(page.locator('.message script').count(),0)
                self.assertEqual(errors,[])
                page.screenshot(path=str(Path(__file__).with_name('preview.png')))
            finally:browser.close()

if __name__=='__main__':unittest.main()
