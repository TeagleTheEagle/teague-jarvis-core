const assert=require('node:assert/strict');
const Voice=require('../../static/voice.js');
function measure(endpoint){let done=false;const v=new Voice({level:()=>{},status:()=>{},command:()=>{done=true;},endpointSeconds:()=>endpoint});v.active=true;v.armed=true;v.generation=1;v.frames=[];v.voiced=v.quiet=v.elapsed=0;v.frame(new Int16Array(5120).fill(3000),1);let frames=0;while(!done&&frames<20){v.frame(new Int16Array(5120),1);frames++;}return frames*320;}
const before=measure(2.56),after=measure(1.28);assert.equal(before,2560);assert.equal(after,1280);
console.log(JSON.stringify({kind:'deterministic microphone-frame simulation, not live speech',before_endpoint_ms:before,after_endpoint_ms:after,saved_ms:before-after}));
