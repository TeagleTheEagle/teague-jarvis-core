/* TEST ONLY. No credentials, native access, browser speech or media acquisition. */
(()=>{'use strict';
 const bridge=window.jarvisStage4;if(!bridge)return;
 const q=s=>document.querySelector(s),all=s=>[...document.querySelectorAll(s)];
 const teague=!!q('#chatForm');
 const input=q('#messageInput,.ask textarea'),send=q('#sendButton,.actions .primary');
 const output=q('#messages,.execution .empty');
 const status=q('#connection,.status h2');status.setAttribute('data-stage4-status','');
 const write=text=>{output.textContent=text;};
 let request=null,busy=false,connected=false;
 // Historical dashboard numbers are not TEST telemetry. Keep actual entry-page
 // controls, but explicitly disable unsupported operations instead of mocking them.
 all('button,input,select,textarea').forEach(e=>{e.disabled=true;e.title='Unavailable in isolated Stage 4 TEST attachment';});
 for(const e of [input,send]){e.disabled=false;e.title='Authenticated STAGE4_TEST Core request';}
 if(teague){
  all('main').forEach(e=>{e.hidden=e.id!=='communicationsView';e.classList.toggle('hidden',e.hidden);});
  document.body.dataset.page='communications';
  all('.nav').forEach(e=>e.classList.toggle('active',e.dataset.view==='communications'));
  q('#communicationsView').classList.remove('hidden');
  q('.time-dashboard')?.remove();
  q('.brand-product small').textContent='STAGE4_TEST · CONNECTING';
  q('#footerStatus').textContent='TEST ONLY · no microphone or physical audio';
 }else{
  q('.node').textContent='STAGE4_TEST · CONNECTING';
  all('.status dd').forEach(e=>e.textContent='NOT VERIFIED');
  q('.cap-grid')?.closest('section')?.remove();
  all('.left .card:not(.status),.right .card,.performance,.pipeline,.verification').forEach(e=>e.remove());
  q('footer span:last-child').textContent='TEST ONLY · no production services';
 }
 const controls=document.createElement('div');controls.setAttribute('aria-label','Stage 4 client controls');
 for(const [label,operation] of [
  ['CANCEL MY REQUEST',()=>request?bridge.cancelRequest(request):Promise.resolve()],
  ['STOP MY CAPTURE',()=>bridge.stopCapture()],['STOP MY PLAYBACK',()=>bridge.stopPlayback()]
 ]){const button=document.createElement('button');button.type='button';button.textContent=label;
  button.onclick=()=>operation().then(()=>write(label+': requested; completion is not implied.')).catch(()=>write('Control unavailable or not owned by this session.'));controls.append(button);}
 output.after(controls);
 async function connection(){
  try{const result=await bridge.connection();connected=result.attached===true;
   status.textContent=connected?'STAGE4_TEST · AUTHENTICATED':'STAGE4_TEST · DISCONNECTED';
   document.body.dataset.stage4Connection=connected?'attached':'disconnected';
   const media=q('#voiceStatus,.status dd:nth-of-type(3)');if(media)media.textContent=result.media;
   if(!teague){q('.node').textContent=status.textContent;q('.status dd').textContent=status.textContent;}
   else q('.brand-product small').textContent=status.textContent;
   document.body.dataset.stage4Ready='true';
  }catch{connected=false;status.textContent='STAGE4_TEST · UNAVAILABLE';document.body.dataset.stage4Connection='disconnected';}
 }
 async function submit(event){
  event?.preventDefault();if(busy||!connected||!input.value.trim())return;
  busy=true;send.disabled=true;document.body.dataset.stage4Done='false';write('Sending through authenticated TEST Core…');
  try{
   const value=await bridge.request(input.value.trim());request=value.request_id;
   document.body.dataset.stage4Request=request;
   const deadline=performance.now()+30000;
   while(performance.now()<deadline){
    const result=await bridge.requestStatus(request);
    if(result.done){
     const answer=result.events.filter(e=>e.event==='assistant.completed').at(-1);
     write(answer?.data?.text||'TEST request finished. Inspect Core evidence for outcome.');
     document.body.dataset.stage4Done='true';return;
    }
    await new Promise(resolve=>setTimeout(resolve,200));
   }
   write('Client observation timed out. Core completion and consumption are not established.');
  }catch{write('TEST request unavailable or denied. No automatic retry.');}
  finally{busy=false;send.disabled=false;}
 }
 if(teague)q('#chatForm').addEventListener('submit',submit);else send.addEventListener('click',submit);
 input.addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();submit();}});
 write('STAGE4_TEST attachment. Text requests only. Core speech uses a silent deterministic fixture; physical voice and capture are unavailable.');
 connection();setInterval(connection,2000);
})();
