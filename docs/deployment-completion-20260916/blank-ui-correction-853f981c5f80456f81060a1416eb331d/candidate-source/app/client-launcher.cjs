'use strict';
const path=require('node:path'),fs=require('node:fs'),{fork}=require('node:child_process');
const release=path.resolve(__dirname,'..');
if(process.argv.length!==3||!/^TEST-STAGE4-[a-f0-9]{32}$/.test(path.basename(process.argv[2])))throw Error('EXPLICIT_TEST_ROOT');
let c=null;
const lines=require('node:readline').createInterface({input:process.stdin});
lines.on('line',line=>{
 const cfg=JSON.parse(line);
 if(!c){
  const fields=['root','app','packageHash','installation','nativePath'];
  if(!cfg||!['teague','intelligence'].includes(cfg.clientId)||!cfg.deployment||
   Object.keys(cfg.deployment).sort().join(',')!==fields.slice().sort().join(',')||
   fields.some(k=>typeof cfg.deployment[k]!=='string'))throw Error('DEPLOYMENT_CONFIG');
  const boot=Buffer.from(JSON.stringify({clientId:cfg.clientId,deployment:cfg.deployment}),'utf8').toString('base64url');
  if(boot.length>16300)throw Error('DEPLOYMENT_BOOTSTRAP');
  c=fork(path.join(__dirname,'deployment-entry.cjs'),['--stage4-test','--stage4-root='+process.argv[2],'--stage4-bootstrap='+boot],{
   execPath:path.join(release,'electron/electron.exe'),stdio:['ignore','pipe','pipe','ipc'],windowsHide:true,
   cwd:release,env:Object.fromEntries(Object.entries(process.env).filter(([k])=>['SYSTEMROOT','WINDIR','TEMP','TMP','USERPROFILE','APPDATA','LOCALAPPDATA','COMSPEC'].includes(k.toUpperCase())))});
  c.stdout.pipe(process.stdout);c.stderr.pipe(process.stderr);
  c.on('exit',code=>process.exit(code===null?1:code));
 }
 c.send(cfg);
});
lines.on('close',()=>{if(c?.connected)c.disconnect();});
