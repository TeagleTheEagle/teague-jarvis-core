/* Shared audio-reactive hologram. No synthetic speech samples. */
(function(root){
'use strict';
const clamp=v=>Math.max(0,Math.min(1,Number(v)||0));
class VoiceCore {
 constructor(canvas){this.canvas=canvas;this.ctx=canvas.getContext('2d');this.energy=0;this.angle=0;this.speed=.035;this.last=0;this.wave=new Float32Array(128);this.trail=new Float32Array(128);this.pulses=[];this.lastPulse=0;this.weights={};this.previousEnergy=0;}
 draw(ms,signal={},reduced=false){
 const dt=Math.min(.05,Math.max(.001,(ms-this.last)/1000||.016));this.last=ms;
 const mix=(a,b,t)=>a+(b-a)*(1-Math.exp(-dt/t));
 const mode=signal.mode||'standby',speaking=mode==='speaking',listening=mode==='listening';
 const target=speaking?clamp(signal.volume):0;
 this.energy=mix(this.energy,target,target>this.energy?.035:mode==='interrupted'?.065:.18);
 for(const key of ['speaking','listening','thinking','processing','error','interrupted','understood'])this.weights[key]=mix(this.weights[key]||0,mode===key?1:0,.18);
 const w=this.weights,e=reduced?0:this.energy;
 this.speed=mix(this.speed,.035+w.thinking*.30+w.processing*.19+e*.13,.25);
 if(!reduced)this.angle+=dt*this.speed;
 const a=this.angle,c=this.ctx; c.clearRect(0,0,760,660);c.save();c.translate(380,330);
 const ring=(r,color,width=1)=>{c.beginPath();c.arc(0,0,r,0,Math.PI*2);c.strokeStyle=color;c.lineWidth=width;c.stroke();};
 const base=[93,213,248],palette={thinking:[154,119,245],processing:[220,173,96],interrupted:[220,173,96],understood:[51,229,177],error:[235,83,94],listening:[65,186,255]};
 const rgb=base.slice();for(const [key,color] of Object.entries(palette))for(let i=0;i<3;i++)rgb[i]+=(color[i]-base[i])*(w[key]||0);const cyan=rgb.map(v=>Math.round(Math.max(0,Math.min(255,v)))).join(',');
 const breath=reduced?0:(.5-.5*Math.cos(ms/1000*Math.PI*2/(w.processing>.5?2.4:3.6)))*(.004+w.thinking*.021+w.processing*.015);
 this.px=mix(this.px||0,reduced?0:Math.max(-1,Math.min(1,signal.pointerX||0))*4,.25);this.py=mix(this.py||0,reduced?0:Math.max(-1,Math.min(1,signal.pointerY||0))*4,.25);
 c.translate(this.px,this.py);
 const glow=c.createRadialGradient(0,0,10,0,0,280);glow.addColorStop(0,`rgba(${cyan},${.12+e*.17+w.listening*.06})`);glow.addColorStop(1,'rgba(0,20,36,0)');c.fillStyle=glow;c.fillRect(-300,-300,600,600);
 const expansion=1+(reduced?0:w.listening*.018+breath*.4);c.save();c.scale(expansion,expansion);
 [267,257,243,225,207,194].forEach((r,i)=>ring(r,`rgba(${cyan},${i%2?.20:.36})`));
 for(let i=0;i<120;i++){const t=i*Math.PI/60;c.beginPath();c.moveTo(Math.cos(t)*(i%5?261:253),Math.sin(t)*(i%5?261:253));c.lineTo(Math.cos(t)*269,Math.sin(t)*269);c.strokeStyle=i%5?'#24495e':'#5c9bb6';c.lineWidth=1;c.stroke();}
 for(let j=0;j<3;j++){c.save();c.rotate(a*(j%2?-1.4:1)+j*.8);for(let i=0;i<8;i++){c.beginPath();c.arc(0,0,247-j*22,i*Math.PI/4+.04,i*Math.PI/4+.24+(j===1?e*clamp(signal.low)*.08:0));c.strokeStyle=`rgba(${cyan},${.25+(i%3===0?.38:0)+e*.12})`;c.lineWidth=j===1?5:2;c.stroke();}c.restore();}
 c.restore();
 // A wire sphere with meridians, latitude contours and deterministic surface nodes.
 const radius=158*(1+e*.035+(reduced?0:Math.sin(a*2)*.003+breath));
 const sphere=c.createRadialGradient(-32,-42,4,0,0,radius);sphere.addColorStop(0,'#12426588');sphere.addColorStop(.7,'#071c3299');sphere.addColorStop(1,`rgba(${cyan},${.20+e*.18})`);c.fillStyle=sphere;c.beginPath();c.arc(0,0,radius,0,Math.PI*2);c.fill();
 c.save();c.beginPath();c.arc(0,0,radius,0,Math.PI*2);c.clip();
 for(let i=-3;i<=3;i++){const y=i*radius/4,rx=Math.sqrt(radius*radius-y*y);c.beginPath();c.ellipse(0,y,rx,rx*.16,0,0,Math.PI*2);c.strokeStyle=`rgba(${cyan},.24)`;c.lineWidth=1;c.stroke();}
 for(let i=0;i<8;i++){c.beginPath();c.ellipse(0,0,Math.max(2,Math.abs(Math.cos(a*.4+i*Math.PI/8))*radius),radius,0,0,Math.PI*2);c.strokeStyle=`rgba(${cyan},.22)`;c.stroke();}
 for(let i=0;i<100;i++){const y=1-2*(i+.5)/100,t=i*2.399963+a*.3,r=Math.sqrt(1-y*y),z=Math.cos(t)*r;if(z<0)continue;c.fillStyle=`rgba(${cyan},${.15+z*.45})`;c.fillRect(Math.sin(t)*r*radius,y*radius,1.3,1.3);}
 c.restore();ring(radius,`rgba(${cyan},${.6+e*.25})`,1.6);ring(radius+4,`rgba(${cyan},.35)`);
 // Internal reasoning orbits and processing streams are state illustrations, not telemetry.
 c.save();c.globalAlpha=Math.min(1,w.thinking+w.processing);c.translate(this.px*.4,this.py*.4);
 for(let j=0;j<3;j++){c.save();c.rotate(a*(j%2?-1:1)+j);c.beginPath();c.ellipse(0,0,145,35+j*12,0,0,Math.PI*2);c.strokeStyle=`rgba(${cyan},.40)`;c.lineWidth=1;c.stroke();c.restore();}
 if(w.processing>.01){for(let j=0;j<5;j++){const x=-110+j*55,y=reduced?0:((ms/8+j*49)%240)-120;c.beginPath();c.moveTo(x,y);c.lineTo(x,y+14);c.strokeStyle=`rgba(${cyan},${w.processing*.55})`;c.stroke();}}
 c.restore();
 for(let j=0;j<4;j++){c.save();c.rotate(j*Math.PI/2);c.beginPath();c.moveTo(275,0);c.lineTo(296,0);c.strokeStyle=`rgba(${cyan},.42)`;c.stroke();c.restore();}

 // Wave points are the actual time-domain samples, smoothed across time and neighbors.
 const samples=signal.samples||[];
 for(let i=0;i<128;i++){const s=speaking&&samples.length?samples[Math.floor(i*(samples.length-1)/127)]:0;this.wave[i]=mix(this.wave[i],Number.isFinite(s)?s:0,.045);this.trail[i]=mix(this.trail[i],this.wave[i],.11);}
 if(w.speaking>.008||this.energy>.002){
 c.save();c.globalAlpha=w.speaking;c.shadowColor='#62dfff';c.shadowBlur=reduced?0:10+e*8;
 for(let pass=0;pass<3;pass++){c.beginPath();for(let i=0;i<128;i++){const taper=Math.pow(Math.sin(i*Math.PI/127),.65),arr=pass===0?this.trail:this.wave;const smooth=(arr[Math.max(0,i-1)]+arr[i]*2+arr[Math.min(127,i+1)])/4;const x=(i/127-.5)*370,y=reduced?0:smooth*180*taper*(pass===2?.65:1);i?c.lineTo(x,y):c.moveTo(x,y);}c.strokeStyle=pass===0?'#39bdee55':pass===1?'#c6faff':'#59d7ff88';c.lineWidth=pass===1?1.8:3;c.stroke();}c.restore();}
 // Pulses require actual energy rises, never random timers during speech.
 if(!reduced&&ms-this.lastPulse>180&&((target-this.previousEnergy>.09)||(listening&&clamp(signal.input)>.035))){this.pulses.push({r:listening?260:radius, inward:listening,alpha:.45});this.lastPulse=ms;}
 this.previousEnergy=mix(this.previousEnergy,target,.10);
 if(reduced)this.pulses=[];
 this.pulses=this.pulses.filter(p=>{p.r+=dt*(p.inward?-100:100);p.alpha-=dt*.65;if(p.alpha<=0)return false;ring(p.r,`rgba(${cyan},${p.alpha})`);return true;});
 if(!reduced&&(w.thinking+w.processing)>.01){c.save();c.globalAlpha=(w.thinking+w.processing)*.35;c.rotate(a*3);c.beginPath();c.arc(0,0,184,-.25,.25);c.strokeStyle='#a3edff';c.lineWidth=2;c.stroke();c.restore();}
 for(let i=0;i<16;i++){const t=i*Math.PI/8+a*(i%2?1:-1),r=181+(i%3)*12+e*(8+clamp(signal.high)*10);c.beginPath();c.arc(Math.cos(t)*r,Math.sin(t)*r,i%4?1.2:2,0,Math.PI*2);c.fillStyle=`rgba(${cyan},${.25+w.thinking*.35+e*.3})`;c.fill();}
 c.restore();
 }
}
root.JarvisVoiceCore=VoiceCore;
})(globalThis);
