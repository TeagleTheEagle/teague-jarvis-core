// Exact local controls bypass model latency and keep permission handling in the
// existing buttons/bridges. Questions and quoted instructions are not commands.
function assistantControlIntent(text){
 const s=String(text).toLowerCase().replace(/[,.!?]/g,'').replace(/\s+/g,' ').trim().replace(/^(?:hey )?jarvis /,'').replace(/ jarvis$/,'').replace(/^(?:please |can you |could you )/,'');
 if(/^(?:activate|enable|show|open|float)(?: a| the| your| my)? (?:hologram|companion|floating jarvis)$/.test(s))return 'show_hologram';
 if(/^(?:hide|close)(?: the| your| my)? (?:hologram|companion|floating jarvis)$/.test(s))return 'hide_hologram';
 if(/^(?:hologram status|is (?:the |your )?hologram (?:open|visible))$/.test(s))return 'hologram_status';
 if(/^(?:mute(?: (?:the |your |my )?(?:mic|microphone))?|turn (?:the |your |my )?(?:mic|microphone) off)$/.test(s))return 'mute';
 if(/^(?:unmute(?: (?:the |your |my )?(?:mic|microphone))?|enable (?:the |your |my )?(?:mic|microphone)|turn (?:the |your |my )?(?:mic|microphone) on)$/.test(s))return 'unmute';
 if(/^(?:(?:stop )*stop(?: speaking| talking)?|be quiet|silence)$/.test(s))return 'stop_speaking';
 if(/^(?:microphone status|mic status|are you listening)$/.test(s))return 'microphone_status';
 if(/^(?:screen sharing status|sharing status|are you sharing my screen)$/.test(s))return 'screen_status';
 return null;
}
function controlSummary(action,result){
 if(result.status==='failed'||result.status==='unavailable'||result.status==='permission_required')return result.error||'The control could not be confirmed.';
 if(result.status==='requested')return 'Screen analysis requested. Completion will be reported separately.';
 if(action.includes('hologram'))return result.active?'The floating hologram is visible.':'The floating hologram is hidden.';
 if(action==='stop_speaking')return 'Speech stopped.';
 if(['mute','unmute','microphone_status'].includes(action))return result.active?'The microphone is receiving audio.':'The microphone is off.';
 return result.active?'Screen sharing is active. AI analysis uses sampled frames.':'Screen sharing is off.';
}
async function performAssistantControl(action){
 try{
  const microphoneActive=()=>!!state.mic&&!!voice.stream?.getAudioTracks().some(t=>t.readyState==='live'&&t.enabled);
  if(action==='mute'){disableMic();return {status:'completed',active:microphoneActive()};}
  if(action==='unmute'){if(!microphoneActive())await toggleMic();return {status:microphoneActive()?'completed':'failed',active:microphoneActive(),error:microphoneActive()?'':'Microphone did not start. Check device permissions.'};}
  if(action==='microphone_status')return {status:'completed',active:microphoneActive()};
  if(action==='stop_speaking'){state.interrupted=true;stopSpeech();return {status:'completed',active:false};}
  if(action==='show_hologram'){
   if(window.jarvisDesktop?.showCompanion){const r=await window.jarvisDesktop.showCompanion();return {status:r.shown?'completed':'failed',active:!!r.shown,error:r.error||''};}
   await document.getElementById('screenFloat').onclick();
   return companionWindow&&!companionWindow.closed?{status:'completed',active:true}:{status:'permission_required',active:false,error:'Use Float hologram to allow a floating browser window.'};
  }
  if(action==='hide_hologram'){
   if(window.jarvisDesktop?.hideCompanion){const r=await window.jarvisDesktop.hideCompanion();return {status:r.visible?'failed':'completed',active:!!r.visible};}
   companionWindow?.close();return {status:'completed',active:!!companionWindow&&!companionWindow.closed};
  }
  if(action==='hologram_status'){
   const r=window.jarvisDesktop?.companionStatus?await window.jarvisDesktop.companionStatus():{visible:!!companionWindow&&!companionWindow.closed};
   return {status:'completed',active:!!r.visible};
  }
  const screenActive=()=>!!screenStream?.getVideoTracks().some(t=>t.readyState==='live');
  if(action==='screen_status')return {status:'completed',active:screenActive(),sampling:screenActive()&&document.getElementById('screenAuto').checked};
  if(action==='stop_sharing'){stopScreenVision();return {status:'completed',active:screenActive()};}
  if(action==='start_sharing'){
   if(window.jarvisDesktop)await startDesktopLive({fromAssistant:true});
   else{openScreenVision();return {status:'permission_required',active:screenActive(),error:'Click Start screenshare and approve a screen in the browser picker.'};}
   return {status:screenActive()?'completed':'failed',active:screenActive(),sampling:screenActive()&&document.getElementById('screenAuto').checked};
  }
  if(action==='analyse_screen'){
   if(state.busy){
    const epoch=screenEpoch,deadline=Date.now()+45000;
    const launch=()=>{if(state.interrupted||screenEpoch!==epoch)return;if(Date.now()>deadline){toast('Queued screen analysis expired before it could start.',true);return;}if(state.busy){setTimeout(launch,200);return;}void send('analyse my screen');};
    setTimeout(launch,200);return {status:'requested',image_submitted:false};
   }
   await send('analyse my screen');return {status:'requested'};
  }
  return {status:'unavailable',error:'Unknown interface control.'};
 }catch{return {status:'failed',error:'The requested control failed; no success confirmed.'};}
}

// Archive/tracker access uses existing authenticated, narrow tools. Reading a
// report never submits images or executes instructions in the archived text.
(() => {
 if(window.JARVIS_INSPECTION)return;
 const dialog=document.createElement('dialog');dialog.setAttribute('aria-label','Inspection archive');
 dialog.style.cssText='width:min(1000px,94vw);max-height:85vh;overflow:auto';
 const title=document.createElement('h2');title.textContent='Inspection archive & improvements';
 const body=document.createElement('div'),bar=document.createElement('div');bar.style.cssText='display:flex;gap:12px;flex-wrap:wrap';
 const status=document.createElement('p');status.setAttribute('role','status');
 const render=async(action)=>{
  body.replaceChildren();status.textContent='Loading saved evidence…';
  try{
   const data=action==='findings'?await api('/api/tool',{name:'inspection_findings',args:{status:'all'}}):await api('/api/tool',{name:'inspection_reports',args:{action}});
   const text=document.createElement('pre');text.style.cssText='white-space:pre-wrap;overflow-wrap:anywhere';text.textContent=data.report||JSON.stringify(data,null,2);body.append(text);
   if(action==='findings')for(const f of data.findings){
    const row=document.createElement('section'),label=document.createElement('p');label.textContent=f.panel+' · '+f.description+' · '+f.status;row.append(label);
    for(const next of ['open','verified','deferred','cancelled']){
     const button=document.createElement('button');button.textContent=next==='verified'?'Record my successful test':'Mark '+next;
     button.onclick=async()=>{const note=prompt(next==='verified'?'What did you test, and what happened? This records your confirmation.':'Why change this finding to '+next+'?');if(!note)return;button.disabled=true;try{await api('/api/inspection-finding',{finding:f.id,status:next,note});await render('findings');}catch(e){status.textContent=e.message;button.disabled=false;}};row.append(button);
    }body.append(row);
   }
   if(action==='list')for(const report of data.inspections){const b=document.createElement('button');b.textContent='Open '+report.created;b.onclick=async()=>{try{const r=await api('/api/tool',{name:'inspection_reports',args:{action:'read',inspection_id:report.id}});text.textContent=r.report;}catch(e){status.textContent=e.message;}};body.append(b);}
   status.textContent='Saved evidence loaded. Original inspection reports are preserved.';
  }catch(e){status.textContent=e.message;}
 };
 for(const [label,action] of [['Latest inspection','latest'],['All inspections','list'],['Compare last two','compare'],['Improvement tracker','findings']]){const b=document.createElement('button');b.textContent=label;b.onclick=()=>render(action);bar.append(b);}
 const close=document.createElement('button');close.textContent='Close';close.onclick=()=>dialog.close();bar.append(close);
 dialog.append(title,bar,status,body);document.body.append(dialog);
 const open=document.createElement('button');open.textContent='INSPECTION ARCHIVE';open.onclick=()=>{dialog.showModal();void render('latest');};document.querySelector('.conversation-actions').append(open);
})();


// Read-only timer queries avoid the language model and retain the configured voice.
function timerStatusIntent(text){
 const s=String(text).toLowerCase().replace(/[,.!?]/g,'').replace(/\s+/g,' ').trim().replace(/^(?:hey )?jarvis /,'').replace(/ jarvis$/,'').replace(/^(?:please |can you |could you )/,'');
 return /^(?:(?:how much|what) time (?:is left|remains|is remaining)(?: on (?:my|the) timer)?|how long (?:is left|remains)(?: on (?:my|the) timer)?|(?:list|show|name)(?: me)?(?: my| the)? active timers|timer status)$/.test(s);
}
function timerStatusText(timers,now=Date.now()){
 if(!timers.length)return 'No active timers were found, Sir.';
 const descriptions=timers.map(t=>{
  const seconds=Math.max(0,Math.ceil(t.due-now/1000)),minutes=Math.floor(seconds/60),rest=seconds%60;
  const duration=minutes?minutes+' minute'+(minutes===1?'':'s')+(rest?' and '+rest+' seconds':''):seconds+' seconds';
  return (timers.length>1?(t.title||t.body||'Timer')+': ':'')+(seconds?duration+' remaining':'the countdown has reached zero');
 });
 return descriptions.join('; ')+', Sir.';
}
async function answerTimerStatus(text){
 message('user',text);
 const output=message('assistant','Checking active timers…'),generation=state.voiceGeneration;
 try{
  const data=await api('/api/tool',{name:'manage_timer',args:{action:'list'}});
  if(!Array.isArray(data.timers))throw new Error('Invalid timer response');
  const fresh=()=>timerStatusText(data.timers);
  const reply=data.timers.length?'When checked: '+fresh():fresh();
  output.p.textContent=reply;
  // Stop/new speech during the read must not be undone by a late reply.
  if(generation!==state.voiceGeneration)return;
  await speak(reply);
 }catch(e){output.p.textContent='I could not check the active timers. Please try again, Sir.';}
}
