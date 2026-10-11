"""Real frontend layout with synthetic data and all network requests intercepted."""
import mimetypes
from pathlib import Path
import sys
import tempfile
import unittest
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / 'review/inspection-deps'), str(ROOT)]
import inspection_runtime as runtime
from store import Store
import workspaces
from playwright.sync_api import sync_playwright
from panel_registry import WORKSPACE_PANELS


class TaskLayoutTests(unittest.TestCase):
    def test_workspace_scroll_preserves_companion_and_draft(self):
        with tempfile.TemporaryDirectory() as tmp, sync_playwright() as pw:
            store = Store(tmp)
            workspaces.setup(store)
            data = runtime.snapshot(store.path)
            browser = pw.chromium.launch(channel='chrome', headless=True)
            page = browser.new_page(reduced_motion='reduce')
            page.add_init_script(runtime.INIT)
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            assets = {('/' if name == 'index.html' else '/' + name): ROOT / 'static' / name for name in runtime.STATIC}
            def route(request):
                path = urlsplit(request.request.url).path
                if request.request.method != 'GET':
                    return request.abort()
                if path in assets:
                    return request.fulfill(body=assets[path].read_bytes(), content_type=mimetypes.guess_type(str(assets[path]))[0] or 'text/plain')
                payload = {'/api/state': data['state'], '/api/history': {'messages': []}, '/api/workspaces': {'projects': []}, '/api/maps/config': {'available': False}}.get(path)
                request.fulfill(json=payload if payload is not None else {}, status=200 if payload is not None else 403)
            page.route('**/*', route)
            page.goto('http://127.0.0.1:8765')
            page.wait_for_function("typeof state!=='undefined' && state.data && document.getElementById('mapsView')")
            page.evaluate("document.getElementById('messageInput').value='Keep my draft'")
            for width, height in [(1920, 1080), (1366, 768), (1024, 768), (390, 844)]:
                page.set_viewport_size({'width': width, 'height': height})
                for panel in WORKSPACE_PANELS:
                    if panel == 'command':
                        continue
                    page.evaluate('name=>view(name)', panel)
                    page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
                    result = page.evaluate("""name=>{
                      const root=document.getElementById(name+'View'), companion=document.getElementById('jarvisCompanion');
                      root.scrollTop=root.scrollHeight;
                      const a=companion.getBoundingClientRect(), b=root.getBoundingClientRect();
                      return {top:b.top,bottom:b.bottom,companionBottom:a.bottom,height:b.height,
                        docOverflow:document.documentElement.scrollWidth-innerWidth,
                        docked:companion.firstElementChild.classList.contains('scroll-compact'),
                        reachedEnd:root.scrollHeight-root.clientHeight-root.scrollTop<2};
                    }""", panel)
                    with self.subTest(panel=panel, viewport=(width, height)):
                        self.assertGreaterEqual(result['top'], result['companionBottom'])
                        self.assertLessEqual(result['bottom'], height)
                        self.assertGreater(result['height'], 100)
                        self.assertLessEqual(result['docOverflow'], 1)
                        self.assertFalse(result['docked'])
                        self.assertTrue(result['reachedEnd'])
                self.assertEqual(page.locator('#messageInput').input_value(), 'Keep my draft')
                page.evaluate("view('settings')")
                page.screenshot(path=str(ROOT / 'review' / f'task-layout-{width}.png'))
            page.set_viewport_size({'width':1920,'height':1080})
            page.evaluate("view('command')")
            self.assertGreater(page.locator('.core-visual').bounding_box()['width'], 400)
            self.assertEqual(page.locator('.core-panel').count(), 1)
            self.assertEqual(errors, [])
            self.assertEqual(page.evaluate('window.__inspectionAttempts'), [])
            browser.close()


if __name__ == '__main__':
    unittest.main()
