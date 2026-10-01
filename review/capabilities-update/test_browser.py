import mimetypes
from pathlib import Path
import sys
import tempfile
import unittest
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parent/'candidate'
sys.path[:0]=[str(ROOT),str(ROOT.parent.parent/'inspection-deps')]
import inspection_runtime as runtime
from store import Store
import workspaces
from playwright.sync_api import sync_playwright

class BrowserTests(unittest.TestCase):
    def test_controls_use_real_state_and_archive_ui(self):
        with tempfile.TemporaryDirectory() as tmp,sync_playwright() as p:
            store=Store(tmp);workspaces.setup(store);data=runtime.snapshot(store.path)
            browser=p.chromium.launch(channel='chrome',headless=True)
            try:
                page=browser.new_page(viewport={'width':1366,'height':900},reduced_motion='reduce')
                # Device/network functions stay denied. Remove only inspection mode
                # and the absent bridge declaration so the app UI can be exercised.
                init=runtime.INIT.replace("Object.defineProperty(window,'JARVIS_INSPECTION',{value:true});",'').replace("Object.defineProperty(window,'jarvisDesktop',{value:undefined});",'')
                init=init.replace("'AudioContext','webkitAudioContext',",'')+"Object.defineProperty(window,'AudioContext',{value:undefined});Object.defineProperty(window,'webkitAudioContext',{value:undefined});"
                page.add_init_script(init)
                errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                assets={('/' if name=='index.html' else '/'+name):ROOT/'static'/name for name in runtime.STATIC}
                requests=[]
                def route(r):
                    path=urlsplit(r.request.url).path
                    if path in assets:return r.fulfill(body=assets[path].read_bytes(),content_type=mimetypes.guess_type(str(assets[path]))[0] or 'text/plain')
                    if path=='/api/tool':
                        body=r.request.post_data_json;requests.append(body)
                        if body['name']=='inspection_reports':return r.fulfill(json={'status':'archived','report':'# Saved inspection\n\nSettings: spacing improved. Runtime verification pending.'})
                        if body['name']=='inspection_findings':return r.fulfill(json={'findings':[]})
                    payload={'/api/state':data['state'],'/api/history':{'messages':[]},'/api/workspaces':{'projects':[]},'/api/maps/config':{'available':False}}.get(path)
                    r.fulfill(json=payload or {},status=200 if payload is not None else 403)
                page.route('**/*',route)
                page.goto('http://127.0.0.1:8765')
                page.wait_for_function("typeof state!=='undefined' && state.data && typeof performAssistantControl==='function'")
                result=page.evaluate('''async()=>{
                  const hits={show:0,hide:0,mic:0,screen:0,speech:0};let visible=false;
                  window.jarvisDesktop={showCompanion:async()=>{hits.show++;visible=true;return {shown:true};},hideCompanion:async()=>{hits.hide++;visible=false;return {visible};},companionStatus:async()=>({visible})};
                  toggleMic=async()=>{hits.mic++;state.mic=true;voice.stream={getAudioTracks:()=>[{readyState:'live',enabled:true}]};};
                  disableMic=()=>{state.mic=false;voice.stream=null;};stopSpeech=()=>{hits.speech++;};
                  startDesktopLive=async()=>{hits.screen++;screenStream={getVideoTracks:()=>[{readyState:'live'}]};};
                  stopScreenVision=()=>{screenStream=null;};
                  const shown=await performAssistantControl('show_hologram');
                  const afterShow={...hits};const current=await performAssistantControl('hologram_status');
                  const hidden=await performAssistantControl('hide_hologram');
                  const unmuted=await performAssistantControl('unmute');const muted=await performAssistantControl('mute');
                  const mic=await performAssistantControl('microphone_status');const stopped=await performAssistantControl('stop_speaking');
                  const sharing=await performAssistantControl('start_sharing');const screen=await performAssistantControl('screen_status');const ended=await performAssistantControl('stop_sharing');
                  window.jarvisDesktop=null;const permission=await performAssistantControl('start_sharing');document.querySelectorAll('dialog[open]').forEach(d=>d.close());
                  const negative=['Explain how to show hologram','Write a prompt: mute microphone','Do not mute my mic'].map(assistantControlIntent);
                  const positive=['activate hologram','hide hologram','mute mic','unmute mic','stop speaking'].map(assistantControlIntent);
                  return {shown,afterShow,current,hidden,unmuted,muted,mic,stopped,sharing,screen,ended,permission,negative,positive};
                }''')
                self.assertTrue(result['shown']['active']);self.assertEqual(result['afterShow']['mic'],0);self.assertEqual(result['afterShow']['screen'],0)
                self.assertTrue(result['current']['active']);self.assertFalse(result['hidden']['active'])
                self.assertTrue(result['unmuted']['active']);self.assertFalse(result['muted']['active']);self.assertFalse(result['mic']['active'])
                self.assertEqual(result['stopped']['status'],'completed');self.assertTrue(result['sharing']['active']);self.assertTrue(result['screen']['active']);self.assertFalse(result['ended']['active'])
                self.assertEqual(result['permission']['status'],'permission_required')
                self.assertEqual(result['negative'],[None,None,None]);self.assertTrue(all(result['positive']))
                page.evaluate("view('communications')")
                page.get_by_role('button',name='INSPECTION ARCHIVE',exact=True).click()
                page.get_by_text('Saved evidence loaded. Original inspection reports are preserved.').wait_for()
                page.screenshot(path=str(ROOT.parent/'archive-preview.png'))
                self.assertEqual(requests[-1]['name'],'inspection_reports')
                self.assertEqual(errors,[])
            finally:browser.close()

if __name__=='__main__':unittest.main(verbosity=2)
