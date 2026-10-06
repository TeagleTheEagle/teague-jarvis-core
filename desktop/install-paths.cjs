// Where this app lives (docs/OWN-APP-PLAN.md section 3.2, release 1.0.17). From an installed release the program
// file is <home>\releases\<id>\electron\JARVIS.exe: the home is three folders up, the rule runtime_paths.install_home
// uses on the Core side. The app then sets the values JARVIS.ps1 used to set (data, config, models, Python) and its
// own profile folder, and a stale start (a taskbar pin or a "recent" entry still pointing at an old release's
// JARVIS.exe after an update) is handed to the current release. In development (the repo) nothing here applies.
const path=require('node:path'),fs=require('node:fs');

function installLayout(execPath,exists=fs.existsSync){
 const exe=path.resolve(execPath);
 const electron=path.dirname(exe),release=path.dirname(electron),releases=path.dirname(release);
 if(path.basename(electron).toLowerCase()!=='electron'||path.basename(releases).toLowerCase()!=='releases')return null;
 if(path.dirname(releases)===releases)return null;                 // a drive root has no home above it
 if(!exists(path.join(release,'manifest.json')))return null;       // the release manifest marks a real installation
 const home=path.dirname(releases);
 return {home,release,releaseId:path.basename(release),exe,
  dataDir:path.join(home,'data'),configDir:path.join(home,'config'),profile:path.join(home,'profile'),
  modelsDir:path.join(release,'models'),python:path.join(release,'python','python.exe'),app:path.join(release,'app','desktop')};
}

// The values the launcher used to set. A value already in the environment wins (a rehearsal pointing at a
// scratch folder); ELECTRON_RUN_AS_NODE never reaches the Core from here.
function applyLayout(layout,env=process.env){
 for(const [name,value] of [['JARVIS_DATA_DIR',layout.dataDir],['JARVIS_CONFIG_DIR',layout.configDir],['JARVIS_MODELS_DIR',layout.modelsDir],['JARVIS_PYTHON',layout.python]]){
  if(!env[name])env[name]=value;
 }
 delete env.ELECTRON_RUN_AS_NODE;
 return env;
}

function currentRelease(home,read=file=>fs.readFileSync(file,'utf8')){
 try{const current=JSON.parse(read(path.join(home,'current.json')));return typeof current.release==='string'&&current.release?current.release:null;}
 catch{return null;}
}

// The current release's JARVIS.exe when this one is not current (and the current one exists), else null.
// A start that was already redirected once is never redirected again (a current.json that names a release whose
// own current.json disagrees must not bounce two programs between each other).
function staleStart(layout,{current,exists=fs.existsSync,env=process.env}={}){
 if(env.JARVIS_REDIRECTED)return null;
 const release=current===undefined?currentRelease(layout.home):current;
 if(!release||release===layout.releaseId)return null;
 const target=path.join(layout.home,'releases',release,'electron','JARVIS.exe');
 return exists(target)?target:null;
}

// The arguments meant for JARVIS itself (--login-launch and the like): never the program, never an app path.
function appArguments(argv){
 return argv.slice(1).filter(argument=>typeof argument==='string'&&argument.startsWith('--'));
}

function redirect(target,args,spawn=require('node:child_process').spawn,env=process.env){
 const child=spawn(target,args,{detached:true,stdio:'ignore',windowsHide:false,env:{...env,JARVIS_REDIRECTED:'1'}});
 child.unref?.();
 return child;
}

module.exports={installLayout,applyLayout,currentRelease,staleStart,appArguments,redirect};
