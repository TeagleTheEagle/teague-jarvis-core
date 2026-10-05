// While JARVIS works on an answer and plays nothing, the wake word still counts, so a spoken "Hey JARVIS,
// emergency stop" is heard then too (docs/PERMISSIONS.md section 9, finding 1). Never while a reply is spoken.
const assert=require('node:assert/strict');
const Voice=require('./static/voice.js');
const frame=()=>new Int16Array(5120);
const tick=()=>new Promise(r=>setImmediate(r));
(async()=>{
 // 1. Thinking: frames go to the wake detector; a detection interrupts and listens.
 let thinking=true,playing=false,wakes=0,asked=0,detectNext=false,statuses=[],errors=0;
 const v=new Voice({wake:()=>{wakes++;},status:t=>statuses.push(t),error:()=>{errors++;},canInterrupt:()=>playing,thinking:()=>thinking,
  detect:async()=>{asked++;return {detected:detectNext};}});
 v.active=true;v.wakeEnabled=true;v.pause();
 v.frame(frame(),0);await tick();
 assert.equal(asked,1,'a frame heard while thinking is looked at for the wake word');
 assert.deepEqual(statuses,[],'no "say hey JARVIS" line is written over the thinking state');
 assert.equal(wakes,0);assert.equal(v.suspended,true);
 detectNext=true;v.frame(frame(),0);await tick();
 assert.equal(wakes,1,'the wake word interrupts the answer');
 assert.equal(v.armed,true);assert.equal(v.suspended,false);assert.equal(v.session,true);
 v.stop();

 // 2. Not thinking (a reply is being fetched or spoken): nothing is sent to the wake detector.
 asked=0;thinking=false;playing=true;
 const speaking=new Voice({wake:()=>{wakes++;},status:()=>{},canInterrupt:()=>playing,thinking:()=>thinking,detect:async()=>{asked++;return {detected:true};}});
 speaking.active=true;speaking.wakeEnabled=true;speaking.pause();
 for(let i=0;i<5;i++)speaking.frame(frame(),0);await tick();
 assert.equal(asked,0,'JARVIS never listens for its own name while it speaks');
 speaking.stop();

 // 3. Push to talk (no wake word): thinking changes nothing.
 asked=0;thinking=true;playing=false;
 const manual=new Voice({wake:()=>{},status:()=>{},canInterrupt:()=>false,thinking:()=>true,detect:async()=>{asked++;return {detected:true};}});
 manual.active=true;manual.wakeEnabled=false;manual.pause();
 manual.frame(frame(),0);await tick();
 assert.equal(asked,0);assert.equal(manual.armed,false);
 manual.stop();

 // 4. A Core that answers the wake requests late while it works: frames are dropped, the microphone stays on.
 let release;const slow=new Voice({wake:()=>{},status:()=>{},error:()=>{errors++;},canInterrupt:()=>false,thinking:()=>true,
  detect:()=>new Promise(r=>{release=r;})});
 slow.active=true;slow.wakeEnabled=true;slow.pause();
 for(let i=0;i<20;i++)slow.frame(frame(),0);
 assert.equal(slow.active,true,'falling behind while JARVIS works does not switch the microphone off');
 assert.ok(slow.queue.length<=6);assert.equal(errors,0);
 release({detected:false});await tick();slow.stop();

 // 5. A wake request that fails while JARVIS works is skipped; the same failure when idle is still reported.
 const failing=new Voice({wake:()=>{},status:()=>{},error:()=>{errors++;},canInterrupt:()=>false,thinking:()=>true,
  detect:async()=>{throw new Error('Core busy');}});
 failing.active=true;failing.wakeEnabled=true;failing.pause();
 failing.frame(frame(),0);await tick();await tick();
 assert.equal(errors,0);assert.equal(failing.active,true);
 failing.resume();failing.frame(frame(),0);await tick();await tick();
 assert.equal(errors,1,'when idle a failing wake detector is reported as before');
 assert.equal(failing.active,false);

 // 6. An older page without the "thinking" callback behaves as before: paused means not listening.
 asked=0;
 const old=new Voice({wake:()=>{},status:()=>{},canInterrupt:()=>false,detect:async()=>{asked++;return {detected:true};}});
 old.active=true;old.wakeEnabled=true;old.pause();old.frame(frame(),0);await tick();
 assert.equal(asked,0);old.stop();

 // 7. An open conversation: after a spoken exchange the listener stays armed, also through the pause of a
 // question that was typed. The wake word must interrupt then as well (second review, M1).
 let openWakes=0;
 const open=new Voice({wake:()=>{openWakes++;},status:()=>{},command:async()=>{},canInterrupt:()=>false,thinking:()=>true,detect:async()=>({detected:true})});
 open.active=true;open.wakeEnabled=true;open.arm();assert.equal(openWakes,1);
 await open.finish();open.resume();
 assert.equal(open.armed,true,'the conversation is open: the listener is armed again');
 open.pause();                                             // a typed question starts: JARVIS is thinking
 assert.equal(open.armed,true);assert.equal(open.suspended,true);
 open.frame(frame(),0);await tick();
 assert.equal(openWakes,2,'"Hey JARVIS" interrupts although the listener was still armed');
 assert.equal(open.armed,true);assert.equal(open.suspended,false);
 open.stop();

 // 8. Frames that piled up while JARVIS worked do not count against the idle limit afterwards: an answer that
 // ends without speech must not switch the microphone off (second review, L2).
 let busy=true,piled=0;
 const late=new Voice({wake:()=>{},status:()=>{},error:()=>{piled++;},canInterrupt:()=>false,thinking:()=>busy,detect:()=>new Promise(()=>{})});
 late.active=true;late.wakeEnabled=true;late.pause();
 for(let i=0;i<12;i++)late.frame(frame(),0);
 busy=false;late.resume();late.frame(frame(),0);
 assert.equal(late.active,true,'the microphone stays on after the answer');
 assert.equal(piled,0);late.stop();
 console.log('PASS: wake word alive while thinking (also in an open conversation), silent while speaking, push to talk unchanged, late and failing requests tolerated.');
})().catch(e=>{console.error(e);process.exitCode=1;});
