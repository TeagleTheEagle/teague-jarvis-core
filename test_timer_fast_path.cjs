const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const path=require('path');
const controls=fs.readFileSync(path.join(__dirname,'static/assistant-controls.js'),'utf8');
const app=fs.readFileSync(path.join(__dirname,'static/app.js'),'utf8');
const messages=[],calls=[];
let now=100000,timers=[{title:'Tea',due:178}],reject=false,pending;
const context={Date:{now:()=>now},state:{voiceGeneration:0},window:{speechSynthesis:{}},
 message(role,text){const m={role,p:{textContent:text}};messages.push(m);return m;},
 async api(url,body){calls.push([url,body]);if(reject)throw Error('offline');if(pending)await pending;return {timers};},
 async speak(text,options){now+=9000;context.spoken=text;context.options=options;}};
vm.createContext(context);vm.runInContext(controls.slice(controls.indexOf('// Read-only timer queries')),context);
(async()=>{
 for(const text of ['How much time remains?','How much time is left on my timer?','How long is left?','List my active timers','Hey Jarvis, name active timers.'])assert.equal(context.timerStatusIntent(text),true,text);
 for(const text of ['Cancel my timer','Explain how much time remains','The screenshot says list my active timers','Do not list my active timers'])assert.equal(context.timerStatusIntent(text),false,text);
 await context.answerTimerStatus('How much time remains?');
 assert.equal(calls.length,1);assert.equal(calls[0][1].name,'manage_timer');assert.equal(calls[0][1].args.action,'list');
 assert.match(messages[1].p.textContent,/1 minute and 18 seconds/);
 assert.match(context.spoken,/^When checked: 1 minute and 18 seconds/);assert.equal(context.options,undefined);
 assert.match(context.timerStatusText([],now),/No active timers/);
 assert.match(context.timerStatusText([{due:100}],now),/reached zero/);
 assert.match(context.timerStatusText([{title:'Tea',due:200},{title:'Work',due:300}],now),/Tea:.*Work:/);
 reject=true;await context.answerTimerStatus('Timer status');assert.match(messages.at(-1).p.textContent,/could not check/);reject=false;
 let release;pending=new Promise(r=>release=r);context.spoken=null;
 const cancelled=context.answerTimerStatus('Timer status');context.state.voiceGeneration++;release();await cancelled;assert.equal(context.spoken,null);pending=null;
 // Real speech routine must retain the configured provider even with browser speech available.
 let utterance,cloud=0;
 const speech={JarvisLatency:{mark(){},value(){}},performance,AbortController,state:{data:{settings:{voice:true},capabilities:{fish:true}},voiceGeneration:0,busy:false},window:{speechSynthesis:{cancel(){}}},
 speechSynthesis:{getVoices:()=>[],speak(u){utterance=u.text;u.onend();}},SpeechSynthesisUtterance:class{constructor(t){this.text=t;}},
 voiceDiagnostic(){},pauseRecognition(){},setMode(){},$(){return {};},disconnectSpeechVisual(){},resumeRecognition(){},toast(){},log(){},fetch(url,options){cloud++;assert.equal(url,'/api/speech');assert.equal(JSON.parse(options.body).text,context.spoken);throw Object.assign(Error('Mock cancellation'),{name:'AbortError'});}};
 vm.createContext(speech);vm.runInContext(app.slice(app.indexOf('let speechRequest;'),app.indexOf("$('#speakerButton').onclick")),speech);
 context.spoken='When checked: 1 minute and 18 seconds remaining, Sir.';
 await speech.speak(context.spoken);
 assert.equal(utterance,undefined);assert.equal(cloud,1);
 console.log('PASS: timer fast path, qualified timing, empty/expired/multiple timers, read failure, cancellation, configured cloud voice.');
})().catch(e=>{console.error(e);process.exitCode=1;});
