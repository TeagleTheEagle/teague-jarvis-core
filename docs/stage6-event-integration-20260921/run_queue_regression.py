import pathlib,json,subprocess,uuid
from evidence_io import create_json,create_bytes
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'active-workspace.json').read_text())['code'])
create_bytes(C/'queue_regression.ps1',(R/'queue_regression.ps1').read_bytes())
root=C/('queue-'+uuid.uuid4().hex);root.mkdir();(root/'temp').mkdir()
args=[r'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe','-NoProfile','-NonInteractive','-File',str(C/'queue_regression.ps1'),'-Code',str(C),'-Run',root.name]
p=subprocess.run(args,capture_output=True,text=True,timeout=80)
create_json(R/'queue-regression-command.json',dict(args=args,exit=p.returncode,stdout=p.stdout,stderr=p.stderr,run=str(root)))
assert p.returncode==0,p.stderr
v=json.loads((root/'queue-regression.json').read_text());create_json(R/'queue-regression-result.json',v)
print(json.dumps(dict(checks=v['regression']['checks'],groups=len(v['regression']['groups']),timingOverflow=v['timingOverflow'],streaming=v['streamingStats'])))
