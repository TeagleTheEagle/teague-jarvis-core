const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const src=fs.readFileSync(__dirname+'/static/app.js','utf8'),ctx={};vm.createContext(ctx);vm.runInContext(src.slice(src.indexOf('function screenIntent('),src.indexOf('async function send(')),ctx);
for(const text of ['start screenshare','Jarvis start screen share','start screen sharing','Open Screen Vision','Can you open screen vision','show me screen vision'])assert.equal(ctx.screenIntent(text),'start');
for(const text of ['What can you see?','Can you see my screen?','Analyse this screen'])assert.equal(ctx.screenIntent(text),'analyse');
assert.equal(ctx.screenIntent('Take a screenshot Jarvis'),'capture');assert.equal(ctx.screenIntent('stop sharing Jarvis'),'stop');assert.equal(ctx.screenIntent('Tell me a story'),null);
console.log('PASS: screen session voice intent and unrelated conversation.');
