from pathlib import Path
r=Path('outputs/jarvis');p=r/'static/app.js';s=p.read_text(encoding='utf-8');start=s.index('// Instrument-style activity visualization');end=s.index("setInterval(()=>{if(state.data)",start)
s=s[:start]+'''const canvas=$('#core'),ctx=canvas.getContext('2d');
const coreRenderer=new JarvisVoiceCore(canvas),coreMotion=matchMedia('(prefers-reduced-motion: reduce)');
let coreAnimationFrame=0,coreAnimationWindow=window,lastCoreFrame=0;
function readCoreSignal(){
 let volume=0,samples=[],low=0,mid=0,high=0;
 if(speechAnalyser&&state.audio&&!state.audio.paused){
  speechAnalyser.getByteTimeDomainData(speechSamples);speechAnalyser.getByteFrequencyData(speechSpectrum);
  let sum=0;for(const v of speechSamples)sum+=((v-128)/128)**2;
  volume=Math.min(1,Math.sqrt(sum/speechSamples.length)*5);
  samples=Array.from({length:64},(_,i)=>(speechSamples[Math.floor(i*(speechSamples.length-1)/63)]-128)/128);
  const band=(from,to)=>{const hz=speechContext.sampleRate/speechAnalyser.fftSize;let sum=0,n=0;for(let i=Math.ceil(from/hz);i<Math.min(speechSpectrum.length,to/hz);i++){sum+=speechSpectrum[i]/255;n++;}return n?sum/n:0;};
  low=band(60,300);mid=band(300,3000);high=band(3000,10000);
 }
 const mode=performance.now()<coreInterruptedUntil?'interrupted':performance.now()<coreErrorUntil?'error':state.mode==='thinking'&&state.run?'processing':state.mode;
 return {mode,volume,samples,low,mid,high,input:Date.now()-voiceDiagnostic.frameAt<250?(voiceDiagnostic.level||0):0,reduced:coreMotion.matches||document.documentElement.dataset.motion==='reduced'};
}
function scheduleCore(){coreAnimationWindow.cancelAnimationFrame(coreAnimationFrame);coreAnimationWindow=canvas.ownerDocument.defaultView;coreAnimationFrame=coreAnimationWindow.requestAnimationFrame(drawCore);}
function drawCore(ms){
 const doc=canvas.ownerDocument,rect=canvas.getBoundingClientRect();
 if(!doc.hidden&&rect.width&&rect.height&&rect.bottom>0&&rect.top<doc.defaultView.innerHeight){
  const signal=readCoreSignal();if(ms-lastCoreFrame>=(signal.reduced?100:15)){coreRenderer.draw(ms,signal,signal.reduced);lastCoreFrame=ms;}
 }
 scheduleCore();
}
scheduleCore();
'''+s[end:]
s=s.replace('let speechContext,speechAnalyser,speechSamples,speechSource;','let speechContext,speechAnalyser,speechSamples,speechSpectrum,speechSource;\nlet coreInterruptedUntil=0,coreErrorUntil=0;').replace('speechAnalyser.fftSize=256;','speechAnalyser.fftSize=2048;speechAnalyser.smoothingTimeConstant=.65;').replace('speechSamples=new Uint8Array(speechAnalyser.fftSize);','speechSamples=new Uint8Array(speechAnalyser.fftSize);speechSpectrum=new Uint8Array(speechAnalyser.frequencyBinCount);').replace('function stopSpeech(){','function stopSpeech(){if(state.audio&&!state.audio.paused)coreInterruptedUntil=performance.now()+180;')
start=s.index('  let volume=0,samples=[];',s.index('window.jarvisDesktop.screenPreference'));end=s.index('status:document.getElementById',start)
s=s[:start]+"  const signal=readCoreSignal();\n  window.jarvisDesktop.updateCompanion({...signal,"+s[end:];p.write_text(s,encoding='utf-8')
for name,old,new in [
('static/index.html','<script src="/app.js" defer>','<script src="/voice-core.js" defer></script><script src="/app.js" defer>'),
('server.py',"mapping = {'/teague.js'","mapping = {'/voice-core.js':'voice-core.js','/teague.js'"),
('inspection_runtime.py',"'teague.js','teague.css'","'voice-core.js','teague.js','teague.css'"),
('desktop/companion.html','<script src="companion.js">','<script src="../static/voice-core.js"></script><script src="companion.js">')]:
 p=r/name;s=p.read_text(encoding='utf-8');assert old in s;s=s.replace(old,new);p.write_text(s,encoding='utf-8')
p=r/'desktop/main.cjs';s=p.read_text(encoding='utf-8').replace("['standby','listening','thinking','speaking'].includes(data.mode)","['standby','listening','thinking','speaking','processing','interrupted','error'].includes(data.mode)");s=s.replace('lastCompanionState={mode:',"lastCompanionState={low:Math.max(0,Math.min(1,Number(data.low)||0)),mid:Math.max(0,Math.min(1,Number(data.mid)||0)),high:Math.max(0,Math.min(1,Number(data.high)||0)),input:Math.max(0,Math.min(1,Number(data.input)||0)),reduced:!!data.reduced,mode:");p.write_text(s,encoding='utf-8')
