// What the Devices panel says (static/devices.js). The Core keeps the list; these are only the words on screen,
// and they must never call a device online, real or usable unless the Core's row says so.
const assert=require('node:assert/strict');
const d=require('./static/devices.js');
const now=2_000_000;
// State in words.
assert.equal(d.stateText({builtin:true,connected:true}),'Online');
assert.equal(d.stateText({connected:true}),'Online');
assert.equal(d.stateText({connected:false}),'Not connected');
assert.equal(d.stateText({connected:true,revoked:1}),'Revoked','a revoked device is never shown as online');
assert.equal(d.stateText({connected:true,simulated:true}),'Simulated test client, connected','a simulated client is never just "online"');
assert.equal(d.stateText({connected:false,simulated:true}),'Simulated test client, not connected');
assert.equal(d.stateText({connected:false,key_valid:false}),'Its key belongs to another installation: pair it again');
assert.equal(d.stateClass({connected:true}),'ok');
assert.equal(d.stateClass({connected:true,simulated:true}),'off','a simulated client is never marked as a working device');
assert.equal(d.stateClass({connected:true,revoked:1}),'warn');
assert.equal(d.stateClass({connected:false,key_valid:false}),'warn');
assert.equal(d.stateClass({connected:false}),'off');
// Last seen: only from a time the Core gave.
assert.equal(d.seenText({last_seen:now-10},now),'Last seen just now');
assert.equal(d.seenText({last_seen:now-600},now),'Last seen 10 minutes ago');
assert.equal(d.seenText({last_seen:now-7200},now),'Last seen 2 hours ago');
assert.equal(d.seenText({last_seen:now-3*86400},now),'Last seen 3 days ago');
assert.equal(d.seenText({last_seen:now+50},now),'Last seen just now','a clock that is a little ahead does not show a negative time');
assert.equal(d.seenText({last_seen:null},now),'');
assert.equal(d.seenText({},now),'');
assert.equal(d.seenText({builtin:true,last_seen:now},now),'');
// The pairing code's remaining time.
assert.equal(d.remainingText(now+300,now),'Good for 5:00');
assert.equal(d.remainingText(now+61,now),'Good for 1:01');
assert.equal(d.remainingText(now+9,now),'Good for 0:09');
assert.equal(d.remainingText(now,now),'This code has run out. Start again.');
assert.equal(d.remainingText(now-30,now),'This code has run out. Start again.');
// Every kind and capability the Core knows has words.
for(const kind of ['pc','phone','glasses','computer','other'])assert.ok(d.KINDS[kind],kind);
for(const capability of ['microphone','camera','speakers','display'])assert.ok(d.CAPABILITIES[capability],capability);
console.log('devices view: ok');
// 1.0.16: the private-network door and the "may save memories and tasks" tick, in words from the Core's own answer.
assert.equal(d.doorText({enabled:false,open:false,message:'Off. JARVIS listens only on this PC.'}),'Off. JARVIS listens only on this PC.');
assert.equal(d.doorText({enabled:true,open:false}),'On, but nothing is open.');
assert.equal(d.doorText({enabled:true,open:true}),'Open.');
assert.equal(d.doorText(null),'The private-network door is not available in this view.');
assert.equal(d.doorClass({enabled:true,open:true}),'ok');
assert.equal(d.doorClass({enabled:true,open:false}),'warn','a switch that is on with nothing open is a warning, never "online"');
assert.equal(d.doorClass({enabled:false,open:false}),'off');
assert.equal(d.doorClass(null),'off');
assert.equal(d.writesText({writes:true}),'May save memories and tasks');
assert.equal(d.writesText({writes:false}),'Reads only');
assert.equal(d.writesText({writes:true,revoked:1}),'Revoked: nothing','a revoked device may change nothing whatever its row once said');
assert.equal(d.WRITES_LABEL,'May save memories and tasks');
console.log('devices view (1.0.16): ok');
