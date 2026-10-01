import sys,json,mimetypes,tempfile
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'review'/'inspection-deps')]
import inspection_runtime as runtime
from server import App
from playwright.sync_api import sync_playwright
out=Path(__file__).parent / (sys.argv[1] if len(sys.argv)>1 else 'before');out.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory() as tmp,sync_playwright() as p:
 app=App(tmp);data=runtime.snapshot(app.store.path)
 browser=p.chromium.launch(channel='chrome',headless=True)
 page=browser.new_page(viewport={'width':1920,'height':1080},reduced_motion='reduce')
 init=runtime.INIT.replace("Object.defineProperty(window,'JARVIS_INSPECTION',{value:true});",'')
 init=init.replace("'AudioContext','webkitAudioContext',",'')+"Object.defineProperty(window,'AudioContext',{value:undefined});Object.defineProperty(window,'webkitAudioContext',{value:undefined});"
 page.add_init_script(init);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def route(r):
  path=urlsplit(r.request.url).path
  if path=='/api/files/jarvis-orbit-background.png':return r.fulfill(body=(ROOT/'data/generated/jarvis-orbit-background.png').read_bytes(),content_type='image/png')
  asset=ROOT/'static'/('index.html' if path=='/' else path.lstrip('/'))
  if asset.is_file() and asset.resolve().is_relative_to(ROOT/'static'):return r.fulfill(body=asset.read_bytes(),content_type=mimetypes.guess_type(str(asset))[0] or 'text/plain')
  payload={'/api/state':data['state'],'/api/history':{'messages':[]},'/api/workspaces':{'projects':[]},'/api/maps/config':{'available':False},'/api/approvals/list':{'items':[]},'/api/tool':{'changes':[],'updates':{'source_revision':'fixture','backend_start_revision':'fixture','releases':json.loads((ROOT/'release-notes.json').read_text(encoding='utf-8')),'observations':[]}},'/api/recovery':{'backups':[],'location':'Local backup folder'}}.get(path)
  r.fulfill(json=payload or {},status=200 if payload is not None else 403)
 page.route('**/*',route);page.goto('http://127.0.0.1:8765');page.wait_for_function("typeof state!=='undefined' && state.data")
 for name in ['command','communications','system','mission','focus','projects','memory','files','web','diagrams','settings','changes','maps']:
  page.locator('.nav[data-view="'+name+'"]').click();page.wait_for_timeout(120)
  page.screenshot(path=str(out/(name+'.png')))
 if out.name=='validated':
  import re
  ids=re.findall(r'id="([^"]+)"',(ROOT/'static/index.html').read_text(encoding='utf-8'))
  missing=page.evaluate('(ids)=>ids.filter(id=>!document.getElementById(id))',ids)
  assert missing==[],missing
  duplicates=page.evaluate('''()=>{const ids=[...document.querySelectorAll('[id]')].map(e=>e.id);return ids.filter((id,i)=>ids.indexOf(id)!==i);}''')
  assert duplicates==[],duplicates
  assert page.locator('#settingsForm #responseLength').count()==1
  assert page.locator('#settingsForm #continuousInput').count()==1
  page.locator('.nav[data-view=settings]').click()
  for category in ['General','AI','Voice','Memory','Privacy','Connections','Desktop','Backups','Appearance','Developer','About']:
   page.locator('[data-settings-category='+category+']').click()
   assert page.locator('[data-setting='+category+']').is_visible(),category
   page.screenshot(path=str(out/('settings-'+category+'.png')))
  page.locator('[data-settings-category=Developer]').click()
  page.locator('#settingsView').hover()
  page.mouse.wheel(0,800)
  page.wait_for_timeout(200)
  assert page.evaluate("document.getElementById('settingsView').scrollTop>0"),'Settings wheel scrolling failed'
  page.evaluate("document.getElementById('settingsView').scrollTop=0")
  page.get_by_text('Voice latency — development timings',exact=True).click()
  assert page.get_by_role('button',name='Refresh timing report').is_visible()
  page.locator('[data-settings-category=Appearance]').click()
  page.locator('[data-setting=Appearance] select').select_option('reduced')
  assert page.locator('html').get_attribute('data-motion')=='reduced'
  page.keyboard.press('Control+k');assert page.locator('#tiPalette').is_visible()
  page.get_by_role('searchbox',name='Search commands').fill('create task')
  page.keyboard.press('Enter');assert page.locator('#entryDialog').is_visible()
  page.locator('#entryDialog .close-dialog').click()
  page.locator('.nav[data-view=focus]').click()
  page.evaluate('''()=>{state.data.tasks=[{id:'a',body:'Review propulsion interface',completed:false,priority:'high',due:Date.now()/1000-3600},{id:'b',body:'Completed review',completed:true,priority:'normal'}];renderTasks();}''')
  page.get_by_role('button',name='Completed',exact=True).click()
  assert page.locator('#tasks .task-row:visible').count()==1
  assert 'Completed review' in page.locator('#tasks .task-row:visible').inner_text()
  page.locator('.nav[data-view=memory]').click()
  page.evaluate('''()=>{renderItems('memory','#memoryList',[{id:'m',body:'Prefer concise briefings',updated:1},{id:'n',body:'Workspace reference',updated:2}]);}''')
  page.get_by_role('searchbox',name='Search memory and notes').fill('concise')
  assert page.locator('#memoryList .saved-item:visible').count()==1
  page.get_by_role('searchbox',name='Search memory and notes').fill('')
  geometry=[]
  for width,height in [(1920,1080),(2560,1440),(3840,2160),(1280,800),(720,640)]:
   page.set_viewport_size({'width':width,'height':height})
   for name in ['command','communications','system','mission','focus','projects','memory','files','web','diagrams','settings','changes','maps']:
    page.locator('.nav[data-view='+name+']').click();page.wait_for_timeout(50)
    overflow=page.evaluate('Math.max(document.documentElement.scrollWidth,document.body.scrollWidth)>innerWidth+2')
    if overflow:geometry.append([width,height,name])
   page.screenshot(path=str(out/('size-'+str(width)+'.png')))
  (out/'overflow.json').write_text(json.dumps(geometry));assert geometry==[],geometry
 (out/'errors.json').write_text(json.dumps(errors));assert errors==[],errors
 browser.close()
 print('Captured 13 panels; page errors:',errors)
