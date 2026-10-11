const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('jarvisDesktop',Object.freeze({
  updateStatus:()=>ipcRenderer.invoke('jarvis:update-status'),
  applyUpdate:revision=>ipcRenderer.invoke('jarvis:apply-update',revision),
  onUpdateAvailable(callback){if(typeof callback==='function')ipcRenderer.on('jarvis:update-available',(_e,update)=>callback(update));},
  micPreference:value=>ipcRenderer.invoke('jarvis:mic-preference',value),
  onResumeMic(callback){if(typeof callback==='function')ipcRenderer.on('jarvis:resume-mic',()=>callback());},
  onLoginGreeting(callback){if(typeof callback==='function')ipcRenderer.on('jarvis:login-greeting',(_e,text)=>callback(String(text||'')));},
  showCompanion:()=>ipcRenderer.invoke('jarvis:companion-show'),
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
