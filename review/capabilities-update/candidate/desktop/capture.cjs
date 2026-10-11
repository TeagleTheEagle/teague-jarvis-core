'use strict';
// Session-only capture authority. No source, image, or consent is persisted.
class ScreenCapture {
 constructor(io){this.io=io;this.generation=0;this.source=null;this.busy=false;}
 stop(){this.generation++;this.source=null;}
 async authorise(){
  if(this.busy)throw new Error('A screen operation is already in progress.');
  this.stop();const generation=this.generation;this.busy=true;
  try{const displays=this.io.displays();const choice=await this.io.choose(displays);
   if(generation!==this.generation)return {authorised:false};
   const selected=displays.find(d=>d.id===choice);
   if(!selected)return {authorised:false};
   if(!this.io.displays().some(d=>d.id===selected.id&&d.signature===selected.signature))throw new Error('Displays changed. Choose again.');
   this.source=selected;return {authorised:true,label:selected.label};
  }finally{this.busy=false;}
 }
 async capture(){
  if(this.busy)throw new Error('A screen operation is already in progress.');
  if(!this.source)throw new Error('Authorise a display in Screen Vision first.');
  const generation=this.generation,source=this.source;
  if(!this.io.displays().some(d=>d.id===source.id&&d.signature===source.signature)){this.stop();throw new Error('The authorised display changed. Choose again.');}
  this.busy=true;
  try{const shot=await this.io.capture(source.id);
   if(generation!==this.generation)throw new Error('Screenshot cancelled.');
   if(!shot?.data)throw new Error('No screenshot was returned.');
   return {...shot,label:source.label,capturedAt:new Date().toISOString()};
  }finally{this.busy=false;}
 }
}
module.exports={ScreenCapture};
