'use strict';
const canvas=document.getElementById('orb'),renderer=new JarvisVoiceCore(canvas);
const motion=matchMedia('(prefers-reduced-motion: reduce)');
let state={mode:'standby'},lastUpdate=0,lastFrame=0;
window.companion.onState(data=>{state=data;lastUpdate=performance.now();document.getElementById('status').textContent=data.status;document.getElementById('screen').textContent=data.screen;document.getElementById('mic').textContent=data.mic?'MUTE MIC':'ENABLE MIC';});
for(const action of ['show','hide','capture','mic','stop','live','stop-screen'])document.getElementById(action).onclick=()=>window.companion.action(action);
window.animationMetrics={frames:0,first:0,last:0};
function draw(ms){
 requestAnimationFrame(draw);if(document.hidden)return;
 const reduced=motion.matches||state.reduced;if(ms-lastFrame<(reduced?100:15))return;lastFrame=ms;
 const stale=ms-lastUpdate>1500;
 renderer.draw(ms,stale?{mode:'standby'}:state,reduced);
 if(stale)document.getElementById('status').textContent='Waiting for JARVIS status…';
 const metrics=window.animationMetrics;metrics.frames++;if(!metrics.first)metrics.first=ms;metrics.last=ms;
}
requestAnimationFrame(draw);
