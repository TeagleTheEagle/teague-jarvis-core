// Where this app lives (docs/OWN-APP-PLAN.md section 3.2, release 1.0.17). From an installed release the program
// file is <home>\releases\<id>\electron\JARVIS.exe: the home is three folders up, the rule runtime_paths.install_home
// uses on the Core side. The app then sets the values JARVIS.ps1 used to set (data, config, models, Python) and its
// own profile folder, and a stale start (a taskbar pin or a "recent" entry still pointing at an old release's
// JARVIS.exe after an update) is handed to the current release. In development (the repo) nothing here applies.
const path=require('node:path'),fs=require('node:fs');

// An 8.3 short name or a junction in the path (a start through RELEAS~1): the real folders decide.
function realPath(file){try{return fs.realpathSync.native(file);}catch{return path.resolve(file);}}

function installLayout(execPath,exists=fs.existsSync,resolve=realPath){
 const exe=resolve(execPath);
 const electron=path.dirname(exe),release=path.dirname(electron),releases=path.dirname(release);
 if(path.basename(electron).toLowerCase()!=='electron'||path.basename(releases).toLowerCase()!=='releases')return null;
 if(path.dirname(releases)===releases)return null;                 // a drive root has no home above it
 if(!exists(path.join(release,'manifest.json')))return null;       // the release manifest marks a real installation
 const home=path.dirname(releases);
 return {home,release,releaseId:path.basename(release),exe,
  dataDir:path.join(home,'data'),configDir:path.join(home,'config'),profile:path.join(home,'profile'),
  modelsDir:path.join(release,'models'),python:path.join(release,'python','python.exe'),app:path.join(release,'app','desktop')};
}

// The values the launcher used to set, set as it set them: always from the installation, so nothing outside it can
// repoint an installed JARVIS (the Stage 6 rule). A rehearsal that must point the app elsewhere says so with
// JARVIS_LAYOUT_OVERRIDE=1 and then keeps the values it set. ELECTRON_RUN_AS_NODE never reaches the Core from here.
function applyLayout(layout,env=process.env){
 const override=env.JARVIS_LAYOUT_OVERRIDE==='1';
 for(const [name,value] of [['JARVIS_DATA_DIR',layout.dataDir],['JARVIS_CONFIG_DIR',layout.configDir],['JARVIS_MODELS_DIR',layout.modelsDir],['JARVIS_PYTHON',layout.python]]){
  if(!(override&&env[name]))env[name]=value;
 }
 delete env.ELECTRON_RUN_AS_NODE;
 return env;
}

function currentRelease(home,read=file=>fs.readFileSync(file,'utf8')){
 try{const current=JSON.parse(read(path.join(home,'current.json')));return typeof current.release==='string'&&current.release?current.release:null;}
 catch{return null;}
}

// null: run as you are (this is the current release, there is no current.json, or this start was already handed on:
// a current.json naming a release whose own current.json disagrees must not bounce two programs between each other).
// Otherwise what to hand the start to: the current release's JARVIS.exe (`program`), or the PowerShell launcher of an
// older current release (`launcher`, 1.0.16 and before), or neither (`current` only: the caller says so and exits).
function staleStart(layout,{current,exists=fs.existsSync,env=process.env}={}){
 if(env.JARVIS_REDIRECTED)return null;
 const release=current===undefined?currentRelease(layout.home):current;
 if(!release||release.toLowerCase()===layout.releaseId.toLowerCase())return null;
 const program=path.join(layout.home,'releases',release,'electron','JARVIS.exe');
 if(exists(program))return {current:release,program,cwd:path.join(layout.home,'releases',release,'app','desktop')};
 const launcher=path.join(layout.home,'JARVIS.ps1');
 if(exists(launcher))return {current:release,launcher};
 return {current:release};
}

// The arguments meant for JARVIS itself (--login-launch and the like): never the program, never an app path.
function appArguments(argv){
 return argv.slice(1).filter(argument=>typeof argument==='string'&&argument.startsWith('--'));
}

function redirect(stale,args,spawn=require('node:child_process').spawn,env=process.env){
 const marked={...env,JARVIS_REDIRECTED:'1'};
 const child=stale.program
  ?spawn(stale.program,args,{cwd:stale.cwd,detached:true,stdio:'ignore',windowsHide:false,env:marked})
  :spawn('powershell.exe',['-NoProfile','-WindowStyle','Hidden','-ExecutionPolicy','Bypass','-File',stale.launcher,...(args.includes('--login-launch')?['-LoginLaunch']:[])],
         {detached:true,stdio:'ignore',windowsHide:true,env:marked});
 child.unref?.();
 return child;
}

module.exports={installLayout,applyLayout,currentRelease,staleStart,appArguments,redirect,realPath};
