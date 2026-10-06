// What the Routine panel says and which notices it shows as toasts (static/routine.js). The Core keeps the blocks
// and the notices; these are only the words on screen and the once-only rule for toasts.
const assert=require('node:assert/strict');
const r=require('./static/routine.js');
assert.deepEqual(r.DAYS,['MO','TU','WE','TH','FR','SA','SU']);
assert.equal(r.blockText({days:'MO,WE',start:'18:00',end:'19:00',label:'Gym'}),'Mon, Wed 18:00 to 19:00: Gym');
assert.equal(r.blockText({days:'SA',start:'09:00',end:'12:00',label:'School'}),'Sat 09:00 to 12:00: School');
const seen=new Set();
assert.deepEqual(r.fresh([{id:'a',kind:'nudge',text:'x'}],seen,true),[],'the first reading seeds the seen ids without toasts');
assert.deepEqual(r.fresh([{id:'a'},{id:'b',kind:'announce',text:'y'}],seen,false).map(n=>n.id),['b'],'only a notice not seen before');
assert.deepEqual(r.fresh([{id:'a'},{id:'b'}],seen,false),[],'never twice');
assert.deepEqual(r.fresh(null,seen,false),[]);
assert.equal(r.noticeText({kind:'nudge',text:'Gym runs till 19:00; "Essay" is due at 19:30.'}),'Nudge: Gym runs till 19:00; "Essay" is due at 19:30.');
assert.equal(r.noticeText({kind:'announce',text:'Ben, Jack texted you: late'}),'Ben, Jack texted you: late');
assert.equal(r.noticeText({kind:'approval',text:'Waiting for your approval: Set a timer'}),'Approval: Waiting for your approval: Set a timer');
assert.equal(r.noticeText({kind:'system',text:'Backup done'}),'JARVIS: Backup done');
assert.equal(r.toastable({kind:'approval',text:'Waiting for your approval: Set a timer'}),false,'the approval card is already on the screen');
assert.equal(r.toastable({kind:'nudge',text:'x'}),true);
assert.equal(r.toastable(null),false);
console.log('routine view: ok');
