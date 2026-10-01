if (process.argv.includes('--stage4-test')) {
 require('../stage4_client.cjs').launchTestClient('intelligence');
} else {
const {app,BrowserWindow,session}=require('electron');
const path=require('node:path');
const fs=require('node:fs');
const {trusted}=require('../desktop/policy.cjs');
let win;
// Keep the dedicated client stable on older Windows graphics drivers. The Core and
// existing Teague desktop process remain unchanged; only this UI client falls back
// to software compositing when Electron's GPU process is unavailable.
app.commandLine.appendSwitch('disable-gpu');
function start(){const sessionFile=path.join(__dirname,'..','desktop','.jarvis-session.json');let link=null;try{link=JSON.parse(fs.readFileSync(sessionFile,'utf8'));}catch{}const ses=session.fromPartition('jarvis-intelligence');if(link?.origin&&link?.token){ses.webRequest.onBeforeSendHeaders((details,callback)=>{const headers={...details.requestHeaders};for(const name of Object.keys(headers)){if(name.toLowerCase()==='x-jarvis-desktop')delete headers[name];}if(trusted(details.url,link.origin))headers['X-Jarvis-Desktop']=link.token;callback({requestHeaders:headers});});}win=new BrowserWindow({width:1680,height:1000,minWidth:1100,minHeight:720,show:true,backgroundColor:'#020a12',title:'JARVIS Intelligence · Teague Industries',webPreferences:{contextIsolation:true,nodeIntegration:false,sandbox:true,session:ses}});win.removeMenu();win.webContents.on('did-fail-load',(_event,code,description)=>{if(!win.isDestroyed())win.loadFile(path.join(__dirname,'index.html'));});win.once('ready-to-show',()=>win.show());if(link?.origin)win.loadURL(link.origin+'/intelligence.html').catch(()=>win.loadFile(path.join(__dirname,'index.html')));else win.loadFile(path.join(__dirname,'index.html'));}
app.whenReady().then(start);app.on('window-all-closed',()=>{if(process.platform!=='darwin')app.quit();});

}
