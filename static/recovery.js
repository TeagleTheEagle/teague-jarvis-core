'use strict';
(()=>{
 const panel=document.createElement('section');panel.className='reliability-panel';
 const title=document.createElement('h2');title.textContent='Backup & recovery';
 const explanation=document.createElement('p');explanation.textContent='Back up saved data and application source locally. API keys, installed runtimes and downloaded voice models are excluded. Backups are unencrypted and contain personal data; nothing is uploaded. This local copy does not protect against disk failure.';
 const controls=document.createElement('div');controls.style.cssText='display:flex;gap:12px;flex-wrap:wrap;align-items:center';
 const create=document.createElement('button');create.textContent='Create verified backup';
 const reload=document.createElement('button');reload.textContent='List backups';
 const select=document.createElement('select');select.setAttribute('aria-label','Saved backup');select.style.maxWidth='100%';
 const rehearse=document.createElement('button');rehearse.textContent='Test restore in temporary folder';
 const restore=document.createElement('button');restore.textContent='Recover to separate folder';
 const status=document.createElement('p');status.setAttribute('role','status');status.style.overflowWrap='anywhere';
 const detail=document.createElement('p');detail.textContent='Restore testing compares files and database contents. It does not launch recovered code. Recovery creates a separate folder; your working app is never overwritten. Keep JARVIS idle during backup. No backups are automatically deleted.';
 let running=false;
 const buttons=[create,reload,rehearse,restore];
 const setBusy=value=>{running=value;buttons.forEach(b=>b.disabled=value);select.disabled=value;rehearse.disabled=restore.disabled=value||!select.value;};
 async function list(){
  const result=await api('/api/recovery',{action:'list'});select.replaceChildren();
  for(const row of result.backups){const option=document.createElement('option');option.value=row.id;option.textContent=new Date(row.created*1000).toLocaleString()+' · '+(row.bytes/1048576).toFixed(1)+' MB';select.append(option);}
  return result;
 }
 async function operate(action){
  if(running||window.JARVIS_INSPECTION)return;
  if(action!=='list'&&(state.busy||state.transcribing)){status.textContent='Finish the active request before running recovery operations.';return;}
  setBusy(true);status.textContent=action==='create'?'Creating and verifying backup…':action==='list'?'Loading saved backups…':'Verifying and restoring files…';
  try{
   if(action==='list'){const result=await list();status.textContent=result.backups.length+' backup(s). Folder: '+result.location;}
   else{
    const result=await api('/api/recovery',{action,...(action==='create'?{}:{id:select.value})});
    status.textContent=action==='create'?'Backup verified: '+result.files+' files. ID: '+result.id:result.status.replaceAll('_',' ')+'. '+result.scope+(result.path?' Folder: '+result.path:'');
    if(action==='create'){await list();select.value=result.id;}
   }
  }catch(e){status.textContent='Recovery operation did not complete: '+e.message;}
  finally{setBusy(false);}
 }
 create.onclick=()=>operate('create');reload.onclick=()=>operate('list');rehearse.onclick=()=>operate('rehearse');restore.onclick=()=>operate('restore');select.onchange=()=>setBusy(false);
 controls.append(create,reload,select,rehearse,restore);panel.append(title,explanation,controls,status,detail);document.getElementById('settingsView').prepend(panel);setBusy(false);
})();
