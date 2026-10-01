const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const context={module:{exports:{}},clearInterval};
vm.runInNewContext(fs.readFileSync(process.argv[2]||require('node:path').join(__dirname,'static/voice.js'),'utf8'),context);
const Voice=context.module.exports;
async function check(change,expectedError){
 let reject,errors=0;
 const voice=new Voice({status(){},error(){errors++;},detect:()=>new Promise((_,r)=>reject=r)});
 voice.active=true;voice.queue=[new Int16Array(5120)];
 const pending=voice.drain(voice.generation);
 change(voice);reject(new Error('Detection failed'));await pending;
 assert.equal(errors,expectedError);
 assert.equal(voice.active,!expectedError);
 return voice;
}
(async()=>{
 await check(v=>v.pause(),0);
 await check(v=>v.endConversation(),0);
 await check(()=>{},1);
 const newer=await check(v=>{v.stop();v.active=true;v.pending=true;},0);
 assert.equal(newer.pending,true,'old cleanup cannot clear newer pending work');
 console.log('PASS: stale pause/reset failures ignored; current failures reported; new session preserved.');
})().catch(e=>{console.error(e);process.exitCode=1;});
