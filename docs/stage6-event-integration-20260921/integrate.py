import pathlib,json,hashlib,difflib
from evidence_io import create_bytes,create_json
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'active-workspace.json').read_text())['code'])
changes=[]
def edit(name,fn):
 p=C/name;before=p.read_bytes();after=fn(before.decode('utf-8-sig')).encode()
 assert before!=after,name
 create_bytes(R/(name+'.before'),before)
 p.write_bytes(after) # New unaccepted candidate source only; original116 remain frozen.
 changes.append(dict(path=str(p),before=hashlib.sha256(before).hexdigest(),after=hashlib.sha256(after).hexdigest()))
 create_bytes(R/(name+'.diff'),''.join(difflib.unified_diff(before.decode('utf-8-sig').splitlines(True),after.decode().splitlines(True),fromfile='frozen/'+name,tofile=str(p))).encode())
def tap(s):
 s=s.replace('static long sequence;','static AuthoritativeEvents authority; public static long Truncated; public static string StreamFailure {get{return authority==null?"NOT_INITIALIZED":authority.Failure;}}\n public static void Initialize(string root){if(authority!=null)throw new InvalidOperationException("Already initialized");authority=new AuthoritativeEvents(root);}\n public static void Finish(){authority.Finish(rows.Count,Truncated);}\n public static string Serialize(TapRow r){var b=new System.Text.StringBuilder("{");bool first=true;foreach(var f in typeof(TapRow).GetFields()){if(!first)b.Append(",");first=false;object v=f.GetValue(r);b.Append(AuthoritativeEvents.Quote(f.Name)).Append(":").Append(v is string||v==null?AuthoritativeEvents.Quote((string)v):Convert.ToString(v,System.Globalization.CultureInfo.InvariantCulture));}return b.Append("}").ToString();}\n public static bool Record(TapRow row){Add(row);return StreamFailure==null;}\n public static void Persisted(string raw,string receipt){if(!authority.Publish("CIM_PROCESS_NOTIFICATION","persistence","{\\\"event\\\":"+raw+",\\\"receipt\\\":"+receipt+"}",null))throw new InvalidOperationException(authority.Failure);}\n static long sequence;')
 s=s.replace('if(r.seq>20000) { Interlocked.Increment(ref Overflow);return; } rows.Enqueue(r);','if(authority==null||!authority.Publish("CIM_PROCESS_NOTIFICATION",r.stage,Serialize(r),r.nativeTime)){Interlocked.Increment(ref Errors);return;}\n  if(r.seq>20000) { Interlocked.Increment(ref Truncated);return; } rows.Enqueue(r);')
 return s
edit('EventTap.cs',tap)
def queue(s):
 s=s.replace('readonly PSEventArgsCollection queue;','readonly bool streaming;\n readonly PSEventArgsCollection queue;')
 s=s.replace('public ExactEventQueue(PSEventArgsCollection q,string[] ids) {','public ExactEventQueue(PSEventArgsCollection q,string[] ids):this(q,ids,false) {}\n public ExactEventQueue(PSEventArgsCollection q,string[] ids,bool streamMode) {\n  streaming=streamMode;')
 s=s.replace('if(sequence>=20000)','if(streaming?entries.Count>=20000:sequence>=20000)')
 s=s.replace('e.Removed=true;removedCount++;selected=null;','e.Removed=true;removedCount++;selected=null;if(streaming)entries.Remove(e.Event);')
 return s
edit('event_queue.cs',queue)
def monitor(s):
 s=s.replace("(Join-Path $PSScriptRoot 'LoopTiming.cs'),","(Join-Path $PSScriptRoot 'AuthoritativeEvents.cs'),(Join-Path $PSScriptRoot 'LoopTiming.cs'),")
 old="function Save($n,$v){Invoke-J6TimedStage ('output.'+$n) {[IO.File]::WriteAllText((Join-Path $root $n),($v|ConvertTo-Json -Depth 12))}}"
 new="function Save($n,$v){Invoke-J6TimedStage ('output.'+$n) {$mode=if($n -eq 'app-health.json'){[IO.FileMode]::Create}else{[IO.FileMode]::CreateNew};$f=[IO.FileStream]::new((Join-Path $root $n),$mode,[IO.FileAccess]::Write,[IO.FileShare]::Read);try{$b=[Text.Encoding]::UTF8.GetBytes(($v|ConvertTo-Json -Depth 12));$f.Write($b,0,$b.Length);$f.Flush($true)}finally{$f.Dispose()}}}"
 assert old in s;s=s.replace(old,new)
 s=s.replace('$exact=[ExactEventQueue]::new($ExecutionContext.Events.ReceivedEvents,[string[]]$ids)','$exact=[ExactEventQueue]::new($ExecutionContext.Events.ReceivedEvents,[string[]]$ids,$true)\n[EventTap]::Initialize($root)')
 s=s.replace('[EventTap]::Overflow -or','[EventTap]::StreamFailure -or')
 old='$script:lastEvent=[Diagnostics.Stopwatch]::GetTimestamp();$receipts.Add(@{queueSequence=$entry.QueueSequence;pid=$row.pid;kind=$row.kind;persistedQpc=$script:lastEvent;removed=$entry.Removed})'
 new='$script:lastEvent=[Diagnostics.Stopwatch]::GetTimestamp();$receipt=@{queueSequence=$entry.QueueSequence;pid=$row.pid;kind=$row.kind;persistedQpc=$script:lastEvent;removed=$entry.Removed};$receipts.Add($receipt);[EventTap]::Persisted(($row|ConvertTo-Json -Compress),($receipt|ConvertTo-Json -Compress))'
 assert old in s;s=s.replace(old,new)
 s=s.replace('[EventTap]::Detach()','[EventTap]::Detach()\n try{[EventTap]::Finish();if([EventTap]::StreamFailure){$success=$false;$errorRecord=@{error=[EventTap]::StreamFailure}}}catch{$success=$false;$errorRecord=@{error=$_.Exception.Message}}')
 s=s.replace('tapOverflow=[EventTap]::Overflow;','tapOverflow=[EventTap]::Overflow;tapTruncated=[EventTap]::Truncated;authoritativeManifest="app-authority.json";')
 s=s.replace('[IO.File]::WriteAllText((Join-Path $root \'stage-timing.json\'),($trace|ConvertTo-Json -Depth 8))',"Save 'stage-timing.json' $trace")
 return s
edit('timed_monitor.ps1',monitor)
create_bytes(C/'AuthoritativeEvents.cs',(R/'AuthoritativeEvents.cs').read_bytes())
create_json(R/'integration-changes-step1.json',changes)
print(json.dumps(dict(changed=len(changes),added='AuthoritativeEvents.cs',code=str(C))))
