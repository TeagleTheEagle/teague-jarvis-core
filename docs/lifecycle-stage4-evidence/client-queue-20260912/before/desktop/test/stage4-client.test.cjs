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
 test('preserves exact Windows creation-time integer',()=>{const raw='{"created":134335772813688018}';assert.equal(client.canonical(client.parse(Buffer.from(raw))),raw);});
 test('unsafe Number rejected',()=>assert.throws(()=>client.canonical({created:134335772813688018}),/UNSAFE_NUMBER/));
 test('canonical protocol bytes sorted with Python-compatible ASCII escapes',()=>assert.equal(client.canonical({z:'é',a:2}),'{"a":2,"z":"\\u00e9"}'));
 test('missing native bridge fails closed',()=>assert.throws(()=>client.loadBridge('./missing-stage4-bridge.node')));
 test('production identity refused before bridge load',()=>assert.throws(()=>client.bootstrap({expectedIdentity:{mode:'PRODUCTION'}}),/TEST_ONLY/));
 test('renderer cannot load native functions',()=>{const old=process.type;process.type='renderer';try{assert.throws(()=>client.loadBridge('./anything'),/MAIN_PROCESS_ONLY/);}finally{if(old===undefined)delete process.type;else process.type=old;}});
}
