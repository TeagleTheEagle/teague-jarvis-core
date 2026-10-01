const {chromium}=require('C:/Users/jonny/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs');
(async()=>{
const session=JSON.parse(fs.readFileSync('desktop/.jarvis-session.json','utf8'));
const browser=await chromium.launch({headless:true,channel:'msedge'});
const context=await browser.newContext({extraHTTPHeaders:{'X-Jarvis-Desktop':session.token}});
await context.addInitScript(()=>{window.JARVIS_INSPECTION=true;});
await context.route('**/*',route=>route.request().method()==='GET'?route.continue():route.abort());
const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.goto(session.origin);await page.waitForTimeout(900);
await page.evaluate(()=>{window.originalCommandCanvas=document.querySelector('#core');});
const backgroundStatus=(await context.request.get(session.origin+'/assets/branding/teague/command-background.png')).status();
const results=[];
for(const [width,height] of [[1920,1080],[1280,900],[720,600]]){
await page.setViewportSize({width,height});await page.evaluate(()=>view('command'));await page.waitForTimeout(200);
results.push(await page.evaluate(()=>{const c=document.querySelector('#core').getBoundingClientRect(),h=document.querySelector('.topbar').getBoundingClientRect();return {width:innerWidth,height:innerHeight,canvas:{x:c.x,y:c.y,width:c.width,height:c.height},centerError:Math.abs(c.x+c.width/2-innerWidth/2),belowHeader:c.y>=h.bottom,withinViewport:c.bottom<=innerHeight,hiddenPanels:['system','mission','focus'].every(n=>getComputedStyle(document.getElementById(n+'View')).display==='none'),canvasCount:document.querySelectorAll('#core').length};}));
await page.screenshot({path:`docs/command-layout-${width}.png`});
if(width===1280)await page.screenshot({path:'docs/command-layout-verified.png'});
}
await page.evaluate(()=>view('system')); const systemVisible=await page.locator('#systemView').isVisible();
await page.evaluate(()=>view('focus'));const focusVisible=await page.locator('#focusView').isVisible();
await page.evaluate(()=>view('mission'));const missionVisible=await page.locator('#missionView').isVisible();
await page.evaluate(()=>view('command'));
const sameCanvas=await page.evaluate(()=>document.querySelector('#core')===window.originalCommandCanvas);
const report={results,systemVisible,focusVisible,missionVisible,sameCanvas,backgroundStatus,errors};
fs.writeFileSync('docs/command-layout-check.json',JSON.stringify(report,null,2));
console.log(JSON.stringify(report,null,2));
await browser.close();
if(!results.every(r=>r.centerError<1&&r.belowHeader&&r.withinViewport&&r.hiddenPanels&&r.canvasCount===1)||!systemVisible||!focusVisible||!missionVisible||!sameCanvas||backgroundStatus!==200||errors.length)throw Error('Command layout verification failed');
})().catch(e=>{console.error(e.message);process.exitCode=1});
