const {contextBridge,ipcRenderer}=require('electron');
if (process.argv.includes('--stage4-test-renderer')) {
 const invoke=(op,args={})=>ipcRenderer.invoke('stage4:ordinary',op,args);
 contextBridge.exposeInMainWorld('jarvisStage4',Object.freeze({
  connection:()=>invoke('connection'),shared:()=>invoke('shared'),
  request:text=>invoke('request',{text}),requestStatus:request_id=>invoke('request-status',{request_id}),
  cancelRequest:request_id=>invoke('cancel',{request_id}),
  stopCapture:()=>invoke('stop-capture',{lease_id:null}),
  stopPlayback:()=>invoke('stop-playback',{lease_id:null})
 }));
} else {
contextBridge.exposeInMainWorld('jarvisDesktop',Object.freeze({
  updateStatus:()=>ipcRenderer.invoke('jarvis:update-status'),
  applyUpdate:revision=>ipcRenderer.invoke('jarvis:apply-update',revision),
  onUpdateAvailable(callback){if(typeof callback==='function')ipcRenderer.on('jarvis:update-available',(_e,update)=>callback(update));},
  micPreference:value=>ipcRenderer.invoke('jarvis:mic-preference',value),
  onResumeMic(callback){if(typeof callback==='function')ipcRenderer.on('jarvis:resume-mic',()=>callback());},
  onNavigationReset(callback){if(typeof callback==='function')ipcRenderer.on('jarvis:reset-navigation',()=>callback());},
  onLoginGreeting(callback){if(typeof callback==='function')ipcRenderer.on('jarvis:login-greeting',(_e,text)=>callback(String(text||'')));},
  showCompanion:()=>ipcRenderer.invoke('jarvis:companion-show'),
  hideCompanion:()=>ipcRenderer.invoke('jarvis:companion-hide'),
  companionStatus:()=>ipcRenderer.invoke('jarvis:companion-status'),
  updateCompanion:data=>ipcRenderer.send('jarvis:companion-update',data),
  onCompanionAction(callback){if(typeof callback==='function')ipcRenderer.on('jarvis:companion-command',(_e,action)=>callback(action));},
  screenPreference:value=>ipcRenderer.invoke('jarvis:screen-preference',value),
  authoriseScreen:()=>ipcRenderer.invoke('jarvis:screen-authorise'),
  liveScreenSource:()=>ipcRenderer.invoke('jarvis:screen-live-source'),
  captureScreen:()=>ipcRenderer.invoke('jarvis:screen-capture'),
  stopScreen:()=>ipcRenderer.invoke('jarvis:screen-stop'),
  onScreenRevoked(callback){if(typeof callback==='function')ipcRenderer.on('jarvis:screen-revoked',()=>callback());},
  onStop(callback){if(typeof callback!=='function')return;ipcRenderer.on('jarvis:stop',()=>callback());}
}));

window.addEventListener('DOMContentLoaded',()=>{if(process.platform==='win32')document.documentElement.classList.add('desktop-integrated-titlebar');});

}
