// Diagnostic-only bounded memory traces. No filesystem/network or authority operations.
using System;
using System.Collections.Concurrent;
using System.Diagnostics;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Threading;
public sealed class TimingRow {public string stage;public long qpc,cpu100ns,sampleEndQpc;public uint nativeThread;}
public sealed class RuntimeRow {public long qpc,allocated,pauseTicks,processCpuTicks,workingSet;public int gc0,gc1,gc2;}
public sealed class WakeRow {public long before,after;public double excessSeconds;}
public static class LoopTiming {
 [DllImport("kernel32.dll")] static extern uint GetCurrentThreadId();
 [DllImport("kernel32.dll")] static extern IntPtr GetCurrentThread();
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetThreadTimes(IntPtr h,out long created,out long exited,out long kernel,out long user);
 static readonly ConcurrentQueue<TimingRow> rows=new ConcurrentQueue<TimingRow>();
 static readonly ConcurrentQueue<RuntimeRow> runtime=new ConcurrentQueue<RuntimeRow>();
 static readonly ConcurrentQueue<WakeRow> wakes=new ConcurrentQueue<WakeRow>();
 static int count;public static int Overflow;static volatile bool stop;static Thread observer;
 public static void Note(string stage){
  if(Interlocked.Increment(ref count)>1000000){Interlocked.Increment(ref Overflow);return;}
  long q=Stopwatch.GetTimestamp();long a,b,k,u;bool ok=GetThreadTimes(GetCurrentThread(),out a,out b,out k,out u);
  var row=new TimingRow{stage=stage,qpc=q,nativeThread=GetCurrentThreadId(),cpu100ns=ok?k+u:-1};row.sampleEndQpc=Stopwatch.GetTimestamp();rows.Enqueue(row);
 }
 public sealed class Region:IDisposable {
  readonly string name;public Region(string n){name=n;Note(n+".begin");}public void Dispose(){Note(name+".end");}
 }
 public static Region Span(string n){return new Region(n);}
 public sealed class QueueLock:IDisposable {
  readonly object target;readonly string name;bool taken;
  public QueueLock(object o,string n){target=o;name="lock."+n;Note(name+".request");Monitor.Enter(target,ref taken);Note(name+".acquired");}
  public void Dispose(){if(taken){Note(name+".release");Monitor.Exit(target);taken=false;}}
 }
 public static QueueLock Lock(object o,[CallerMemberName]string name=""){return new QueueLock(o,name);}
 public static void RuntimeSample(){using(var p=Process.GetCurrentProcess())runtime.Enqueue(new RuntimeRow{qpc=Stopwatch.GetTimestamp(),allocated=GC.GetTotalAllocatedBytes(false),pauseTicks=GC.GetTotalPauseDuration().Ticks,gc0=GC.CollectionCount(0),gc1=GC.CollectionCount(1),gc2=GC.CollectionCount(2),processCpuTicks=p.TotalProcessorTime.Ticks,workingSet=p.WorkingSet64});}
 public static void StartObserver(){observer=new Thread(()=>{while(!stop){long b=Stopwatch.GetTimestamp();Thread.Sleep(100);long a=Stopwatch.GetTimestamp();if(wakes.Count<7000)wakes.Enqueue(new WakeRow{before=b,after=a,excessSeconds=Math.Max(0,(a-b)/(double)Stopwatch.Frequency-.1)});else Interlocked.Increment(ref Overflow);}});observer.IsBackground=true;observer.Name="DiagnosticWakeObserver";observer.Start();}
 public static void StopObserver(){stop=true;if(observer!=null && !observer.Join(5000))throw new InvalidOperationException("Diagnostic observer exit deadline");}
 public static TimingRow[] Snapshot(){return rows.ToArray();}
 public static RuntimeRow[] RuntimeSnapshot(){return runtime.ToArray();}
 public static WakeRow[] ObserverSnapshot(){return wakes.ToArray();}
}
