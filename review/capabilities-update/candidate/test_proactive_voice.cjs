const assert=require('node:assert/strict'),Voice=require('./static/voice.js');
const v=new Voice({status(){},wake(){}});
assert.equal(v.inviteConversation(),false,'never enables muted microphone');
v.active=true;assert.equal(v.inviteConversation(),true);v.resume();assert.equal(v.armed,true,'can answer without wake word');
v.endConversation();assert.equal(v.inviteConversation(),false);v.resume();assert.equal(v.armed,false,'end phrase prevents reopening');
v.arm();assert.equal(v.endedByUser,false,'new explicit wake reopens');
v.endConversation();assert.equal(v.inviteConversation(true),true,'new sharing session can invite again');
console.log('PASS: invited conversation, muted microphone, end phrase latch and explicit restart.');
