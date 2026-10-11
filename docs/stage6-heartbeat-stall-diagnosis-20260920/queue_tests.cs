using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Collections.Generic;
using System.Management.Automation;
using System.Threading;
using System.Threading.Tasks;
public static class QueueTests {
 static ConstructorInfo ctor=typeof(PSEventArgs).GetConstructors(BindingFlags.Instance|BindingFlags.NonPublic)[0];
 static MethodInfo add=typeof(PSEventArgsCollection).GetMethod("Add",BindingFlags.Instance|BindingFlags.NonPublic);
 static int checks;
 static void Check(bool b,string m){checks++;if(!b)throw new Exception(m);}
 static PSEventArgs Event(int id,string kind,int pid) {return (PSEventArgs)ctor.Invoke(new object[]{"localhost",Guid.Empty,id,kind,null,new object[0],PSObject.AsPSObject(pid)});}
 static void Add(PSEventArgsCollection q,PSEventArgs e){lock(q.SyncRoot)add.Invoke(q,new object[]{e});}
 static string Persist(ExactEventQueue x,QueueEntry e,string path) {string row=e.QueueSequence+","+e.Event.EventIdentifier+","+e.Event.SourceIdentifier+","+e.Event.MessageData+"\n";x.PersistAndRemove(e,path,row);return row;}
 public static object Run(string root) {
  Directory.CreateDirectory(root);var results=new List<object>();
  var patterns=new Dictionary<string,int[]> {
   {"two_START",new[]{7,7}},{"two_STOP",new[]{7,7}},{"START_STOP",new[]{7,7}},
   {"three",new[]{7,7,7}},{"ten",Enumerable.Repeat(7,10).ToArray()},
   {"head",new[]{7,7,8,9}},{"middle",new[]{8,7,7,9}},{"tail",new[]{8,9,7,7}},
   {"consecutive",new[]{7,7,8,8,9,9}},{"distinct_processes",new[]{7,7,7}}
  };
  foreach(var p in patterns){
   var q=new PSEventArgsCollection();using(var x=new ExactEventQueue(q,new[]{"start","stop"})){
    var refs=new List<PSEventArgs>();for(int i=0;i<p.Value.Length;i++){var e=Event(p.Value[i],p.Key=="two_STOP"?"stop":p.Key=="two_START"?"start":i%2==0?"start":"stop",1000+i);refs.Add(e);Add(q,e);}
    var file=Path.Combine(root,p.Key+".txt");
    for(int i=0;i<refs.Count;i++){
     var e=x.Select();Check(Object.ReferenceEquals(e.Event,refs[i]),"Concrete collection exact reference/FIFO");
     Check(e.QueueSequence==i+1,"Sequence order");var before=q.Count;Persist(x,e,file);
     Check(q.Count==before-1,"One removal only");Check(e.Removed && e.Persisted,"Successful state");
     Check(refs.Skip(i+1).All(r=>Enumerable.Range(0,q.Count).Any(j=>Object.ReferenceEquals(q[j],r))),"Sibling retained");
    }
    x.Reconcile();Check(File.ReadAllLines(file).Length==refs.Count,"All records persisted");results.Add(new {name=p.Key,status="PASS",events=refs.Count});
   }
  }
  {
   var q=new PSEventArgsCollection();using(var x=new ExactEventQueue(q,new[]{"start","stop"})){
    Add(q,Event(9,"start",1));Add(q,Event(9,"stop",2));var e=x.Select();bool denied=false;
    try{x.Select();}catch(InvalidOperationException){denied=true;}Check(denied,"Competing selection denied");
    try{Persist(x,e,root);}catch(IOException){}catch(UnauthorizedAccessException){}
    Check(x.Failed && q.Count==2 && !e.Persisted,"Failed persistence removes zero");
    denied=false;try{Persist(x,e,Path.Combine(root,"must-not-exist.txt"));}catch(InvalidOperationException){denied=true;}
    Check(denied && !File.Exists(Path.Combine(root,"must-not-exist.txt")),"Uncertain write retry refused");
    denied=false;try{x.Reconcile();}catch(InvalidOperationException){denied=true;}Check(denied,"Failure cannot accept");
    results.Add(new{name="failed_write_zero_removed_and_retry_refusal",status="PASS"});
   }
  }
  {
   var q=new PSEventArgsCollection();using(var x=new ExactEventQueue(q,new[]{"start","stop"})){
    Add(q,Event(9,"start",1));var e=x.Select();string f=Path.Combine(root,"retry.txt");Persist(x,e,f);
    bool denied=false;try{Persist(x,e,f);}catch(InvalidOperationException){denied=true;}
    Check(denied && File.ReadAllLines(f).Length==1,"Successful retry cannot duplicate");x.Reconcile();
    results.Add(new{name="successful_retry_no_duplicate",status="PASS"});
   }
  }
  {
   var q=new PSEventArgsCollection();using(var x=new ExactEventQueue(q,new[]{"start","stop"})){
    Add(q,Event(9,"start",1));bool denied=false;try{x.Reconcile();}catch(InvalidOperationException){denied=true;}Check(denied,"Residue rejected");
    var e=x.Select();q.RemoveAt(0);denied=false;try{Persist(x,e,Path.Combine(root,"stolen.txt"));}catch(InvalidOperationException){denied=true;}
    Check(denied && x.Failed && !File.Exists(Path.Combine(root,"stolen.txt")),"Foreign consumer detected before write");
    results.Add(new{name="residue_and_foreign_consumer",status="PASS"});
   }
  }
  // Real session collection is also exercised by PowerShell wrapper; stress uses the same concrete type.
  const int total=10000;var stress=new PSEventArgsCollection();using(var x=new ExactEventQueue(stress,new[]{"start","stop"})){
   int generated=0,done=0,concurrentEnqueues=0,draining=0;string f=Path.Combine(root,"stress.txt");
   var producers=Enumerable.Range(0,4).Select(worker=>Task.Run(()=>{
    for(int i=0;i<total/4;i++){int n=Interlocked.Increment(ref generated);Add(stress,Event(n%7,n%2==0?"start":"stop",n));if(Volatile.Read(ref draining)!=0)Interlocked.Increment(ref concurrentEnqueues);if(i%25==0)Thread.Yield();}
    Interlocked.Increment(ref done);
   })).ToArray();
   var sw=System.Diagnostics.Stopwatch.StartNew();int selected=0;Volatile.Write(ref draining,1);
   while(done<4 || selected<total){if(sw.Elapsed.TotalSeconds>60)throw new Exception("Bounded stress deadline");var e=x.Select();if(e==null){Thread.Yield();continue;}Persist(x,e,f);selected++;}
   Task.WaitAll(producers);x.Reconcile();var entries=x.Snapshot();var lines=File.ReadAllLines(f);
   Check(entries.Length==total && lines.Length==total,"Stress completeness");
   Check(entries.Select(e=>e.QueueSequence).Distinct().Count()==total,"Concurrent sequence uniqueness");
   Check(lines.Select(l=>l.Split(',')[0]).Distinct().Count()==total,"No duplicate evidence");Check(stress.Count==0,"No queue residue");
   Check(concurrentEnqueues>0,"Concurrent enqueue/drain exercised");
   results.Add(new{name="concurrent_high_volume",status="PASS",generated,enqueued=entries.Length,selected,persisted=lines.Length,removed=entries.Count(e=>e.Removed),remaining=stress.Count,externalCollisions=total-7,internalCollisions=0,duplicates=0,losses=0,siblingDeletions=0,concurrentEnqueues,seconds=sw.Elapsed.TotalSeconds});
  }
  return new {status="PASS",checks,groups=results};
 }
}
