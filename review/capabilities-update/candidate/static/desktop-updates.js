'use strict';
(() => {
 const bridge=window.jarvisDesktop;
 if(window.JARVIS_INSPECTION||!bridge?.updateStatus)return;
 const bar=document.createElement('aside');bar.setAttribute('aria-label','Application update');bar.hidden=true;
 bar.style.cssText='position:fixed;bottom:18px;left:24px;right:24px;z-index:10000;padding:14px 18px;background:#092231;border:1px solid #91d9ee;color:#e1f6ff;display:none;align-items:center;gap:16px;box-shadow:0 5px 24px #0008';
 const label=document.createElement('span');label.setAttribute('role','status');label.style.flex='1';
 const button=document.createElement('button');button.type='button';
 bar.append(label,button);document.body.append(bar);
 let pending=null,applying=false,lastInput=Date.now();
 const edited=new Map();
 document.addEventListener('focusin',e=>{if(e.target.matches('input,textarea,select')&&!edited.has(e.target))edited.set(e.target,e.target.type==='checkbox'?e.target.checked:e.target.value);});
 document.addEventListener('input',()=>{lastInput=Date.now();});
 document.addEventListener('pointerdown',()=>{lastInput=Date.now();});
 document.addEventListener('keydown',()=>{lastInput=Date.now();});
 function blocked(){
  if(typeof state==='undefined'||!state.data)return true;
  if(state.busy||state.transcribing||state.mic||state.audio||state.attachment)return true;
  if(typeof screenStream!=='undefined'&&(screenStream||screenBlob||screenSending||screenCaptureBusy||desktopLiveStarting))return true;
  if(document.querySelector('dialog[open]')||document.querySelector('#inspectionResults')?.childElementCount)return true;
  if(document.querySelector('#messageInput')?.value.trim())return true;
  for(const [el,value] of edited){if(el.isConnected&&(el.type==='checkbox'?el.checked:el.value)!==value)return true;}
  return [...document.querySelectorAll('audio,video')].some(el=>!el.paused&&!el.ended);
 }
 function render(){
  bar.hidden=!pending;bar.style.display=pending?'flex':'none';if(!pending)return;
  const busy=blocked();button.disabled=busy||applying;
  button.textContent=pending.kind==='restart'?'RESTART TO UPDATE':'APPLY UPDATE';
  label.textContent=busy?'Update ready. Finish your activity, save drafts, close reports and mute the microphone to apply it.':pending.kind==='restart'?'Application update ready. Restart JARVIS to load the updated code.':'Interface update ready. It will reload automatically when idle.';
 }
 async function apply(){
  if(!pending||applying||blocked())return;
  applying=true;button.disabled=true;
  try{const result=await bridge.applyUpdate(pending.revision);if(!result.applied){pending=await bridge.updateStatus();applying=false;render();}}
  catch{applying=false;label.textContent='The update could not be applied. Quit JARVIS from its tray menu and reopen the desktop shortcut.';}
 }
 button.onclick=apply;
 function receive(update){pending=update;render();}
 bridge.onUpdateAvailable(receive);bridge.updateStatus().then(receive).catch(()=>{});
 setInterval(()=>{render();if(pending?.kind==='reload'&&!blocked()&&Date.now()-lastInput>15000)void apply();},2000);
})();
