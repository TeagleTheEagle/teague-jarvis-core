import json,pathlib,queue,subprocess,sys,threading,uuid
R=pathlib.Path(__file__).resolve().parent;C=pathlib.Path(json.loads((R/'candidate.json').read_text())['code']);sys.path.insert(0,str(C))
from workspace import new_run,activate_temp
root=new_run('ready-publication-'+uuid.uuid4().hex);activate_temp(root)
s=(C/'health_publication.ps1').read_text(encoding='utf8');needle='    [IO.File]::Move($temp,$final)'
assert s.count(needle)==1
# Deterministic fixture gate only, after close/flush and before final publication.
s=s.replace(needle,"    [Console]::Out.WriteLine('STAGED');[Console]::Out.Flush();if([Console]::In.ReadLine() -ne 'GO'){throw 'fixture gate'}\n"+needle)
(root/'gated.ps1').write_text(s,encoding='utf8')
script=root/'run.ps1';script.write_text('''param([string]$Root)
$ErrorActionPreference='Stop'
. (Join-Path $Root 'gated.ps1')
$p=New-J6HealthPublisher $Root @{run='fixture';pid=$PID;created='123';frequency=10000000}
try{Write-J6HealthRecord $p 1;Publish-J6Ready $Root $p @{pid=$PID;created='123'};[Console]::Out.WriteLine('PUBLISHED')}finally{Close-J6HealthPublisher $p}
''',encoding='utf8')
pwsh=r'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
p=subprocess.Popen([pwsh,'-NoProfile','-File',str(script),'-Root',str(root)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,creationflags=0x08000000)
q=queue.Queue();thread=threading.Thread(target=lambda:[q.put(x.strip()) for x in p.stdout],daemon=True);thread.start()
checks=0
try:
    assert q.get(timeout=10)=='STAGED';checks+=1
    assert not (root/'app-ready.json').exists();checks+=1
    assert json.loads((root/'app-ready.pending').read_text())['pid']==p.pid;checks+=1
    p.stdin.write('GO\n');p.stdin.flush();assert q.get(timeout=10)=='PUBLISHED';checks+=1
    assert p.wait(10)==0;checks+=1
    assert json.loads((root/'app-ready.json').read_text())['pid']==p.pid;checks+=1
    assert not (root/'app-ready.pending').exists();checks+=1
finally:
    p.stdin.close()
    p.wait(10);thread.join(2);assert not thread.is_alive()
    err=p.stderr.read();p.stdout.close();p.stderr.close()
with (R/'readiness-result.json').open('x') as f:json.dump(dict(status='PASS',checks=checks,root=str(root),pid=p.pid,exit=p.returncode,stderr=err),f,indent=2)
print(json.dumps(dict(status='PASS',checks=checks)))
