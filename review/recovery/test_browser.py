import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'review'/'update-history'))
from test_history_browser import *

class RecoveryBrowserTest(unittest.TestCase):
    def test_controls(self):
        with tempfile.TemporaryDirectory() as tmp,sync_playwright() as p:
            store=Store(tmp);workspaces.setup(store);data=runtime.snapshot(store.path)
            browser=p.chromium.launch(channel='chrome',headless=True)
            try:
                page=browser.new_page(viewport={'width':1366,'height':900})
                init=runtime.INIT.replace("Object.defineProperty(window,'JARVIS_INSPECTION',{value:true});",'')
                init=init.replace("'AudioContext','webkitAudioContext',",'')+"Object.defineProperty(window,'AudioContext',{value:undefined});Object.defineProperty(window,'webkitAudioContext',{value:undefined});"
                page.add_init_script(init);errors=[];calls=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                assets={('/' if n=='index.html' else '/'+n):ROOT/'static'/n for n in runtime.STATIC}
                def route(r):
                    path=urlsplit(r.request.url).path
                    if path in assets:return r.fulfill(body=assets[path].read_bytes(),content_type=mimetypes.guess_type(str(assets[path]))[0] or 'text/plain')
                    if path=='/api/recovery':
                        body=r.request.post_data_json;calls.append(body);action=body['action']
                        if action=='create':return r.fulfill(json={'status':'backup_verified','files':12,'id':'a'*32})
                        if action=='list':return r.fulfill(json={'backups':[{'id':'a'*32,'created':1,'bytes':1000}],'location':'test-folder'})
                        if action=='rehearse':return r.fulfill(json={'status':'restore_rehearsal_passed','scope':'Fixture only; live app untouched.'})
                        return r.fulfill(status=400,json={'error':'Existing directory cannot be overwritten.'})
                    payload={'/api/state':data['state'],'/api/history':{'messages':[]},'/api/workspaces':{'projects':[]},'/api/maps/config':{'available':False}}.get(path)
                    return r.fulfill(json=payload or {},status=200 if payload is not None else 403)
                page.route('**/*',route);page.goto('http://127.0.0.1:8765')
                page.wait_for_function("typeof state!=='undefined' && state.data")
                page.get_by_role('button',name='SETTINGS',exact=True).click()
                page.get_by_role('button',name='Create verified backup',exact=True).click()
                page.get_by_text('Backup verified: 12 files.',exact=False).wait_for()
                page.get_by_role('button',name='Test restore in temporary folder').click()
                page.get_by_text('restore rehearsal passed.',exact=False).wait_for()
                page.get_by_role('button',name='Recover to separate folder').click()
                page.get_by_text('Recovery operation did not complete:',exact=False).wait_for()
                self.assertEqual(calls,[{'action':'create'},{'action':'list'},{'action':'rehearse','id':'a'*32},{'action':'restore','id':'a'*32}])
                self.assertEqual(errors,[])
                page.screenshot(path=str(Path(__file__).with_name('preview.png')))
            finally:browser.close()

if __name__=='__main__':unittest.main(defaultTest='RecoveryBrowserTest')
