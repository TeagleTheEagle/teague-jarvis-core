from pathlib import Path
import unittest
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent.parent

class UpdateTests(unittest.TestCase):
    def test_idle_reload_and_activity_guards(self):
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='chrome',headless=True)
            try:
                page=browser.new_page()
                page.set_content('<textarea id="messageInput"></textarea><dialog id="report"></dialog><div id="inspectionResults"></div>')
                page.add_script_tag(content='''
                  const state={data:{},mic:false};let screenStream=null,screenBlob=null,screenSending=false,screenCaptureBusy=false,desktopLiveStarting=false;
                  let tick,receive,calls=[];let now=100000;Date.now=()=>now;window.setInterval=f=>{tick=f;};
                  window.jarvisDesktop={updateStatus:async()=>null,onUpdateAvailable:f=>receive=f,applyUpdate:async r=>{calls.push(r);return {applied:true};}};
                ''')
                page.add_script_tag(path=str(ROOT/'static/desktop-updates.js'))
                page.evaluate('receive({kind:"reload",revision:"test"});now+=30000')
                for guard in ['state.mic','state.busy','state.transcribing','state.attachment','screenStream','screenBlob','screenSending']:
                    page.evaluate(f'{guard}=true;tick()')
                    self.assertEqual(page.evaluate('calls.length'),0,guard)
                    page.evaluate(f'{guard}=false')
                page.evaluate('document.querySelector("#report").showModal();tick()')
                self.assertEqual(page.evaluate('calls.length'),0)
                page.evaluate('document.querySelector("#report").close();document.querySelector("#messageInput").value="unsaved";tick()')
                self.assertEqual(page.evaluate('calls.length'),0)
                page.evaluate('document.querySelector("#messageInput").value="";receive({kind:"restart",revision:"restart"});tick()')
                self.assertEqual(page.evaluate('calls.length'),0,'backend restart must be explicit')
                page.evaluate('receive({kind:"reload",revision:"test"});tick()')
                self.assertEqual(page.evaluate('calls'),['test'])
            finally:browser.close()

if __name__=='__main__':unittest.main(verbosity=2)
