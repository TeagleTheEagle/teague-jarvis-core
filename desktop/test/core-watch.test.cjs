// How the desktop app tells a requested Core stop from a crash (fix list item 3: no "Core
// stopped" box after a requested shutdown). Fake probes and temporary files only: no Core, no windows.
const {test}=require('node:test'),assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs'),os=require('node:os');
const {spawn}=require('node:child_process');
const {connectionState,processAlive,watchCore,coreEnded,restartAllowed}=require('../backend.cjs');

const link={origin:'http://127.0.0.1:50000',token:'a'.repeat(64),pid:4242};
function folder(){return fs.mkdtempSync(path.join(os.tmpdir(),'jarvis-core-watch-'));}
function write(file,data){fs.writeFileSync(file,JSON.stringify(data));}
const fast={intervalMs:10,probeMs:20,recheckMs:20,unresponsiveMs:200};
function watch(file,options){
 return new Promise(resolve=>{const calls=[];const stop=watchCore(link,file,reason=>{calls.push(reason);resolve({reason,calls,stop});},{...fast,...options});});
}
function within(ms,promise){return Promise.race([promise,new Promise((_,reject)=>setTimeout(()=>reject(new Error('no result within '+ms+' ms')),ms))]);}

test('connection state: ours, replaced, missing, unreadable',()=>{
 const file=path.join(folder(),'core-connection.json');
 assert.equal(connectionState(file,link),'missing');
 write(file,link);assert.equal(connectionState(file,link),'ours');
 write(file,{...link,token:'b'.repeat(64)});assert.equal(connectionState(file,link),'replaced');
 fs.writeFileSync(file,'{not json');assert.equal(connectionState(file,link),'unreadable');
 fs.rmSync(file);fs.mkdirSync(file);assert.equal(connectionState(file,link),'unreadable');  // never 'missing'
});

test('processAlive: this process yes, an exited child no, no pid unknown',async()=>{
 assert.equal(processAlive(process.pid),true);
 const child=spawn(process.execPath,['-e','0'],{env:{...process.env,ELECTRON_RUN_AS_NODE:'1'}});
 await new Promise(resolve=>child.once('exit',resolve));
 assert.equal(processAlive(child.pid),false);
 assert.equal(processAlive(undefined),null);
});

test('requested stop: the Core removed its file and no longer answers, so the app is told "stopped"',async()=>{
 const file=path.join(folder(),'core-connection.json');write(file,link);
 // As in a real stop, the process is gone once its file is gone: that must still read as "stopped".
 const result=within(2000,watch(file,{probe:async()=>fs.existsSync(file),alive:()=>fs.existsSync(file)}));
 setTimeout(()=>fs.rmSync(file),60);
 assert.deepEqual((await result).calls,['stopped']);
});

test('a miss already pending when the Core removes its file and exits is still a requested stop',async()=>{
 const file=path.join(folder(),'core-connection.json');write(file,link);
 const result=within(2000,watch(file,{probe:async()=>false,alive:()=>fs.existsSync(file)}));
 setTimeout(()=>fs.rmSync(file),45);
 assert.equal((await result).reason,'stopped');
});

test('a wall-clock jump backwards does not stop the watcher noticing a crash',async()=>{
 const file=path.join(folder(),'core-connection.json');write(file,link);
 const realNow=Date.now;let probes=0;
 try{
  const result=within(2000,watch(file,{probe:async()=>{if(++probes===1)Date.now=()=>realNow()-3600e3;return false;},alive:()=>false}));
  assert.equal((await result).reason,'crashed');
 }finally{Date.now=realNow;}
});

test('a probe still running when the file goes does not turn a requested stop into a crash',async()=>{
 const file=path.join(folder(),'core-connection.json');write(file,link);
 let first=true;
 const probe=()=>first?(first=false,new Promise(resolve=>setTimeout(()=>resolve(false),150))):Promise.resolve(false);
 const result=within(2000,watch(file,{probe,alive:()=>fs.existsSync(file)}));
 setTimeout(()=>fs.rmSync(file),30);  // gone while the first, slow probe is in flight
 assert.equal((await result).reason,'stopped');
});

test('crash: file left behind unchanged, the Core process is gone, so the app is told "crashed"',async()=>{
 const file=path.join(folder(),'core-connection.json');write(file,link);
 let probes=0;
 const result=await within(2000,watch(file,{probe:async()=>(probes++,false),alive:()=>false}));
 assert.equal(result.reason,'crashed');
 assert.ok(probes>=2,'a crash needs two failed probes');
});

test('a new Core (update, rollback) is never reported as a crash',async()=>{
 const file=path.join(folder(),'core-connection.json');write(file,link);
 const result=within(2000,watch(file,{probe:async()=>connectionState(file,link)==='ours',alive:()=>false}));
 setTimeout(()=>write(file,{...link,token:'c'.repeat(64),pid:5555}),40);
 assert.equal((await result).reason,'replaced');
});

test('file removed by hand while this Core still answers: keep watching, without probing every tick',async()=>{
 const file=path.join(folder(),'core-connection.json');
 let probes=0,ended=null;
 const stop=watchCore(link,file,reason=>{ended=reason;},{intervalMs:10,probeMs:100000,recheckMs:50,probe:async()=>(probes++,true),alive:()=>true});
 await new Promise(r=>setTimeout(r,400));stop();
 assert.equal(ended,null);
 assert.ok(probes>=1&&probes<=3,'one confirming probe, then back to the normal interval; got '+probes);
});

test('hung Core: alive but not answering is reported only after the unresponsive time',async()=>{
 const file=path.join(folder(),'core-connection.json');write(file,link);
 const started=Date.now();
 const result=await within(3000,watch(file,{probe:async()=>false,alive:()=>true,unresponsiveMs:300}));
 assert.equal(result.reason,'unresponsive');
 assert.ok(Date.now()-started>=300);
});

test('reports at most once, and nothing after unwatch',async()=>{
 const file=path.join(folder(),'core-connection.json');write(file,link);
 const calls=[];
 const stop=watchCore(link,file,reason=>calls.push(reason),{...fast,probe:async()=>false,alive:()=>false});
 await new Promise(r=>setTimeout(r,300));
 assert.deepEqual(calls,['crashed']);
 const quiet=[];
 const unwatch=watchCore(link,file,reason=>quiet.push(reason),{...fast,probe:async()=>false,alive:()=>false});unwatch();
 await new Promise(r=>setTimeout(r,200));
 assert.deepEqual(quiet,[]);stop();
});

test('the app quits quietly after a requested stop and shows the box only for a crash; it never stops the Core',()=>{
 for(const [reason,box] of [['stopped',false],['replaced',false],['crashed',true],['unresponsive',true]]){
  const shown=[],quits=[];
  coreEnded(reason,{quitting:()=>false,showErrorBox:text=>shown.push(text),quit:(...args)=>quits.push(args)});
  assert.equal(shown.length,box?1:0,reason);
  if(box)assert.match(shown[0],reason==='crashed'?/stopped unexpectedly/:/not responding/);
  assert.deepEqual(quits,[[]],reason+': quit() once, with no "stop the Core" argument');
 }
 const shown=[],quits=[];
 coreEnded('crashed',{quitting:()=>true,showErrorBox:text=>shown.push(text),quit:()=>quits.push(1)});
 assert.deepEqual([shown,quits],[[],[]],'nothing while the app is already quitting');
});

// Emergency authority (standing.py C, owner 2026-10-13): one automatic restart after a crash, on the owner's switch.
test('after a crash the Core is started again once when standing.json allows it; otherwise the box as before',async()=>{
 const dir=folder();
 assert.equal(restartAllowed('C:/none',dir),false,'no standing.json: no automatic restart');
 fs.writeFileSync(path.join(dir,'standing.json'),JSON.stringify({emergency_restart:false}));
 assert.equal(restartAllowed('C:/none',dir),false,'the switch off');
 fs.writeFileSync(path.join(dir,'standing.json'),JSON.stringify({emergency_restart:true,restart_window_seconds:600}));
 let clock=1000000;const state={};
 assert.equal(restartAllowed('C:/none',dir,state,()=>clock),true,'the switch on: once');
 clock+=5*60*1000;
 assert.equal(restartAllowed('C:/none',dir,state,()=>clock),false,'a second crash inside the window is not restarted');
 clock+=6*60*1000;
 assert.equal(restartAllowed('C:/none',dir,state,()=>clock),true,'after the window, again');
 fs.writeFileSync(path.join(dir,'standing.json'),'not json');
 assert.equal(restartAllowed('C:/none',dir,{},()=>clock),false,'an unreadable file means no restart');
 const shown=[],quits=[],restarts=[];
 await coreEnded('crashed',{quitting:()=>false,showErrorBox:t=>shown.push(t),quit:()=>quits.push(1),restart:async()=>restarts.push(1),mayRestart:()=>true});
 assert.deepEqual([shown,quits,restarts],[[],[],[1]],'a crash with the switch on: restarted, no box, no quit');
 await coreEnded('crashed',{quitting:()=>false,showErrorBox:t=>shown.push(t),quit:()=>quits.push(1),restart:async()=>{throw new Error('no');},mayRestart:()=>true});
 assert.deepEqual([shown.length,quits],[1,[1]],'a restart that fails: the box and the quit as before');
 const shown2=[],quits2=[],restarts2=[];
 coreEnded('crashed',{quitting:()=>false,showErrorBox:t=>shown2.push(t),quit:()=>quits2.push(1),restart:async()=>restarts2.push(1),mayRestart:()=>false});
 assert.deepEqual([shown2.length,quits2,restarts2],[1,[1],[]],'not allowed: as before');
 coreEnded('unresponsive',{quitting:()=>false,showErrorBox:t=>shown2.push(t),quit:()=>quits2.push(1),restart:async()=>restarts2.push(1),mayRestart:()=>true});
 assert.deepEqual([shown2.length,restarts2],[2,[]],'only a crash is restarted; a Core that stopped answering is reported');
 fs.rmSync(dir,{recursive:true,force:true});
});
