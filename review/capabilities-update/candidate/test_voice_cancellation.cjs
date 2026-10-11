const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(__dirname+'/static/app.js','utf8');
const start=source.indexOf('let speechRequest;'),end=source.indexOf("$('#speakerButton').onclick",start);
const pending=[],messages=[];
const context={performance,voiceDiagnostic(){},state:{data:{settings:{voice:true},capabilities:{fish:true}},voiceGeneration:0,busy:true},AbortController,window:{speechSynthesis:{cancel(){}}},pauseRecognition(){},setMode(){},$(){return {}},disconnectSpeechVisual(){},resumeRecognition(){},toast(t){messages.push(t)},log(){},fetch(url,options){return new Promise((resolve,reject)=>{pending.push(options.signal);options.signal.addEventListener('abort',()=>reject(Object.assign(new Error('cancelled'),{name:'AbortError'})));})}};
vm.createContext(context);vm.runInContext(source.slice(start,end),context);
(async()=>{const first=context.speak('First');const second=context.speak('Second');assert.equal(pending[0].aborted,true);assert.equal(pending[1].aborted,false);await first;assert.equal(pending[1].aborted,false);context.stopSpeech();await second;assert.equal(pending[1].aborted,true);assert.deepEqual(messages,[]);console.log('PASS: superseded speech aborts; cancellation is silent; old cleanup preserves current request.');})().catch(e=>{console.error(e);process.exitCode=1;});
