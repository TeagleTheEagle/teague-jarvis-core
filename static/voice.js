 'use strict';
// Local continuous wake detection and PCM transcription. Audio stays in memory.
class JarvisVoice {
  constructor(callbacks){this.cb=callbacks;this.generation=0;this.active=false;this.armed=false;this.frames=[];this.pre=[];this.queue=[];this.epoch=0;}
  async start(deviceId='',options={}){
    this.stop();const generation=this.generation;let stream,context;
    this.deviceId=deviceId;this.startOptions={wake:options.wake!==false};
    if(!options.recovery)this.recoveryAttempts=0;
    try{
      stream=await navigator.mediaDevices.getUserMedia({audio:{...(deviceId?{deviceId:{exact:deviceId}}:{}),echoCancellation:true,noiseSuppression:true,autoGainControl:true},video:false});
      if(generation!==this.generation){stream.getTracks().forEach(t=>t.stop());return;}
      this.stream=stream;this.cb.status('PREPARING LOCAL WAKE DETECTOR…');
      this.wakeEnabled=options.wake!==false;
      if(this.wakeEnabled)await this.cb.prepare?.();
      if(generation!==this.generation){stream.getTracks().forEach(t=>t.stop());return;}
      context=new AudioContext();this.context=context;await context.audioWorklet.addModule('/mic-worklet.js');
      if(generation!==this.generation){stream.getTracks().forEach(t=>t.stop());await context.close().catch(()=>{});return;}
      this.node=new AudioWorkletNode(context,'jarvis-microphone');this.source=context.createMediaStreamSource(stream);this.source.connect(this.node);this.node.connect(context.destination);
      this.client=crypto.randomUUID();this.active=true;this.pending=false;this.processing=false;this.suspended=false;this.lastFrame=Date.now();
      this.node.port.onmessage=e=>this.frame(new Int16Array(e.data),generation);
      stream.getAudioTracks()[0].onended=()=>{if(generation===this.generation)void this.recover();};
      this.watch=setInterval(()=>{if(this.active&&Date.now()-this.lastFrame>4000)void this.recover();},1000);
      await context.resume();this.cb.status(this.wakeEnabled?'STARTING LOCAL WAKE DETECTOR…':'PUSH TO TALK READY');
    }catch(e){stream?.getTracks().forEach(t=>t.stop());context?.close().catch(()=>{});if(generation===this.generation){this.stop();throw e;}}
  }
  stop(){this.generation++;this.epoch++;this.active=false;this.session=false;this.armed=false;this.frames=[];this.pre=[];this.queue=[];clearInterval(this.watch);this.node?.disconnect();this.source?.disconnect();this.stream?.getTracks().forEach(t=>t.stop());this.context?.close().catch(()=>{});}
  fail(e){this.stop();this.cb.error(e);}
  async recover(){
    if(!this.active||this.recovering)return;
    if((this.recoveryAttempts||0)>=3){this.fail(new Error('Microphone recovery failed repeatedly. Check the selected input and enable it again.'));return;}
    this.recovering=true;this.recoveryAttempts=(this.recoveryAttempts||0)+1;
    const device=this.deviceId,options={...this.startOptions,recovery:true};
    this.cb.status('RECONNECTING MICROPHONE…');
    this.cb.diagnostic?.('Microphone','Audio stopped; reconnecting selected input');
    try{await this.start(device,options);if(this.active&&this.cb.canInterrupt?.())this.pause();}
    catch(e){this.cb.error(e);}
    finally{this.recovering=false;}
  }
  pause(){this.bargeFrames=[];this.bargeVoiced=0;this.suspended=true;this.epoch++;this.queue=[];this.pre=[];}
  resume(){this.suspended=false;this.queue=[];this.continueListening();}
  continueListening(){if(!this.active||!this.session||this.processing||this.suspended||this.armed)return;this.armed=true;this.manual=false;this.frames=[];this.pre=[];this.elapsed=this.quiet=this.voiced=0;this.cb.status('CONVERSATION OPEN · SAY “THANK YOU JARVIS” TO FINISH');}
  inviteConversation(explicitStart=false){if(!this.active||(!explicitStart&&this.endedByUser))return false;if(explicitStart)this.endedByUser=false;this.session=true;this.nudged=false;return true;}
  endConversation(){this.endedByUser=true;this.session=false;this.armed=false;this.manual=false;this.frames=[];this.pre=[];this.queue=[];this.epoch++;this.cb.status('SAY “HEY JARVIS”');}
  static isEndPhrase(text){const words=text.toLowerCase().replace(/[^a-z\s]/g,' ').replace(/\s+/g,' ').trim();return /^(?:(?:all right|alright|okay|ok) )?thank you (?:jarvis|travis|jeremy)$/.test(words);}
  arm(manual=false){if(!this.active||this.armed||this.processing)return;this.epoch++;this.queue=[];this.suspended=false;this.endedByUser=false;this.session=true;this.nudged=false;this.manual=manual;this.armed=true;this.frames=manual?[]:this.pre.slice();this.elapsed=this.quiet=this.voiced=0;this.cb.wake();this.cb.status('LISTENING · SPEAK YOUR COMMAND');}
  async finish(){if(!this.armed)return;const generation=this.generation,frames=this.frames;this.armed=false;this.frames=[];this.pre=[];this.processing=true;this.cb.timing?.('speech_ended',this.lastVoicedAt);this.cb.status('TRANSCRIBING LOCALLY…');
    try{if(frames.length)await this.cb.command(new Blob(frames,{type:'application/octet-stream'}),generation);}
    catch(e){if(generation===this.generation)this.cb.error(e);}
    finally{if(generation===this.generation){this.processing=false;this.continueListening();if(!this.session)this.cb.status('SAY “HEY JARVIS”');}}
  }
  frame(pcm,generation){
    if(!this.active||generation!==this.generation)return;this.lastFrame=Date.now();
    this.cb.level?.(Math.sqrt(pcm.reduce((sum,v)=>sum+v*v,0)/pcm.length)/32768);
    if(this.processing)return;
    if(this.suspended){
      // While JARVIS works on an answer and plays nothing, the wake word still counts: "Hey JARVIS" interrupts
      // the answer and listens, so a spoken "emergency stop" is heard then too. Never while a reply is being
      // spoken (it would hear itself); there the barge-in below applies.
      if(this.wakeEnabled!==false&&this.cb.thinking?.()){this.bargeFrames=[];this.bargeVoiced=0;this.listenForWake(pcm,generation,true);return;}
      // Headset barge-in: sustained microphone energy after browser echo cancellation.
      // No wake requests or transcription are sent for the playback monitoring frames.
      if(!this.session||!this.cb.canInterrupt?.()){this.bargeFrames=[];this.bargeVoiced=0;return;}
      this.bargeFrames=this.bargeFrames||[];this.bargeFrames.push(pcm);if(this.bargeFrames.length>4)this.bargeFrames.shift();
      const rms=Math.sqrt(pcm.reduce((sum,v)=>sum+v*v,0)/pcm.length)/32768;
      const threshold=this.cb.interruptThreshold?.()||.012;
      this.cb.interruptLevel?.(rms,threshold);
      this.bargeVoiced=rms>threshold?(this.bargeVoiced||0)+pcm.length/16000:0;
      if(this.bargeVoiced>=.64){
        this.cb.diagnostic?.('Interruption','Sustained microphone energy detected; stopping reply');
        const captured=this.bargeFrames.slice();this.bargeFrames=[];this.bargeVoiced=0;
        this.armed=false;this.pre=captured;this.arm(false);
        this.voiced=.64;this.elapsed=captured.reduce((n,f)=>n+f.length/16000,0);
        this.cb.status('INTERRUPTED · LISTENING TO YOU');
      }
      return;
    }
    if(this.armed){this.frames.push(pcm);const rms=Math.sqrt(pcm.reduce((s,v)=>s+v*v,0)/pcm.length)/32768;
      if(rms>.015){if(!this.voiced)this.cb.timing?.('speech_started',performance.now());this.lastVoicedAt=performance.now();this.voiced+=.32;this.quiet=0;this.nudged=false;}else this.quiet+=.32;
      if(this.voiced>0||this.manual)this.elapsed+=.32;else if(this.frames.length>4)this.frames.shift();
      if(this.elapsed>=28||(!this.manual&&this.voiced>=.32&&this.quiet>=(this.cb.endpointSeconds?.()||1.28)))this.finish();
      else if(!this.manual&&this.voiced===0&&this.quiet>=12&&!this.nudged){this.nudged=true;this.armed=false;this.frames=[];this.pre=[];this.cb.idle?.();}return;}
    if(this.wakeEnabled===false)return;
    this.listenForWake(pcm,generation,false);
  }
  // working: JARVIS is busy with an answer. The Core may answer the wake requests late then, so frames that
  // cannot be looked at in time are dropped instead of switching the microphone off.
  listenForWake(pcm,generation,working){
    this.pre.push(pcm);if(this.pre.length>4)this.pre.shift();
    if(this.queue.length>=6){if(!working){this.fail(new Error('Wake detection fell behind. Enable the microphone again.'));return;}this.queue.shift();}
    this.queue.push(pcm);this.drain(generation);
  }
  async drain(generation){if(this.pending)return;this.pending=true;
    try{while(this.queue.length&&this.active&&generation===this.generation){const epoch=this.epoch;let data;
      try{data=await this.cb.detect(this.queue.shift(),this.client);}
      catch(e){
        // A request from an earlier listening state must not stop the current one.
        if(generation!==this.generation)return;
        if(epoch!==this.epoch||this.suspended)continue;
        throw e;
      }
      if(generation!==this.generation)return;if(epoch!==this.epoch)continue;
      if(data.detected){this.cb.diagnostic?.('Wake word','Detected');if(this.suspended)this.armed=false;this.arm();}else if(!this.armed&&!this.suspended)this.cb.status('SAY “HEY JARVIS”');}}
    catch(e){if(generation===this.generation)this.fail(e);}
    finally{if(generation===this.generation)this.pending=false;}
  }
  static wav(frames){
    const count=frames.reduce((n,f)=>n+f.length,0),buffer=new ArrayBuffer(44+count*2),view=new DataView(buffer);
    const text=(offset,s)=>[...s].forEach((c,i)=>view.setUint8(offset+i,c.charCodeAt(0)));
    text(0,'RIFF');view.setUint32(4,36+count*2,true);text(8,'WAVE');text(12,'fmt ');view.setUint32(16,16,true);view.setUint16(20,1,true);view.setUint16(22,1,true);view.setUint32(24,16000,true);view.setUint32(28,32000,true);view.setUint16(32,2,true);view.setUint16(34,16,true);text(36,'data');view.setUint32(40,count*2,true);
    let offset=44;for(const frame of frames)for(const n of frame){view.setInt16(offset,n,true);offset+=2;}
    return new Blob([buffer],{type:'audio/wav'});
  }
}
if(typeof module!=='undefined')module.exports=JarvisVoice;
