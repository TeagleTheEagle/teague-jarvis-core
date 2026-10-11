from pathlib import Path
r=Path('outputs/jarvis');p=r/'static/voice-core.js';s=p.read_text(encoding='utf-8')
s=s.replace("'error','interrupted'","'error','interrupted','understood'")
s=s.replace("const cyan=w.error>.1?'225,157,87':'93,213,248';",'''const base=[93,213,248],palette={thinking:[154,119,245],processing:[220,173,96],interrupted:[220,173,96],understood:[51,229,177],error:[235,83,94],listening:[65,186,255]};
 const rgb=base.slice();for(const [key,color] of Object.entries(palette))for(let i=0;i<3;i++)rgb[i]+=(color[i]-base[i])*(w[key]||0);const cyan=rgb.map(v=>Math.round(Math.max(0,Math.min(255,v)))).join(',');
 const breath=reduced?0:(.5-.5*Math.cos(ms/1000*Math.PI*2/(w.processing>.5?2.4:3.6)))*(.004+w.thinking*.021+w.processing*.015);
 this.px=mix(this.px||0,reduced?0:Math.max(-1,Math.min(1,signal.pointerX||0))*4,.25);this.py=mix(this.py||0,reduced?0:Math.max(-1,Math.min(1,signal.pointerY||0))*4,.25);
 c.translate(this.px,this.py);''')
s=s.replace('w.listening*.018','w.listening*.018+breath*.4').replace('Math.sin(a*2)*.003','Math.sin(a*2)*.003+breath')
s=s.replace("c.strokeStyle='#4eacd23d'","c.strokeStyle=`rgba(${cyan},.24)`").replace("c.strokeStyle='#73cdea30'","c.strokeStyle=`rgba(${cyan},.22)`")
s=s.replace("ring(radius+4,'#3c8fab55');",'''ring(radius+4,`rgba(${cyan},.35)`);
 // Internal reasoning orbits and processing streams are state illustrations, not telemetry.
 c.save();c.globalAlpha=Math.min(1,w.thinking+w.processing);c.translate(this.px*.4,this.py*.4);
 for(let j=0;j<3;j++){c.save();c.rotate(a*(j%2?-1:1)+j);c.beginPath();c.ellipse(0,0,145,35+j*12,0,0,Math.PI*2);c.strokeStyle=`rgba(${cyan},.40)`;c.lineWidth=1;c.stroke();c.restore();}
 if(w.processing>.01){for(let j=0;j<5;j++){const x=-110+j*55,y=reduced?0:((ms/8+j*49)%240)-120;c.beginPath();c.moveTo(x,y);c.lineTo(x,y+14);c.strokeStyle=`rgba(${cyan},${w.processing*.55})`;c.stroke();}}
 c.restore();
 for(let j=0;j<4;j++){c.save();c.rotate(j*Math.PI/2);c.beginPath();c.moveTo(275,0);c.lineTo(296,0);c.strokeStyle=`rgba(${cyan},.42)`;c.stroke();c.restore();}
''')
p.write_text(s,encoding='utf-8')
p=r/'static/app.js';s=p.read_text(encoding='utf-8').replace('let coreInterruptedUntil=0,coreErrorUntil=0;','let coreInterruptedUntil=0,coreErrorUntil=0,coreAcknowledgedUntil=0,coreWorking=0;\nlet corePointerX=0,corePointerY=0;\ndocument.addEventListener(\'pointermove\',e=>{corePointerX=e.clientX/innerWidth*2-1;corePointerY=e.clientY/innerHeight*2-1;},{passive:true});')
s=s.replace("if(!text)return;\n      if(/", "if(!text)return;coreAcknowledgedUntil=performance.now()+450;\n      if(/")
s=s.replace("if(event.event==='tool.started'){", "if(event.event==='tool.started'){coreWorking++;").replace("if(event.event==='tool.completed'){", "if(event.event==='tool.completed'){coreWorking=Math.max(0,coreWorking-1);").replace("if(event.event==='tool.failed'){", "if(event.event==='tool.failed'){coreWorking=Math.max(0,coreWorking-1);coreErrorUntil=performance.now()+700;")
s=s.replace("finally{output.p.dataset.activity='';state.run=null;", "finally{coreWorking=0;output.p.dataset.activity='';state.run=null;")
s=s.replace("state.mode==='thinking'&&state.run?'processing':state.mode", "performance.now()<coreAcknowledgedUntil?'understood':coreWorking?'processing':state.mode")
s=s.replace('return {mode,volume,samples,low,mid,high,input:', 'return {mode,volume,samples,low,mid,high,pointerX:corePointerX,pointerY:corePointerY,input:')
p.write_text(s,encoding='utf-8')
p=r/'desktop/main.cjs';s=p.read_text(encoding='utf-8').replace("'interrupted','error'].includes", "'interrupted','error','understood'].includes");p.write_text(s,encoding='utf-8')
