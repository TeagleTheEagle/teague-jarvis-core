// Settings > About shows the running release (fix list item 4).
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const src=fs.readFileSync(__dirname+'/static/teague.js','utf8');
const start=src.indexOf('function releaseLabel(');assert.ok(start>0,'teague.js defines releaseLabel');
const ctx={};vm.createContext(ctx);vm.runInContext(src.slice(start,src.indexOf('\n',start)),ctx);
assert.equal(ctx.releaseLabel({installed_release:'1.0.12-0123456789ab',source_revision:'d6dfac6c1711497b'}),'Version 1.0.12-0123456789ab (installed)');
assert.equal(ctx.releaseLabel({installed_release:null,source_revision:'d6dfac6c1711497b'}),'Development copy, source revision d6dfac6c1711497b');
assert.equal(ctx.releaseLabel({installed_release:null}),'Development copy, source revision unknown');
assert.equal(ctx.releaseLabel(undefined),'Version not included in this view.');
// Wiring: the line sits in About and is rewritten only when the text changes (a rewrite every 1.5 s would clear a selection).
assert.match(src,/versionLine\.id='settingsVersion'/);
assert.match(src,/groups\.About\.append\([^;]*versionLine/);
assert.match(src,/versionText=releaseLabel\(d\.updates\);if\(version&&version\.textContent!==versionText\)version\.textContent=versionText;/);
console.log('PASS: Settings > About shows the installed release, the development revision, or says it is not in this view.');
