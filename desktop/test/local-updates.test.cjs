const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const {snapshot,classify,watchUpdates}=require('../local-updates.cjs');
test('classifies frontend and backend changes, ignores personal data',()=>{
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'jarvis-updates-'));
 try{
  for(const d of ['static','desktop','data'])fs.mkdirSync(path.join(root,d));
  fs.writeFileSync(path.join(root,'static','app.js'),'a');
  const before=snapshot(root);
  fs.writeFileSync(path.join(root,'.env'),'private');fs.writeFileSync(path.join(root,'desktop','preferences.json'),'{}');
  fs.writeFileSync(path.join(root,'data','notes.txt'),'personal');
  assert.deepEqual(snapshot(root),before);
  fs.writeFileSync(path.join(root,'static','app.js'),'b');
  assert.equal(classify(before,snapshot(root)).kind,'reload');
  fs.writeFileSync(path.join(root,'server.py'),'changed');
  assert.equal(classify(before,snapshot(root)).kind,'restart');
 }finally{fs.rmSync(root,{recursive:true,force:true});}
});
test('waits for stable files, rejects stale revisions and acknowledges only applied updates',async()=>{
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'jarvis-updates-'));
 let watcher;
 try{
  for(const d of ['static','desktop'])fs.mkdirSync(path.join(root,d));
  const file=path.join(root,'static','app.js');fs.writeFileSync(file,'a');
  watcher=watchUpdates(root,()=>{},{interval:10,stableMs:40});
  fs.writeFileSync(file,'b');
  const wait=ms=>new Promise(r=>setTimeout(r,ms));
  await wait(20);assert.equal(watcher.get(),null);
  for(let i=0;i<50&&!watcher.get();i++)await wait(10);
  const revision=watcher.get().revision;assert.ok(watcher.validate(revision));
  fs.writeFileSync(file,'c');assert.equal(watcher.validate(revision),false);
  await wait(20);assert.equal(watcher.get(),null);
  for(let i=0;i<50&&!watcher.get();i++)await wait(10);
  assert.notEqual(watcher.get().revision,revision);
  watcher.acknowledge();assert.equal(watcher.get(),null);
 }finally{watcher?.close();fs.rmSync(root,{recursive:true,force:true});}
});
