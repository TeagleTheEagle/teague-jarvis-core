import ast,difflib,hashlib,json,os,uuid,zipfile
from pathlib import Path
R=Path(__file__).resolve().parent;P=R.parent/'stage6-medium-v5-fresh-20260922'
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,indent=2);f.flush();os.fsync(f.fileno())
files=load(P/'candidate-frozen.json')['files'];old=Path(load(P/'preflight.json')['code'])
for x in files:assert sha(x['path'])==x['sha256']
a=load(P/'archive-verification.json');archive=Path(a['archive']);manifest=archive.parent/'manifest.json'
assert sha(archive)==a['archiveSHA256'] and sha(manifest)==a['manifestSHA256']
with zipfile.ZipFile(archive) as z:
    assert len(z.namelist())==a['membersVerified']==len(set(z.namelist()))
    for x in load(manifest)['files']:
        b=z.read(x['name']);assert hashlib.sha256(b).hexdigest()==x['sha256'] and len(b)==x['bytes']
C=Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code';C.mkdir(parents=True)
for x in files:
    src=Path(x['path']);p=C/src.relative_to(old);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(src.read_bytes())
for n in ('health_reader.py','health_publication.ps1'):
    with (C/n).open('xb') as f:f.write((R/n).read_bytes())
p=C/'timed_monitor.ps1';s=p.read_text(encoding='utf8')
needle="Add-Type -Path @(";assert s.count(needle)==1
s=s.replace(needle,". (Join-Path $PSScriptRoot 'health_publication.ps1')\n$healthPublisher=$null\n"+needle)
s=s.replace("$mode=if($n -eq 'app-health.json'){[IO.FileMode]::Create}else{[IO.FileMode]::CreateNew};", "$mode=[IO.FileMode]::CreateNew;")
needle=" Save 'app-ready.json' @{pid=$PID;created=$me.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=$me.Path;frequency=$frequency;qpc=[Diagnostics.Stopwatch]::GetTimestamp();source='independent CIM subscriptions'}"
assert s.count(needle)==1
s=s.replace(needle," $ready=@{pid=$PID;created=$me.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=$me.Path;frequency=$frequency;qpc=[Diagnostics.Stopwatch]::GetTimestamp();source='independent CIM subscriptions'}\n $healthPublisher=New-J6HealthPublisher $root @{run=$Run;pid=$PID;created=$ready.created;frequency=$frequency}")
needle="  Invoke-J6TimedStage 'heartbeat.publish.overwrite' {Save 'app-health.json' @{qpc=$now;frequency=$frequency;pid=$PID;healthy=$true}}"
assert s.count(needle)==1
s=s.replace(needle,"  Invoke-J6TimedStage 'heartbeat.publish.append' {Write-J6HealthRecord $healthPublisher $now}\n  if($healthPublisher.Sequence -eq 1){Invoke-J6TimedStage 'ready.publish.complete' {Publish-J6Ready $root $healthPublisher $ready}}")
needle=" $success=$true";assert s.count(needle)==1
s=s.replace(needle," Close-J6HealthPublisher $healthPublisher\n"+needle)
needle="finally{\n";assert s.count(needle)==1
s=s.replace(needle,needle+" if($null -ne $healthPublisher -and !$healthPublisher.Closed){try{Close-J6HealthPublisher $healthPublisher}catch{$success=$false;$errorRecord=@{error=$_.Exception.Message}}}\n")
p.write_text(s,encoding='utf8')
p=C/'qualified_worker.py';s=p.read_text(encoding='utf8')
s=s.replace('from journal import ticks,frequency,PublisherWatch','from journal import ticks,frequency\nfrom health_reader import HealthReader')
s=s.replace('watch=PublisherWatch(ready);health_samples=[]','health_reader=HealthReader(root,ready);health_samples=[]')
start=s.index(' watch.check()');end=s.index('\nb=NativeBridge',start)
s=s[:start]+" v=health_reader.poll()\n health_samples.append(dict(qpc=ticks(),age=v['age']))"+s[end:]
s=s.replace("  time.sleep(.05)\nexcept", "  time.sleep(.05)\n health_reader.finalize()\nexcept")
s=s.replace("finally:\n closure=[]", "finally:\n health_reader.close()\n closure=[]")
s=s.replace('watch.close()\n','')
# Reader ownership covers bridge initialization failure too.
s=s.replace('b=NativeBridge(root);b.install();probes=[];failure=None\ntry:', 'probes=[];failure=None\ntry:\n b=NativeBridge(root);b.install()')
ast.parse(s);p.write_text(s,encoding='utf8')
changes=[]
for x in files:
    src=Path(x['path']);p=C/src.relative_to(old)
    if sha(p)!=x['sha256']:
        changes.append(dict(path=str(p),before=x['sha256'],after=sha(p)))
        (R/(p.name+'.diff')).write_text(''.join(difflib.unified_diff(src.read_text(encoding='utf8').splitlines(True),p.read_text(encoding='utf8').splitlines(True),fromfile=str(src),tofile=str(p))),encoding='utf8')
assert {Path(x['path']).name for x in changes}=={'qualified_worker.py','timed_monitor.ps1'}
save(R/'candidate.json',dict(code=str(C),old=str(old),priorFiles=files,changes=changes,priorArchive=a,newFiles=[dict(path=str(C/n),sha256=sha(C/n)) for n in ('health_reader.py','health_publication.ps1')],liveRunPrepared=False))
print(json.dumps(dict(status='IMPLEMENTED_TEST_CANDIDATE',code=str(C),changes=changes)))
