'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),{EventEmitter}=require('node:events');
const source=fs.readFileSync(path.join(__dirname,'../../deployment_test/package.py'),'utf8');
const template=name=>{const m=source.match(new RegExp(name+" = '''([\\s\\S]*?)'''"));assert.ok(m);return m[1];};
const entry=template('ELECTRON_ENTRY'),launcher=template('NODE_LAUNCHER');
const deployment={root:'C:\\TEST-INSTALL-'+'a'.repeat(32)+'\\state\\TEST-STAGE4-'+'b'.repeat(32),
 app:'C:\\TEST-INSTALL-'+'a'.repeat(32)+'\\releases\\build\\app',
 packageHash:'c'.repeat(64),installation:'TEST-INSTALL-'+'a'.repeat(32),nativePath:'C:\\TEST\\peer_identity.node'};
const config={clientId:'teague',deployment,serverKey:'SYNTHETIC_SERVER_SECRET',clientKey:'SYNTHETIC_CLIENT_SECRET',expectedIdentity:{mode:'TEST'},driver:true};
function entryRun(metadata,extra={}){
 const p=new EventEmitter();p.send=()=>{};p.argv=['electron.exe','entry.cjs','--stage4-bootstrap='+Buffer.from(JSON.stringify(metadata)).toString('base64url')];Object.assign(p,extra);
 const calls=[];vm.runInNewContext(entry,{process:p,Buffer,require:name=>{assert.equal(name,'./stage4_client.cjs');return {launchTestClient:(...a)=>{calls.push(a);p.on('message',m=>calls.push(['private-config',m]));}};}});
 return {p,calls};
}
function launchRun(){
 const lines=new EventEmitter(),child=new EventEmitter(),forks=[],messages=[],exits=[];
 Object.assign(child,{connected:true,stdout:{pipe(){}},stderr:{pipe(){}},send:m=>messages.push(m),disconnect(){this.connected=false;}});
 const p={argv:['node.exe','launcher.cjs',deployment.root],env:{SystemRoot:'C:\\Windows',OPENAI_API_KEY:'UNRELATED_SECRET',PATH:'UNRELATED_PATH'},stdin:{},stdout:{},stderr:{},exit:n=>exits.push(n)};
 vm.runInNewContext(launcher,{process:p,Buffer,__dirname:deployment.app,require:name=>({
  'node:path':path.win32,'node:fs':{},'node:child_process':{fork:(...a)=>{forks.push(a);return child;}},
  'node:readline':{createInterface:()=>lines}})[name]});
 return {lines,child,forks,messages,exits};
}
test('entry initializes synchronously before any private IPC configuration',()=>{
 const {p,calls}=entryRun({clientId:'teague',deployment});assert.equal(calls.length,1);
 assert.equal(calls[0][0],'teague');assert.equal(calls[0][1].root,deployment.root);
 p.emit('message',config);assert.equal(calls.length,2);assert.equal(calls[1][0],'private-config');assert.equal(calls[1][1],config);
});
test('entry rejects absent or ambiguous bootstrap metadata',()=>{
 assert.throws(()=>entryRun({}, {argv:[]}),/DEPLOYMENT_BOOTSTRAP/);
 assert.throws(()=>entryRun({}, {argv:['--stage4-bootstrap=x','--stage4-bootstrap=y']}),/DEPLOYMENT_BOOTSTRAP/);
});
test('entry rejects ordinary launch and unsupported client',()=>{
 assert.throws(()=>entryRun({clientId:'teague',deployment},{send:undefined}),/TRUSTED_TEST_LAUNCHER_REQUIRED/);
 assert.throws(()=>entryRun({clientId:'production',deployment}),/DEPLOYMENT_CONFIG/);
});
test('entry rejects additional bootstrap fields rather than accepting secret configuration',()=>{
 assert.throws(()=>entryRun({...config}),/DEPLOYMENT_CONFIG/);
});
test('launcher waits for configuration without starting any Electron process',()=>{
 const f=launchRun();assert.equal(f.forks.length,0);f.lines.emit('close');assert.equal(f.forks.length,0);
});
test('launcher passes only nonsecret metadata and preserves private IPC configuration',()=>{
 const f=launchRun();f.lines.emit('line',JSON.stringify(config));assert.equal(f.forks.length,1);
 const [exe,args,options]=f.forks[0];assert.equal(exe,path.win32.join(deployment.app,'deployment-entry.cjs'));
 const encoded=args.find(a=>a.startsWith('--stage4-bootstrap=')).split('=')[1];
 assert.deepEqual(JSON.parse(Buffer.from(encoded,'base64url').toString()),{clientId:'teague',deployment});
 assert.ok(!JSON.stringify([args,options]).includes('SECRET'));assert.ok(!options.env.PATH);
 assert.equal(options.execPath,path.win32.join(deployment.app,'../electron/electron.exe'));
 assert.equal(options.stdio[3],'ipc');assert.equal(options.cwd,path.win32.resolve(deployment.app,'..'));
 assert.deepEqual(JSON.parse(JSON.stringify(f.messages)),[config]);
});
test('invalid initial configuration cannot start a child',()=>{
 for(const bad of [{...config,clientId:'other'},{...config,deployment:{...deployment,secret:'NO'}},{...config,deployment:null}]){
  const f=launchRun();assert.throws(()=>f.lines.emit('line',JSON.stringify(bad)),/DEPLOYMENT_CONFIG/);assert.equal(f.forks.length,0);
 }
});
test('fixed actions forward once and normal launcher disconnect remains intact',()=>{
 const f=launchRun();f.lines.emit('line',JSON.stringify(config));f.lines.emit('line',JSON.stringify({action:'snapshot'}));
 assert.equal(f.forks.length,1);assert.equal(f.messages.length,2);assert.equal(f.messages[1].action,'snapshot');
 f.lines.emit('close');assert.equal(f.child.connected,false);f.child.emit('exit',0);assert.deepEqual(f.exits,[0]);
});

