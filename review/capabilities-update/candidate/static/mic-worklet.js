class JarvisMicrophone extends AudioWorkletProcessor {
  constructor(){super();this.samples=new Int16Array(5120);this.position=0;this.phase=0;this.sum=0;this.count=0;}
  process(inputs){
    const channel=inputs[0]?.[0];
    if(channel)for(const sample of channel){
      this.sum+=sample;this.count++;this.phase+=16000;
      if(this.phase>=sampleRate){
        this.phase-=sampleRate;
        const value=Math.max(-1,Math.min(1,this.sum/this.count));this.sum=0;this.count=0;
        this.samples[this.position++]=Math.round(value*(value<0?32768:32767));
        if(this.position===5120){this.port.postMessage(this.samples.buffer,[this.samples.buffer]);this.samples=new Int16Array(5120);this.position=0;}
      }
    }
    return true;
  }
}
registerProcessor('jarvis-microphone',JarvisMicrophone);
