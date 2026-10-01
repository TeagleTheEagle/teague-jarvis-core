const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('companion',Object.freeze({onState:callback=>{if(typeof callback==='function')ipcRenderer.on('jarvis:companion-state',(_e,data)=>callback(data));},action:action=>ipcRenderer.send('jarvis:companion-action',action)}));
