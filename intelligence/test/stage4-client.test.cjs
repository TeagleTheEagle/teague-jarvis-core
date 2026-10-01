'use strict';
const test=require('node:test');const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const client=require('../../stage4_client.cjs');
test('application result may contain finite timestamps without changing identity transcript parsing',()=>{
 assert.equal(client.parse(Buffer.from('{"time":0.25}'),true).time,.25);
 assert.throws(()=>client.parse(Buffer.from('{"created":0.25}')),/EXACT_INTEGER_REQUIRED/);
 assert.throws(()=>client.parse(Buffer.from('{"time":1e999}'),true),/EXACT_INTEGER_REQUIRED/);
 assert.equal(client.parse(Buffer.from('{"created":134335772813688018}'),true).created,134335772813688018n);
});
test('invalid namespace cannot initialize an Electron TEST profile',()=>{
 assert.throws(()=>client.validateTestRoot(path.resolve(__dirname,'../..')),/TEST_ROOT/);
});
test('Intelligence external renderer is inert without gated preload',()=>{
 const vm=require('node:vm');const source=fs.readFileSync(path.join(__dirname,'../stage4-renderer.js'),'utf8');
 vm.runInNewContext(source,{window:{},document:new Proxy({},{get(){throw Error('Legacy page touched');}})});
});
