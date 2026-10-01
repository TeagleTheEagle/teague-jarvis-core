'use strict';
// Prototype only. No assistant tools, cloud speech, or persistent audio storage.
class OrderedWakeQueue {
  constructor(detect, result, fail){this.detect=detect;this.result=result;this.fail=fail;this.queue=[];this.running=false;this.closed=false;}
  push(pcm){if(this.closed)return;if(this.queue.length>=6){this.close();this.fail(new Error('Wake detection fell behind. Enable the microphone again; audio was not silently skipped.'));return;}this.queue.push(pcm);this.drain();}
  close(){this.closed=true;this.queue=[];}
  async drain(){if(this.running||this.closed)return;this.running=true;try{while(this.queue.length&&!this.closed){const result=await this.detect(this.queue.shift());if(!this.closed)this.result(result);}}catch(e){if(!this.closed){this.close();this.fail(e);}}finally{this.running=false;}}
}
if(typeof module!=='undefined')module.exports=OrderedWakeQueue;
if(typeof document!=='undefined')(()=>{
const $=id=>document.getElementById(id);
let stream,context,node,source,queue,controller,client,generation=0,active=false,mode='muted',frames=[],pre=[],elapsed=0,quiet=0,voiced=0,manual=false,lastFrame=0,sampleUrl;
let detections=0,misses=0,falseTriggers=0;
function state(value,detail){mode=value;$('indicator').dataset.state=value;$('state').textContent={muted:'Muted',ready:'Ready · say “Hey Jarvis”',starting:'Starting local detector',listening:'Listening',processing:'Processing locally',speaking:'Speaking · microphone paused'}[value]||value;if(detail)$('detail').textContent=detail;$('ptt').disabled=!active||!['ready','listening'].includes(value);}
function counts(){$('counts').textContent=`${detections} detections · ${misses} marked misses · ${falseTriggers} marked false triggers`;}
function encode(parts){let result='';for(const part of parts){const bytes=new Uint8Array(part.buffer,part.byteOffset,part.byteLength);for(let i=0;i<bytes.length;i+=8192)result+=String.fromCharCode(...bytes.subarray(i,i+8192));}return btoa(result);}
async function post(path,body,signal){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal});const data=await r.json();if(!r.ok)throw new Error(data.error||'Local request failed.');return data;}
function stop(detail='Microphone muted. Enable it to resume.'){
generation++;active=false;queue?.close();controller?.abort();node?.disconnect();source?.disconnect();stream?.getTracks().forEach(t=>t.stop());context?.close().catch(()=>{});stream=context=node=source=null;frames=[];pre=[];manual=false;$('level').value=0;$('mute').disabled=true;$('start').disabled=false;$('device').disabled=false;state('muted',detail);
}
function fail(e){stop(e.name==='NotAllowedError'?'Microphone permission was denied. Allow microphone access in your browser, then retry.':e.name==='NotFoundError'?'No microphone was exposed by this browser. Try Chrome or Edge with your SteelSeries headset.':e.message);}
function newQueue(g){queue?.close();queue=new OrderedWakeQueue(async pcm=>{const t=performance.now();const r=await post('/api/wake',{client,data:encode([pcm]),sensitivity:$('sensitivity').value},controller.signal);return {...r,ms:Math.round(performance.now()-t)};},r=>{if(g!==generation||!active)return;$('metrics').textContent=`Wake score ${r.score} · request ${r.ms} ms · ${queue.queue.length} queued chunks`;if(mode==='starting')state('ready','Local detector ready. Audio is processed continuously.');if(r.detected&&mode==='ready'){detections++;counts();arm(false);}},fail);}
async function devices(){const selected=$('device').value;const list=(await navigator.mediaDevices.enumerateDevices()).filter(d=>d.kind==='audioinput');$('device').replaceChildren();const fallback=new Option('System default','');$('device').append(fallback);for(const d of list)$('device').append(new Option(d.label||'Microphone (permission needed)',d.deviceId));$('device').value=selected;}
async function start(){stop();$('playback').pause();const g=generation;$('mute').disabled=false;$('start').disabled=true;$('device').disabled=true;state('starting','Opening the selected microphone…');try{
const chosen=$('device').value;localStorage.setItem('jarvisMicrophone',chosen);const opened=await navigator.mediaDevices.getUserMedia({audio:{...(chosen?{deviceId:{exact:chosen}}:{}),echoCancellation:true,noiseSuppression:true,autoGainControl:true},video:false});
if(g!==generation){opened.getTracks().forEach(t=>t.stop());return;}stream=opened;context=new AudioContext();await context.audioWorklet.addModule('/mic-worklet.js');if(g!==generation)return;
node=new AudioWorkletNode(context,'jarvis-microphone');source=context.createMediaStreamSource(stream);source.connect(node);node.connect(context.destination);controller=new AbortController();client=crypto.randomUUID();active=true;lastFrame=performance.now();newQueue(g);
stream.getAudioTracks()[0].onended=()=>{if(g===generation)stop('Microphone disconnected. Reconnect it and enable again.');};
node.port.onmessage=e=>frame(new Int16Array(e.data),g);await context.resume();if(g!==generation)return;$('mute').disabled=false;await devices();$('deviceInfo').textContent='Active input: '+stream.getAudioTracks()[0].label;
}catch(e){if(g===generation)fail(e);}}
function arm(held){if(!active||!['ready','starting'].includes(mode))return;queue?.close();manual=held;frames=held?[]:pre.slice();elapsed=quiet=voiced=0;state('listening',held?'Speak while holding; release to transcribe.':'Wake word heard. Speak now, then pause.');}
async function finish(){if(mode!=='listening')return;const g=generation;const captured=frames;frames=[];pre=[];manual=false;state('processing','Running local Silero speech filtering and Whisper transcription…');try{
if(!captured.length)return;const r=await post('/api/voice-lab/transcribe',{data:encode(captured)},controller.signal);if(g!==generation)return;$('transcript').textContent=r.text||'No speech detected.';$('engine').textContent=`Local transcription: ${r.latency_ms} ms for ${r.audio_seconds} seconds of audio. No cloud used.`;
}catch(e){if(g===generation)$('transcript').textContent=e.message;}finally{if(g===generation&&active){state('ready','Ready for another wake word or push-to-talk.');newQueue(g);}}}
function frame(pcm,g){if(!active||g!==generation)return;lastFrame=performance.now();const rms=Math.sqrt(pcm.reduce((s,v)=>s+v*v,0)/pcm.length)/32768;$('level').value=Math.min(1,rms*5);
if(mode==='processing'||mode==='speaking')return;
if(mode==='listening'){frames.push(pcm);elapsed+=.32;if(rms>.015){voiced+=.32;quiet=0;}else quiet+=.32;
if(elapsed>=28||(!manual&&voiced>.3&&quiet>=1.28))finish();else if(!manual&&elapsed>=7&&voiced===0){frames=[];state('ready','No speech captured. Try again or hold to talk.');newQueue(g);}return;}
pre.push(pcm);if(pre.length>4)pre.shift();queue?.push(pcm);}
$('start').onclick=start;$('mute').onclick=()=>stop();
$('ptt').onpointerdown=e=>{e.preventDefault();$('ptt').setPointerCapture(e.pointerId);arm(true);};$('ptt').onpointerup=()=>{if(manual)finish();};$('ptt').onpointercancel=()=>{if(manual)stop('Push-to-talk cancelled.');};
$('ptt').onkeydown=e=>{if(e.code==='Space'){e.preventDefault();if(!e.repeat)arm(true);}};$('ptt').onkeyup=e=>{if(e.code==='Space'){e.preventDefault();if(manual)finish();}};$('ptt').onblur=()=>{if(manual)finish();};
$('miss').onclick=()=>{misses++;counts();};$('false').onclick=()=>{falseTriggers++;counts();};$('reset').onclick=()=>{detections=misses=falseTriggers=0;counts();};$('clear').onclick=()=>{$('transcript').textContent='Transcript cleared.';};
$('sample').onchange=()=>{stop();$('playback').pause();if(sampleUrl)URL.revokeObjectURL(sampleUrl);const file=$('sample').files[0];if(file){sampleUrl=URL.createObjectURL(file);$('playback').src=sampleUrl;}};
$('playback').onplay=()=>{stop('Local audio is playing.');state('speaking','Microphone disabled during playback.');};$('playback').onpause=$('playback').onended=()=>{if(mode==='speaking')state('muted','Playback paused. Enable the microphone to resume.');};
window.addEventListener('pagehide',()=>stop());window.addEventListener('blur',()=>{if(manual)stop('Push-to-talk cancelled when the window lost focus.');});
document.addEventListener('visibilitychange',()=>{if(document.hidden&&active)stop('Lab paused when hidden. Enable the microphone when you return.');});
navigator.mediaDevices?.addEventListener('devicechange',async()=>{await devices().catch(()=>{});if(active)stop('Audio devices changed. Check the selected microphone and enable again.');});
setInterval(()=>{if(active&&performance.now()-lastFrame>4000)stop('Microphone audio stopped or the computer slept. Enable the microphone to reconnect.');},1000);
fetch('/api/voice-lab/status').then(r=>{if(!r.ok)throw new Error('Status unavailable');return r.json();}).then(r=>{$('engine').textContent=r.installed?r.engine+' · installed locally. First transcription also loads the model.':'Local model is not installed yet.';}).catch(()=>{$('engine').textContent='Could not check local engine.';});
})();
