const fs=require('node:fs');
const path=require('node:path');
const {createHash}=require('node:crypto');

// Watch application code, never databases, credentials, logs, or generated reports.
function snapshot(root){
 const result={};
 for(const folder of ['','static','desktop']){
  for(const entry of fs.readdirSync(path.join(root,folder),{withFileTypes:true})){
   if(!entry.isFile())continue;
   const name=entry.name;
   const included=folder==='static'?/\.(js|css|html|svg|png|jpg|webp)$/.test(name):folder==='desktop'?/\.(cjs|html|css)$/.test(name):(/\.py$/.test(name)&&!name.startsWith('test_'))||name==='requirements.txt'||name==='release-notes.json';
   if(included){const key=folder+'/'+name;result[key]=createHash('sha256').update(fs.readFileSync(path.join(root,folder,name))).digest('hex');}
  }
 }
 return result;
}
function classify(before,after){
 const changed=[...new Set([...Object.keys(before),...Object.keys(after)])].filter(k=>before[k]!==after[k]);
 if(!changed.length)return null;
 return {kind:changed.every(k=>k.startsWith('static/'))?'reload':'restart',revision:createHash('sha256').update(JSON.stringify(after)).digest('hex').slice(0,16)};
}
function watchUpdates(root,notify,{interval=2000,stableMs=20000}={}){
 let baseline=snapshot(root),candidate='',since=0,pending=null;
 const timer=setInterval(()=>{
  try{
   const next=snapshot(root),encoded=JSON.stringify(next);
   if(encoded!==candidate){candidate=encoded;since=Date.now();if(pending){pending=null;notify(null);}return;}
   if(Date.now()-since<stableMs)return;
   const update=classify(baseline,next);
   if(JSON.stringify(update)!==JSON.stringify(pending)){pending=update;notify(pending);}
  }catch{/* An editor may be replacing a file; retry once the source settles. */}
 },interval);
 timer.unref();
 return {get:()=>pending,validate:revision=>{const current=classify(baseline,snapshot(root));return !!pending&&pending.revision===revision&&current?.revision===revision;},acknowledge:()=>{baseline=snapshot(root);pending=null;candidate='';notify(null);},close:()=>clearInterval(timer)};
}
module.exports={snapshot,classify,watchUpdates};
