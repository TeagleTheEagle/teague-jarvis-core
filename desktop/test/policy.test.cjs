const {test}=require('node:test'),assert=require('node:assert/strict');
const {trusted,external}=require('../policy.cjs');
test('strict origin matching',()=>{const o='http://127.0.0.1:8765';assert.ok(trusted(o+'/api/chat',o));for(const u of ['http://127.0.0.1:8766/','http://127.0.0.1.evil.test:8765','file:///tmp/x','https://example.com','garbage'])assert.equal(trusted(u,o),false);});
test('external links reject executable and credential-bearing URLs',()=>{assert.ok(external('https://example.com/page'));for(const u of ['javascript:alert(1)','file:///C:/Windows','ms-settings:','https://user:pass@example.com'])assert.equal(external(u),false);});
