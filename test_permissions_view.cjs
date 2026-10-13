// What the interface says about permissions and the emergency stop (static/permissions.js). The Core decides;
// these are only the words on screen, so they must not say more than the Core's rows say.
const assert=require('node:assert/strict');
const p=require('./static/permissions.js');
// The stop words: the whole message only.
for(const text of ['Emergency stop','JARVIS, emergency stop','hey jarvis stop everything now','Stop all.','kill switch'])assert.equal(p.stopPhrase(text),true,text);
for(const text of ['stop','stop speaking','stop the timer','what is an emergency stop?','resume','',null,undefined,'x'.repeat(200)])assert.equal(p.stopPhrase(text),false,String(text));
// Capitals and punctuation do not matter: speech recognition adds its own.
for(const text of ['Emergency stop?','Emergency, stop.','Hey, Jarvis, emergency stop.','EMERGENCY STOP!!!'])assert.equal(p.stopPhrase(text),true,text);
for(const text of ["don't stop everything",'stop all timers','non-emergency stop','?!'])assert.equal(p.stopPhrase(text),false,text);
// The commands the window answers by itself obey the emergency stop and the owner's switches (the Core's state).
assert.equal(p.windowMay(null,'navigate_panel'),true);                                  // before the first state
assert.equal(p.windowMay({control:{stopped:false},permissions:{}},'navigate_panel'),true);
assert.equal(p.windowMay({control:{stopped:false}},'navigate_panel'),true);            // an older Core sends no switches
assert.equal(p.windowMay({control:{stopped:false},permissions:{navigate_panel:'off'}},'navigate_panel'),false);
assert.equal(p.windowMay({control:{stopped:false},permissions:{inspect_interface:'ask'}},'inspect_interface'),false);
assert.equal(p.windowMay({control:{stopped:false},permissions:{navigate_panel:'off'}},'assistant_control'),true);
assert.equal(p.windowMay({control:{stopped:true},permissions:{}},'navigate_panel'),false);  // stopped: nothing
assert.equal(p.windowMay({control:{stopped:true}}),false);
assert.equal(p.windowMay({control:{stopped:false},permissions:{navigate_panel:'off'}}),true);  // no tool: only the stop counts
// One switch position in words.
const change={label:'Set a timer',effect:'changes',asks:'no',mode:'default',modes:['default','ask','off']};
assert.deepEqual(change.modes.map(m=>p.modeText(change,m)),['Allowed','Ask first','Off']);
const self={label:'Propose a change',effect:'changes',asks:'always',mode:'default',modes:['default','off']};
assert.deepEqual(self.modes.map(m=>p.modeText(self,m)),['Always asks','Off']);
const words={label:'Change a saved fact',effect:'changes',asks:'your own words',mode:'default',modes:['default','off']};
assert.equal(p.modeText(words,'default'),'On your words only');
const read={label:'Search the web',effect:'reads',asks:'no',mode:'default',modes:['default','off']};
assert.equal(p.modeText(read,'default'),'Allowed');
// What a row says about asking: never "does not ask" for a tool that asks, and nothing at all for a read.
assert.equal(p.asksText(change),'Does not ask first.');
assert.equal(p.asksText({...change,mode:'ask'}),'Asks you on screen first (your switch).');
assert.equal(p.asksText({...change,mode:'ask',shipped:'ask'}),'Asks you on screen first (as shipped; set it to Allowed for a mission to run commands unattended).','the workshop commands ship as ask first (docs/WORKSHOP.md)');
assert.equal(p.asksText({...change,mode:'off'}),'Off: JARVIS cannot do this when answering.');
assert.equal(p.asksText(self),'Always asks you on screen first.');
assert.equal(p.asksText(words),'Only when your own words ask for exactly this.');
assert.equal(p.asksText(read),'');
assert.equal(p.asksText({...read,mode:'off'}),'Off: JARVIS cannot do this when answering.');
// The banner line: nothing while running or unknown; when and where once stopped.
const now=new Date(2026,9,6,15,30);
assert.equal(p.stopText(null,now),'');assert.equal(p.stopText({stopped:false},now),'');
const today=p.stopText({stopped:true,since:new Date(2026,9,6,14,2).getTime()/1000,device:'pc',saved:true},now);
assert.match(today,/^JARVIS answers nothing and does nothing until you resume\. Stopped at .*02.* on this PC\.$/);
const earlier=p.stopText({stopped:true,since:new Date(2026,9,5,23,59).getTime()/1000,device:'local-wearable-client'},now);
assert.match(earlier,/Stopped on .* at .*59.* from local wearable client\.$/);
// A paired device is named by the name the owner gave it, when the Core sends one.
assert.match(p.stopText({stopped:true,since:new Date(2026,9,6,14,2).getTime()/1000,device:'a1b2c3d4e5f60718',device_name:'My phone'},now),/ from My phone\.$/);
// A stop record that could not be read has no time: say only what is known.
assert.equal(p.stopText({stopped:true,since:null,device:null},now),'JARVIS answers nothing and does nothing until you resume.');
assert.match(p.stopText({stopped:true,since:now.getTime()/1000,device:'pc',saved:false},now),/could not be saved to disk: it holds until JARVIS is restarted\.$/);
assert.equal(p.lockdownText(null),'');
assert.match(p.lockdownText({lockdown:true,switches:[]}),/^LOCKDOWN IS ON: every action asks you first/);
assert.match(p.lockdownText({lockdown:false,switches:[]}),/^No lockdown\./);
console.log('permissions view: ok');
