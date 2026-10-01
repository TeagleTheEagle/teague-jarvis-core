from pathlib import Path
import json,hashlib,difflib
R=Path(__file__).parent;C=Path(json.loads((R/'freeze.json').read_text())['newCode'])
p=C/'AuthoritativeEvents.cs';old=p.read_text();s=old
def rep(a,b):
 global s
 assert a in s,a
 s=s.replace(a,b)
rep('readonly Thread writer;', 'readonly int batchSize;readonly Thread writer;')
rep('int delay=0,int fault=0)', 'int delay=0,int fault=0,int batch=1)')
rep('  root=Path.GetFullPath(directory);','  if(batch<1||batch>128)throw new ArgumentException("Bounded batch required");batchSize=batch;root=Path.GetFullPath(directory);')
rep('queue.Count>=itemLimit','(accepted-persisted)>=itemLimit')
rep('while(true){Item item;long lw=', 'while(true){var batchItems=new List<Item>(batchSize);long batchBytes=0;long lw=')
rep('item=queue.Dequeue();queued-=item.bytes.Length;diag.Add(7,dq);','while(batchItems.Count<batchSize&&queue.Count>0){var next=queue.Dequeue();batchItems.Add(next);batchBytes+=next.bytes.Length;}diag.Add(7,dq);')
rep('    if(delayMs>0)', '    foreach(var item in batchItems){\n    if(delayMs>0)')
rep('diag.Add(16,update);\n   }','diag.Add(16,update);\n    }\n    lock(gate){queued-=batchBytes;}\n   }')
with (R/'AuthoritativeEvents.instrumented-before-batch.cs').open('x') as f:f.write(old)
p.write_text(s)
with (R/'batch-experiment.diff').open('x') as f:f.writelines(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='instrumented',tofile='bounded batch experiment'))
p=C/'WriterBench.cs';s=p.read_text();s=s.replace('int count,int pad)','int count,int pad,int batch)');s=s.replace('new AuthoritativeEvents(root);','new AuthoritativeEvents(root,batch:batch);');p.write_text(s)
p=C/'bench.ps1';s=p.read_text().replace('[switch]$Raw)','[switch]$Raw,[int]$Batch=1)').replace('($run,$Rate,$Count,$Padding)','($run,$Rate,$Count,$Padding,$Batch)');p.write_text(s)
with (R/'batch-design.json').open('x') as f:json.dump({'reason':'Measured producer-lock starvation: consumer 210ms lock wait during 228ms producer burst, before rollover. Test bounded dequeue amortization; no durability deferral.','batchMaximum':128,'default':1,'itemLimit':65536,'byteLimit':67108864,'pendingInFlightIncludedInAdmission':True,'append':'one ordered record at a time; count advances only after Write and incremental hash succeed','partialBatch':'sticky failure, incomplete run, no retry; unpersisted admitted rows fail manifest validation','durableFlush':'unchanged at each segment end','adoption':'EXPERIMENT ONLY pending throughput and fault validation','hashes':{n:hashlib.sha256((C/n).read_bytes()).hexdigest() for n in ['AuthoritativeEvents.cs','WriterBench.cs','bench.ps1']}},f,indent=2)
