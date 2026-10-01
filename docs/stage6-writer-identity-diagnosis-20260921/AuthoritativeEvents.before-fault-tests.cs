// TEST acceptance infrastructure only. One bounded sequenced stream; no command execution.
using System;
using System.IO;
using System.Text;
using System.Collections.Generic;
using System.Diagnostics;
using System.Security.Cryptography;
using System.Threading;

public sealed class AuthoritativeEvents {
 readonly WriterTiming diag=new WriterTiming(); long lastSample;
 void Sample(string why){long t=Stopwatch.GetTimestamp();if(why!="periodic"||t-lastSample>Stopwatch.Frequency/20){lastSample=t;diag.Point(t,why,accepted,persisted,queue.Count,queued);}}
 public void DiagnosticSave(string p){diag.Save(p);}
 sealed class Item { public byte[] bytes; public long seq; public int segment; }
 readonly object gate=new object(); readonly Queue<Item> queue=new Queue<Item>();
 readonly List<string> segments=new List<string>(); readonly string root;
 readonly long memoryLimit,storageLimit,recordLimit; readonly int itemLimit,segmentLimit,delayMs,inject;
 readonly int batchSize;readonly Thread writer; long attempted,accepted,persisted,queued,totalBytes,written,peakBytes;int peakItems,nextSegment;long segmentAssigned;
 bool closing,closed;string failure;double maxWrite,maxRollover;long firstQpc,lastQpc;
 public static string Quote(string s) { if(s==null)return "null";var b=new StringBuilder("\"");foreach(char c in s){switch(c){case '\\':b.Append("\\\\");break;case '"':b.Append("\\\"");break;case '\n':b.Append("\\n");break;case '\r':b.Append("\\r");break;case '\t':b.Append("\\t");break;default:if(c<32)b.Append("\\u"+((int)c).ToString("x4"));else b.Append(c);break;}}return b.Append('"').ToString(); }
 static string Number(double n){return n.ToString("R",System.Globalization.CultureInfo.InvariantCulture);}
 public AuthoritativeEvents(string directory,long memory=67108864,int items=65536,int segmentBytes=8388608,long storage=137438953472,long records=196531200,int delay=0,int fault=0,int batch=1) {
  if(batch<1||batch>128)throw new ArgumentException("Bounded batch required");batchSize=batch;root=Path.GetFullPath(directory);
  if(!root.StartsWith(@"D:\JARVIS-STAGE6-LIVE\",StringComparison.OrdinalIgnoreCase)||directory.Contains("..")||!Directory.Exists(root))throw new InvalidOperationException("Prepared D: run required");
  for(var d=new DirectoryInfo(root);d!=null;d=d.Parent)if((d.Attributes&FileAttributes.ReparsePoint)!=0)throw new InvalidOperationException("Reparse path rejected");
  if(memory<8192||items<1||segmentBytes<8192||storage<8192||records<1||delay<0||delay>500)throw new ArgumentException("Invalid finite bound");
  // Fail before a writer starts if any prior stream artifact occupies this run.
  if(Directory.GetFiles(root,"app-authority-*").Length!=0||File.Exists(Path.Combine(root,"app-authority.json")))throw new IOException("EVIDENCE_EXISTS: "+root);
  memoryLimit=memory;itemLimit=items;segmentLimit=segmentBytes;storageLimit=storage;recordLimit=records;delayMs=delay;inject=fault;
  writer=new Thread(WriteLoop);writer.IsBackground=true;writer.Name="J6AuthoritativeWriter";writer.Start();
 }
 void Fail(string s){lock(gate){if(failure==null)failure=s;Monitor.PulseAll(gate);}}
 public string Failure {get{lock(gate)return failure;}}
 public bool Publish(string source,string type,string raw,string rawTimestamp) {
  long enter=Stopwatch.GetTimestamp(); Monitor.Enter(gate); diag.Add(0,enter);long held=Stopwatch.GetTimestamp();try{
   attempted++;Sample("periodic");
   if(closing||failure!=null){if(failure==null)failure="ADMISSION_AFTER_CLOSE";return false;}
   long seq=accepted+1;int seg=nextSegment;long qpc=Stopwatch.GetTimestamp();
   Func<int,string> frame=n=>"{\"seq\":"+seq+",\"segment\":"+n+",\"source\":"+Quote(source)+",\"eventType\":"+Quote(type)+",\"qpc\":"+qpc+",\"rawTimestamp\":"+Quote(rawTimestamp)+",\"canonicalIdentity\":null,\"identityStatus\":\"UNRESOLVED\",\"serialized\":true,\"raw\":"+raw+"}\n";
   long ts=Stopwatch.GetTimestamp();string framed=frame(seg);diag.Add(2,ts);ts=Stopwatch.GetTimestamp();byte[] bytes=Encoding.UTF8.GetBytes(framed);diag.Add(3,ts);
   if(segmentAssigned+bytes.Length>segmentLimit){seg++;bytes=Encoding.UTF8.GetBytes(frame(seg));}
   long valid=Stopwatch.GetTimestamp();
   if(bytes.Length>8192||bytes.Length>segmentLimit||accepted>=recordLimit||totalBytes+bytes.Length>storageLimit||queued+bytes.Length>memoryLimit||(accepted-persisted)>=itemLimit||seg>=16384){failure="AUTHORITATIVE_CAPACITY_EXCEEDED";diag.Add(4,valid);Sample("reject");Monitor.PulseAll(gate);return false;}
   diag.Add(4,valid);
   if(seg!=nextSegment){nextSegment=seg;segmentAssigned=0;}segmentAssigned+=bytes.Length;
   accepted=seq;totalBytes+=bytes.Length;queued+=bytes.Length;queue.Enqueue(new Item{bytes=bytes,seq=seq,segment=seg});
   peakBytes=Math.Max(peakBytes,queued);peakItems=Math.Max(peakItems,queue.Count);if(firstQpc==0)firstQpc=qpc;lastQpc=qpc;Monitor.PulseAll(gate);return true;
  }finally{diag.Add(1,held);Monitor.Exit(gate);}
 }
 void WriteLoop() {
  FileStream stream=null;SHA256 hash=null;int current=-1;long count=0,size=0,first=0,last=0;
  Action close=()=>{if(stream==null)return;long q=Stopwatch.GetTimestamp();lock(gate)Sample("rollover-before");long st=Stopwatch.GetTimestamp();stream.Flush(true);diag.Add(9,st);st=Stopwatch.GetTimestamp();stream.Dispose();diag.Add(10,st);stream=null;st=Stopwatch.GetTimestamp();hash.TransformFinalBlock(Array.Empty<byte>(),0,0);string digest=BitConverter.ToString(hash.Hash).Replace("-","").ToLowerInvariant();hash.Dispose();hash=null;diag.Add(12,st);st=Stopwatch.GetTimestamp();
   if(inject==4)throw new IOException("INJECTED_HASH_FAILURE");
   segments.Add("{\"number\":"+current+",\"name\":"+Quote("app-authority-"+current.ToString("D5")+".jsonl")+",\"first\":"+first+",\"last\":"+last+",\"records\":"+count+",\"bytes\":"+size+",\"sha256\":"+Quote(digest)+"}");diag.Add(13,st);maxRollover=Math.Max(maxRollover,(Stopwatch.GetTimestamp()-q)/(double)Stopwatch.Frequency);diag.Add(14,q);lock(gate)Sample("rollover-after");};
  try {
   diag.Mark("writer-start");while(true){var batchItems=new List<Item>(batchSize);long batchBytes=0;long lw=Stopwatch.GetTimestamp();Monitor.Enter(gate);diag.Add(5,lw);long lh=Stopwatch.GetTimestamp();try{while(queue.Count==0&&!closing)Monitor.Wait(gate);if(queue.Count==0&&closing)break;long dq=Stopwatch.GetTimestamp();while(batchItems.Count<batchSize&&queue.Count>0){var next=queue.Dequeue();batchItems.Add(next);batchBytes+=next.bytes.Length;}diag.Add(7,dq);}finally{diag.Add(6,lh);Monitor.Exit(gate);}
    foreach(var item in batchItems){
    if(delayMs>0)Thread.Sleep(delayMs);
    if(item.segment!=current){close();current=item.segment;count=size=0;first=item.seq;if(inject==3)throw new IOException("INJECTED_CREATE_FAILURE");long op=Stopwatch.GetTimestamp();stream=new FileStream(Path.Combine(root,"app-authority-"+current.ToString("D5")+".jsonl"),FileMode.CreateNew,FileAccess.Write,FileShare.Read,65536,FileOptions.SequentialScan);hash=SHA256.Create();diag.Add(8,op);}
    if(inject==1||inject==2)throw new IOException(inject==1?"INJECTED_WRITE_FAILURE":"INJECTED_DISK_FULL");
    long q=Stopwatch.GetTimestamp();stream.Write(item.bytes,0,item.bytes.Length);diag.Add(15,q);long hh=Stopwatch.GetTimestamp();hash.TransformBlock(item.bytes,0,item.bytes.Length,null,0);diag.Add(11,hh);maxWrite=Math.Max(maxWrite,(Stopwatch.GetTimestamp()-q)/(double)Stopwatch.Frequency);
    long update=Stopwatch.GetTimestamp();size+=item.bytes.Length;written+=item.bytes.Length;count++;last=item.seq;Interlocked.Increment(ref persisted);diag.Add(16,update);
    }
    lock(gate){queued-=batchBytes;}
   }
   close();diag.Mark("writer-exit");
  }catch(Exception e){Fail(e.GetType().Name+": "+e.Message);}finally{if(stream!=null)stream.Dispose();if(hash!=null)hash.Dispose();}
 }
 public void Finish(int viewRows,long truncated) {
  lock(gate){if(closed)throw new InvalidOperationException("Already finalized");closing=true;Monitor.PulseAll(gate);}
  if(!writer.Join(5000)){Fail("WRITER_CLOSE_BOUND");throw new InvalidOperationException("Writer did not exit");}
  long mf=Stopwatch.GetTimestamp();lock(gate){closed=true;if(accepted!=persisted||attempted!=accepted||queue.Count!=0)if(failure==null)failure="INCOMPLETE_STREAM";
   string json="{\"format\":\"application-authority-v1\",\"fault\":"+Quote(failure)+",\"attempted\":"+attempted+",\"accepted\":"+accepted+",\"persisted\":"+persisted+",\"bytes\":"+written+",\"first\":"+(persisted>0?1:0)+",\"last\":"+persisted+",\"peakQueueBytes\":"+peakBytes+",\"peakQueueItems\":"+peakItems+",\"remaining\":"+queue.Count+",\"memoryBound\":"+memoryLimit+",\"itemBound\":"+itemLimit+",\"recordBound\":"+recordLimit+",\"storageBound\":"+storageLimit+",\"maxWriteSeconds\":"+Number(maxWrite)+",\"maxRolloverSeconds\":"+Number(maxRollover)+",\"firstQpc\":"+firstQpc+",\"lastQpc\":"+lastQpc+",\"frequency\":"+Stopwatch.Frequency+",\"tapRows\":"+viewRows+",\"tapTruncated\":"+truncated+",\"writerExited\":true,\"segments\":["+string.Join(",",segments)+"]}";
   using(var f=new FileStream(Path.Combine(root,"app-authority.json"),FileMode.CreateNew,FileAccess.Write,FileShare.Read)){var bytes=Encoding.UTF8.GetBytes(json);f.Write(bytes,0,bytes.Length);f.Flush(true);}
   diag.Add(17,mf);
  }
 }
}
