using System;using System.IO;using System.Collections.Generic;
public static class WriterFaults {
 public static string Run(string parent){var results=new List<string>();foreach(int fault in new[]{0,1,2,3,4,5,6}){
  string root=Path.Combine(parent,"fault-"+fault+"-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(root);var s=new AuthoritativeEvents(root,segmentBytes:8192,fault:fault,batch:128);int admitted=0;
  for(int i=0;i<100;i++){if(!s.Publish("test","ordered","{\"i\":"+i+",\"pad\":\""+new string('x',100)+"\"}",null))break;admitted++;}s.Finish(0,0);
  bool first=(fault==0?s.Failure==null:s.Failure!=null);bool reject=!s.Publish("test","late","{}",null);bool doubleFinish=false;try{s.Finish(0,0);}catch(InvalidOperationException){doubleFinish=true;}
  results.Add("{\"fault\":"+fault+",\"path\":"+AuthoritativeEvents.Quote(root)+",\"admitted\":"+admitted+",\"expectedDisposition\":"+(first?"true":"false")+",\"lateRejected\":"+(reject?"true":"false")+",\"doubleFinishRejected\":"+(doubleFinish?"true":"false")+"}");}
  string cap=Path.Combine(parent,"capacity-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(cap);var bounded=new AuthoritativeEvents(cap,items:1,delay:100,batch:128);int accepted=0;for(int i=0;i<100;i++){if(!bounded.Publish("test","cap","{}",null))break;accepted++;}bounded.Finish(0,0);bool sticky=!bounded.Publish("test","after-cap","{}",null);
  string text="{\"runs\":["+string.Join(",",results)+"],\"capacityPath\":"+AuthoritativeEvents.Quote(cap)+",\"capacityAccepted\":"+accepted+",\"capacitySticky\":"+(sticky?"true":"false")+"}";WriterTiming.SaveNew(Path.Combine(parent,"focused-faults.json"),text);return text;
 }
}
