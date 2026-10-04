const {test}=require('node:test'),assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs'),os=require('node:os');
const {spawn}=require('node:child_process');
// A stand-in Core: answers like JARVIS; on /api/shutdown it removes its connection file, stops listening and drops every
// connection at once, but its process lives 1.5 s longer. The real Core can still answer on an already-open connection
// in that moment (release 1.0.13 regression, desktop/test/backend.test.cjs "shared background Core").
const FAKE_CORE=`const http=require('http'),fs=require('fs');const file=process.argv[1];const sockets=new Set();
const server=http.createServer((req,res)=>{
 if(req.url==='/api/shutdown'){res.end('{"status":"shutting down"}');
  setImmediate(()=>{fs.rmSync(file,{force:true});server.close();for(const s of sockets)s.destroy();setTimeout(()=>process.exit(0),1500);});return;}
 res.setHeader('Set-Cookie','jarvis_session=test');res.end('<title>JARVIS</title>');});
server.on('connection',s=>{sockets.add(s);s.on('close',()=>sockets.delete(s));});
server.listen(0,'127.0.0.1',()=>{fs.writeFileSync(file+'.tmp',JSON.stringify({origin:'http://127.0.0.1:'+server.address().port,token:'t'.repeat(64),pid:process.pid}));fs.renameSync(file+'.tmp',file);});`;
function running(pid){try{process.kill(pid,0);return true;}catch(e){return e.code==='EPERM';}}
async function joinStandIn(t){
 const {connectCore}=require('../backend.cjs');
 const folder=fs.mkdtempSync(path.join(os.tmpdir(),'jarvis-shutdown-wait-'));
 const file=path.join(folder,'core-connection.json');
 const core=spawn(process.execPath,['-e',FAKE_CORE,file],{stdio:'ignore',windowsHide:true,env:{...process.env,ELECTRON_RUN_AS_NODE:'1'}});
 t.after(()=>{if(running(core.pid))core.kill();fs.rmSync(folder,{recursive:true,force:true});});
 for(const deadline=Date.now()+20000;!fs.existsSync(file);await new Promise(r=>setTimeout(r,50)))if(Date.now()>deadline)throw new Error('the stand-in Core did not start');
 // The test folder as the app root: if joining failed, no real Core could be started from it.
 const app=await connectCore(folder,{dataDir:folder});
 assert.equal(app.started,false,'the app must join the running Core');
 return {app,core,file};
}
test('"Quit JARVIS completely" returns only after the Core process has exited',{timeout:60000},async t=>{
 const {app,core,file}=await joinStandIn(t);
 await app.shutdown();
 assert.equal(running(core.pid),false,'shutdown() returned while the Core process was still running');
 assert.equal(await app.alive(),false);
 assert.equal(fs.existsSync(file),false);
});
test('"Quit JARVIS completely" after a Core crash returns at once',{timeout:60000},async t=>{
 const {app,core,file}=await joinStandIn(t);
 core.kill();                                // a crash leaves the connection file behind
 for(const deadline=Date.now()+10000;running(core.pid)&&Date.now()<deadline;)await new Promise(r=>setTimeout(r,50));
 assert.equal(fs.existsSync(file),true);
 const started=Date.now();
 await app.shutdown();
 assert.ok(Date.now()-started<5000,'shutdown() waited '+(Date.now()-started)+' ms for a Core that had crashed');
});
