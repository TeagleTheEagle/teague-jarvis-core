// Instrumented copy of desktop/test/backend.test.cjs "shared background Core" (debugging only; sandbox data folder).
const path=require('node:path'),fs=require('node:fs'),os=require('node:os'),http=require('node:http');
const app=process.argv[2];
const {connectCore}=require(path.join(app,'desktop','backend.cjs'));
const t0=Date.now();const log=(...a)=>console.log(((Date.now()-t0)/1000).toFixed(2).padStart(6),...a);
function fresh(link){ // a probe on a brand-new connection (no keep-alive pool)
 return new Promise(resolve=>{const u=new URL(link.origin);const req=http.request({host:u.hostname,port:u.port,path:'/',headers:{'X-Jarvis-Desktop':link.token,Connection:'close'},agent:false,timeout:3000},res=>{res.resume();resolve('status '+res.statusCode);});req.on('error',e=>resolve('error '+e.code));req.on('timeout',()=>{req.destroy();resolve('timeout');});req.end();});
}
function pidAlive(pid){try{process.kill(pid,0);return true;}catch(e){return e.code==='EPERM';}}
(async()=>{
 const folder=fs.mkdtempSync(path.join(os.tmpdir(),'jarvis-shared-core-debug-'));
 const first=await connectCore(app,{dataDir:folder});
 const link=JSON.parse(fs.readFileSync(path.join(folder,'core-connection.json'),'utf8'));
 log('first started',first.started,'pid',link.pid);
 const second=await connectCore(app,{dataDir:folder});
 log('second joined',!second.started);
 await second.stop();await second.quit();
 log('first alive (pooled fetch)',await first.alive());
 const s=Date.now();await first.shutdown();log('shutdown() returned after',(Date.now()-s)+' ms');
 for(let i=0;i<40;i++){
  const pooled=await first.alive();const f=await fresh(link);
  log('pooled fetch alive='+pooled,'| fresh connection:',f,'| file exists:',fs.existsSync(path.join(folder,'core-connection.json')),'| pid alive:',pidAlive(link.pid));
  if(!pooled&&!pidAlive(link.pid))break;
  await new Promise(r=>setTimeout(r,250));
 }
})().catch(e=>{console.error(e);process.exit(1);});
