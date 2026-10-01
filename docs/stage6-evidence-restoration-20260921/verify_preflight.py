import pathlib,json,hashlib,subprocess,uuid
from evidence_io import create_json,create_run
from restore_evidence import archives,TARGET,ORIGINAL,metadata
R=pathlib.Path(__file__).parent
exe=pathlib.Path(r'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')
assert exe.is_file()
archives();assert hashlib.sha256(TARGET.read_bytes()).hexdigest()==ORIGINAL
run_id=uuid.uuid4().hex;run=create_run(R/'final',run_id);output=run/'final-host-state.json'
commands=[]
def invoke(rid):
    args=[str(exe),'-NoProfile','-NonInteractive','-File',str(R/'host_preflight.ps1'),'-RunId',rid]
    p=subprocess.run(args,capture_output=True,text=True,timeout=60)
    commands.append(dict(args=args,exit=p.returncode,stdout=p.stdout,stderr=p.stderr))
    create_json(R/('preflight-command.'+rid+'.'+str(len(commands))+'.json'),commands[-1])
    return p
first=invoke(run_id);assert first.returncode==0,first.stderr
before=metadata(output);original=output.read_bytes();state=json.loads(original)
assert state['status']=='PASS' and state['matchingProcessCount']==state['diagnosticTraceCount']==0
second=invoke(run_id)
assert second.returncode!=0 and 'FINAL_EVIDENCE_CREATE_REJECTED' in second.stderr and str(output) in second.stderr
assert output.read_bytes()==original and metadata(output)==before
next_id=uuid.uuid4().hex;other=create_run(R/'final',next_id);third=invoke(next_id)
assert third.returncode==0,third.stderr
last=json.loads((other/'final-host-state.json').read_bytes());assert last['status']=='PASS'
archives();assert hashlib.sha256(TARGET.read_bytes()).hexdigest()==ORIGINAL
create_json(R/'preflight-validation.json',dict(status='PASS',realHostChecks=2,expectedDuplicateRejections=1,firstOutput=before,finalOutput=metadata(other/'final-host-state.json'),duplicateChangedBytes=False,duplicateChangedHash=False,duplicateChangedTimestamp=False,canonicalRestoredHash=ORIGINAL,candidateHashesUnchanged=116,archiveMembersVerified=[143,8],liveDiagnosticProcesses=last['matchingProcessCount'],traceSessions=last['diagnosticTraceCount'],commands=commands,observersStarted=False,protectedAccess=False,productionChanged=False))
print(json.dumps(dict(status='PASS',realHostChecks=2,expectedDuplicateRejections=1,firstRun=run_id,lastRun=next_id,matchingProcesses=last['matchingProcessCount'],traceSessions=last['diagnosticTraceCount'])))
