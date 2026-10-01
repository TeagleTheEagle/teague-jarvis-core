from pathlib import Path
r=Path('outputs/jarvis')
def edit(name,a,b):
 p=r/name;s=p.read_text(encoding='utf-8');assert a in s,(name,a);p.write_text(s.replace(a,b),encoding='utf-8')
edit('static/index.html','<script src="/voice-core.js"','<script src="/latency.js" defer></script><script src="/voice-core.js"')
edit('server.py',"mapping = {'/voice-core.js'","mapping = {'/latency.js':'latency.js','/voice-core.js'")
edit('inspection_runtime.py',"'voice-core.js','teague.js'","'latency.js','voice-core.js','teague.js'")
edit('static/voice.js','this.cb.status(\'TRANSCRIBING LOCALLY…\');',"this.cb.timing?.('speech_ended',this.lastVoicedAt);this.cb.status('TRANSCRIBING LOCALLY…');")
edit('static/voice.js','if(rms>.015){this.voiced+=.32;',"if(rms>.015){if(!this.voiced)this.cb.timing?.('speech_started',performance.now());this.lastVoicedAt=performance.now();this.voiced+=.32;")
# Conservative adjustable endpoint; manual push-to-talk remains release driven.
edit('static/voice.js','this.quiet>=2.56',"this.quiet>=(this.cb.endpointSeconds?.()||1.28)")
edit('static/app.js','  diagnostic: voiceDiagnostic,',"  diagnostic: voiceDiagnostic,\n  endpointSeconds:()=>Number(localStorage.getItem('jarvis.endpointSeconds'))||1.28,\n  timing:(name,at)=>{if(name==='speech_started')JarvisLatency.begin();JarvisLatency.mark(name,at);},")
edit('static/app.js',"const transcriptionStarted=performance.now();", "JarvisLatency.mark('transcription_started');const transcriptionStarted=performance.now();")
edit('static/app.js',"voiceDiagnostic('Transcription',(data.text", "JarvisLatency.mark('transcription_complete');JarvisLatency.value('local_stt_ms',data.latency_ms);voiceDiagnostic('Transcription',(data.text")
edit('static/app.js',"if(event.event==='response.timing'){voiceDiagnostic", "if(event.event==='response.timing'){if(event.data.stage==='provider first token'){JarvisLatency.mark('first_LLM_token');JarvisLatency.value('provider_first_token_ms',event.data.ms);}if(event.data.stage==='provider request')JarvisLatency.mark('LLM_request_started');voiceDiagnostic")
edit('server.py','provider_started = time.perf_counter()',"provider_started = time.perf_counter()\n                        run.emit('response.timing', {'stage':'provider request','ms':0})")
edit('static/app.js',"if(event.event==='assistant.completed'){completed", "if(event.event==='assistant.completed'){JarvisLatency.mark('LLM_complete');completed")
edit('static/app.js',"const synthesisStarted=performance.now();", "JarvisLatency.mark('TTS_started');const synthesisStarted=performance.now();")
edit('static/app.js',"const blob=await response.blob();if(generation", "const blob=await response.blob();JarvisLatency.mark('first_audio_ready');if(generation")
edit('static/app.js',"audio.onplaying=()=>{voiceDiagnostic", "audio.onplaying=()=>{JarvisLatency.mark('audio_playback_started');voiceDiagnostic")
p=r/'static/latency.js';s=p.read_text(encoding='utf-8');s+='''
document.addEventListener('DOMContentLoaded',()=>{setTimeout(()=>{const host=document.querySelector('[data-setting=Developer]')||document.getElementById('settingsForm');if(!host)return;const details=document.createElement('details'),summary=document.createElement('summary'),pre=document.createElement('pre'),button=document.createElement('button');summary.textContent='Voice latency — development timings';button.type='button';button.textContent='Refresh timing report';button.onclick=()=>{pre.textContent=JSON.stringify(JarvisLatency.report(),null,2);};pre.style.cssText='white-space:pre-wrap;overflow-wrap:anywhere';details.append(summary,button,pre);host.append(details);},0);});
''';p.write_text(s,encoding='utf-8')
