const {test}=require('node:test'),assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs'),os=require('node:os');
const {startBackend}=require('../backend.cjs');
test('owned backend: ephemeral port, authentication, graceful shutdown',async()=>{
const folder=fs.mkdtempSync(path.join(os.tmpdir(),'jarvis-shell-test-'));const b=startBackend(path.resolve(__dirname,'../..'),{dataDir:folder});
try{const {origin,token}=await b.ready;assert.notEqual(origin,'http://127.0.0.1:8765');assert.equal((await fetch(origin)).status,403);assert.equal((await fetch(origin,{headers:{'X-Jarvis-Desktop':token}})).status,200);const page=await fetch(origin,{headers:{'X-Jarvis-Desktop':token}});const cookie=page.headers.get('set-cookie').split(';')[0];const ready=await fetch(origin+'/api/wake/prepare',{method:'POST',headers:{'X-Jarvis-Desktop':token,Cookie:cookie,'Content-Type':'application/json'},body:'{}',signal:AbortSignal.timeout(10000)});assert.equal(ready.status,200);assert.equal((await ready.json()).ready,true);b.stop();await b.quit();assert.notEqual(b.child.exitCode,null);}finally{await b.quit();}
// Test database retained in OS temp for inspection; no production data touched.
});
test('desktop update script is served by the authenticated backend',async()=>{
 const folder=fs.mkdtempSync(path.join(os.tmpdir(),'jarvis-update-route-'));
 const b=startBackend(path.resolve(__dirname,'../..'),{dataDir:folder});
 try{
  const {origin,token}=await b.ready;
  const response=await fetch(origin+'/desktop-updates.js',{headers:{'X-Jarvis-Desktop':token}});
  assert.equal(response.status,200);
  assert.match(await response.text(),/bridge\.onUpdateAvailable/);
 }finally{await b.quit();}
});
test('one Core per data folder: a second desktop backend is refused, not started',async()=>{
 const folder=fs.mkdtempSync(path.join(os.tmpdir(),'jarvis-one-core-'));
 const first=startBackend(path.resolve(__dirname,'../..'),{dataDir:folder});
 try{
  await first.ready;
  const second=startBackend(path.resolve(__dirname,'../..'),{dataDir:folder});
  await assert.rejects(second.ready,error=>error.code==='CORE_ALREADY_RUNNING'&&/already running for this data folder/.test(error.message));
  await second.quit();
 }finally{await first.quit();}
});
