if (process.argv.includes('--stage4-test')) {
 require('../stage4_client.cjs').launchTestClient('teague');
} else {
const {app,BrowserWindow,Tray,Menu,nativeImage,dialog,shell,session,ipcMain,desktopCapturer,screen,globalShortcut}=require('electron');
const path=require('node:path');
const {trusted,external,desktopHeaders}=require('./policy.cjs');
const {connectCore}=require('./backend.cjs');
const {ScreenCapture}=require('./capture.cjs');
const {watchUpdates}=require('./local-updates.cjs');
let updates;
let companionWanted=false;
let unwatchCore,win,tray,backend,quitting=false,origin='',capture,companion,lastCompanionState,resumeMicOnShow=false,liveGrantUntil=0;
// Installed releases keep owner files outside the read-only program folder.
const configDir=process.env.JARVIS_CONFIG_DIR||__dirname;
const sessionFile=path.join(process.env.JARVIS_DATA_DIR||__dirname,'.jarvis-session.json');
const preferencesFile=path.join(configDir,'preferences.json');
if(!require('node:fs').existsSync(preferencesFile))require('node:fs').copyFileSync(path.join(__dirname,'preferences.json'),preferencesFile);
const loginLaunch=process.argv.includes('--login-launch');
const preferences=JSON.parse(require('node:fs').readFileSync(preferencesFile,'utf8').replace(/^\uFEFF/,''));
if(!app.requestSingleInstanceLock()){app.quit();}else{
 app.on('second-instance',()=>show());
 app.on('before-quit',event=>{if(!quitting){event.preventDefault();void quit();}});
 app.on('window-all-closed',()=>{});
 app.whenReady().then(start).catch(async(error)=>{if((process.argv.includes('--smoke-test')||process.argv.includes('--animation-test')||process.argv.includes('--live-test')))require('node:fs').writeFileSync(path.join(__dirname,'smoke-result.json'),JSON.stringify({passed:false,error:String(error)}));else dialog.showErrorBox('JARVIS desktop',['CORE_ALREADY_RUNNING','CORE_START_FAILED'].includes(error?.code)?error.message:'The desktop shell could not start. The browser version has not been stopped. Check that the JARVIS Python environment exists.');await quit();});
}
function show(){if(win&&!win.isDestroyed()){if(win.isMinimized())win.restore();win.show();win.focus();win.webContents.send('jarvis:reset-navigation');if(resumeMicOnShow){resumeMicOnShow=false;win.webContents.send('jarvis:resume-mic');}}}
// stopLocal: this app's own activity (screen grant, capture, mic/speech in the window).
// stop: emergency stop for the whole shared Core (tray, shortcut, companion STOP ALL).
function stopLocal(){liveGrantUntil=0;capture?.stop();if(win&&!win.isDestroyed()){win.webContents.send('jarvis:stop');}}
function stop(){stopLocal();backend?.stop();}
async function quit(stopCore=false){if(quitting)return;quitting=true;updates?.close();liveGrantUntil=0;capture?.stop();unwatchCore?.();if(stopCore)await backend?.shutdown();else await backend?.quit();try{require('node:fs').unlinkSync(sessionFile);}catch{}globalShortcut.unregisterAll();companion?.destroy();tray?.destroy();app.quit();}
async function start(){
 app.setAppUserModelId('local.jarvis.desktop');
 backend=await connectCore(path.resolve(__dirname,'..'));
 const ready=await backend.ready;origin=ready.origin;
 require('node:fs').writeFileSync(sessionFile,JSON.stringify({origin,token:ready.token,created:new Date().toISOString()}),'utf8');
 const ses=session.fromPartition('jarvis-desktop'); // memory-only session
 ses.webRequest.onBeforeSendHeaders((details,callback)=>callback({requestHeaders:desktopHeaders(details.requestHeaders,details.url,origin,ready.token)}));
 let micApproved=Boolean(preferences.microphoneAllowed);
 ses.setPermissionCheckHandler((contents,permission,requestingOrigin,details)=>((permission==='media'&&micApproved&&details.mediaType!=='video')||(permission==='display-capture'&&capture?.source&&Date.now()<liveGrantUntil))&&contents===win?.webContents&&trusted(requestingOrigin,origin));
 ses.setPermissionRequestHandler(async(contents,permission,callback,details)=>{
  if(contents===win?.webContents&&trusted(contents.getURL(),origin)&&(permission==='display-capture'||(permission==='media'&&details.mediaTypes?.length===0&&details.isMainFrame))&&capture?.source&&Date.now()<liveGrantUntil){liveGrantUntil=0;return callback(true);}
  if(contents!==win?.webContents||!trusted(contents.getURL(),origin)||permission!=='media'||!details.mediaTypes?.includes('audio')||details.mediaTypes.includes('video'))return callback(false);
  if(micApproved)return callback(true);
  const result=await dialog.showMessageBox(win,{type:'question',buttons:['Keep microphone off','Enable microphone'],defaultId:0,cancelId:0,message:'Enable JARVIS microphone?',detail:'Microphone audio uses the existing local voice pipeline. Closing to tray stops activity. You can mute it in JARVIS.'});micApproved=result.response===1;if(micApproved){preferences.microphoneAllowed=true;require('node:fs').writeFileSync(preferencesFile,JSON.stringify(preferences,null,2));}callback(micApproved);
 });
 ses.setDisplayMediaRequestHandler((_request,callback)=>callback({}));
 win=new BrowserWindow({width:1280,height:900,minWidth:720,minHeight:540,show:false,...(process.platform==='win32'?{titleBarStyle:'hidden',titleBarOverlay:{color:'#03111b',symbolColor:'#bcefff',height:36}}:{}),backgroundColor:'#101820',title:'Teague Industries Command Center · JARVIS',webPreferences:{preload:path.join(__dirname,'preload.cjs'),session:ses,nodeIntegration:false,contextIsolation:true,sandbox:true,webSecurity:true,backgroundThrottling:false}});
 win.removeMenu();
 updates=watchUpdates(path.resolve(__dirname,'..'),update=>{if(!win.isDestroyed())win.webContents.send('jarvis:update-available',update);});
 function updateSender(event){if(event.sender!==win.webContents||event.senderFrame!==win.webContents.mainFrame||!trusted(event.senderFrame.url,origin))throw new Error('Untrusted update request.');}
 ipcMain.handle('jarvis:update-status',event=>{updateSender(event);return updates.get();});
 ipcMain.handle('jarvis:apply-update',(event,revision)=>{
  updateSender(event);const pending=updates.get();
  if(!pending||!updates.validate(revision))return {applied:false};
  if(pending.kind==='restart'){
   app.relaunch({execPath:process.execPath,args:[app.getAppPath()]});
   setImmediate(()=>void quit(true)); // a code update must restart the Core as well
  }else{
   updates.acknowledge();setImmediate(()=>{stop();win.webContents.reloadIgnoringCache();});
  }
  return {applied:true};
 });
 capture=new ScreenCapture({
  displays:()=>screen.getAllDisplays().map((d,i)=>({id:String(d.id),label:`Display ${i+1} � ${d.size.width} � ${d.size.height} � ${Math.round(d.scaleFactor*100)}%`,signature:JSON.stringify([d.bounds,d.scaleFactor,d.rotation])})),
  choose:async displays=>{if(preferences.requestedPrimaryDisplayScreenshots)return String(screen.getPrimaryDisplay().id);show();const result=await dialog.showMessageBox(win,{type:'question',title:'Authorise single screenshots',message:'Which display may JARVIS capture this session?',detail:'Capture happens only when you request a screenshot. Capture & Analyse and voice screenshot commands send the chosen image to your configured AI vision provider. Capture only keeps a local preview. Windows display thumbnails may be created locally; only the chosen display is returned. Stop, closing to tray, or restarting revokes this permission.',buttons:['Cancel',...displays.map(d=>d.label)],defaultId:0,cancelId:0,noLink:true});return displays[result.response-1]?.id;},
  capture:async id=>{const restore=companion?.isVisible();if(restore)companion.hide();try{const sources=await desktopCapturer.getSources({types:['screen'],thumbnailSize:{width:1920,height:1080},fetchWindowIcons:false});const source=sources.find(s=>s.display_id===id);if(!source||source.thumbnail.isEmpty())throw new Error('Display capture unavailable. Authorise the display again.');const size=source.thumbnail.getSize();return {data:source.thumbnail.toJPEG(85).toString('base64'),width:size.width,height:size.height};}finally{if(restore&&companionWanted&&!quitting&&companion&&!companion.isDestroyed())companion.showInactive();}}
 });
 function captureSender(event){if(event.sender!==win.webContents||event.senderFrame!==win.webContents.mainFrame||!trusted(event.senderFrame.url,origin))throw new Error('Untrusted screen request.');}
 for(const [channel,action] of [['authorise',()=>capture.authorise()],['capture',()=>capture.capture()],['stop',()=>{liveGrantUntil=0;capture.stop();return {stopped:true};}]])ipcMain.handle('jarvis:screen-'+channel,async event=>{captureSender(event);try{return await action();}catch(e){return {error:e.message};}});
 ipcMain.handle('jarvis:screen-live-source',async event=>{captureSender(event);const generation=capture.generation;if(!capture.source)return {error:'Start a screen session first.'};const id=capture.source.id;const sources=await desktopCapturer.getSources({types:['screen'],thumbnailSize:{width:0,height:0},fetchWindowIcons:false});if(generation!==capture.generation)return {error:'Screen session cancelled.'};const selected=sources.find(s=>s.display_id===id);if(selected)liveGrantUntil=Date.now()+5000;return selected?{id:selected.id,label:capture.source.label}:{error:'Display unavailable.'};});
 function showCompanion(){
  companionWanted=true;
  if(companion&&!companion.isDestroyed()){companion.showInactive();return {shown:true};}
  const bounds=screen.getPrimaryDisplay().workArea;
  companion=new BrowserWindow({width:320,height:350,x:bounds.x+bounds.width-340,y:bounds.y+bounds.height-370,frame:false,alwaysOnTop:true,skipTaskbar:true,resizable:false,show:false,backgroundColor:'#10232e',webPreferences:{preload:path.join(__dirname,'companion-preload.cjs'),nodeIntegration:false,contextIsolation:true,sandbox:true,webSecurity:true}});
  companion.setContentProtection(true);
  companion.webContents.setWindowOpenHandler(()=>({action:'deny'}));companion.webContents.on('will-navigate',e=>e.preventDefault());
  companion.on('closed',()=>{companion=null;companionWanted=false;});
  companion.loadFile(path.join(__dirname,'companion.html')).then(()=>{if(companionWanted&&companion&&!companion.isDestroyed()){companion.showInactive();if(lastCompanionState)companion.webContents.send('jarvis:companion-state',lastCompanionState);}});
  return {shown:true};
 }
 ipcMain.handle('jarvis:companion-show',async event=>{captureSender(event);await showCompanion();for(let i=0;i<100;i++){if(companion&&!companion.isDestroyed()&&companion.isVisible())return {shown:true};await new Promise(r=>setTimeout(r,50));}return {shown:false,error:'Companion did not become visible.'};});
 ipcMain.handle('jarvis:companion-hide',event=>{captureSender(event);companionWanted=false;if(companion&&!companion.isDestroyed())companion.hide();return {visible:!!companion&&!companion.isDestroyed()&&companion.isVisible()};});
 ipcMain.handle('jarvis:companion-status',event=>{captureSender(event);return {visible:!!companion&&!companion.isDestroyed()&&companion.isVisible()};});
 ipcMain.on('jarvis:companion-update',(event,data)=>{try{captureSender(event);}catch{return;}if(!data||!Number.isFinite(data.volume)||!Array.isArray(data.samples)||data.samples.length>64||data.samples.some(v=>!Number.isFinite(v)))return;lastCompanionState={low:Math.max(0,Math.min(1,Number(data.low)||0)),mid:Math.max(0,Math.min(1,Number(data.mid)||0)),high:Math.max(0,Math.min(1,Number(data.high)||0)),input:Math.max(0,Math.min(1,Number(data.input)||0)),reduced:!!data.reduced,mode:['standby','listening','thinking','speaking','processing','interrupted','error','understood'].includes(data.mode)?data.mode:'standby',volume:Math.max(0,Math.min(1,data.volume)),samples:data.samples.map(v=>Math.max(-1,Math.min(1,v))),status:String(data.status||'').slice(0,200),screen:String(data.screen||'').slice(0,200),mic:!!data.mic};if(companion&&!companion.isDestroyed())companion.webContents.send('jarvis:companion-state',lastCompanionState);});
 ipcMain.on('jarvis:companion-action',(event,action)=>{if(!companion||event.sender!==companion.webContents||event.senderFrame!==companion.webContents.mainFrame)return;if(action==='show')show();else if(action==='hide'){companionWanted=false;companion.hide();}else if(action==='stop')stop();else if(['capture','mic','live','stop-screen'].includes(action))win.webContents.send('jarvis:companion-command',action);});
 const stopKey=preferences.emergencyStopShortcut||'CommandOrControl+Alt+Shift+X';
 if(!globalShortcut.register(stopKey,stop))dialog.showMessageBox(win,{type:'warning',message:'The emergency stop shortcut is unavailable.',detail:'Use the tray Stop activity or the floating companion STOP ALL button.'});
 ipcMain.handle('jarvis:screen-preference', (event,value)=>{captureSender(event);if(typeof value==='boolean'){preferences.requestedPrimaryDisplayScreenshots=value;capture.stop();require('node:fs').writeFileSync(preferencesFile,JSON.stringify(preferences,null,2));}return {primary:!!preferences.requestedPrimaryDisplayScreenshots,shortcut:stopKey,micOnLaunch:!!preferences.micOnLaunch&&!process.argv.some(a=>['--smoke-test','--animation-test','--live-test'].includes(a))};});
 ipcMain.handle('jarvis:mic-preference',(event,value)=>{captureSender(event);if(typeof value!=='boolean')throw new Error('Invalid microphone preference.');preferences.micOnLaunch=value;require('node:fs').writeFileSync(preferencesFile,JSON.stringify(preferences,null,2));return {saved:true};});
 const revokeCapture=()=>{capture.stop();if(!win.isDestroyed())win.webContents.send('jarvis:screen-revoked');};
 screen.on('display-removed',revokeCapture);screen.on('display-metrics-changed',revokeCapture);
 win.webContents.on('did-start-navigation',(_e,_url,inPlace,mainFrame)=>{if(mainFrame&&!inPlace)capture.stop();});
 win.webContents.on('will-attach-webview',event=>event.preventDefault());
 const openExternal=url=>{if(external(url))void shell.openExternal(url).catch(()=>{});};
 win.webContents.setWindowOpenHandler(({url})=>{openExternal(url);return {action:'deny'};});
 win.webContents.on('will-navigate',(event,url)=>{if(!trusted(url,origin)){event.preventDefault();openExternal(url);}});
 win.webContents.on('will-redirect',(event,url)=>{if(!trusted(url,origin))event.preventDefault();});
 win.webContents.on('render-process-gone',()=>{capture?.stop();backend.stop();dialog.showErrorBox('JARVIS desktop','The interface stopped. Voice requests were cancelled. Quit and relaunch JARVIS Desktop.');});
 win.on('close',event=>{if(!quitting){event.preventDefault();stopLocal();resumeMicOnShow=!!preferences.micOnLaunch;win.hide();}});
 win.on('show',()=>win.webContents.setAudioMuted(false));
 unwatchCore=backend.watch(()=>{if(!quitting){dialog.showErrorBox('JARVIS desktop','The JARVIS Core stopped. Open JARVIS again to restart it.');void quit();}});
 tray=new Tray(nativeImage.createFromPath(path.join(__dirname,'tray.png')));
 tray.setToolTip('JARVIS · closing this window keeps JARVIS running');
 tray.setContextMenu(Menu.buildFromTemplate([{label:'Show JARVIS',click:show},{label:'Floating JARVIS',click:showCompanion},{label:'Stop activity',click:stop},{type:'separator'},{label:'Close desktop app (JARVIS keeps running)',click:()=>void quit()},{label:'Quit JARVIS completely',click:()=>void quit(true)}]));tray.on('double-click',show);
 win.webContents.once('did-finish-load',()=>{
  if(loginLaunch&&!process.argv.some(a=>['--smoke-test','--animation-test','--live-test'].includes(a)))setTimeout(()=>{if(!quitting&&!win.isDestroyed()){const hour=new Date().getHours();win.webContents.send('jarvis:login-greeting',hour<12?'Good morning, Mr. Teague. JARVIS is online and ready for your day, sir.':hour<18?'Good afternoon, Mr. Teague. JARVIS is online and ready, sir.':'Good evening, Mr. Teague. JARVIS is online and ready, sir.');}},1400);
 });
 await win.loadURL(origin+'/');
 if(process.argv.includes('--live-test')){
  const assert=require('node:assert/strict');win.show();
  const result=await win.webContents.executeJavaScript(`startDesktopLive({automatic:false}).then(()=>({live:desktopLive,width:document.getElementById('screenLive').videoWidth,status:document.getElementById('screenStatus').textContent,automatic:document.getElementById('screenAuto').checked}))`);
  assert.equal(result.live,true,result.status);assert.ok(result.width>0);assert.equal(result.automatic,false);
  const stopped=await win.webContents.executeJavaScript('(()=>{const track=screenStream.getVideoTracks()[0];stopScreenVision();return {ended:track.readyState,live:desktopLive};})()');assert.equal(stopped.ended,'ended');assert.equal(stopped.live,false);
  require('node:fs').writeFileSync(path.join(__dirname,'live-result.json'),JSON.stringify({passed:true,...result,stopped}));await quit(backend.started);return;
 }
 if(process.argv.includes('--animation-test')){
  const assert=require('node:assert/strict');showCompanion();win.show();win.minimize();
  await new Promise(r=>setTimeout(r,2000));
  const result=await companion.webContents.executeJavaScript('({...window.animationMetrics,status:document.getElementById("status").textContent})');
  result.fps=Number(((result.frames-1)*1000/(result.last-result.first)).toFixed(1));assert.ok(result.frames>30);assert.ok(!result.status.includes('Waiting for'));
  require('node:fs').writeFileSync(path.join(__dirname,'animation-result.json'),JSON.stringify(result));await quit(backend.started);return;
 }
 if(process.argv.includes('--smoke-test')){
   const assert=require('node:assert/strict');
   const result=await win.webContents.executeJavaScript(`({title:document.title,bridge:typeof window.jarvisDesktop?.onStop,node:typeof require,screenDisabled:document.getElementById('captureScreen').disabled,mic:document.getElementById('micButton').textContent})`);
   assert.equal(result.bridge,'function');assert.equal(result.node,'undefined');assert.equal(result.screenDisabled,false);assert.equal(result.mic,'ENABLE MIC');
   assert.equal(capture.source,null);
   const auth=await win.webContents.executeJavaScript('window.jarvisDesktop.authoriseScreen()');assert.equal(auth.authorised,true);
   const shot=await win.webContents.executeJavaScript('window.jarvisDesktop.captureScreen().then(s=>({error:s.error,width:s.width,height:s.height,bytes:s.data?.length}))');assert.ok(!shot.error,shot.error);assert.ok(shot.width>0&&shot.height>0&&shot.bytes>100);
   await win.webContents.executeJavaScript('window.jarvisDesktop.showCompanion()');
   await new Promise(r=>setTimeout(r,700));assert.ok(companion.isAlwaysOnTop());assert.ok(companion.isVisible());
   const mirrored=await companion.webContents.executeJavaScript('({node:typeof require,frames:window.animationMetrics.frames})');assert.equal(mirrored.node,'undefined');assert.ok(mirrored.frames>0);
   await win.webContents.executeJavaScript('captureDesktopScreen(false,"")');
   const preview=await win.webContents.executeJavaScript('({local:!!screenBlob,status:document.getElementById("screenStatus").textContent})');assert.equal(preview.local,true);assert.ok(preview.status.includes('has not been submitted'));
   require('node:fs').writeFileSync(path.join(__dirname,'companion-test.png'),(await companion.webContents.capturePage()).toPNG());
   stop();assert.equal(capture.source,null);
   await new Promise(r=>setTimeout(r,100));assert.equal(await win.webContents.executeJavaScript('screenBlob===null'),true);
   win.show();win.close();assert.equal(win.isDestroyed(),false);assert.equal(win.isVisible(),false);assert.equal(await backend.alive(),true);show();assert.equal(win.isVisible(),true);
   require('node:fs').writeFileSync(path.join(__dirname,'smoke-result.json'),JSON.stringify({passed:true,checks:['page loaded','isolated preload','no renderer Node','screen controls available without capture authority','native single capture','renderer local preview and discard','floating hologram mirrored','stop revokes capture','muted startup','close to tray','restore'],at:new Date().toISOString()}));await quit(backend.started);
 }else {win.show();showCompanion();}
}


}
