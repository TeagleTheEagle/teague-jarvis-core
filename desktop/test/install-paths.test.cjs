// The app knows where it lives, and a stale start is handed to the current release (docs/OWN-APP-PLAN.md 3.2).
// Temporary folders and fake spawns only: no Electron, no Core.
const {test}=require('node:test'),assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs'),os=require('node:os');
const {installLayout,applyLayout,currentRelease,staleStart,appArguments,redirect}=require('../install-paths.cjs');

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
 assert.equal(layout.home,h);
 assert.equal(layout.releaseId,'1.0.17-abc');
 assert.equal(layout.dataDir,path.join(h,'data'));
 assert.equal(layout.configDir,path.join(h,'config'));
 assert.equal(layout.profile,path.join(h,'profile'));
 assert.equal(layout.modelsDir,path.join(h,'releases','1.0.17-abc','models'));
 assert.equal(layout.python,path.join(h,'releases','1.0.17-abc','python','python.exe'));
 assert.equal(layout.app,path.join(h,'releases','1.0.17-abc','app','desktop'));
});

test('development and anything else is not an installation',()=>{
 const h=home();
 assert.equal(installLayout(path.join(h,'desktop','node_modules','electron','dist','electron.exe')),null);
 assert.equal(installLayout(release(h,'1.0.17-abc',{manifest:false})),null);           // no manifest: not a release
 assert.equal(installLayout(path.join(h,'releases','x','other','JARVIS.exe')),null);      // not the electron folder
 assert.equal(installLayout(path.join(h,'somewhere','x','electron','JARVIS.exe')),null); // not under releases
});

test('the launcher values are set unless already given, and node mode never reaches the Core',()=>{
 const h=home();const layout=installLayout(release(h,'1.0.17-abc'));
 const env=applyLayout(layout,{JARVIS_DATA_DIR:'D:\\scratch\\data',ELECTRON_RUN_AS_NODE:'1'});
 assert.equal(env.JARVIS_DATA_DIR,'D:\\scratch\\data');                       // an explicit value wins
 assert.equal(env.JARVIS_CONFIG_DIR,path.join(h,'config'));
 assert.equal(env.JARVIS_MODELS_DIR,layout.modelsDir);
 assert.equal(env.JARVIS_PYTHON,layout.python);
 assert.equal('ELECTRON_RUN_AS_NODE' in env,false);
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

test('a stale start is handed to the current release; the current release, a missing one and a redirected start are not',()=>{
 const h=home();
 const old=release(h,'1.0.16-old'),current=release(h,'1.0.17-new');
 fs.writeFileSync(path.join(h,'current.json'),JSON.stringify({release:'1.0.17-new',previous:'1.0.16-old'}));
 assert.equal(staleStart(installLayout(old),{env:{}}),current);
 assert.equal(staleStart(installLayout(current),{env:{}}),null);                        // the current one runs
 assert.equal(staleStart(installLayout(old),{env:{JARVIS_REDIRECTED:'1'}}),null);        // never a second hop
 assert.equal(staleStart(installLayout(old),{current:'1.0.18-gone',env:{}}),null);       // no such program: run as you are
 assert.equal(staleStart(installLayout(old),{current:null,env:{}}),null);                // no current.json (an uninstall in progress)
});

test('only JARVIS arguments travel with a redirect, and the child is detached with the redirect mark',()=>{
 assert.deepEqual(appArguments(['C:\\x\\JARVIS.exe','C:\\x\\app\\desktop','--login-launch','--user-data-dir=C:\\p']),['--login-launch','--user-data-dir=C:\\p']);
 assert.deepEqual(appArguments(['C:\\x\\JARVIS.exe']),[]);
 const calls=[];
 const child=redirect('C:\\h\\releases\\1.0.17-new\\electron\\JARVIS.exe',['--login-launch'],(file,args,options)=>{calls.push({file,args,options});return {unref(){calls.push('unref');}};},{PATH:'x'});
 assert.equal(calls[0].file,'C:\\h\\releases\\1.0.17-new\\electron\\JARVIS.exe');
 assert.deepEqual(calls[0].args,['--login-launch']);
 assert.equal(calls[0].options.detached,true);
 assert.equal(calls[0].options.env.JARVIS_REDIRECTED,'1');
 assert.equal(calls[0].options.env.PATH,'x');
 assert.equal(calls[1],'unref');
 assert.ok(child);
});
