// What the Connectors panel says (static/connectors.js). The Core decides what is configured; these are only the
// words on screen, and they must never call a connector configured unless the Core's flag says so.
const assert=require('node:assert/strict');
const c=require('./static/connectors.js');
const [mail,calendar]=c.CARDS;
assert.equal(mail.service,'mail');assert.equal(calendar.service,'calendar');
assert.equal(c.stateText(null,mail),'Not known yet');
assert.equal(c.stateText({},mail),'Not configured');
assert.equal(c.stateText({mail_connected:true},mail),'Configured');
assert.equal(c.stateText({mail_connected:true},calendar),'Not configured','one flag never speaks for the other');
assert.equal(c.stateClass({calendar_connected:true},calendar),'ok');
assert.equal(c.stateClass({calendar_connected:false},calendar),'off');
assert.equal(c.stateClass(null,calendar),'off');
assert.equal(c.resultText(null),'');
assert.equal(c.resultText({status:'not_configured',detail:'Put the lines in the key file.'}),'NOT CONFIGURED: Put the lines in the key file.');
assert.ok(c.resultText({status:'passed',checked_at:1759800000,detail:'Signed in.'}).startsWith('OK at '));
assert.ok(c.resultText({status:'failed',detail:'Gmail refused the app password.'}).startsWith('FAILED: Gmail refused'));
for(const card of c.CARDS){assert.ok(card.what&&card.setup&&card.flag.endsWith('_connected'),card.service);assert.ok(!/@|password=|https?:/.test(card.what+card.setup),'no secrets in the words');}
console.log('connectors view: ok');
