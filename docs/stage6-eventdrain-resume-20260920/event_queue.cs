// Validation infrastructure only. External EventIdentifier is never a removal key.
using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Management.Automation;
using System.Runtime.CompilerServices;
using System.Threading;

public sealed class QueueEntry {
 public long QueueSequence {get; internal set;}
 public PSEventArgs Event {get; internal set;}
 public bool Persisted {get; internal set;}
 public bool Removed {get; internal set;}
 public long EnqueueQpc {get; internal set;}
}
public sealed class EventReferenceComparer : IEqualityComparer<PSEventArgs> {
 public bool Equals(PSEventArgs a,PSEventArgs b) {return Object.ReferenceEquals(a,b);}
 public int GetHashCode(PSEventArgs a) {return RuntimeHelpers.GetHashCode(a);}
}
public sealed class ExactEventQueue : IDisposable {
 readonly PSEventArgsCollection queue;
 readonly HashSet<string> sources;
 readonly Dictionary<PSEventArgs,QueueEntry> entries=new Dictionary<PSEventArgs,QueueEntry>(new EventReferenceComparer());
 QueueEntry selected;
 long sequence,selectedCount,persistedCount,removedCount;
 int publishing;
 public bool Failed {get; private set;}
 public string Failure {get; private set;}
 public int MaxDepth {get; private set;}
 public ExactEventQueue(PSEventArgsCollection q,string[] ids) {
  queue=q;sources=new HashSet<string>(ids);
  using(LoopTiming.Lock(queue.SyncRoot)) {
   if(CountOwned()!=0)throw new InvalidOperationException("Attach before owned events exist");
   queue.PSEventReceived+=Enqueued;
  }
 }
 int CountOwned() {using(LoopTiming.Span("queue.CountOwned")){int n=0;for(int i=0;i<queue.Count;i++)if(sources.Contains(queue[i].SourceIdentifier))n++;return n;}}
 void Enqueued(object sender,PSEventArgs ev) {
  if(!sources.Contains(ev.SourceIdentifier))return;
  using(LoopTiming.Lock(queue.SyncRoot)) {
   if(entries.ContainsKey(ev)){Fail("Same event reference enqueued twice");return;}
   if(sequence>=20000){Fail("Bounded queue identity capacity exceeded");return;}
   entries.Add(ev,new QueueEntry{QueueSequence=++sequence,Event=ev,EnqueueQpc=System.Diagnostics.Stopwatch.GetTimestamp()});
   MaxDepth=Math.Max(MaxDepth,CountOwned());
  }
 }
 void Fail(string text) {Failed=true;Failure=text;}
 void Healthy() {if(Failed)throw new InvalidOperationException(Failure);}
 int Index(QueueEntry e) {using(LoopTiming.Span("queue.reference.Index")){for(int i=0;i<queue.Count;i++)if(Object.ReferenceEquals(queue[i],e.Event))return i;return -1;}}
 void Valid(QueueEntry e) {
  if(e==null || !Object.ReferenceEquals(selected,e) || !entries.TryGetValue(e.Event,out var known) || !Object.ReferenceEquals(known,e))throw new InvalidOperationException("Unowned selection");
  if(!sources.Contains(e.Event.SourceIdentifier) || Index(e)<0){Fail("Selected exact entry disappeared; competing consumer or corruption");Healthy();}
 }
 public QueueEntry Select() {
  using(LoopTiming.Lock(queue.SyncRoot)) {
   Healthy();if(selected!=null)throw new InvalidOperationException("One consumer/selection only");
   for(int i=0;i<queue.Count;i++) {
    PSEventArgs ev;using(LoopTiming.Span("queue.item.read")){ev=queue[i];}if(!sources.Contains(ev.SourceIdentifier))continue;
    QueueEntry e;using(LoopTiming.Span("queue.identity.lookup")){if(!entries.TryGetValue(ev,out e)){Fail("Enqueue identity unavailable");Healthy();}}
    if(e.Removed || e.Persisted){Fail("Invalid queued state");Healthy();}
    selected=e;selectedCount++;return e;
   }
   return null;
  }
 }
 // No queue lock is held during serialization (caller) or file I/O (here).
 // An uncertain/partial append latches failure; it cannot be retried into duplicate evidence.
 public void PersistAndRemove(QueueEntry e,string path,string serialized) {
  if(Interlocked.CompareExchange(ref publishing,1,0)!=0)throw new InvalidOperationException("Concurrent consumer rejected");
  try {
   using(LoopTiming.Lock(queue.SyncRoot)){Healthy();Valid(e);if(e.Persisted)throw new InvalidOperationException("Already persisted");}
   try {using(LoopTiming.Span("event.File.AppendAllText")){File.AppendAllText(path,serialized);}}
   catch(Exception ex){using(LoopTiming.Lock(queue.SyncRoot)){Fail("Persistence failed: "+ex.GetType().Name);}throw;}
   using(LoopTiming.Lock(queue.SyncRoot)) {
    e.Persisted=true;persistedCount++;
    Valid(e);
    using(LoopTiming.Span("queue.exact.RemoveAt")){queue.RemoveAt(Index(e));} // exact reference matched, exactly one index, same SyncRoot
    e.Removed=true;removedCount++;selected=null;
   }
  } finally {Interlocked.Exchange(ref publishing,0);}
 }
 public object Stats() {
  using(LoopTiming.Lock(queue.SyncRoot))return new {enqueued=sequence,selected=selectedCount,persisted=persistedCount,removed=removedCount,remaining=CountOwned(),maxDepth=MaxDepth,failed=Failed,failure=Failure,identity="reference + bounded monotonic enqueue sequence"};
 }
 public QueueEntry[] Snapshot() {using(LoopTiming.Lock(queue.SyncRoot))return entries.Values.OrderBy(e=>e.QueueSequence).ToArray();}
 public void Reconcile() {
  using(LoopTiming.Lock(queue.SyncRoot)){Healthy();if(selected!=null || CountOwned()!=0 || sequence!=persistedCount || sequence!=removedCount)throw new InvalidOperationException("Queue residue/count mismatch");}
 }
 public void Dispose(){using(LoopTiming.Lock(queue.SyncRoot))queue.PSEventReceived-=Enqueued;}
}
