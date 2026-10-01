const assert=require('node:assert/strict');
const Voice=require('./static/voice.js');
(async()=>{
 let release,connected=false,stopped=false;
 Object.defineProperty(global,'navigator',{configurable:true,value:{mediaDevices:{getUserMedia:async()=>({getTracks:()=>[{stop(){stopped=true;}}]})}}});
 global.AudioContext=class {constructor(){connected=true;}};
 const v=new Voice({status(){},prepare:()=>new Promise(r=>release=r)});
 const start=v.start();await new Promise(r=>setImmediate(r));
 assert.equal(connected,false,'capture graph must wait for preparation');
 v.stop();release();await start;
 assert.equal(connected,false,'cancelled preparation must never connect capture');
 assert.equal(stopped,true);
 console.log('PASS: preparation precedes capture; mute during preparation prevents capture.');
})().catch(e=>{console.error(e);process.exitCode=1;});

