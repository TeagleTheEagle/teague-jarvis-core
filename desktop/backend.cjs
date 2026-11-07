const {spawn}=require('node:child_process');
const {randomBytes}=require('node:crypto');
const path=require('node:path');
// Installed releases set JARVIS_PYTHON / JARVIS_DATA_DIR (docs/RELEASE-DESIGN.md); development uses the repo.
function pythonPath(root){return process.env.JARVIS_PYTHON||path.join(root,'.venv','Scripts','python.exe');}
function defaultDataDir(root){return process.env.JARVIS_DATA_DIR||path.join(root,'data');}
function startBackend(root,options={}){
 const token=randomBytes(32).toString('hex');
 const child=spawn(pythonPath(root),['-B','-u',path.join(root,'server.py'),'--port','0',...(options.dataDir?['--data-dir',options.dataDir]:[])],{cwd:root,windowsHide:true,env:{...process.env,JARVIS_DESKTOP_TOKEN:token},stdio:['pipe','pipe','pipe']});
 child.stdin.on('error',()=>{});child.stderr.resume();
 const ready=new Promise((resolve,reject)=>{
  // Cold Windows native-library loading can take over 30 seconds before wake preparation finishes.
  let buffer='';const timer=setTimeout(()=>{child.kill();reject(new Error('JARVIS backend did not become ready within 90 seconds.'));},90000);
  child.once('error',()=>{clearTimeout(timer);reject(new Error('Could not start the existing JARVIS Python runtime.'));});
  child.once('exit',()=>{clearTimeout(timer);reject(new Error('JARVIS backend exited before startup completed.'));});
  child.stdout.on('data',data=>{buffer=(buffer+data.toString()).slice(-4096);
   // One Core per data folder: a second start is refused rather than sharing memory.
   const owned=buffer.match(/JARVIS Core is already running for this data folder[^\r\n]*/);
   if(owned){clearTimeout(timer);const error=new Error(owned[0]);error.code='CORE_ALREADY_RUNNING';reject(error);return;}
   const match=buffer.match(/JARVIS ready at (http:\/\/127\.0\.0\.1:\d+)/);if(match){clearTimeout(timer);resolve({origin:match[1],token});}});
 });
 function stop(){if(child.exitCode===null&&!child.killed)child.stdin.write('stop\n');}
 async function quit(){if(!child.pid||child.exitCode!==null||child.killed)return;await new Promise(resolve=>{const timer=setTimeout(()=>{child.kill();resolve();},4000);child.once('exit',()=>{clearTimeout(timer);resolve();});child.stdin.end('quit\n');});}
 return {child,ready,stop,quit};
}

// ONE CORE, MANY CLIENTS: the shared background Core outlives any one app. Clients
// find it through <data>/core-connection.json and start it only if none is running.
const fs=require('node:fs');
const LOCAL_ORIGIN=/^http:\/\/127\.0\.0\.1:\d+$/;
function connectionFile(root,dataDir){return path.join(dataDir||defaultDataDir(root),'core-connection.json');}
function readConnection(file){
 try{const link=JSON.parse(fs.readFileSync(file,'utf8'));if(LOCAL_ORIGIN.test(link.origin)&&typeof link.token==='string'&&link.token.length>=32)return link;}catch{}
 return null;
}
async function coreAlive(link){
 try{const response=await fetch(link.origin+'/',{headers:{'X-Jarvis-Desktop':link.token},signal:AbortSignal.timeout(3000)});return response.status===200&&(await response.text()).includes('JARVIS');}catch{return false;}
}
function spawnBackgroundCore(root,dataDir){
 const logs=path.join(dataDir||defaultDataDir(root),'logs');fs.mkdirSync(logs,{recursive:true});
 const log=path.join(logs,'core.log');
 try{if(fs.statSync(log).size>5*1024*1024)fs.renameSync(log,log+'.1');}catch{} // keep one previous 5 MB log
 const out=fs.openSync(log,'a');
 const env={...process.env};delete env.JARVIS_DESKTOP_TOKEN;delete env.ELECTRON_RUN_AS_NODE;
 const child=spawn(pythonPath(root),['-B','-u',path.join(root,'server.py'),'--port','0','--background',...(dataDir?['--data-dir',dataDir]:[])],{cwd:root,detached:true,windowsHide:true,env,stdio:['ignore',out,out]});
 fs.closeSync(out);child.unref();
 let exitCode=null;child.once('exit',code=>{exitCode=code;});child.once('error',()=>{exitCode=-1;});
 return {exited:()=>exitCode};
}
async function connectCore(root,options={}){
 const file=connectionFile(root,options.dataDir);
 let link=readConnection(file),started=false;
 if(!(link&&await coreAlive(link))){
  const launch=spawnBackgroundCore(root,options.dataDir);started=true;
  const deadline=Date.now()+(options.timeoutMs||90000);
  let refusedAt=0;
  for(link=null;!link;){
   if(Date.now()>deadline)throw new Error('JARVIS Core did not become ready within 90 seconds. See data/logs/core.log.');
   await new Promise(r=>setTimeout(r,250));
   const candidate=readConnection(file);
   if(candidate&&await coreAlive(candidate)){link=candidate;break;}
   const code=launch.exited();
   if(code===3){
    // Another Core owns this data folder. If it is a background Core started by another
    // client at the same moment, its connection file appears shortly; attach to it.
    started=false;refusedAt||=Date.now();
    if(Date.now()-refusedAt>5000){const error=new Error('Another JARVIS (the browser version, or an older or test copy) already owns this memory and cannot be joined. Close it, then open JARVIS again.');error.code='CORE_ALREADY_RUNNING';throw error;}
   }else if(code!==null){
    const error=new Error('JARVIS Core exited during startup. See data/logs/core.log.');error.code='CORE_START_FAILED';throw error;
   }
  }
 }
 const {origin,token}=link;let cookie='';
 async function request(route,body){
  if(!cookie){const page=await fetch(origin+'/',{headers:{'X-Jarvis-Desktop':token},signal:AbortSignal.timeout(5000)});cookie=(page.headers.get('set-cookie')||'').split(';')[0];}
  const response=await fetch(origin+route,{method:'POST',headers:{'X-Jarvis-Desktop':token,Cookie:cookie,'Content-Type':'application/json'},body:JSON.stringify(body||{}),signal:AbortSignal.timeout(10000)});
  if(!response.ok)throw new Error('JARVIS Core refused '+route+' ('+response.status+').');
  return response.json();
 }
 return {
  origin,token,started,
  ready:Promise.resolve({origin,token}),
  alive:()=>coreAlive(link),
  stop:()=>request('/api/cancel-all').catch(()=>{}),       // stops what runs now; the Core keeps running and answering
  // The emergency stop that holds: nothing is answered or run until resume(). A Core that does not know the
  // route (never the case within one release) still gets everything running stopped.
  // Answers {stopped:true,...} when the stop holds; {status:'cancel requested'} when only the running work was
  // cancelled; {error} when the Core did not answer at all. The app tells the owner when the stop did not hold.
  emergencyStop:()=>request('/api/emergency-stop',{reason:'Stop from the desktop app (tray, shortcut or floating JARVIS)'}).catch(()=>request('/api/cancel-all')).catch(e=>({error:e.message})),
  resume:()=>request('/api/resume').catch(e=>({error:e.message})),
  quit:async()=>{},                                         // closing an app never stops the shared Core
  async shutdown(){                                          // "Quit JARVIS completely"
   await request('/api/shutdown').catch(()=>{});
   // Done only when the Core process has exited: until then it can still answer on a connection that was already
   // open (HTTP keep-alive), although it refuses new ones and has removed its connection file (release 1.0.13 check).
   // A crashed Core's process is gone at once, so quitting after a crash does not wait.
   const gone=async()=>!processAlive(link.pid)&&!await coreAlive(link);
   for(const deadline=Date.now()+10000;Date.now()<deadline&&!await gone();)await new Promise(r=>setTimeout(r,200));
  },
  watch(onEnd,options){return watchCore(link,file,onEnd,options);} // tells a requested stop from a crash
 };
}
// How the Core ended, told from the connection file this app joined with: a requested stop
// (another app's "Quit JARVIS completely", an update, an uninstall) removes the file as the
// Core's last step; a new Core replaces it with another token; a crash leaves it unchanged.
function connectionState(file,link){
 let current;try{current=JSON.parse(fs.readFileSync(file,'utf8'));}catch(e){return e&&e.code==='ENOENT'?'missing':'unreadable';}
 return current&&current.origin===link.origin&&current.token===link.token?'ours':'replaced';
}
function processAlive(pid){if(!Number.isInteger(pid)||pid<=0)return null;try{process.kill(pid,0);return true;}catch(e){return e.code==='EPERM';}}
// A Core that is alive but not answering is reported after unresponsiveMs. Right after sign-in the PC is busy (Windows,
// OneDrive, the Core itself loading) and a healthy Core can miss probes for longer than that: on 2026-10-13 the window
// closed on "not responding" 7.5 minutes after sign-in while the Core ran on, and the owner saw a "self restart". So for
// patienceMs after the watch starts (the app passes 10 minutes on a login launch, 0 otherwise) the window waits
// patientMs (60 s) instead; a crash is still reported at once, and a requested stop still closes quietly.
function watchCore(link,file,onEnd,{intervalMs=500,probeMs=5000,recheckMs=1000,crashMisses=2,unresponsiveMs=15000,patienceMs=0,patientMs=60000,probe=coreAlive,alive=processAlive}={}){
 const now=()=>performance.now();  // a steady clock: the wall clock can jump (time sync, a VM)
 const started=now();
 let done=false,probing=false,lastProbe=now(),misses=0,firstMiss=0,answeredWith='ours';
 const timer=setInterval(tick,intervalMs);timer.unref?.();
 function end(reason){if(done)return;done=true;clearInterval(timer);onEnd(reason);}
 async function check(state){
  probing=true;lastProbe=now();
  try{
   const answered=await probe(link);if(done)return;
   if(answered){misses=0;firstMiss=0;answeredWith=state;return;}  // e.g. the file was removed by hand: keep going
   misses++;firstMiss||=now();
   const current=connectionState(file,link);
   if(current==='missing')return end('stopped');
   if(current==='replaced')return end('replaced');
   const exists=alive(link.pid);
   if(exists===false&&misses>=crashMisses)return end('crashed');
   const allowed=now()-started<patienceMs?Math.max(patientMs,unresponsiveMs):unresponsiveMs;
   if(misses>=3&&now()-firstMiss>=allowed)end(exists===false?'crashed':'unresponsive');
  }finally{probing=false;}
 }
 function tick(){
  if(done||probing)return;
  const state=connectionState(file,link);
  const wait=misses>0||state!==answeredWith?recheckMs:probeMs;  // check at once when something changed
  if(now()-lastProbe>=wait)void check(state);
 }
 return ()=>{done=true;clearInterval(timer);};
}
const UNEXPECTED_STOP='The JARVIS Core stopped unexpectedly. Open JARVIS again to restart it.';
const NOT_RESPONDING='The JARVIS Core is not responding, so this window will close. If JARVIS does not open again, wait a minute or restart Windows.';
// A requested stop closes this app quietly; only a crash or a Core that stopped answering is
// reported. Never stops the Core: it is gone, it is a new one that must keep running, or it is
// not responding (and could not be reached to stop it anyway).
// Emergency authority (standing.py, owner 2026-10-13): after a crash the app starts the Core again, once. The owner's
// switch is read from standing.json beside the Core's data (the Core writes it); a second crash inside the window is
// reported as before. `state` remembers the last automatic restart for the life of this app.
function restartAllowed(root,dataDir,state={},now=Date.now){
 let allowed=false,window=600000;
 try{const s=JSON.parse(fs.readFileSync(path.join(dataDir||defaultDataDir(root),'standing.json'),'utf8'));allowed=s.emergency_restart===true;if(Number.isFinite(s.restart_window_seconds)&&s.restart_window_seconds>0)window=s.restart_window_seconds*1000;}catch{}
 if(!allowed)return false;
 if(state.last&&now()-state.last<window)return false;
 state.last=now();return true;
}
function coreEnded(reason,{quitting,showErrorBox,quit,restart,mayRestart}){
 if(quitting())return;
 if(reason==='crashed'&&restart&&mayRestart&&mayRestart()){
  // The restart is the app's (main.cjs restartCore); when it fails, the box and the quit as before.
  return Promise.resolve().then(restart).catch(()=>{if(quitting())return;showErrorBox(UNEXPECTED_STOP);quit();});
 }
 if(reason==='crashed')showErrorBox(UNEXPECTED_STOP);
 else if(reason==='unresponsive')showErrorBox(NOT_RESPONDING);
 quit();
}
module.exports={startBackend,connectCore,readConnection,connectionState,processAlive,watchCore,coreEnded,restartAllowed};
