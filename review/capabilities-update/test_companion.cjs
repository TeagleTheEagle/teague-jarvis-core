const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(__dirname+'/candidate/desktop/main.cjs','utf8');
const handlers={};let resolveLoad,created=0;
class Window {
 constructor(){this.visible=false;this.webContents={setWindowOpenHandler(){},on(){},send(){}};created++;}
 isDestroyed(){return false;}isVisible(){return this.visible;}showInactive(){this.visible=true;}hide(){this.visible=false;}
 setContentProtection(){}on(){}loadFile(){return new Promise(r=>{resolveLoad=r;});}
}
const context={BrowserWindow:Window,screen:{getPrimaryDisplay:()=>({workArea:{x:0,y:0,width:1000,height:800}})},path:require('node:path'),__dirname,ipcMain:{handle:(name,fn)=>handlers[name]=fn},captureSender:e=>{if(e!=='trusted')throw Error('untrusted');},setTimeout,Promise};
vm.createContext(context);
vm.runInContext('let companion,companionWanted=false,lastCompanionState;'+source.slice(source.indexOf(' function showCompanion(){'),source.indexOf(" ipcMain.on('jarvis:companion-update'")),context);
(async()=>{
 assert.throws(()=>handlers['jarvis:companion-status']('untrusted'));
 const show=handlers['jarvis:companion-show']('trusted');
 handlers['jarvis:companion-hide']('trusted');resolveLoad();
 assert.equal((await show).shown,false,'hide during loading must win');
 assert.equal(handlers['jarvis:companion-status']('trusted').visible,false);
 assert.equal((await handlers['jarvis:companion-show']('trusted')).shown,true);
 assert.equal(created,1,'repeat show reuses the existing window');
 assert.equal(handlers['jarvis:companion-hide']('trusted').visible,false);
 console.log('PASS: trusted companion status, show/hide, singleton and hide-during-load race (mocked Electron).');
})().catch(e=>{console.error(e);process.exitCode=1;});
