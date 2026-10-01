import pathlib,json,hashlib,uuid,shutil,ast,difflib
R=pathlib.Path(__file__).parent;O=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\1c1f5d0c390b42cc9ba9f4f6221dabc6\code');D=pathlib.Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code'
rows=json.loads((O/'baseline-source.json').read_text())
for x in rows:assert hashlib.sha256((O/x['name']).read_bytes()).hexdigest()==x['sha256']
D.mkdir(parents=True,exist_ok=False)
for x in rows:shutil.copyfile(O/x['name'],D/x['name'])
changes=[]
def change(name,fn):
 before=(D/name).read_text();after=fn(before);assert before!=after;(D/name).write_text(after);changes.append(dict(name=name,before=hashlib.sha256((O/name).read_bytes()).hexdigest(),after=hashlib.sha256((D/name).read_bytes()).hexdigest()));(R/(name+'.diff')).write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='original/'+name,tofile='candidate/'+name)))
def checker(s):
 s=s.replace('import pathlib,json,collections,sys','import pathlib,json,collections,sys\nfrom lineage import associate,parent_valid')
 a=s.index(' # Derive the app tree independently');b=s.index(' for x in producer[',a)
 s=s[:a]+''' # Bind independent application records to time-qualified identities, never PID-only ancestry.
 association=associate(rows,events,scope)
 if association['unknown']:fail('UNKNOWN_APPLICATION_LINEAGE')
 for x in tracked:
  if x['sequence']!=roots[0]['sequence'] and not parent_valid(x,byseq.get(x['parentSequence'],dict(pid=-1,sequence='',created='0',exitFiletime='0',startQpc=0,stopQpc=0))):fail('UNKNOWN_PARENT_IDENTITY')
'''+s[b:]
 s=s.replace("starts=[a for a in events if a['pid']==x['pid'] and a['kind']=='start'];stops=[a for a in events if a['pid']==x['pid'] and a['kind']=='stop']","starts=[a for a in association['bound'].get(x['sequence'],[]) if a['kind']=='start'];stops=[a for a in association['bound'].get(x['sequence'],[]) if a['kind']=='stop']")
 s=s.replace("  if len(ks)!=1:why.append('PID_REUSE_AMBIGUITY')", "  if len([a for a in ks if a['created']==x['created']])!=1:why.append('CREATION_IDENTITY_AMBIGUITY')")
 s=s.replace("primaryFailure=producer.get('primary_failure')", "lineageUnknown=association['unknown'],lineageExcluded=association['outside'],primaryFailure=producer.get('primary_failure')")
 return s
change('cleanup_checker.py',checker)
def support(s):
 s=s.replace("if not parents or any(k[0]==pid for k in self.rows):continue","if not parents:continue")
 s=s.replace("ts=times(h);matches=", "ts=times(h)\n      if (pid,ts[0]) in self.rows:K.CloseHandle(h);continue\n      matches=")
 return s
change('evidence_support.py',support)
def timing(s):
 s=s.replace('public sealed class TimingRow {public string stage;', 'public sealed class SpanRow {public string stage;public long start,end,loop,thread;public double seconds;}\npublic sealed class TimingRow {public long loop;public string stage;')
 s=s.replace('public static class LoopTiming {','public static class LoopTiming {\n static long loopSequence;public static long CurrentLoop {get{return Interlocked.Read(ref loopSequence);}}\n public static void BeginLoop(){Interlocked.Increment(ref loopSequence);}\n static readonly ConcurrentQueue<SpanRow> spans=new ConcurrentQueue<SpanRow>();\n public static SpanRow[] SpanSnapshot(){return spans.ToArray();}')
 s=s.replace('var row=new TimingRow{stage=stage,', 'var row=new TimingRow{loop=CurrentLoop,stage=stage,')
 a=s.index(' public sealed class Region:IDisposable');b=s.index(' public static Region Span',a)
 s=s[:a]+''' public sealed class Region:IDisposable {
  readonly string name;readonly long begin,loop,thread;bool done;
  public Region(string n){name=n;begin=Stopwatch.GetTimestamp();loop=CurrentLoop;thread=GetCurrentThreadId();Note(n+".begin");}
  public void Dispose(){if(done)return;done=true;long end=Stopwatch.GetTimestamp();if(spans.Count<1000000)spans.Enqueue(new SpanRow{stage=name,start=begin,end=end,loop=loop,thread=thread,seconds=(end-begin)/(double)Stopwatch.Frequency});else Interlocked.Increment(ref Overflow);Note(name+".end");}
 }
'''+s[b:]
 s=s.replace('Monitor.Enter(target,ref taken);','using(Span("queue.lock.acquire."+n)){Monitor.Enter(target,ref taken);}')
 return s
change('LoopTiming.cs',timing)
def tap(s):
 s=s.replace(' public static void Capture(object a,string kind,string stage,object collection) {',' public static void Capture(object a,string kind,string stage,object collection) {\n  using(LoopTiming.Span("callback."+stage)){')
 s=s.replace(' static string Attach(object target', ' }\n static string Attach(object target')
 return s
change('EventTap.cs',tap)
change('probe_timing.py',lambda s:s.replace("self.row['popenReturnedQpc']=ticks();", "self.row['handleRetainedQpc']=ticks();self.row['popenReturnedQpc']=ticks();"))
for p in R.iterdir():
 if p.suffix in ('.py','.ps1') and p.name not in ('build_candidate.py',):shutil.copyfile(p,D/p.name)
for p in D.glob('*.py'):ast.parse(p.read_text())
(D/'controls-config.json').write_text(json.dumps(dict(variants=['A_D'],c_image_dir='DISABLED')))
# Launcher is a new fixed diagnostic driver, preserving all observer and cleanup bounds.
launcher=(R.parent/'stage6-large-correlation-20260920'/'diag_launch.ps1').read_text()
launcher=launcher.replace("param([ValidateSet('ladder','heartbeat')][string]$Mode)","param()")
launcher=launcher.replace("'diagnostic-hashes.json'","'hardening-hashes.json'").replace("'correlation-'+$Mode+'-'","'hardening-'").replace("'baseline_monitor.ps1'","'timed_monitor.ps1'").replace("'diag_collect.py') $Run $Mode","'hardened_collect.py') $Run")
(D/'hardening_launch.ps1').write_text(launcher)
manifest=[dict(name=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(D.iterdir()) if p.is_file()]
(D/'hardening-hashes.json').write_text(json.dumps(manifest,indent=2))
with (R/'candidate.json').open('x') as f:json.dump(dict(code=str(D),original=str(O),changes=changes,hashes=manifest,originalHashes=rows),f,indent=2)
print(D)
