from pathlib import Path
import sys
r=Path(__file__).resolve().parents[1];sys.path.insert(0,str(r/'review/inspection-deps'))
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
 b=p.chromium.launch(channel='chrome',headless=True);page=b.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.add_init_script("window.companion={onState:cb=>window.receive=cb,action:()=>{}}")
 page.goto((r/'desktop/companion.html').as_uri());page.wait_for_function('typeof receive===\"function\"')
 page.evaluate("receive({mode:'speaking',volume:.3,samples:[0,.1,0,-.1],low:.4,mid:.3,high:.1,status:'Audio fixture',screen:'No screen capture',mic:false})")
 page.wait_for_timeout(300);assert page.evaluate('animationMetrics.frames')>2
 page.screenshot(path=str(r/'review/voice-core/companion.png'));assert not errors,errors
 print('Floating companion loads shared renderer; receives audio fixture; renders without page errors.');b.close()
