const assert=require('node:assert/strict');
const Queue=require('./static/voice-lab.js');
const tick=()=>new Promise(r=>setImmediate(r));
(async()=>{
  const seen=[],results=[];let release;
  const q=new Queue(async x=>{seen.push(x);if(x===1)await new Promise(r=>release=r);return x;},x=>results.push(x),e=>{throw e;});
  q.push(1);q.push(2);q.push(3);assert.deepEqual(seen,[1]);release();await tick();assert.deepEqual(seen,[1,2,3]);assert.deepEqual(results,[1,2,3]);
  let resolve,called=false;
  const cancelled=new Queue(()=>new Promise(r=>resolve=r),()=>called=true,()=>{});
  cancelled.push(1);cancelled.close();resolve(1);await tick();assert.equal(called,false);
  let error='';const overloaded=new Queue(()=>new Promise(()=>{}),()=>{},e=>error=e.message);
  for(let i=0;i<8;i++)overloaded.push(i);
  assert.match(error,/fell behind/);assert.equal(overloaded.queue.length,0);
  console.log('Voice lab: ordered audio, cancellation and overload checks passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
