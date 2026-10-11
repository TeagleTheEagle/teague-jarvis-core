// Sacrificial diagnostics only. No event consumption, production or filesystem access.
using System;
using System.Collections;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Linq.Expressions;
using System.Reflection;
using System.Threading;

public sealed class TapRow {
 public long seq,qpc; public string utc,stage,kind,source,nativeTime,name,error;
 public int parentPid,pid,eventId,queueDepth,thread;
}
public static class EventTap {
 static readonly ConcurrentQueue<TapRow> rows=new ConcurrentQueue<TapRow>();
 static readonly List<Tuple<object,EventInfo,Delegate>> hooks=new List<Tuple<object,EventInfo,Delegate>>();
 static long sequence; public static int Errors,Overflow; public static string StartId,StopId;
 static object Get(object o,string n) { return o==null?null:o.GetType().GetProperty(n)?.GetValue(o); }
 static void Add(TapRow r) {
  r.seq=Interlocked.Increment(ref sequence);r.qpc=Stopwatch.GetTimestamp();r.utc=DateTime.UtcNow.ToString("o");r.thread=Environment.CurrentManagedThreadId;
  if(r.seq>20000) { Interlocked.Increment(ref Overflow);return; } rows.Enqueue(r);
 }
 public static void Capture(object a,string kind,string stage,object collection) {
  try {
   var r=new TapRow {kind=kind,stage=stage,eventId=-1,queueDepth=-1};
   object args=a;
   if(stage=="A-enqueue") {
    r.source=Convert.ToString(Get(a,"SourceIdentifier"));
    if(r.source!=StartId && r.source!=StopId)return;
    r.kind=r.source==StartId?"start":"stop";
    r.eventId=Convert.ToInt32(Get(a,"EventIdentifier"));args=Get(a,"SourceEventArgs");
    r.queueDepth=Convert.ToInt32(Get(collection,"Count"));
   }
   object n=Get(args,"NewEvent");
   if(n==null)throw new InvalidOperationException("No NewEvent on "+args?.GetType().FullName);
   var props=Get(n,"CimInstanceProperties")??Get(n,"Properties");
   foreach(object p in (IEnumerable)props) {
    string name=Convert.ToString(Get(p,"Name"));object value=Get(p,"Value");
    if(name=="ParentProcessID")r.parentPid=Convert.ToInt32(value);
    else if(name=="ProcessID")r.pid=Convert.ToInt32(value);
    else if(name=="ProcessName")r.name=Convert.ToString(value);
    else if(name=="TIME_CREATED")r.nativeTime=Convert.ToString(value);
   }
   Add(r);
  } catch(Exception e) {Interlocked.Increment(ref Errors);Add(new TapRow{stage=stage,kind=kind,error=e.GetType().Name+": "+e.Message});}
 }
 static string Attach(object target,string eventName,string kind,string stage,object collection) {
  EventInfo ev=target.GetType().GetEvent(eventName)??throw new InvalidOperationException("Missing public event "+eventName);
  var ps=ev.EventHandlerType.GetMethod("Invoke").GetParameters().Select(p=>Expression.Parameter(p.ParameterType,p.Name)).ToArray();
  var call=Expression.Call(typeof(EventTap).GetMethod("Capture"),Expression.Convert(ps[ps.Length-1],typeof(object)),Expression.Constant(kind),Expression.Constant(stage),Expression.Constant(collection,typeof(object)));
  Delegate handler=Expression.Lambda(ev.EventHandlerType,call,ps).Compile();ev.AddEventHandler(target,handler);
  hooks.Add(Tuple.Create(target,ev,handler));return target.GetType().FullName+"."+eventName;
 }
 public static string AttachSource(object target,string eventName,string kind) {return Attach(target,eventName,kind,"A-callback",null);}
 public static string AttachSecondary(object target,string kind) {return Attach(target,"EventArrived",kind,"B-WMI-callback",null);}
 public static string AttachQueue(object queue,string start,string stop) {StartId=start;StopId=stop;return Attach(queue,"PSEventReceived","", "A-enqueue",queue);}
 public static TapRow[] Snapshot() {return rows.ToArray();}
 public static void Detach() {foreach(var h in hooks)h.Item2.RemoveEventHandler(h.Item1,h.Item3);hooks.Clear();}
}
