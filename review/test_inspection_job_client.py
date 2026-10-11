"""Real browser UI with synthetic jobs, no model calls or private records."""
from pathlib import Path
import unittest
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent.parent

class ClientTests(unittest.TestCase):
    def test_natural_whole_request_and_one_job(self):
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='chrome',headless=True)
            try:
                page=browser.new_page()
                page.set_content('<nav><button class="nav" data-view="communications">Communications</button><button class="nav" data-view="projects">Projects</button></nav><div id="communicationsView"></div><div id="projectsView"></div><div class="conversation-actions"></div><textarea id="draft">Keep my draft</textarea>')
                page.add_script_tag(content='''
                let calls=[],ordinary=[],jobStatus='completed';const state={data:{capabilities:{vision_provider:'TEST'}}};
                async function send(text){ordinary.push(text);}
                async function api(path,body){calls.push(body);if(body.operation==='start')return {job_id:'fixture'};
                  if(body.operation==='cancel'){jobStatus='cancelled';return {};}
                  return {id:'fixture',status:jobStatus,panels:['communications','projects'],results:[{requested_panel:'communications',assessment_mode:'visual_analysis',analysis:'Readable headings',screenshots:[]}],review:'Combined visual findings',review_status:'consolidated'};
                }
                ''')
                page.add_script_tag(path=str(ROOT/'static/inspection-client.js'))
                page.evaluate("send('Hey Jarvis, inspect the whole interface and suggest improvements.')")
                page.wait_for_function('!document.querySelector("#inspectionStart").disabled')
                self.assertEqual(page.evaluate('calls.filter(c=>c.operation==="start").length'),1)
                self.assertEqual(page.evaluate('calls[0].request.panel'),'all')
                self.assertEqual(page.evaluate('calls[0].request.scope'),'full_panel')
                self.assertTrue(page.evaluate('calls[0].transmit'))
                self.assertEqual(page.evaluate('ordinary.length'),0)
                self.assertIn('Combined visual findings',page.locator('#inspectionResults').inner_text())
                self.assertEqual(page.locator('#draft').input_value(),'Keep my draft')
                page.locator('#inspectionClose').click()
                page.evaluate("send('Give me a prompt to inspect the whole interface')")
                self.assertEqual(page.evaluate('ordinary.length'),1)
                page.evaluate("jobStatus='running';send('Inspect the entire application')")
                page.wait_for_function('document.querySelector("#inspectionStop").disabled===false')
                page.locator('#inspectionStop').click()
                page.wait_for_function('!document.querySelector("#inspectionStart").disabled')
                self.assertIn('cancelled',page.locator('#inspectionStatus').inner_text())
                self.assertIn('Combined visual findings',page.locator('#inspectionResults').inner_text())
            finally:browser.close()

if __name__=='__main__':unittest.main(verbosity=2)
