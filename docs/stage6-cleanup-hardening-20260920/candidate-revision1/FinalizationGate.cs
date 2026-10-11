// Sacrificial validation infrastructure. Does not replace or remove queue entries.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Management.Automation;

public sealed class FinalizationGate : IDisposable {
 readonly object sync=new object();
 readonly PSEventArgsCollection queue;
 readonly HashSet<string> sources;
 readonly Dictionary<int,string> expected=new Dictionary<int,string>();
 readonly Dictionary<int,int> starts=new Dictionary<int,int>(),stops=new Dictionary<int,int>();
 readonly Func<long> clock;
 readonly double frequency,quietSeconds,deadlineSeconds;
 long closedAt,lastEvent,quietAt=-1,lastBeat,generation,closingGeneration;
 int active,resets,late;
 bool proof,closing,disposed;
 string state="RUNNING",failure;
 readonly List<string> transitions=new List<string>{"RUNNING"};
 public FinalizationGate(PSEventArgsCollection q,string[] ids,double quiet,double deadline)
  :this(q,ids,quiet,deadline,Stopwatch.Frequency,Stopwatch.GetTimestamp){}
 public FinalizationGate(PSEventArgsCollection q,string[] ids,double quiet,double deadline,double freq,Func<long> now){
  if(quiet<=0 || deadline<=quiet || freq<=0)throw new ArgumentException("Invalid finite bound");
  queue=q;sources=new HashSet<string>(ids);quietSeconds=quiet;deadlineSeconds=deadline;frequency=freq;clock=now;
  lastEvent=lastBeat=clock();queue.PSEventReceived+=OnEvent;
 }
 void Move(string next){state=next;transitions.Add(next);}
 void Fail(string reason){if(failure==null)failure=reason;}
 void Check(){if(failure!=null)throw new InvalidOperationException(failure);}
 void OnEvent(object sender,PSEventArgs ev){if(!sources.Contains(ev.SourceIdentifier))return;lock(sync){
  generation++;lastEvent=clock();if(quietAt>=0){resets++;late++;quietAt=-1;}
  if(closing)Fail("Event arrived after permitted subscription boundary");
 }}
 public void Heartbeat(){lock(sync){long n=clock();if((n-lastBeat)/frequency>=10)Fail("Heartbeat interval >= 10 seconds");lastBeat=n;Check();}}
 public void ProducersClosed(){lock(sync){Check();if(state!="RUNNING")throw new InvalidOperationException("Producer closure repeated");closedAt=clock();Move("PRODUCERS_CLOSED");Move("WAITING_FOR_PROCESS_EXITS");}}
 // Only retained-handle ground truth is admitted here. This NEVER creates lifecycle records.
 public void ConfirmExits(int[] pids,string[] creations,bool allSignaled){lock(sync){Check();
  if(state!="WAITING_FOR_PROCESS_EXITS" || !allSignaled || pids.Length==0 || pids.Length!=creations.Length)throw new InvalidOperationException("Incomplete retained-handle proof");
  for(int i=0;i<pids.Length;i++){if(pids[i]<=0 || String.IsNullOrEmpty(creations[i]) || expected.ContainsKey(pids[i]))throw new InvalidOperationException("Ambiguous retained identity");expected.Add(pids[i],creations[i]);}
  proof=true;Move("EVENT_QUIESCENCE");
 }}
 public void BeginPersistence(){lock(sync){if(active!=0)throw new InvalidOperationException("Concurrent consumer");active++;quietAt=-1;}}
 public void Persisted(int pid,string kind){lock(sync){
  var map=kind=="start"?starts:kind=="stop"?stops:null;
  if(map==null){Fail("Unknown event kind");return;}
  map.TryGetValue(pid,out int n);map[pid]=n+1;if(n!=0)Fail("Duplicate persisted lifecycle record");
 }}
 public void EndPersistence(){lock(sync){if(active!=1)throw new InvalidOperationException("Invalid consumer state");active--;}}
 bool Complete(){if(!proof || starts.Count!=expected.Count || stops.Count!=expected.Count)return false;
  foreach(int pid in expected.Keys)if(!starts.TryGetValue(pid,out int s)||s!=1||!stops.TryGetValue(pid,out int t)||t!=1)return false;return true;
 }
 public bool Ready(bool queueEmpty,bool subscriberHealthy){lock(sync){Check();long n=clock();
  if(state=="RUNNING")return false;
  if((n-closedAt)/frequency>=deadlineSeconds){Fail("Fixed finalization deadline exhausted");Check();}
  if(!subscriberHealthy){Fail("Subscriber unhealthy");Check();}
  if((n-lastBeat)/frequency>=10){Fail("Stale heartbeat during finalization");Check();}
  if(state!="EVENT_QUIESCENCE" || !proof || !queueEmpty || active!=0){quietAt=-1;return false;}
  if(quietAt<0)quietAt=Math.Max(n,lastEvent);
  return Complete() && (n-quietAt)/frequency>=quietSeconds;
 }}
 public void BeginClose(bool queueEmpty,bool subscriberHealthy){lock(sync){if(!Ready(queueEmpty,subscriberHealthy))throw new InvalidOperationException("Premature teardown");closing=true;closingGeneration=generation;Move("FINAL_DRAIN");}}
 public void SubscriptionClosed(){lock(sync){Check();if(state!="FINAL_DRAIN")throw new InvalidOperationException("Closure order");Move("SUBSCRIPTION_CLOSED");}}
 public void FinalDrainComplete(bool empty){lock(sync){Check();if(state!="SUBSCRIPTION_CLOSED" || !empty || active!=0 || !Complete() || generation!=closingGeneration)throw new InvalidOperationException("Final drain/reconciliation mismatch");Move("DURABLE_FINALIZATION");}}
 public void Seal(bool durable,bool reconciled){lock(sync){Check();if(state!="DURABLE_FINALIZATION" || !durable || !reconciled || !Complete())throw new InvalidOperationException("Unverified final evidence");Move("RECONCILIATION");Move("SEALED");}}
 public void AssertSealed(){lock(sync){Check();if(state!="SEALED" || active!=0 || !Complete() || generation!=closingGeneration)throw new InvalidOperationException("Not sealed");}}
 public object Snapshot(){lock(sync)return new{state,failure,quietSeconds,deadlineSeconds,generation,closingGeneration,quiescenceResets=resets,lateEventsAfterQuietStart=late,expected=expected.Count,starts=starts.Count,stops=stops.Count,active,allHandlesConfirmed=proof,transitions=transitions.ToArray()};}
 public void Dispose(){if(disposed)return;queue.PSEventReceived-=OnEvent;disposed=true;}
}
