const assert=require('node:assert/strict');
const Voice=require('./static/voice.js');
const tick=()=>new Promise(r=>setImmediate(r));
(async()=>{
 let release;const seen=[],commands=[];
 const voice=new Voice({detect:async pcm=>{seen.push(pcm[0]);if(pcm[0]===1)await new Promise(r=>release=r);return {detected:false};},status:()=>{},wake:()=>{},error:e=>{throw e;},command:async blob=>commands.push(blob)});
 voice.active=true;voice.pending=false;
 for(let n=1;n<=3;n++)voice.frame(new Int16Array(5120).fill(n),0);
 assert.deepEqual(seen,[1]);release();await tick();assert.deepEqual(seen,[1,2,3]);
 voice.pause();voice.frame(new Int16Array(5120),0);await tick();assert.equal(seen.length,3);
 voice.arm(true);voice.frame(new Int16Array(5120).fill(1000),0);await voice.finish();
 assert.equal(commands.length,1);assert.equal(commands[0].size,10240);assert.equal(commands[0].type,'application/octet-stream');
 let delayed;let wakes=0;
 const stale=new Voice({detect:()=>new Promise(r=>delayed=r),status:()=>{},wake:()=>wakes++,error:()=>{}});
 stale.active=true;stale.frame(new Int16Array(5120),0);stale.pause();delayed({detected:true});await tick();assert.equal(wakes,0);
 stale.stop();voice.stop();
 console.log('Main local voice: continuous audio, playback suppression, PCM and stale-wake checks passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
