from pathlib import Path
import json,hashlib,difflib
R=Path(__file__).parent;C=Path(json.loads((R/'freeze.json').read_text())['newCode'])
p=C/'AuthoritativeEvents.cs';old=p.read_text();s=old
def change(a,b):
 global s
 assert a in s,a
 s=s.replace(a,b)
change('public sealed class AuthoritativeEvents {','public sealed class AuthoritativeEvents {\n readonly WriterTiming diag=new WriterTiming(); long lastSample;\n void Sample(string why){long t=Stopwatch.GetTimestamp();if(why!="periodic"||t-lastSample>Stopwatch.Frequency/20){lastSample=t;diag.Point(t,why,accepted,persisted,queue.Count,queued);}}\n public void DiagnosticSave(string p){diag.Save(p);}')
change('  lock(gate){\n   attempted++;','  long enter=Stopwatch.GetTimestamp(); Monitor.Enter(gate); diag.Add(0,enter);long held=Stopwatch.GetTimestamp();try{\n   attempted++;Sample("periodic");')
change('byte[] bytes=Encoding.UTF8.GetBytes(frame(seg));','long ts=Stopwatch.GetTimestamp();string framed=frame(seg);diag.Add(2,ts);ts=Stopwatch.GetTimestamp();byte[] bytes=Encoding.UTF8.GetBytes(framed);diag.Add(3,ts);')
change('   if(bytes.Length>8192','   long valid=Stopwatch.GetTimestamp();\n   if(bytes.Length>8192')
change('failure="AUTHORITATIVE_CAPACITY_EXCEEDED";Monitor.PulseAll(gate);return false;','failure="AUTHORITATIVE_CAPACITY_EXCEEDED";diag.Add(4,valid);Sample("reject");Monitor.PulseAll(gate);return false;')
change('   if(seg!=nextSegment)','   diag.Add(4,valid);\n   if(seg!=nextSegment)')
change('  }\n }\n void WriteLoop()', '  }finally{diag.Add(1,held);Monitor.Exit(gate);}\n }\n void WriteLoop()')
change('Action close=()=>{if(stream==null)return;long q=Stopwatch.GetTimestamp();stream.Flush(true);stream.Dispose();stream=null;hash.TransformFinalBlock(Array.Empty<byte>(),0,0);string digest=BitConverter.ToString(hash.Hash).Replace("-","").ToLowerInvariant();hash.Dispose();hash=null;', 'Action close=()=>{if(stream==null)return;long q=Stopwatch.GetTimestamp();lock(gate)Sample("rollover-before");long st=Stopwatch.GetTimestamp();stream.Flush(true);diag.Add(9,st);st=Stopwatch.GetTimestamp();stream.Dispose();diag.Add(10,st);stream=null;st=Stopwatch.GetTimestamp();hash.TransformFinalBlock(Array.Empty<byte>(),0,0);string digest=BitConverter.ToString(hash.Hash).Replace("-","").ToLowerInvariant();hash.Dispose();hash=null;diag.Add(12,st);st=Stopwatch.GetTimestamp();')
change('maxRollover=Math.Max(maxRollover,(Stopwatch.GetTimestamp()-q)/(double)Stopwatch.Frequency);};','diag.Add(13,st);maxRollover=Math.Max(maxRollover,(Stopwatch.GetTimestamp()-q)/(double)Stopwatch.Frequency);diag.Add(14,q);lock(gate)Sample("rollover-after");};')
change('   while(true){Item item;lock(gate){while(queue.Count==0&&!closing)Monitor.Wait(gate);if(queue.Count==0&&closing)break;item=queue.Dequeue();queued-=item.bytes.Length;}', '   diag.Mark("writer-start");while(true){Item item;long lw=Stopwatch.GetTimestamp();Monitor.Enter(gate);diag.Add(5,lw);long lh=Stopwatch.GetTimestamp();try{while(queue.Count==0&&!closing)Monitor.Wait(gate);if(queue.Count==0&&closing)break;long dq=Stopwatch.GetTimestamp();item=queue.Dequeue();queued-=item.bytes.Length;diag.Add(7,dq);}finally{diag.Add(6,lh);Monitor.Exit(gate);}')
change('stream=new FileStream(Path.Combine(root,','long op=Stopwatch.GetTimestamp();stream=new FileStream(Path.Combine(root,')
change('hash=SHA256.Create();}', 'hash=SHA256.Create();diag.Add(8,op);}')
change('stream.Write(item.bytes,0,item.bytes.Length);hash.TransformBlock(item.bytes,0,item.bytes.Length,null,0);','stream.Write(item.bytes,0,item.bytes.Length);diag.Add(15,q);long hh=Stopwatch.GetTimestamp();hash.TransformBlock(item.bytes,0,item.bytes.Length,null,0);diag.Add(11,hh);')
change('    size+=item.bytes.Length;','    long update=Stopwatch.GetTimestamp();size+=item.bytes.Length;')
change('Interlocked.Increment(ref persisted);','Interlocked.Increment(ref persisted);diag.Add(16,update);')
change('   close();','   close();diag.Mark("writer-exit");')
change('  lock(gate){closed=true;','  long mf=Stopwatch.GetTimestamp();lock(gate){closed=true;')
change('f.Write(bytes,0,bytes.Length);f.Flush(true);}','f.Write(bytes,0,bytes.Length);f.Flush(true);}\n   diag.Add(17,mf);')
before=R/'AuthoritativeEvents.cs.before'
with before.open('x') as f:f.write(old)
p.write_text(s)
with (R/'instrumentation.diff').open('x') as f:f.writelines(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='before',tofile='diagnostic'))
for name in ['WriterTiming.cs','WriterBench.cs','bench.ps1']:
 with (C/name).open('xb') as f:f.write((R/name).read_bytes())
with (R/'instrumentation-hashes.json').open('x') as f:json.dump({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [C/'AuthoritativeEvents.cs',C/'WriterTiming.cs',C/'WriterBench.cs',C/'bench.ps1']},f,indent=2)
print(C)
