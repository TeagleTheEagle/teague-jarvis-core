(()=>{
  const box=document.createElement('fieldset');box.style.cssText='padding:18px;margin:18px 0;border:1px solid #285164';
  const title=document.createElement('legend');title.textContent='VOICE PREVIEW';
  const select=document.createElement('select');select.setAttribute('aria-label','Voice profile');
  [['auto','Current automatic voice'],['qwen','Qwen — cloned JARVIS voice'],['fish','Fish — current voice'],['openai','OpenAI — Cedar']].forEach(([v,t])=>select.add(new Option(t,v)));
  const info=document.createElement('p');info.textContent='Preview uses provider credits. OpenAI Cedar is an AI-generated voice. Qwen needs your cloned voice ID (QWEN_TTS_VOICE) in the local key file.';
  const preview=document.createElement('button');preview.type='button';preview.textContent='PREVIEW VOICE';
  const save=document.createElement('button');save.type='button';save.textContent='USE THIS VOICE';save.style.marginLeft='8px';
  const audio=document.createElement('audio');audio.controls=true;audio.style.cssText='width:100%;margin-top:12px';let url;
  preview.onclick=async()=>{preview.disabled=true;stopSpeech();audio.pause();pauseRecognition();try{const response=await fetch('/api/speech',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({profile:select.value,text:'Good evening, Mr. Teague. Your project is ready for review. Shall we refine the design, or give your next brilliant idea a head start, Sir?'})});if(!response.ok)throw Error((await response.json()).error||'Voice preview failed.');if(url)URL.revokeObjectURL(url);url=URL.createObjectURL(await response.blob());audio.src=url;await audio.play();}catch(e){toast(e.message,true);resumeRecognition();}finally{preview.disabled=false;}};
  audio.onended=audio.onpause=()=>resumeRecognition();
  save.onclick=async()=>{try{await api('/api/settings',{voice_profile:select.value});await refresh();toast('Voice preference saved.');}catch(e){toast(e.message,true);}};
  box.append(title,select,info,preview,save,audio);document.querySelector('#settingsForm').append(box);
  api('/api/state').then(d=>select.value=d.settings.voice_profile||'auto').catch(()=>{});
})();
