import pathlib,json,subprocess,sys,uuid,time
from evidence_io import create_json,create_bytes
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'active-workspace.json').read_text())['code'])
for name in ('IntegratedStreamTests.cs','run_stream.ps1'):create_bytes(C/name,(R/name).read_bytes())
run=C/('tap-'+uuid.uuid4().hex);run.mkdir();(run/'temp').mkdir()
exe=r'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
args=[exe,'-NoProfile','-NonInteractive','-File',str(C/'run_stream.ps1'),'-Code',str(C),'-Run',run.name,'-Events','12000']
p=subprocess.run(args,capture_output=True,text=True,timeout=60)
create_json(R/'tap-load-command.json',dict(args=args,exit=p.returncode,stdout=p.stdout,stderr=p.stderr,run=str(run)))
assert p.returncode==0,p.stderr
sys.path.insert(0,str(C));from application_authority import verify,load_inputs
v=verify(run);t,e,r=load_inputs(run);assert len(t)==24000 and len(e)==len(r)==12000 and v['records']==36000 and v['tapRows']==20000 and v['tapTruncated']==4000
create_json(R/'tap-integration-focused.json',dict(status='PASS',run=str(run),verification=v,completeCallbackRecords=len(t),completeRawEvents=len(e),completeReceipts=len(r),snapshotNotUsed=True,limitation='Actual EventTap/sink/reader path; generated inputs, no Windows lifecycle or full cleanup acceptance'))
print(json.dumps(dict(status='PASS',verification=v)))
