import pathlib,json,hashlib,uuid,shutil,zipfile
R=pathlib.Path(__file__).parent;OLD=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\e863e012a81649fe9c82fce9838aa2e3\code')
P=R.parent/'stage6-probe-acceptance-20260920'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
z=P/'evidence.zip'
assert sha(z)=='1497b9124102c4388f967141a44c31f6b7c9e8685643a8f2cc876085be640ef3'
m=json.loads((P/'archive-manifest.json').read_text())
with zipfile.ZipFile(z) as f:
 for x in m['files']:assert hashlib.sha256(f.read(x['name'])).hexdigest()==x['sha256']
 assert len(f.namelist())==848
before=[]
for x in json.loads((P/'final-source-hashes.json').read_text()):
 p=OLD/x['name'];assert sha(p)==x['sha256'];before.append(dict(path=str(p),name=p.name,sha256=sha(p),size=p.stat().st_size))
D=pathlib.Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code'
D.mkdir(parents=True)
for x in before:shutil.copyfile(x['path'],D/x['name'])
for n in ('native_probe.c','J6ProbeNative.exe','J6ProbeToken.exe'):
 shutil.copyfile(pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\90e9469000dd4530a86b98fad67d7089\code')/n,D/n)
for n in ('controls.py',):shutil.copyfile(pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\90e9469000dd4530a86b98fad67d7089\code')/n,D/n)
(D/'controls-config.json').write_text(json.dumps(dict(variants=['A_D','B_D','C_D','D_D'])))
p=D/'probe_timing.py';s=p.read_text().replace('def __init__(self,executable):','def __init__(self,executable,args=None,startupinfo=None):\n  args=[] if args is None else args').replace('arguments=[]','arguments=args').replace('subprocess.Popen([str(executable)],stdout=', 'subprocess.Popen([str(executable),*args],startupinfo=startupinfo,stdout=')
# Diagnostic recording only: retain observer timeout, then sample current handle independently.
s=s.replace("if self.observer.is_alive() or self.row.get('observerResult')!=0:raise RuntimeError('Probe exit observation/cleanup uncertain')", "self.row['independentObserverFailed']=self.observer.is_alive() or self.row.get('observerResult')!=0")
p.write_text(s)
p=D/'EventTap.cs';s=p.read_text().replace('public int pid,eventId','public int parentPid,pid,eventId').replace('if(name=="ProcessID")','if(name=="ParentProcessID")r.parentPid=Convert.ToInt32(value);\n    else if(name=="ProcessID")');p.write_text(s)
p=D/'monitor.ps1';s=p.read_text().replace('("SELECT * FROM "+$pair[0]+" WHERE ProcessName LIKE \'J6Probe%\'")','("SELECT * FROM "+$pair[0])')
s=s.replace('$exact.Reconcile();$gate.Seal($true,$true);$gate.AssertSealed();$success=$true','$exact.Reconcile();Mark \'diagnostic.freeze.without.acceptance.seal\';$success=$true')
s=s[:s.index('# A zero exit and this receipt')]+"Save 'diagnostic-monitor-result.json' @{status='DIAGNOSTIC_ONLY';run=$nonce;events=$count;success=$success;acceptance=$false}\n$gate.Dispose()\n"
p.write_text(s)
p=D/'resources.ps1';s=p.read_text().replace('pwsh,python,MsMpEng','pwsh,python,MsMpEng,J6Probe,J6ProbeNative,J6ProbeToken').replace('state=[string]$_.ThreadState;priority=',"state=[string]$_.ThreadState;waitReason=$(if($_.ThreadState -eq 'Wait'){[string]$_.WaitReason}else{'NOT_WAITING'});priority=");p.write_text(s)
plan=dict(live_code=str(D),previous=str(OLD),report=str(R),archive=r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 DRY PROBE DIAGNOSIS 20260920',baselineArchiveSHA256=sha(z),baselineMembers=848,diagnosticOnly=True,ladder=['A','B','C','D','E','F'],stopAtFirstHardDeadline=True)
for name,value in [('plan.json',plan),('source-before.json',before)]:
 with (R/name).open('x') as f:json.dump(value,f,indent=2)
print(json.dumps(plan))
