import pathlib,json,subprocess,sys,uuid,statistics
from evidence_io import create_json
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'active-workspace.json').read_text())['code']);sys.path.insert(0,str(C))
from application_authority import verify
exe=r'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
results=[]
for label,count,padding in [('high-rate',200000,0),('large-record',200000,500)]:
 run=C/(label+'-'+uuid.uuid4().hex);run.mkdir();(run/'temp').mkdir()
 args=[exe,'-NoProfile','-NonInteractive','-File',str(C/'run_stream.ps1'),'-Code',str(C),'-Run',run.name,'-Events',str(count),'-Padding',str(padding)]
 p=subprocess.run(args,capture_output=True,text=True,timeout=60)
 result=dict(label=label,run=str(run),args=args,exit=p.returncode,stdout=p.stdout,stderr=p.stderr,scope='Actual EventTap/Persisted/sink code; generated events, not actual Windows/ETW/queue/heartbeat acceptance')
 if (run/'app-authority.json').exists():
  m=json.loads((run/'app-authority.json').read_text());result['manifest']=m
  if m['fault'] is None:
   result['verified']=verify(run);result['generated']=json.loads((run/'generated-load.json').read_text())
   sizes=[]
   for part in m['segments']:
    with (run/part['name']).open('rb') as f:sizes.extend(len(line) for line in f)
   sizes.sort();result['sizes']=dict(mean=statistics.mean(sizes),p95=sizes[int((len(sizes)-1)*.95)],p99=sizes[int((len(sizes)-1)*.99)],max=max(sizes))
 result['result']='PASS_COMPONENT_ONLY' if p.returncode==0 and result.get('generated',{}).get('recordsPerSecond',0)>=100080 else 'FAIL'
 create_json(R/(label+'-result.json'),result);results.append(dict(label=label,result=result['result'],run=str(run),exit=p.returncode,generated=result.get('generated'),fault=result.get('manifest',{}).get('fault')))
 print(json.dumps(results[-1]),flush=True)
 # Preserve each failed case; no rerun. A distinct larger-payload diagnostic is not a retry.
create_json(R/'capacity-results.json',results)
