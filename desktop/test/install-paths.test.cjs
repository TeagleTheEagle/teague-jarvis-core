// The app knows where it lives, and a stale start is handed to the current release (docs/OWN-APP-PLAN.md 3.2).
// Temporary folders and fake spawns only: no Electron, no Core.
const {test}=require('node:test'),assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs'),os=require('node:os');
const {installLayout,applyLayout,currentRelease,staleStart,appArguments,redirect,realPath}=require('../install-paths.cjs');

function home(){return fs.mkdtempSync(path.join(os.tmpdir(),'jarvis-install-paths-'));}
function release(h,id,{manifest=true,exe=true}={}){
 const folder=path.join(h,'releases',id);
 fs.mkdirSync(path.join(folder,'electron'),{recursive:true});
 if(manifest)fs.writeFileSync(path.join(folder,'manifest.json'),'{}');
 if(exe)fs.writeFileSync(path.join(folder,'electron','JARVIS.exe'),'MZ');
 return path.join(folder,'electron','JARVIS.exe');
}

test('an installed release is recognised by its layout and the manifest beside it',()=>{
 const h=home();const exe=release(h,'1.0.17-abc');
 const layout=installLayout(exe);
 assert.equal(layout.home,realPath(h));
 assert.equal(layout.releaseId,'1.0.17-abc');
 assert.equal(layout.dataDir,path.join(realPath(h),'data'));
 assert.equal(layout.configDir,path.join(realPath(h),'config'));
 assert.equal(layout.profile,path.join(realPath(h),'profile'));
 assert.equal(layout.modelsDir,path.join(realPath(h),'releases','1.0.17-abc','models'));
 assert.equal(layout.python,path.join(realPath(h),'releases','1.0.17-abc','python','python.exe'));
 assert.equal(layout.app,path.join(realPath(h),'releases','1.0.17-abc','app','desktop'));
});

test('a start through a short name or a junction is resolved to the real folders',()=>{
 const resolve=file=>file.replace('RELEAS~1','releases').replace('1017~1','1.0.17-abc');
 const layout=installLayout('C:\\h\\RELEAS~1\\1017~1\\electron\\JARVIS.exe',()=>true,resolve);
 assert.equal(layout.home,'C:\\h');
 assert.equal(layout.releaseId,'1.0.17-abc');
 assert.equal(realPath('C:\\no\\such\\folder\\JARVIS.exe'),path.resolve('C:\\no\\such\\folder\\JARVIS.exe'));  // unresolvable: as given
});

test('development and anything else is not an installation',()=>{
 const h=home();
 assert.equal(installLayout(path.join(h,'desktop','node_modules','electron','dist','electron.exe')),null);
 assert.equal(installLayout(release(h,'1.0.17-abc',{manifest:false})),null);           // no manifest: not a release
 assert.equal(installLayout(path.join(h,'releases','x','other','JARVIS.exe')),null);      // not the electron folder
 assert.equal(installLayout(path.join(h,'somewhere','x','electron','JARVIS.exe')),null); // not under releases
});

test('the launcher values are set from the installation; an override is honoured only when asked for by name',()=>{
 const h=home();const layout=installLayout(release(h,'1.0.17-abc'));
 const env=applyLayout(layout,{JARVIS_DATA_DIR:'D:\\stray\\data',ELECTRON_RUN_AS_NODE:'1'});
 assert.equal(env.JARVIS_DATA_DIR,layout.dataDir);                            // a stray value cannot repoint JARVIS
 assert.equal(env.JARVIS_CONFIG_DIR,layout.configDir);
 assert.equal(env.JARVIS_MODELS_DIR,layout.modelsDir);
 assert.equal(env.JARVIS_PYTHON,layout.python);
 assert.equal('ELECTRON_RUN_AS_NODE' in env,false);
 const kept=applyLayout(layout,{JARVIS_LAYOUT_OVERRIDE:'1',JARVIS_DATA_DIR:'D:\\scratch\\data'});
 assert.equal(kept.JARVIS_DATA_DIR,'D:\\scratch\\data');                      // a rehearsal's own folder, said so
 assert.equal(kept.JARVIS_CONFIG_DIR,layout.configDir);                      // the rest still from the installation
});

test('current.json: the release, or null when missing, unreadable or odd',()=>{
 const h=home();
 assert.equal(currentRelease(h),null);
 fs.writeFileSync(path.join(h,'current.json'),JSON.stringify({release:'1.0.17-abc',previous:null}));
 assert.equal(currentRelease(h),'1.0.17-abc');
 fs.writeFileSync(path.join(h,'current.json'),'{broken');
 assert.equal(currentRelease(h),null);
 fs.writeFileSync(path.join(h,'current.json'),JSON.stringify({release:7}));
 assert.equal(currentRelease(h),null);
});

test('a stale start is handed to the current release; the current release, a missing current.json and a redirected start run as they are',()=>{
 const h=home();
 const old=release(h,'1.0.16-old'),current=release(h,'1.0.17-new');
 fs.writeFileSync(path.join(h,'current.json'),JSON.stringify({release:'1.0.17-new',previous:'1.0.16-old'}));
 const stale=staleStart(installLayout(old),{env:{}});
 assert.equal(stale.program,realPath(current));
 assert.equal(stale.current,'1.0.17-new');
 assert.equal(stale.cwd,path.join(realPath(h),'releases','1.0.17-new','app','desktop'));
 assert.equal(staleStart(installLayout(current),{env:{}}),null);                        // the current one runs
 assert.equal(staleStart(installLayout(current),{current:'1.0.17-NEW',env:{}}),null);   // the same release, another casing
 assert.equal(staleStart(installLayout(old),{env:{JARVIS_REDIRECTED:'1'}}),null);        // never a second hop
 assert.equal(staleStart(installLayout(old),{current:null,env:{}}),null);                // no current.json (an uninstall in progress)
});

test('when the current release is an older one, the start goes to its launcher script, or stops with no program to hand to',()=>{
 const h=home();
 const pinned=release(h,'1.0.17-new');release(h,'1.0.16-old',{exe:false});
 fs.writeFileSync(path.join(h,'current.json'),JSON.stringify({release:'1.0.16-old',previous:'1.0.17-new'}));   // after a rollback
 assert.deepEqual(staleStart(installLayout(pinned),{env:{}}),{current:'1.0.16-old'});    // no JARVIS.ps1 yet: nothing to hand to
 fs.writeFileSync(path.join(h,'JARVIS.ps1'),'# launcher');
 assert.deepEqual(staleStart(installLayout(pinned),{env:{}}),{current:'1.0.16-old',launcher:path.join(realPath(h),'JARVIS.ps1')});
});

test('only JARVIS arguments travel with a redirect; the child is detached, marked, and started in the right folder',()=>{
 assert.deepEqual(appArguments(['C:\\x\\JARVIS.exe','C:\\x\\app\\desktop','--login-launch','--user-data-dir=C:\\p']),['--login-launch','--user-data-dir=C:\\p']);
 assert.deepEqual(appArguments(['C:\\x\\JARVIS.exe']),[]);
 const calls=[];
 const fake=(file,args,options)=>{calls.push({file,args,options});return {unref(){calls.push('unref');}};};
 redirect({current:'1.0.17-new',program:'C:\\h\\releases\\1.0.17-new\\electron\\JARVIS.exe',cwd:'C:\\h\\releases\\1.0.17-new\\app\\desktop'},['--login-launch'],fake,{PATH:'x'});
 assert.equal(calls[0].file,'C:\\h\\releases\\1.0.17-new\\electron\\JARVIS.exe');
 assert.deepEqual(calls[0].args,['--login-launch']);
 assert.equal(calls[0].options.cwd,'C:\\h\\releases\\1.0.17-new\\app\\desktop');
 assert.equal(calls[0].options.detached,true);
 assert.equal(calls[0].options.env.JARVIS_REDIRECTED,'1');
 assert.equal(calls[0].options.env.PATH,'x');
 assert.equal(calls[1],'unref');
 redirect({current:'1.0.16-old',launcher:'C:\\h\\JARVIS.ps1'},['--login-launch'],fake,{});
 assert.equal(calls[2].file,'powershell.exe');
 assert.deepEqual(calls[2].args,['-NoProfile','-WindowStyle','Hidden','-ExecutionPolicy','Bypass','-File','C:\\h\\JARVIS.ps1','-LoginLaunch']);
 redirect({current:'1.0.16-old',launcher:'C:\\h\\JARVIS.ps1'},[],fake,{});
 assert.deepEqual(calls[4].args.slice(-2),['-File','C:\\h\\JARVIS.ps1']);
});
