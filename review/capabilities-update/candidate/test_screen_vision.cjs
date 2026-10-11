const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const elements=new Map();
function element(){return {hidden:false,disabled:false,value:'Review this screen',checked:false,videoWidth:100,videoHeight:100,events:{},append(){},addEventListener(name,fn){this.events[name]=fn;},removeAttribute(){},showModal(){this.open=true;},close(){this.open=false;this.events.close?.();},async play(){},getContext(){return {drawImage(){},getImageData(){return {data:new Uint8ClampedArray(32*18*4)}}};},toBlob(fn){fn({size:10});}};}
const get=id=>{if(!elements.has(id))elements.set(id,element());return elements.get(id);};
const timers=[];let stopped=0,uploads=0,sends=0;const track={stop(){stopped++;},addEventListener(){}};
let acquire=async()=>({getTracks:()=>[track],getVideoTracks:()=>[track]});
const context={document:{createElement:()=>element(),getElementById:get,body:{append(){}},querySelector:()=>element()},window:{addEventListener(){}},navigator:{mediaDevices:{getDisplayMedia:()=>acquire()}},URL:{createObjectURL:()=> 'blob:test',revokeObjectURL(){}},Date,Math,Promise,Uint8ClampedArray,setInterval(fn){timers.push(fn);},voice:{armed:false,inviteConversation(){return true;}},message(){},speak:async()=>{},resumeRecognition(){},state:{busy:false,transcribing:false},toast(){},view(){},blobBase64:async()=> 'mock',api:async path=>{if(path==='/api/upload')uploads++;return {id:'test'};},send:async(text,attachment)=>{assert.equal(attachment.id,'test');sends++;return true;}};
vm.createContext(context);const source=fs.readFileSync(__dirname+'/static/app.js','utf8');vm.runInContext(source.slice(source.indexOf('// Screen vision:')),context);
(async()=>{
context.openScreenVision();await get('screenChoose').onclick();await new Promise(setImmediate);assert.equal(uploads,0,'guidance asked before first analysis');await context.captureSharedScreen(true,true);
assert.equal(uploads,1,'starting session enables first observation');assert.equal(sends,1);
await get('screenCapture').onclick();assert.equal(stopped,0,'capture preserves source');assert.equal(uploads,1,'manual capture does not duplicate analysis');
context.stopScreenVision();await get('screenSend').onclick();assert.equal(uploads,1,'discarded capture cannot submit');assert.equal(get('screenAuto').checked,false);
await get('screenChoose').onclick();await new Promise(setImmediate);await context.captureSharedScreen(true,true);assert.equal(uploads,2);
await context.captureSharedScreen(true,true);assert.equal(uploads,2,'unchanged frame does not resend');
await context.captureSharedScreen(true,false,'What can you see?');assert.equal(uploads,3,'direct question gets fresh image');
get('screenAuto').checked=true;vm.runInContext('screenAutoCount=10',context);timers[0]();assert.equal(get('screenAuto').checked,false);
let resolve;acquire=()=>new Promise(r=>resolve=r);const pending=get('screenChoose').onclick();context.stopScreenVision();resolve({getTracks:()=>[track],getVideoTracks:()=>[track]});await pending;assert.equal(stopped,3);assert.equal(uploads,3);
console.log('PASS: unified start, observations, fresh question capture, deduplication, stop, limit and cancelled picker.');
})().catch(e=>{console.error(e);process.exitCode=1;});
