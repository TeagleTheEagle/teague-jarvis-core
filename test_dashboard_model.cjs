// What the dashboard may claim (static/dashboard-model.js): unknown instead of stale or guessed values, and
// "configured" only for what is really set up.
const assert=require('node:assert/strict');
const m=require('./static/dashboard-model.js');
const now=1e12,fresh={connected:true,hasData:true,busy:false,stateAt:now-4000,heartbeatAt:0,now};
// Connection states.
assert.equal(m.link({now}),'connecting');
assert.equal(m.link({...fresh}),'online');
assert.equal(m.link({...fresh,connected:false}),'lost');
assert.equal(m.link({...fresh,stateAt:now-60000}),'checking','nothing heard for a minute is not "online"');
assert.equal(m.link({...fresh,stateAt:now-60000,heartbeatAt:now-2000}),'online','the dashboard readings count as hearing from the Core');
assert.equal(m.link({...fresh,stateAt:now-60000,busy:true}),'online','a reply that is arriving is the Core answering');
assert.equal(m.link({...fresh,inspection:true}),'snapshot');
assert.equal(m.link({...fresh,connected:false,busy:true}),'lost','a failed request wins over everything else');
// While not connected, every Core value is unknown; only the Core row says why.
for(const state of ['connecting','checking','lost']){
  const rows=m.systems(state,{capabilities:{brain:'OpenRouter configured',search:'OpenRouter web search',fish:true,voice_provider:'fish'},memory:[1,2],devices:[{device_id:'pc',connected:true}]});
  assert.deepEqual(rows.slice(1).map(r=>r[2]),['UNKNOWN','UNKNOWN','UNKNOWN','UNKNOWN','UNKNOWN'],state);
  assert.equal(m.summary(state,rows).counted,false);assert.equal(m.devices(state,{devices:[{device_id:'pc',connected:true}]})[0].text,'Unknown');
}
assert.deepEqual(m.systems('lost',{})[0],['Core','warn','OFFLINE']);assert.equal(m.summary('lost',m.systems('lost',{})).text,'CORE OFFLINE');
assert.deepEqual(m.systems('connecting',null)[0],['Core','off','CONNECTING']);
// A fully set up Core.
const full={capabilities:{brain:'OpenRouter configured',model:'qwen/qwen3.8-max-0902',search:'SerpApi configured',fish:true,voice_provider:'fish'},
  settings:{voice_profile:'auto'},memory:[{},{}],devices:[{device_id:'pc',connected:true},{device_id:'mock-glasses',connected:true,simulated:true}]};
let rows=m.systems('online',full);
assert.deepEqual(rows,[['Core','ok','ONLINE'],['AI','ok','OPENROUTER'],['Memory','ok','2 SAVED'],['Voice','ok','FISH AUDIO'],['Search','ok','SERPAPI'],['Devices','ok','1 ONLINE']]);
assert.deepEqual(m.summary('online',rows),{ready:6,total:6,counted:true,warn:false,text:'ALL CONFIGURED'});
// OpenRouter (docs/VERONICA-MERGE-PLAN.md): its brain and its web search are named as such, and both count as configured.
rows=m.systems('online',{capabilities:{brain:'OpenRouter configured',search:'OpenRouter web search',fish:true,voice_provider:'fish'},
  settings:{voice_profile:'auto'},memory:[],devices:[{device_id:'pc',connected:true}]});
assert.deepEqual(rows.map(r=>r[1]+':'+r[2]),['ok:ONLINE','ok:OPENROUTER','ok:0 SAVED','ok:FISH AUDIO','ok:OPENROUTER','ok:1 ONLINE']);
assert.equal(m.summary('online',rows).text,'ALL CONFIGURED');
// Configured is checked, not assumed: no key, a chosen voice that is not set up, search without a key.
rows=m.systems('online',{capabilities:{brain:'OpenRouter not configured',search:'DuckDuckGo best effort',fish:false,voice_provider:'browser'},
  settings:{voice_profile:'fish'},memory:[],devices:[{device_id:'pc',connected:true}]});
assert.deepEqual(rows.map(r=>r[1]+':'+r[2]),['ok:ONLINE','warn:NO KEY','ok:0 SAVED','warn:FISH NOT SET UP','basic:BEST EFFORT','ok:1 ONLINE']);
assert.deepEqual(m.summary('online',rows),{ready:3,total:6,counted:true,warn:true,text:'3 OF 6 CONFIGURED'});
assert.equal(m.systems('online',{capabilities:{brain:'Unsupported provider groq: use openrouter'}})[1][2],'CHECK SETTING');
// The OpenAI and Qwen voices are removed (owner, 2026-10-13). The Core reads an old saved choice as "auto" (store.py);
// should one still arrive, it is shown as unknown, never as a voice that is set up.
for(const old of ['openai','qwen']){
  rows=m.systems('online',{capabilities:{brain:'OpenRouter configured',fish:true,openai_voice:true,qwen_voice:true,voice_provider:'fish'},settings:{voice_profile:old}});
  assert.deepEqual(rows[3],['Voice','off','UNKNOWN'],old);
}
// Without Fish Audio the browser's own voice speaks.
rows=m.systems('online',{capabilities:{brain:'OpenRouter configured',fish:false,voice_provider:'browser'},settings:{voice_profile:'auto'}});
assert.deepEqual(rows[3],['Voice','ok','BROWSER VOICE']);
// The inspection picture carries no capabilities and no device list: nothing may be invented from that.
rows=m.systems('snapshot',{capabilities:{},settings:{voice_profile:'auto'},memory:[{}]});
assert.deepEqual(rows.map(r=>r[2]),['SNAPSHOT','UNKNOWN','1 SAVED','UNKNOWN','UNKNOWN','UNKNOWN']);
assert.equal(rows.some(r=>r[1]==='warn'),false,'an inspection picture must not report a missing key');
assert.deepEqual(m.summary('snapshot',rows),{ready:1,total:6,counted:false,warn:false,text:'SNAPSHOT'});
assert.deepEqual(m.devices('snapshot',{}).map(d=>d.text),['Unknown','Unknown','Unknown']);
// Devices: simulated is said before online or offline, and is never counted.
const places=m.devices('online',{devices:[{device_id:'pc',connected:true},{device_id:'mock-glasses',connected:false,simulated:true},{device_id:'iphone',connected:false}]});
assert.deepEqual(places.map(p=>p.state+':'+p.text),['ok:Online','offline:Offline','simulated:Simulated only']);
assert.equal(m.devices('online',{devices:[]})[1].text,'Not paired');
assert.equal(m.systems('online',{devices:[{device_id:'mock-glasses',connected:true,simulated:true}]})[5][2],'0 ONLINE');
// Paired devices (1.0.15) are found by what they are, not by a word in their id. A place shows its best device:
// a real connected one before a real one before the simulated test client; a revoked one is not shown.
const pc={device_id:'pc',kind:'pc',builtin:true,connected:true,simulated:false};
const testClient={device_id:'local-wearable-client',kind:'glasses',connected:true,simulated:true};
const phone={device_id:'a1b2c3d4e5f60718',kind:'phone',name:'My phone',connected:true,simulated:false};
const show=list=>m.devices('online',{devices:list}).map(p=>p.state+':'+p.text);
assert.deepEqual(show([pc,testClient,phone]),['ok:Online','ok:Online','simulated:Simulated only']);
assert.deepEqual(show([pc,{...phone,connected:false}]),['ok:Online','offline:Offline','none:Not paired']);
assert.deepEqual(show([pc,{...phone,connected:false,revoked:1790000000}]),['ok:Online','none:Not paired','none:Not paired'],'a revoked device is not a paired device');
const halo={device_id:'0f0e0d0c0b0a0908',kind:'glasses',name:'Halo',connected:false,simulated:false};
assert.deepEqual(show([pc,testClient,halo])[2],'offline:Offline','a real pair of glasses is shown before the test client');
assert.deepEqual(show([pc,testClient,{...halo,connected:true}])[2],'ok:Online');
assert.deepEqual(show([pc,{...phone,connected:false},{...phone,device_id:'ffff',connected:true}])[1],'ok:Online','the connected phone of two');
assert.equal(m.systems('online',{devices:[pc,testClient,phone,{...halo,revoked:1}]})[5][2],'2 ONLINE');
// Voice line.
assert.equal(m.voiceLine({micOn:false}),'Microphone off. Press F4 to turn it on.');
assert.equal(m.voiceLine({micOn:true,armed:true,manual:true}),'Listening while you hold to talk.');
assert.equal(m.voiceLine({micOn:true,armed:true}),'Listening.');
assert.equal(m.voiceLine({micOn:true,suspended:true}),'Microphone paused while JARVIS replies.');
assert.equal(m.voiceLine({micOn:true,wakeEnabled:false}),'Microphone on, without the wake word.');
assert.equal(m.voiceLine({micOn:true,wakeEnabled:true}),'Say "Hey Jarvis", then your request.');
// The emergency stop: said only while the Core is heard from and says so; never guessed.
assert.equal(m.stopped('online',{control:{stopped:true}}),true);
assert.equal(m.stopped('online',{control:{stopped:false}}),false);
assert.equal(m.stopped('online',{}),false);assert.equal(m.stopped('online',null),false);
for(const state of ['connecting','checking','lost','snapshot'])assert.equal(m.stopped(state,{control:{stopped:true}}),false,state);
console.log('Dashboard model checks passed.');
