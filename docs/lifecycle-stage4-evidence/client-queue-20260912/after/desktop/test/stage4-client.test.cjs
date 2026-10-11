'use strict';
const assert=require('node:assert/strict');
const test=require('node:test');
const client=require('../../stage4_client.cjs');

if(process.argv.includes('--native-case')){
 let input='';process.stdin.setEncoding('utf8');process.stdin.on('data',d=>input+=d);process.stdin.on('end',()=>{
  const config=JSON.parse(input);
  try{
   if(config.action==='bootstrap'){
    const result=client.bootstrap({...config,expectedIdentity:{...config.expectedIdentity,created:BigInt(config.expectedIdentity.created)},
     serverKey:Buffer.from(config.serverKey,'hex'),clientKey:Buffer.from(config.clientKey,'hex')});
    assert.equal(result.result,'OK');process.stdout.write(JSON.stringify({passed:true}));return;
   }
   const bridge=client.loadBridge(config.nativePath);
   if(config.action==='self'){
    const value=bridge.currentProcessIdentity();assert.equal(value.pid,process.pid);assert.match(value.created,/^\d+$/);assert.match(value.exe_digest,/^[a-f0-9]{64}$/);
    assert.equal(bridge.inspectProcess,undefined);process.stdout.write(JSON.stringify({passed:true}));return;
   }
   const pipe=config.core?bridge.connectTestPipe(config.endpoint,config.peer,config.core):bridge.connectTestPipe(config.endpoint,config.peer);
   try{
    if(config.verify){
     if(config.verify==='argument')pipe.verifyCore({pid:process.pid});
     else if(config.verify==='closed'){pipe.close();pipe.verifyCore();}
     else {if(config.verify==='immutable')config.core.created='1';assert.equal(pipe.verifyCore(),true);}
    }
    pipe.send(Buffer.from('{"test":"hello"}'));assert.equal(client.parse(pipe.receive()).result,'OK');}
   finally{pipe.close();}
   process.stdout.write(JSON.stringify({passed:true}));
  }catch(e){process.stdout.write(JSON.stringify({passed:false,error:e.message}));}
 });
}else{
 function queueFixture(){
  let now=0;const sent=[],timers=new Map(),failures=[];
  const queue=new client.TransportQueue(m=>sent.push(m),{timeout:10,limit:2,clock:()=>now,
   setTimer:fn=>{const id=Symbol();timers.set(id,fn);return id;},clearTimer:id=>timers.delete(id),onFailure:r=>failures.push(r)});
  const result=(op)=>queue.call(op).then(value=>({value}),error=>({error:error.message}));
  return {queue,sent,timers,failures,result,advance:n=>{now=n;}};
 }
 test('queue deadline includes waiting; expired work is never dispatched',async()=>{
  const f=queueFixture(),a=f.result('request'),b=f.result('request');
  f.advance(11);f.queue.receive({id:1,result:'late'});
  assert.deepEqual(await a,{error:'TRANSPORT_DEADLINE'});assert.deepEqual(await b,{error:'TRANSPORT_DEADLINE'});
  assert.equal(f.sent.length,1);assert.equal(f.timers.size,0);assert.deepEqual(f.failures,['TRANSPORT_DEADLINE']);
  assert.deepEqual(await f.result('request'),{error:'TRANSPORT_DEADLINE'});
 });
 test('stalled transport timer rejects all admitted calls without replay',async()=>{
  const f=queueFixture(),a=f.result('request'),b=f.result('request');
  f.timers.values().next().value();
  assert.equal((await a).error,'TRANSPORT_DEADLINE');assert.equal((await b).error,'TRANSPORT_DEADLINE');
  f.queue.receive({id:1,result:'late'});assert.equal(f.sent.length,1);
 });
 test('closing cancels undispatched requests but permits cooperative detach',async()=>{
  const f=queueFixture(),a=f.result('request'),b=f.result('request');
  f.queue.cancelQueued();assert.equal((await b).error,'CLIENT_CLOSING');
  const detach=f.result('detach');f.queue.receive({id:1,result:'finished'});
  assert.deepEqual(await a,{value:'finished'});assert.deepEqual(f.sent.map(m=>m.op),['request','detach']);
  f.queue.receive({id:3,result:'DETACHED'});assert.deepEqual(await detach,{value:'DETACHED'});
  assert.equal(f.timers.size,0);
 });
 test('bridge exit rejects active and queued calls and ignores stale replies',async()=>{
  const f=queueFixture(),a=f.result('request'),b=f.result('request');f.queue.fail('BRIDGE_EXITED');
  assert.equal((await a).error,'BRIDGE_EXITED');assert.equal((await b).error,'BRIDGE_EXITED');
  f.queue.receive({id:1,result:'late'});assert.equal(f.sent.length,1);assert.equal(f.timers.size,0);
 });
 test('queue limit rejects excess work without sending it',async()=>{
  const f=queueFixture(),a=f.result('request'),b=f.result('request');assert.equal((await f.result('request')).error,'CLIENT_BUSY');
  f.queue.fail('BRIDGE_FAILED');await a;await b;assert.equal(f.sent.length,1);
 });
 test('ordinary operation denial does not poison a healthy transport',async()=>{
  const f=queueFixture(),a=f.result('request'),b=f.result('shared');
  f.queue.receive({id:1,error:'CORE_DENIED'});assert.equal((await a).error,'CORE_DENIED');
  f.queue.receive({id:2,result:'state'});assert.equal((await b).value,'state');assert.equal(f.failures.length,0);
 });
 test('worker send failure fails closed without a leaked timer',async()=>{
  const f=queueFixture();f.queue.send=()=>{throw Error('worker gone');};
  assert.equal((await f.result('request')).error,'BRIDGE_FAILED');assert.equal(f.timers.size,0);
 });
 test('preserves exact Windows creation-time integer',()=>{const raw='{"created":134335772813688018}';assert.equal(client.canonical(client.parse(Buffer.from(raw))),raw);});
 test('unsafe Number rejected',()=>assert.throws(()=>client.canonical({created:134335772813688018}),/UNSAFE_NUMBER/));
 test('canonical protocol bytes sorted with Python-compatible ASCII escapes',()=>assert.equal(client.canonical({z:'é',a:2}),'{"a":2,"z":"\\u00e9"}'));
 test('missing native bridge fails closed',()=>assert.throws(()=>client.loadBridge('./missing-stage4-bridge.node')));
 test('production identity refused before bridge load',()=>assert.throws(()=>client.bootstrap({expectedIdentity:{mode:'PRODUCTION'}}),/TEST_ONLY/));
 test('renderer cannot load native functions',()=>{const old=process.type;process.type='renderer';try{assert.throws(()=>client.loadBridge('./anything'),/MAIN_PROCESS_ONLY/);}finally{if(old===undefined)delete process.type;else process.type=old;}});
}
