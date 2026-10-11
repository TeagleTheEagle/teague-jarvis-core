'use strict';
const canvas=document.getElementById('orb'),ctx=canvas.getContext('2d');
const motion=matchMedia('(prefers-reduced-motion: reduce)');
let state={mode:'standby'},targetVolume=0,voiceEnergy=0,speechSamples=[],lastUpdate=0,lastFrame=0;
window.companion.onState(data=>{state.mode=data.mode;targetVolume=data.volume;speechSamples=data.samples;lastUpdate=performance.now();document.getElementById('status').textContent=data.status;document.getElementById('screen').textContent=data.screen;document.getElementById('mic').textContent=data.mic?'MUTE MIC':'ENABLE MIC';});
for(const action of ['show','hide','capture','mic','stop','live','stop-screen'])document.getElementById(action).onclick=()=>window.companion.action(action);
window.animationMetrics={frames:0,first:0,last:0};
function draw(ms){
 requestAnimationFrame(draw);
 if(document.hidden)return;
 const reduceMotion=motion.matches;
 if(reduceMotion&&ms-lastFrame<100)return;
 const delta=Math.min(100,ms-lastFrame||16.67);lastFrame=ms;
 const stale=ms-lastUpdate>1500;const volume=stale?0:targetVolume;
 if(stale){state.mode='standby';document.getElementById('status').textContent='Waiting for JARVIS status…';speechSamples=[];}
 voiceEnergy+=(volume-voiceEnergy)*(1-Math.exp(-delta/(volume>voiceEnergy?45:100)));
  const t=reduceMotion?0:ms/1000;const active=state.mode!=='standby';const speed=state.mode==='thinking'?.32:.055;const cx=380,cy=330;
  ctx.clearRect(0,0,760,660);ctx.save();ctx.translate(cx,cy);
  const glow=ctx.createRadialGradient(0,0,20,0,0,285);glow.addColorStop(0,'#0d517c24');glow.addColorStop(.6,'#06314d30');glow.addColorStop(1,'#00132200');ctx.fillStyle=glow;ctx.fillRect(-380,-330,760,660);
  const circle=(r,color,width=1)=>{ctx.beginPath();ctx.arc(0,0,r,0,Math.PI*2);ctx.strokeStyle=color;ctx.lineWidth=width;ctx.stroke();};
  [260,246,230,202,190,160,146,125].forEach((r,i)=>circle(r,i%2?'#264d6388':'#2c687da0',i===2?2:1));
  for(let i=0;i<120;i++){const a=i*Math.PI*2/120;const r=i%5===0?251:257;ctx.beginPath();ctx.moveTo(Math.cos(a)*r,Math.sin(a)*r);ctx.lineTo(Math.cos(a)*264,Math.sin(a)*264);ctx.strokeStyle=i%5===0?'#5198b6':'#285066';ctx.lineWidth=i%5===0?2:1;ctx.stroke();}
  for(let j=0;j<3;j++){ctx.save();ctx.rotate(t*speed*(j%2?-1:1)+j*.73);const r=222-j*27;for(let k=0;k<4;k++){ctx.beginPath();ctx.arc(0,0,r,k*Math.PI/2+.09,k*Math.PI/2+.82);ctx.strokeStyle=j===0?'#399ec2':'#62d9ed';ctx.lineWidth=j===0?7:3;ctx.globalAlpha=j===0?.64:.45;ctx.stroke();}ctx.restore();}
  for(let i=0;i<40;i++){ctx.save();ctx.rotate(i*Math.PI/20-t*.023);ctx.fillStyle=i%4===0?'#66d9ed':'#123a52';ctx.fillRect(173,-2,i%4===0?10:5,4);ctx.restore();}
  ctx.save();ctx.rotate(-t*.11);for(let i=0;i<12;i++){ctx.beginPath();ctx.arc(0,0,113,i*Math.PI/6+.06,i*Math.PI/6+.3);ctx.strokeStyle=i%3===0?'#7ce6f2':'#285a76';ctx.lineWidth=12;ctx.stroke();}ctx.restore();
  // Fine concentric circuitry and orbiting nodes share the sphere's centre.
  ctx.save();ctx.rotate(t*.035);ctx.setLineDash([2,9]);circle(278,'#48869b66');circle(136,'#6ed6e866');ctx.setLineDash([]);
  for(let i=0;i<8;i++){const a=i*Math.PI/4;const x=Math.cos(a)*237,y=Math.sin(a)*237;ctx.beginPath();ctx.arc(x,y,3,0,Math.PI*2);ctx.fillStyle='#9aeeff';ctx.shadowColor='#57d7ff';ctx.shadowBlur=8;ctx.fill();}
  ctx.restore();
  ctx.save();ctx.rotate(-t*.065);for(let i=0;i<6;i++){const a=i*Math.PI/3;ctx.beginPath();ctx.arc(0,0,96,a,a+.34);ctx.strokeStyle='#85e7ff88';ctx.lineWidth=2;ctx.stroke();}ctx.restore();
  const pulse=active?.8+Math.sin(t*3)*.2:.7;const inner=ctx.createRadialGradient(0,0,2,0,0,85);inner.addColorStop(0,`rgba(177,249,255,${pulse})`);inner.addColorStop(.16,'#72dcf2');inner.addColorStop(.38,'#2595bb');inner.addColorStop(.63,'#0b456c');inner.addColorStop(1,'#061728');ctx.fillStyle=inner;ctx.beginPath();ctx.arc(0,0,83,0,Math.PI*2);ctx.fill();
  ctx.beginPath();ctx.arc(0,0,86,0,Math.PI*2);ctx.strokeStyle='#4fa1c7';ctx.lineWidth=1;ctx.stroke();
  // Audio-driven aperture: no fabricated speech motion when playback is silent.
  const energy=reduceMotion?0:voiceEnergy;
  ctx.save();ctx.translate(0,0);ctx.strokeStyle='#c2faff';ctx.lineWidth=3;ctx.shadowColor='#5de5ff';ctx.shadowBlur=12+energy*18;
  ctx.beginPath();ctx.ellipse(0,0,62+energy*14,4+energy*42,0,0,Math.PI*2);ctx.stroke();
  ctx.beginPath();for(let i=0;i<=100;i++){const x=(i/100-.5)*118;const sample=speechSamples.length&&volume?speechSamples[Math.floor(i/100*(speechSamples.length-1))]:0;const y=reduceMotion?0:sample*65; i?ctx.lineTo(x,y):ctx.moveTo(x,y);}ctx.lineWidth=1.5;ctx.stroke();ctx.restore();
  for(let i=0;i<4;i++){ctx.save();ctx.rotate(i*Math.PI/2);ctx.beginPath();ctx.moveTo(270,0);ctx.lineTo(294,0);ctx.strokeStyle='#447a9180';ctx.stroke();ctx.restore();}
  ctx.restore();
 const metrics=window.animationMetrics;metrics.frames++;if(!metrics.first)metrics.first=ms;metrics.last=ms;
}
requestAnimationFrame(draw);
