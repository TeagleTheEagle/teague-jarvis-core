from pathlib import Path
import sys,json
r=Path(__file__).resolve().parents[1];sys.path.insert(0,str(r/'review/inspection-deps'))
from playwright.sync_api import sync_playwright
out=r/'review/voice-core';out.mkdir(exist_ok=True)
with sync_playwright() as p:
 browser=p.chromium.launch(channel='chrome',headless=True,args=['--autoplay-policy=no-user-gesture-required']);page=browser.new_page(viewport={'width':900,'height':760})
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.set_content('<body style="background:#050d18;margin:0;display:grid;place-items:center"><canvas id="core" width="760" height="660"></canvas>')
 page.add_script_tag(path=str(r/'static/voice-core.js'))
 result=page.evaluate('''async()=>{
 const renderer=new JarvisVoiceCore(document.getElementById('core'));
 const ac=new AudioContext(),osc=ac.createOscillator(),gain=ac.createGain(),an=ac.createAnalyser(),silent=ac.createGain();
 an.fftSize=2048;osc.frequency.value=220;gain.gain.value=.12;silent.gain.value=0;
 osc.connect(gain);gain.connect(an);an.connect(silent);silent.connect(ac.destination);await ac.resume();osc.start();
 const b=new Uint8Array(an.fftSize),f=new Uint8Array(an.frequencyBinCount);let now=0;
 const sample=()=>{an.getByteTimeDomainData(b);an.getByteFrequencyData(f);let sum=0;for(const v of b)sum+=((v-128)/128)**2;return {mode:'speaking',volume:Math.min(1,Math.sqrt(sum/b.length)*5),samples:Array.from(b,v=>(v-128)/128),low:.5,mid:.4,high:.1};};
 await new Promise(r=>setTimeout(r,120));let signal=sample();window.capturedSignal=signal;for(let i=0;i<50;i++)renderer.draw(now+=16,signal);
 const loud=renderer.energy,peak=Math.max(...renderer.wave.map(Math.abs));
 if(!(loud>.2&&peak>.05))throw Error('Actual audio did not drive core');
 gain.gain.value=.025;await new Promise(r=>setTimeout(r,120));signal=sample();for(let i=0;i<60;i++)renderer.draw(now+=16,signal);const quiet=renderer.energy;if(!(quiet<loud*.5))throw Error('Quiet audio response');
 gain.gain.value=0;await new Promise(r=>setTimeout(r,120));signal=sample();renderer.draw(now+=16,signal);const settling=renderer.energy;if(!(settling>0))throw Error('Abrupt pause');for(let i=0;i<120;i++)renderer.draw(now+=16,signal);if(renderer.energy>.01)throw Error('Silent audio not settled');
 for(const mode of ['standby','listening','thinking','processing','speaking','interrupted','error'])renderer.draw(now+=200,{mode,input:.1});
 const angle=renderer.angle;renderer.draw(now+=200,{mode:'thinking'},true);if(angle!==renderer.angle)throw Error('Reduced motion rotates');
 osc.stop();await ac.close();window.testRenderer=renderer;window.testNow=now;
 return {loud,quiet,peak,settling,silence:renderer.energy,audio:'Real Web Audio oscillator; muted output; no provider calls',errors:[]};
}''')
 for mode in ['standby','listening','thinking','speaking','interrupted','processing','error']:
  page.evaluate('''mode=>{for(let i=0;i<60;i++)testRenderer.draw(testNow+=16,{mode,volume:mode==='speaking'?.55:0,samples:mode==='speaking'?capturedSignal.samples:[],input:mode==='listening'?.08:0});}''',mode)
  page.screenshot(path=str(out/(mode+'.png')))
 assert errors==[],errors
 (out/'results.json').write_text(json.dumps(result,indent=2));browser.close();print(json.dumps(result))
