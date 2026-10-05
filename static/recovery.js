'use strict';
(()=>{
 const panel=document.createElement('section');panel.className='reliability-panel';
 const title=document.createElement('h2');title.textContent='Backup & recovery';
 const explanation=document.createElement('p');explanation.textContent='Back up saved data and application source locally. API keys, installed runtimes and downloaded voice models are excluded. Backups are unencrypted and contain personal data; nothing is uploaded. A backup on the same disk as JARVIS does not protect against disk failure: automatic backups below can go to another drive.';
 const controls=document.createElement('div');controls.style.cssText='display:flex;gap:12px;flex-wrap:wrap;align-items:center';
 const create=document.createElement('button');create.textContent='Create verified backup';
 const reload=document.createElement('button');reload.textContent='List backups';
 const select=document.createElement('select');select.setAttribute('aria-label','Saved backup');select.style.maxWidth='100%';
 const rehearse=document.createElement('button');rehearse.textContent='Test restore in temporary folder';
 const restore=document.createElement('button');restore.textContent='Recover to separate folder';
 const status=document.createElement('p');status.setAttribute('role','status');status.style.overflowWrap='anywhere';
 const detail=document.createElement('p');detail.textContent='Restore testing compares files and database contents. It does not launch recovered code. Recovery creates a separate folder; your working app is never overwritten. Keep JARVIS idle during backup. A backup made by hand is never deleted automatically.';
 let running=false;
 let autoIds=new Set(); // the automatic backups on the Core's record (the Automatic backups block below fills it)
 const buttons=[create,reload,rehearse,restore];
 const setBusy=value=>{running=value;buttons.forEach(b=>b.disabled=value);select.disabled=value;rehearse.disabled=restore.disabled=value||!select.value;};
 async function list(){
  const result=await api('/api/recovery',{action:'list'});select.replaceChildren();
  for(const row of result.backups){const option=document.createElement('option');option.value=row.id;option.textContent=new Date(row.created*1000).toLocaleString()+' · '+(row.bytes/1048576).toFixed(1)+' MB';select.append(option);}
  // The automatic backups, when a folder is chosen and reachable: listed with the others, marked as automatic.
  result.automatic=0;
  try{const more=await api('/api/recovery',{action:'list',where:'automatic'});for(const row of more.backups){const option=document.createElement('option');option.value=row.id;option.dataset.where='automatic';option.textContent=new Date(row.created*1000).toLocaleString()+' · '+(row.bytes/1048576).toFixed(1)+' MB · '+(autoIds.has(row.id)?'automatic':'made by hand, in the folder of the automatic ones');select.append(option);result.automatic++;}}catch(e){/* none chosen, or the drive is not connected: the line under Automatic backups says so */}
  return result;
 }
 async function operate(action){
  if(running||window.JARVIS_INSPECTION)return;
  if(action!=='list'&&(state.busy||state.transcribing)){status.textContent='Finish the active request before running recovery operations.';return;}
  setBusy(true);status.textContent=action==='create'?'Creating and verifying backup…':action==='list'?'Loading saved backups…':'Verifying and restoring files…';
  try{
   if(action==='list'){const result=await list();status.textContent=result.backups.length+' backup(s). Folder: '+result.location+(result.automatic?' Also listed: '+result.automatic+' backup(s) from the folder of the automatic ones.':'');}
   else{
    const where=action==='create'?null:select.selectedOptions[0]?.dataset.where;
    const result=await api('/api/recovery',{action,...(action==='create'?{}:{id:select.value}),...(where?{where}:{})});
    status.textContent=action==='create'?'Backup verified: '+result.files+' files. ID: '+result.id:result.status.replaceAll('_',' ')+'. '+result.scope+(result.path?' Folder: '+result.path:'');
    if(action==='create'){await list();select.value=result.id;}
   }
  }catch(e){status.textContent='Recovery operation did not complete: '+e.message;}
  finally{setBusy(false);}
 }
 create.onclick=()=>operate('create');reload.onclick=()=>operate('list');rehearse.onclick=()=>operate('rehearse');restore.onclick=()=>operate('restore');select.onchange=()=>setBusy(false);
 controls.append(create,reload,select,rehearse,restore);panel.append(title,explanation,controls,status,detail);
 // ---- automatic backups (auto_backup.py): on a schedule, to a folder the owner chooses; off until then ----
 const el=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e;};
 const auto=el('div');auto.className='auto-backup';
 const autoIntro=el('p','On a schedule, to a folder you choose, for example on your backup drive. Each one is made and checked exactly like a backup made by hand. Of the automatic ones JARVIS keeps every backup of the last 7 days, then one a week for 8 weeks, then one a month for a year, and removes the others; it never removes a backup made by hand. Off until you choose a folder. Nothing is uploaded.');
 const folder=el('input');folder.type='text';folder.maxLength=400;folder.placeholder='Folder, for example E:\\JARVIS-BACKUP';folder.setAttribute('aria-label','Folder for automatic backups');folder.style.cssText='flex:1 1 320px;min-width:0';
 const every=el('select');every.setAttribute('aria-label','How often');every.add(new Option('Every day','day'));every.add(new Option('Every week','week'));
 const at=el('input');at.type='time';at.value='12:00';at.setAttribute('aria-label','Time of day');
 const save=el('button','TURN ON'),off=el('button','TURN OFF'),now=el('button','BACK UP NOW');[save,off,now].forEach(b=>b.type='button');
 const row=el('div');row.style.cssText='display:flex;gap:12px;flex-wrap:wrap;align-items:center';row.append(folder,every,at,save,off,now);
 const autoState=el('p');autoState.setAttribute('role','status');autoState.style.overflowWrap='anywhere';
 const when=seconds=>seconds?new Date(seconds*1000).toLocaleString():'never';
 // What the Core says about automatic backups, in plain words.
 const describe=s=>{
  if(!s)return 'Not known yet.';
  if(!s.folder)return 'Off. Choose a folder and press TURN ON.';
  const parts=[s.enabled?'On: '+(s.every==='week'?'every week':'every day')+' at '+s.at+'.':'Off (the folder and the backups already made are kept).','Backups go to: '+s.backups_in+(s.folder_reachable?'.':'. THIS FOLDER IS NOT REACHABLE NOW (is the drive connected?).'),'Last automatic backup: '+when(s.last_success)+'.'];
  if(s.running)parts.push('A backup is being made now.');
  else if(s.enabled&&s.next_due)parts.push('Next: '+(s.next_due*1000>Date.now()+60000?when(s.next_due):s.stop_holds?'when the emergency stop is lifted':'as soon as JARVIS is idle')+'.');
  if(s.kept)parts.push(s.kept+' automatic backup'+(s.kept===1?'':'s')+' on record.');
  if(s.last_error)parts.push('The last try did not work: '+s.last_error);
  if(s.overdue)parts.push('ATTENTION: no automatic backup has succeeded for more than two periods.');
  else if(s.never_succeeded)parts.push('ATTENTION: no automatic backup has succeeded yet.');
  return parts.join(' ');
 };
 let autoBusy=false;
 // fields: also put the saved folder, time and frequency into the boxes (not after a refusal: what was typed stays).
 const show=(s,fields=true)=>{autoState.textContent=describe(s);if(!s)return;autoIds=new Set(s.ids||[]);if(fields){if(document.activeElement!==folder&&s.folder)folder.value=s.folder;every.value=s.every==='week'?'week':'day';if(document.activeElement!==at&&s.at)at.value=s.at;}save.textContent=s.enabled?'SAVE CHANGES':'TURN ON';off.disabled=autoBusy||!s.enabled;now.disabled=autoBusy||!s.folder||s.running;};
 const autoLoad=async(fields=true)=>{if(window.JARVIS_INSPECTION){autoState.textContent='Not shown during an inspection.';return;}try{const r=await fetch('/api/auto-backup');if(r.status===404){auto.hidden=true;return;}if(!r.ok)throw new Error(r.status===401?'sign in on this PC to see them.':'the Core did not answer properly ('+r.status+').');show(await r.json(),fields);}catch(e){autoState.textContent='Automatic backups: '+e.message;}};
 const autoAct=async(body,working)=>{if(autoBusy||window.JARVIS_INSPECTION)return;autoBusy=true;[save,off,now].forEach(b=>b.disabled=true);autoState.textContent=working;let problem='';try{show(await api('/api/auto-backup',body));}catch(e){problem=e.message;}finally{autoBusy=false;save.disabled=false;await autoLoad(!problem);if(problem)autoState.textContent=problem+' ('+autoState.textContent+')';}};
 save.onclick=()=>autoAct({action:'configure',folder:folder.value,every:every.value,at:at.value},'Checking the folder…');
 off.onclick=()=>autoAct({action:'off'},'Turning off…');
 now.onclick=()=>{if(state.busy||state.transcribing){autoState.textContent='Finish the active request before backing up.';return;}autoAct({action:'run'},'Making and checking a backup…');};
 auto.append(el('h3','Automatic backups'),autoIntro,row,autoState);panel.append(auto);
 document.getElementById('settingsView').prepend(panel);setBusy(false);
 const settingsNav=document.querySelector('.nav[data-view="settings"]');if(settingsNav)settingsNav.addEventListener('click',()=>autoLoad());
 autoLoad();
})();
