const {test}=require('node:test');
const assert=require('node:assert/strict');
const path=require('node:path'),fs=require('node:fs'),os=require('node:os');
const {startBackend}=require('../backend.cjs');
test('one authenticated job captures the actual 13 panels with no external submission', {timeout:120000},async()=>{
 const dataDir=fs.mkdtempSync(path.join(os.tmpdir(),'jarvis-inspection-job-'));
 const backend=startBackend(path.resolve(__dirname,'../..'),{dataDir});
 try{
  const {origin,token}=await backend.ready;
  const page=await fetch(origin,{headers:{'X-Jarvis-Desktop':token}});
  const cookie=page.headers.get('set-cookie').split(';')[0];
  const post=async body=>{const response=await fetch(origin+'/api/interface-inspection',{method:'POST',headers:{'X-Jarvis-Desktop':token,Cookie:cookie,Origin:origin,'Content-Type':'application/json'},body:JSON.stringify(body)});assert.equal(response.status,200);return response.json();};
  const started=await post({operation:'start',request:{panel:'all',scope:'viewport'},transmit:false});
  assert.equal(started.panels.length,13);
  let result;
  const deadline=Date.now()+100000;
  do{await new Promise(r=>setTimeout(r,300));result=await post({operation:'status',job_id:started.job_id});}while(result.status==='running'&&Date.now()<deadline);
  assert.equal(result.status,'partial','Local-only capture must not claim visual analysis');
  assert.equal(result.results.length,13);
  for(const panel of result.results){
   assert.equal(panel.status,'captured',JSON.stringify({panel:panel.requested_panel,errors:panel.errors}));
   assert.equal(panel.verified_panel,panel.requested_panel);
   assert.equal(panel.stages.image_submitted,'not_attempted');
   assert.deepEqual(panel.isolation.side_effect_attempts,[]);
  }
  assert.equal(result.review_status,'combined_panel_reports');
 }finally{await backend.quit();}
});
