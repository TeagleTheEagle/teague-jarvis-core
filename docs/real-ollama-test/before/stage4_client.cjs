'use strict';
// TEST ONLY trusted main-process bootstrap. Never expose this module via preload.
const crypto=require('node:crypto');
function requireThat(ok,reason){if(!ok)throw new Error(reason);}
function mainOnly(){requireThat(process.type!=='renderer','MAIN_PROCESS_ONLY');}
function canonical(value){
 if(value===null)return 'null';
 if(typeof value==='bigint')return value.toString();
 if(typeof value==='number'){requireThat(Number.isSafeInteger(value),'UNSAFE_NUMBER');return String(value);}
 if(typeof value==='boolean')return String(value);
 if(typeof value==='string')return JSON.stringify(value).replace(/[\u007f-\uffff]/g,c=>'\\u'+c.charCodeAt(0).toString(16).padStart(4,'0'));
 if(Array.isArray(value))return '['+value.map(canonical).join(',')+']';
 requireThat(value&&Object.getPrototypeOf(value)===Object.prototype,'PLAIN_OBJECT_REQUIRED');
 return '{'+Object.keys(value).sort().map(k=>canonical(k)+':'+canonical(value[k])).join(',')+'}';
}
function parse(bytes, applicationReply=false){
 const source=new TextDecoder('utf-8',{fatal:true}).decode(bytes);
 const value=JSON.parse(source,(key,value,context)=>{
  if(typeof value==='number'&&!Number.isSafeInteger(value)){
   if(applicationReply && context && /[.eE]/.test(context.source) && Number.isFinite(value))return value;
   requireThat(context&&/^-?\d+$/.test(context.source),'EXACT_INTEGER_REQUIRED');return BigInt(context.source);
  }
  return value;
 });
 requireThat(value&&!Array.isArray(value)&&typeof value==='object','OBJECT_REQUIRED');return value;
}
function exact(value,keys){requireThat(value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).sort().join('\0')===[...keys].sort().join('\0'),'UNKNOWN_FIELDS');}
function same(a,b){return canonical(a)===canonical(b);}
function proof(key,label,value){requireThat(Buffer.isBuffer(key)&&key.length===32,'TEST_KEY_REQUIRED');return crypto.createHmac('sha256',key).update(label+'\0').update(canonical(value)).digest('hex');}
function proofEquals(a,b){return typeof a==='string'&&/^[0-9a-f]{64}$/.test(a)&&crypto.timingSafeEqual(Buffer.from(a,'hex'),Buffer.from(b,'hex'));}
function loadBridge(nativePath){mainOnly();const bridge=require(nativePath);requireThat(typeof bridge.connectTestPipe==='function'&&typeof bridge.currentProcessIdentity==='function','BRIDGE_UNAVAILABLE');return bridge;}
function normalizePeer(peer){exact(peer,['pid','created','exe_digest']);return {pid:peer.pid,created:BigInt(peer.created),exe_digest:peer.exe_digest};}
function negotiate(a,b){for(const p of [a,b])requireThat(Array.isArray(p)&&p.length===2&&p.every(Number.isSafeInteger)&&p[0]>=2&&p[0]<=p[1]&&p[1]<=3,'PROTOCOL_RANGE');const n=Math.min(a[1],b[1]);requireThat(n>=Math.max(a[0],b[0]),'PROTOCOL_INCOMPATIBLE');return n;}
function bootstrap({nativePath,endpoint,pinnedPeer,expectedIdentity,serverKey,clientId,clientKey,request,protocol=[2,3]}){
 mainOnly();requireThat(expectedIdentity?.mode==='TEST','TEST_ONLY');
 const bridge=loadBridge(nativePath);
 // Independently pinned by trusted main state, never selected by the transcript
 // or renderer. Native connection captures an immutable copy of this pin.
 const pipe=bridge.connectTestPipe(endpoint,{...pinnedPeer,created:String(pinnedPeer.created)},
  {pid:expectedIdentity.pid,created:String(expectedIdentity.created),exe_digest:expectedIdentity.exe_digest});
 try{
  const hello={client:clientId,nonce:crypto.randomBytes(32).toString('hex'),range:protocol};
  pipe.send(Buffer.from(canonical(hello)));
  const answer=parse(pipe.receive());exact(answer,['transcript','proof']);const t=answer.transcript;
  exact(t,['hello','server_nonce','identity','selected','peer']);
  requireThat(same(t.hello,hello),'REPLAY');
  requireThat(proofEquals(answer.proof,proof(serverKey,'server',t)),'SERVER_PROOF');
  requireThat(same(t.identity,expectedIdentity),'CORE_IDENTITY');
  requireThat(typeof pipe.verifyCore==='function' && pipe.verifyCore()===true,'CORE_LIVE_IDENTITY');
  requireThat(same(t.peer,normalizePeer(bridge.currentProcessIdentity())),'CLIENT_PROCESS_BINDING');
  requireThat(t.selected===negotiate(protocol,expectedIdentity.protocol),'DOWNGRADE');
  pipe.send(Buffer.from(canonical({proof:proof(clientKey,'client',t)})));
  pipe.send(Buffer.from(canonical(request)));
  return parse(pipe.receive(),true);
 }finally{pipe.close();}
}
module.exports={bootstrap,canonical,parse,loadBridge};

// Admission-to-reply deadline includes queue time. A timed-out transport is
// uncertain: abandon queued work, never replay it or infer zero consumption.
class TransportQueue {
 constructor(send,{timeout=6500,limit=8,onFailure=()=>{},clock=()=>performance.now(),setTimer=setTimeout,clearTimer=clearTimeout}={}){
  this.send=send;this.timeout=timeout;this.limit=limit;this.onFailure=onFailure;
  this.clock=clock;this.setTimer=setTimer;this.clearTimer=clearTimer;
  this.jobs=new Map();this.active=null;this.serial=0;this.failure=null;
 }
 call(op,args={}){
  if(this.failure)return Promise.reject(Error(this.failure));
  if(this.jobs.size>=this.limit)return Promise.reject(Error('CLIENT_BUSY'));
  return new Promise((resolve,reject)=>{
   const id=++this.serial;
   const job={id,op,args,resolve,reject,deadline:this.clock()+this.timeout};
   this.jobs.set(id,job);
   job.timer=this.setTimer(()=>this.fail('TRANSPORT_DEADLINE'),this.timeout);
   this.pump();
  });
 }
 pump(){
  if(this.failure||this.active!==null)return;
  const job=this.jobs.values().next().value;if(!job)return;
  if(this.clock()>=job.deadline){this.fail('TRANSPORT_DEADLINE');return;}
  this.active=job.id;
  try{this.send({id:job.id,op:job.op,args:job.args});}catch{this.fail('BRIDGE_FAILED');}
 }
 receive(message){
  const job=this.jobs.get(message.id);
  if(this.failure||!job||this.active!==message.id)return;
  if(this.clock()>=job.deadline){this.fail('TRANSPORT_DEADLINE');return;}
  this.jobs.delete(job.id);this.clearTimer(job.timer);this.active=null;
  message.error?job.reject(Error(message.error)):job.resolve(message.result);
  this.pump();
 }
 cancelQueued(){
  for(const [id,job] of this.jobs){
   if(id===this.active)continue;
   this.jobs.delete(id);this.clearTimer(job.timer);job.reject(Error('CLIENT_CLOSING'));
  }
 }
 fail(reason){
  if(this.failure)return;this.failure=reason;
  for(const job of this.jobs.values()){this.clearTimer(job.timer);job.reject(Error(reason));}
  this.jobs.clear();this.active=null;this.onFailure(reason);
 }
}
module.exports.TransportQueue=TransportQueue;

// Only an explicitly launched TEST entry point can enter this branch. Native IO
// runs on a worker; a blocked pipe cannot block the Electron UI/stop controls.
const threads=require('node:worker_threads');
if(!threads.isMainThread && threads.workerData?.stage4Transport===true){
 const cfg=threads.workerData.config;
 cfg.expectedIdentity.created=BigInt(cfg.expectedIdentity.created);
 cfg.pinnedPeer.created=BigInt(cfg.pinnedPeer.created);
 cfg.serverKey=Buffer.from(cfg.serverKey,'hex');cfg.clientKey=Buffer.from(cfg.clientKey,'hex');
 let token=null;
 threads.parentPort.on('message',({id,op,args})=>{
  try{
   const reply=bootstrap({...cfg,request:{op,token,args}});
   requireThat(reply.result!=='DENIED','CORE_DENIED');
   if(op==='attach'||op==='renew'){token=reply.token;delete reply.token;}
   if(op==='detach')token=null;
   threads.parentPort.postMessage({id,result:reply});
  }catch(error){threads.parentPort.postMessage({id,error:'ATTACHMENT_OR_OPERATION_DENIED'});}
 });
}

function validateTestRoot(root){
 const fs=require('node:fs'),path=require('node:path');
 const base=path.resolve(__dirname,'tests/lifecycle_stage1/evidence');
 requireThat(path.dirname(path.resolve(root))===base && /^TEST-STAGE4-[a-f0-9]{32}$/.test(path.basename(root)),'TEST_ROOT');
 for(let p=path.resolve(root);;p=path.dirname(p)){
  requireThat(!fs.lstatSync(p).isSymbolicLink(),'TEST_REPARSE');if(path.dirname(p)===p)break;
 }
 requireThat(fs.readFileSync(path.join(root,'TEST_ONLY'),'utf8')==='NO PRODUCTION SERVICES','TEST_MARKER');
 return path.resolve(root);
}

function launchTestClient(clientId){
 mainOnly();requireThat(['teague','intelligence'].includes(clientId),'TEST_CLIENT');
 const {app,BrowserWindow,ipcMain,protocol,session}=require('electron');
 const fs=require('node:fs'),path=require('node:path');
 const root=validateTestRoot(process.argv.find(a=>a.startsWith('--stage4-root='))?.slice(14)||'');
 const profile=path.join(root,'STAGE4_TEST-profile-'+clientId+'-'+crypto.randomUUID());
 fs.mkdirSync(profile);app.setPath('userData',profile);app.setPath('sessionData',profile);
 app.disableHardwareAcceleration();app.commandLine.appendSwitch('disable-gpu');
 protocol.registerSchemesAsPrivileged([{scheme:'stage4-test',privileges:{standard:true,secure:true,supportFetchAPI:true}}]);
 const page='stage4-test://app/'+(clientId==='teague'?'index.html':'intelligence.html');
 const lines=typeof process.send==='function'?null:require('node:readline').createInterface({input:process.stdin});
 let worker,win,attached=false,closing=false,configuration,identity=null,heartbeat;
 const transportQueue=new TransportQueue(message=>worker.postMessage(message),{onFailure:()=>{attached=false;}});
 const emit=value=>process.stdout.write('STAGE4 '+JSON.stringify(value,(_k,v)=>typeof v==='bigint'?String(v):v)+'\n');
 function call(op,args={}){
  if(closing&&op!=='detach')return Promise.reject(Error('CLIENT_CLOSING'));
  return transportQueue.call(op,args);
 }
 async function close(){
  if(closing)return;closing=true;
  clearInterval(heartbeat);
  transportQueue.cancelQueued();
  process.stderr.write('STAGE4_TEST client close; attached='+attached+'\n');
  try{if(attached)await call('detach');}catch{emit({event:'detach-unconfirmed',expiry_required:true});}
  attached=false;
  if(win&&!win.isDestroyed())win.destroy();
  // Terminating a transport worker revokes no Core ownership and spawns nothing.
  if(worker)await worker.terminate();app.quit();
 }
 const exposed=Object.freeze({
  shared:[],request:['text'],'request-status':['request_id'],cancel:['request_id'],
  'request-text-only':['text','operation'],'last-response-provider':[],
  'stop-capture':['lease_id'],'stop-playback':['lease_id']
 });
 function argsFor(op,args){
  requireThat(Object.hasOwn(exposed,op),'ORDINARY_OPERATION_ONLY');exact(args,exposed[op]);
  if(op==='request')requireThat(typeof args.text==='string'&&args.text.length>0&&args.text.length<=12000,'TEXT');
  if(op==='request-text-only')requireThat(typeof args.text==='string'&&args.text.length>0&&args.text.length<=11000&&typeof args.operation==='string'&&/^[a-f0-9]{32}$/.test(args.operation),'TEXT_ONLY_REQUEST');
  if('request_id' in args)requireThat(typeof args.request_id==='string'&&/^[a-f0-9]{32}$/.test(args.request_id),'REQUEST_ID');
  if('lease_id' in args)requireThat(args.lease_id===null || typeof args.lease_id==='string'&&/^[a-f0-9]{32}$/.test(args.lease_id),'LEASE_ID');
  return args;
 }
 ipcMain.handle('stage4:ordinary',async(event,op,args)=>{
  requireThat(win&&!win.isDestroyed() && event.sender===win.webContents && event.senderFrame===win.webContents.mainFrame && event.senderFrame.url===page,'IPC_SENDER');
  if(op==='connection')return {mode:'STAGE4_TEST',attached,identity,client:clientId,media:'UNAVAILABLE: no hardware capture; silent Core fixture only'};
  requireThat(attached&&!closing,'NOT_ATTACHED');return call(op,argsFor(op,args));
 });
 const allowed=new Map([
  ['/index.html','static/index.html'],['/intelligence.html','intelligence/index.html'],
  ['/app.js','intelligence/stage4-renderer.js'],['/stage4-renderer.js','intelligence/stage4-renderer.js'],
  ...['style','gallery','pro','teague'].map(n=>['/'+n+'.css','static/'+n+'.css']),
  ['/intelligence.css','intelligence/style.css'],
  ['/assets/branding/teague/teague-mark.svg','static/assets/branding/teague/teague-mark.svg'],
  ['/assets/branding/teague/command-background.png','static/assets/branding/teague/command-background.png'],
 ]);
 async function start(cfg){
  process.stderr.write('STAGE4_TEST configuration received\n');
  requireThat(cfg.clientId===clientId&&cfg.expectedIdentity?.mode==='TEST'&&cfg.expectedIdentity.data_id?.startsWith('TEST-'),'TEST_CONFIG');
  requireThat(cfg.expectedIdentity.data_id===JSON.parse(fs.readFileSync(path.join(root,'STAGE4_TEST-data/STAGE4_TEST.json'),'utf8')).data_id,'DATA_PIN');
  const nativePath=path.resolve(__dirname,'../stage4-toolchain/peer-build/Release/peer_identity.node');
  configuration={driver:cfg.driver===true};
  worker=new threads.Worker(__filename,{workerData:{stage4Transport:true,config:{...cfg,nativePath}},env:{SYSTEMROOT:process.env.SYSTEMROOT||process.env.SystemRoot}});
  worker.on('message',message=>transportQueue.receive(message));
  worker.on('error',()=>transportQueue.fail('BRIDGE_FAILED'));
  worker.on('exit',()=>transportQueue.fail('BRIDGE_EXITED'));
  const result=await call('attach',{scopes:['attach','read','request','media']});identity=result.identity;attached=true;
  heartbeat=setInterval(()=>{if(attached&&!closing)call('renew').catch(()=>{attached=false;});},30000);
  await app.whenReady();const ses=session.fromPartition('stage4-test-'+crypto.randomUUID());
  ses.setPermissionRequestHandler((_wc,_p,callback)=>callback(false));ses.setPermissionCheckHandler(()=>false);
  ses.webRequest.onBeforeRequest((details,callback)=>callback({cancel:!details.url.startsWith('stage4-test://app/')}));
  ses.protocol.handle('stage4-test',request=>{
   const url=new URL(request.url);const item=allowed.get(url.pathname);
   if(request.method!=='GET'||url.protocol!=='stage4-test:'||url.hostname!=='app'||url.port||url.username||url.password||url.search||url.hash||!item)return new Response('TEST route unavailable',{status:403});
   const file=path.resolve(__dirname,item);
   for(let p=file;p!==__dirname;p=path.dirname(p)){if(fs.lstatSync(p).isSymbolicLink())return new Response('Denied',{status:403});}
   const type={'.html':'text/html','.css':'text/css','.js':'text/javascript','.svg':'image/svg+xml','.png':'image/png'}[path.extname(file)];
   return new Response(fs.readFileSync(file),{headers:{'Content-Type':type,'Content-Security-Policy':"default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'none'; media-src 'none'; object-src 'none'; frame-src 'none'; base-uri 'none'; form-action 'none'",'Cache-Control':'no-store'}});
  });
  win=new BrowserWindow({width:1280,height:850,show:true,title:clientId+' — STAGE4_TEST',webPreferences:{preload:path.join(__dirname,'desktop/preload.cjs'),additionalArguments:['--stage4-test-renderer'],contextIsolation:true,nodeIntegration:false,sandbox:true,session:ses}});
  win.removeMenu();win.webContents.setWindowOpenHandler(()=>({action:'deny'}));
  win.webContents.on('will-navigate',(event,url)=>{if(url!==page)event.preventDefault();});
  win.webContents.on('will-redirect',event=>event.preventDefault());
  win.webContents.on('render-process-gone',()=>{close();});
  win.on('close',event=>{event.preventDefault();close();});
  await win.loadURL(page);
  // The hidden Windows launcher can suppress the initial ShowWindow. Explicitly
  // show only this authenticated TEST window after loading its isolated page.
  win.show();
  emit({event:'ready',client:clientId,pid:process.pid,identity,profile,electron:process.versions.electron});
 }
 // Trusted TEST-parent driver: fixed actions only, never renderer-selected code,
 // process IDs, paths, native functions, credentials or lifecycle operations.
 async function drive(command){
  requireThat(configuration?.driver&&win&&!win.isDestroyed(),'DRIVER_UNAVAILABLE');
  if(command.action==='close'){await close();return;}
  if(command.action==='snapshot'){
   const result=await win.webContents.executeJavaScript("({ready:document.body.dataset.stage4Ready,connection:document.body.dataset.stage4Connection,request:document.body.dataset.stage4Request||null,done:document.body.dataset.stage4Done||null,status:document.querySelector('[data-stage4-status]')?.textContent,node:typeof require,bridge:Object.keys(window.jarvisStage4||{}),size:[innerWidth,innerHeight]})");emit({event:'snapshot',id:command.id,result});return;
  }
  if(command.action==='submit'){
   requireThat(typeof command.text==='string'&&command.text.length<12001,'DRIVER_TEXT');
   await win.webContents.executeJavaScript("(()=>{const input=document.querySelector('#messageInput,.ask textarea');input.value="+JSON.stringify(command.text)+";document.querySelector('#sendButton,.actions .primary').click();})()");emit({event:'submitted',id:command.id});return;
  }
  if(command.action==='shared'){emit({event:'shared',id:command.id,result:await call('shared')});return;}
  if(command.action==='renew'){emit({event:'renewed',id:command.id,result:await call('renew')});return;}
  if(command.action==='foreign-cancel'){
   argsFor('cancel',{request_id:command.request_id});
   const result=await win.webContents.executeJavaScript('window.jarvisStage4.cancelRequest('+JSON.stringify(command.request_id)+').then(()=>({denied:false}),()=>({denied:true}))');
   emit({event:'foreign-cancel',id:command.id,result});return;
  }
  if(command.action==='boundaries'){
   const result=await win.webContents.executeJavaScript("(async()=>({networkDenied:await fetch('http://127.0.0.1:1').then(()=>false,()=>true),invalidRequestDenied:await window.jarvisStage4.cancelRequest('invalid').then(()=>false,()=>true),shutdownExposed:'shutdown' in window.jarvisStage4,productionBridge:!!window.jarvisDesktop}))()");
   emit({event:'boundaries',id:command.id,result});return;
  }
  if(command.action==='capture'){
   const file=path.join(root,clientId+'-'+crypto.randomUUID()+'.png');
   try{
    const frame=await win.webContents.capturePage();
    requireThat(!frame.isEmpty(),'EMPTY_CAPTURE');
    fs.writeFileSync(file,frame.toPNG());emit({event:'capture',id:command.id,file});
   }catch(error){
    // Preserve a failed visual gate without disguising it as auth failure or
    // preventing independent lifecycle diagnostics. No capture retry/fallback.
    emit({event:'capture',id:command.id,failed:true,error:String(error.message).slice(0,160),
     window:{visible:win.isVisible(),minimized:win.isMinimized(),focused:win.isFocused(),bounds:win.getBounds()}});
   }
   return;
  }
  if(command.action==='crash-renderer'){win.webContents.forcefullyCrashRenderer();return;}
  throw Error('DRIVER_ACTION_DENIED');
 }
 let configured=false;let lineQueue=Promise.resolve();
 const input=value=>{lineQueue=lineQueue.then(async()=>{if(!configured){configured=true;await start(value);}else await drive(value);}).catch(error=>{process.stderr.write('STAGE4_TEST '+String(error.stack).slice(0,2000)+'\n');emit({event:'denied',reason:'TEST_CLIENT_OPERATION_FAILED'});});};
 if(lines){lines.on('line',line=>input(JSON.parse(line)));lines.on('close',()=>close());}
 else {process.on('message',input);process.on('disconnect',()=>close());}
 app.on('window-all-closed',()=>close());
}
module.exports.launchTestClient=launchTestClient;
module.exports.validateTestRoot=validateTestRoot;
