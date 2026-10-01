using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Management.Automation;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
public static class FinalizationTests {
 static int checks;static List<object> results=new List<object>();
 static void Check(bool ok,string message){checks++;if(!ok)throw new Exception(message);}
 static void Denied(Action a,string message){bool failed=false;try{a();}catch(InvalidOperationException){failed=true;}Check(failed,message);}
 sealed class Case:IDisposable {
  public long now;public PSEventArgsCollection q=new PSEventArgsCollection();public ExactEventQueue x;public FinalizationGate g;public string file;
  public Case(string root,string name){file=Path.Combine(root,name+".jsonl");x=new ExactEventQueue(q,new[]{"start","stop"});g=new FinalizationGate(q,new[]{"start","stop"},4.6,45,1000000,()=>Interlocked.Read(ref now));}
  public void Add(int pid,string kind){var ctor=typeof(PSEventArgs).GetConstructors(BindingFlags.Instance|BindingFlags.NonPublic)[0];var e=(PSEventArgs)ctor.Invoke(new object[]{"localhost",Guid.Empty,7,kind,null,new object[0],PSObject.AsPSObject(pid)});lock(q.SyncRoot)typeof(PSEventArgsCollection).GetMethod("Add",BindingFlags.Instance|BindingFlags.NonPublic).Invoke(q,new object[]{e});}
  public void Drain(Action during=null){QueueEntry e;bool once=false;while((e=x.Select())!=null){g.BeginPersistence();try{if(!once&&during!=null){once=true;during();}x.PersistAndRemove(e,file,e.QueueSequence+","+e.Event.SourceIdentifier+","+e.Event.MessageData+"\n");g.Persisted((int)e.Event.MessageData.BaseObject,e.Event.SourceIdentifier);}finally{g.EndPersistence();}}}
  public void Proof(int count=1){g.ProducersClosed();g.ConfirmExits(Enumerable.Range(1,count).ToArray(),Enumerable.Range(1,count).Select(i=>"creation-"+i).ToArray(),true);}
  public bool Ready(){return g.Ready(q.Count==0,true);}
  public void Finish(){Check(Ready(),"Quiet interval + complete identities");g.BeginClose(q.Count==0,true);g.SubscriptionClosed();Drain();x.Reconcile();g.FinalDrainComplete(q.Count==0);using(var f=new FileStream(file,FileMode.Open,FileAccess.ReadWrite)){f.Flush(true);}g.Seal(true,true);g.AssertSealed();}
  public void Dispose(){g.Dispose();x.Dispose();}
 }
 public static object Run(string root){
  foreach(int delay in new[]{0,1000,10000,25000,100000,4599000,4600000})using(var c=new Case(root,"late-"+delay)){
   c.Add(1,"start");c.Drain();c.Proof();Check(!c.Ready(),"No STOP, cannot seal");c.now=delay;c.Add(1,"stop");c.Drain();Check(!c.Ready(),"Late STOP restarts quiet");c.now+=4599999;Check(!c.Ready(),"Not early by microsecond");c.now++;c.g.Heartbeat();c.Finish();Check(File.ReadAllLines(c.file).Length==2,"Late STOP persisted exactly once");results.Add(new{name="late-"+delay,status="PASS",state=c.g.Snapshot()});
  }
  using(var c=new Case(root,"during-drain")){c.Add(1,"start");c.Proof();c.Drain(()=>{c.Add(1,"stop");Check(!c.Ready(),"Active persistence cannot close");});Check(!c.Ready(),"Quiet starts after drain");c.now=4600000;c.Finish();results.Add(new{name="during-drain",status="PASS"});}
  using(var c=new Case(root,"after-closed")){c.Add(1,"start");c.Add(1,"stop");c.Drain();c.Proof();c.Ready();c.now=4600000;c.Finish();c.Add(1,"stop");Denied(()=>c.g.AssertSealed(),"Late closed-boundary event invalidates sealing");c.Drain();Check(File.ReadAllLines(c.file).Length==3,"Unexpected late evidence preserved");results.Add(new{name="after-closed-fails",status="PASS"});}
  foreach(string failure in new[]{"subscriber","heartbeat","consumer","write","flush","never-exits","missing-stop","mismatch","pre-teardown","duplicate","ambiguous"})using(var c=new Case(root,"fail-"+failure)){
   c.Add(1,"start");c.Drain();
   if(failure=="never-exits"){c.g.ProducersClosed();Denied(()=>c.g.ConfirmExits(new[]{1},new[]{"x"},false),"Unsignaled handles rejected");for(int i=1;i<=9;i++){c.now=i*5000000L;c.g.Heartbeat();}Denied(()=>c.Ready(),"Unexited process deadline");}
   else if(failure=="ambiguous"){c.g.ProducersClosed();Denied(()=>c.g.ConfirmExits(new[]{1,1},new[]{"x","y"},true),"Duplicate identity rejected");}
   else {c.Proof();
    if(failure!="missing-stop"){c.Add(1,"stop");c.Drain();}c.Ready();
    if(failure=="heartbeat"){c.now=10000000;Denied(()=>c.Ready(),"Heartbeat failure");}
    else if(failure=="subscriber")Denied(()=>c.g.Ready(true,false),"Subscriber failure");
    else if(failure=="missing-stop"){for(int i=1;i<=9;i++){c.now=i*5000000L;c.g.Heartbeat();}Denied(()=>c.Ready(),"Missing STOP deadline");}
    else if(failure=="consumer"){c.g.BeginPersistence();c.now=4600000;Denied(()=>c.g.BeginClose(true,true),"Active consumer denied");c.g.EndPersistence();}
    else if(failure=="write"){c.Add(2,"start");var e=c.x.Select();try{c.x.PersistAndRemove(e,root,"bad");}catch(IOException){}catch(UnauthorizedAccessException){}Denied(()=>c.x.Reconcile(),"Failed write queue cannot seal");}
    else if(failure=="duplicate"){c.Add(1,"stop");c.Drain();Denied(()=>c.Ready(),"Duplicate cannot seal");}
    else {c.now=4600000;c.g.BeginClose(true,true);
     if(failure=="pre-teardown"){c.Add(1,"stop");Denied(()=>c.g.SubscriptionClosed(),"Closing race fails");}
     else {c.g.SubscriptionClosed();c.g.FinalDrainComplete(true);Denied(()=>c.g.Seal(failure!="flush",failure!="mismatch"),"Durability/reconciliation failure");}
    }
   }
   Denied(()=>c.g.AssertSealed(),"Failure cannot be accepted");results.Add(new{name=failure,status="PASS"});
  }
  using(var c=new Case(root,"clustered-concurrent")){
   const int total=1000;c.Proof(total);int done=0;
   var tasks=Enumerable.Range(0,4).Select(worker=>Task.Run(()=>{for(int i=worker+1;i<=total;i+=4){c.Add(i,"start");c.Add(i,"stop");Thread.Yield();}Interlocked.Increment(ref done);})).ToArray();
   var sw=System.Diagnostics.Stopwatch.StartNew();while(done<4 || c.q.Count>0){if(sw.Elapsed.TotalSeconds>30)throw new Exception("Stress deadline");c.Drain();Check(!c.Ready(),"Temporary empty queue cannot seal before quiet");Thread.Yield();}Task.WaitAll(tasks);c.Drain();c.Ready();c.now=4600000;c.Finish();Check(c.x.Snapshot().Select(e=>e.QueueSequence).Distinct().Count()==2000,"Unique internal IDs under collisions");Check(File.ReadAllLines(c.file).Length==2000,"All clustered events persisted");results.Add(new{name="clustered-concurrent",status="PASS",processes=1000,events=2000,externalCollisions=1999,internalCollisions=0});
  }
  return new{status="PASS",checks,groups=results};
 }
}
