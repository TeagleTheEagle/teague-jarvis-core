'use strict';
// Isolated in-memory observation instrumentation; source files remain untouched.
const fs=require('node:fs'),path=require('node:path'),Module=require('node:module');
const original=path.resolve(__dirname,'../stage4_client.cjs');
let source=fs.readFileSync(original,'utf8');
const anchor="  if(command.action==='snapshot'){";
if(source.split(anchor).length!==2)throw Error('DIAGNOSTIC_SOURCE_MISMATCH');
const observe=`
  if(command.action==='diagnose-render'){
   const samples=[];
   for(const delay of [0,250,1000]){
    await new Promise(r=>setTimeout(r,delay));
    const result=await win.webContents.executeJavaScript("(()=>{const e=document.getElementById('test-fallback-result');const out=document.querySelector('#messages,.execution .empty');const info=n=>{if(!n)return null;const s=getComputedStyle(n),r=n.getBoundingClientRect();return {tag:n.tagName,id:n.id,textLength:n.textContent.length,display:s.display,visibility:s.visibility,opacity:s.opacity,position:s.position,zIndex:s.zIndex,rect:{x:r.x,y:r.y,width:r.width,height:r.height},topAtCenter:document.elementFromPoint(Math.max(0,Math.min(innerWidth-1,r.x+r.width/2)),Math.max(0,Math.min(innerHeight-1,r.y+r.height/2)))?.tagName};};return {at:performance.now(),ready:document.readyState,viewport:[innerWidth,innerHeight],scroll:[scrollX,scrollY],result:info(e),output:info(out),body:info(document.body),overlay:{position:getComputedStyle(document.body,'::before').position,zIndex:getComputedStyle(document.body,'::before').zIndex,background:getComputedStyle(document.body,'::before').backgroundColor},resultText:e?.textContent||null};})()");
    samples.push({delay,result});
   }
   emit({event:'diagnose-render',samples});return;
  }
`;
source=source.replace(anchor,observe+anchor);
const compiled=new Module(original,module);compiled.filename=original;compiled.paths=Module._nodeModulePaths(path.dirname(original));
compiled._compile(source,original);compiled.exports.launchTestClient('teague');
