const assert=require('node:assert/strict');
const Voice=require('./static/voice.js');
(async()=>{
 let acquisitions=0,release,errors=[];
 Object.defineProperty(global,'navigator',{configurable:true,value:{mediaDevices:{getUserMedia:async()=>{
  acquisitions++;if(release===true)await new Promise(r=>release=r);
  const track={readyState:'live',stop(){this.readyState='ended';}};
  return {getTracks:()=>[track],getAudioTracks:()=>[track]};
 }}}});
 global.AudioContext=class{audioWorklet={addModule:async()=>{}};destination={};createMediaStreamSource(){return {connect(){},disconnect(){}};}async resume(){}async close(){}};
 global.AudioWorkletNode=class{port={};connect(){}disconnect(){}};
 const v=new Voice({status(){},prepare:async()=>{},error:e=>errors.push(e.message)});
 await v.start('chosen-input');v.session=true;
 await v.recover();assert.equal(acquisitions,2);assert.equal(v.active,true);assert.equal(v.session,false,'recovery must return to wake-word standby');assert.equal(v.deviceId,'chosen-input');
 release=true;const pending=v.recover();await new Promise(r=>setImmediate(r));v.stop();release();await pending;
 assert.equal(v.active,false,'mute during reconnect must win');
 await v.start();await v.recover();await v.recover();await v.recover();await v.recover();
 assert.equal(v.active,false);assert.equal(errors.length,1,'repeated stalls must stop with a visible error');
 console.log('PASS: selected-input recovery, standby, mute cancellation and bounded retries.');
})().catch(e=>{console.error(e);process.exitCode=1;});
