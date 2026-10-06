// What the Music panel says (static/music.js). The Core plays and decides; these are only the words on screen.
const assert=require('node:assert/strict');
const m=require('./static/music.js');
assert.equal(m.nowText(null),'Nothing is playing.');
assert.equal(m.nowText({state:'nothing'}),'Nothing is playing.');
assert.equal(m.nowText({state:'playing',title:'Shoot to Thrill',nickname:'workshop warrior'}),'Playing: Shoot to Thrill (workshop warrior)');
assert.equal(m.nowText({state:'paused',title:'Shoot to Thrill',nickname:null}),'Paused: Shoot to Thrill');
assert.equal(m.timeText(0),'0:00');
assert.equal(m.timeText(65000),'1:05');
assert.equal(m.timeText(null),'');
assert.equal(m.timeText(-5),'');
assert.equal(m.filesText(0),'No music files yet.');
assert.equal(m.filesText(1),'1 music file.');
assert.equal(m.filesText(7),'7 music files.');
assert.equal(m.volumeText(80),'Volume 80%');
assert.equal(m.rowText({present:true,title:'Shoot to Thrill',file:'Shoot to Thrill.mp3'}),'Shoot to Thrill');
assert.equal(m.rowText({present:false,title:'Gone',file:'Gone.mp3'}),'Gone.mp3 (file not in the folder)','a missing file is said, never shown as playable');
console.log('music view: ok');
