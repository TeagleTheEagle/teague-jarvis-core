const {spawn}=require('node:child_process');
const {randomBytes}=require('node:crypto');
const path=require('node:path');
function startBackend(root,options={}){
 const token=randomBytes(32).toString('hex');
 const child=spawn(path.join(root,'.venv','Scripts','python.exe'),['-u',path.join(root,'server.py'),'--port','0',...(options.dataDir?['--data-dir',options.dataDir]:[])],{cwd:root,windowsHide:true,env:{...process.env,JARVIS_DESKTOP_TOKEN:token},stdio:['pipe','pipe','pipe']});
 child.stdin.on('error',()=>{});child.stderr.resume();
 const ready=new Promise((resolve,reject)=>{
  // Cold Windows native-library loading can take over 30 seconds before wake preparation finishes.
  let buffer='';const timer=setTimeout(()=>{child.kill();reject(new Error('JARVIS backend did not become ready within 90 seconds.'));},90000);
  child.once('error',()=>{clearTimeout(timer);reject(new Error('Could not start the existing JARVIS Python runtime.'));});
  child.once('exit',()=>{clearTimeout(timer);reject(new Error('JARVIS backend exited before startup completed.'));});
  child.stdout.on('data',data=>{buffer=(buffer+data.toString()).slice(-4096);const match=buffer.match(/JARVIS ready at (http:\/\/127\.0\.0\.1:\d+)/);if(match){clearTimeout(timer);resolve({origin:match[1],token});}});
 });
 function stop(){if(child.exitCode===null&&!child.killed)child.stdin.write('stop\n');}
 async function quit(){if(!child.pid||child.exitCode!==null||child.killed)return;await new Promise(resolve=>{const timer=setTimeout(()=>{child.kill();resolve();},4000);child.once('exit',()=>{clearTimeout(timer);resolve();});child.stdin.end('quit\n');});}
 return {child,ready,stop,quit};
}
module.exports={startBackend};
