"""Prepare a new synthetic-validation candidate; never access VM paths."""
import pathlib, hashlib, json, shutil, datetime
R=pathlib.Path(__file__).resolve().parent
D=R/'stage6-stop-event-diagnosis-20260920'
O=R/'stage6-heartbeat-decoupled-20260918'
S=R/'stage6-heartbeat-resume-20260920'
N=R/'stage6-eventidentity-fix-20260920'
N.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inventory=[]
for root in (D,O,S):
 for p in sorted(root.rglob('*')):
  if p.is_file():inventory.append(dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns))
(N/'preserved-before.json').write_text(json.dumps(inventory,indent=2))
mapping={}
for name in ('monitor.ps1','EventTap.cs','collect.py','launch.ps1'):mapping[name]=D/name
for name in ('journal.py','workload.py','resources.ps1','J6Probe.exe','finalize.py','campaign.py','hash_sources.py','Start-DryRun.ps1','test_journal.py','test_processes.py','process_fixture.py','test_finalization.py','test_extended_finalization.py','test_probe_handles.py'):mapping[name]=O/name
for name in ('run_focused.py','test_event_rejection.py'):mapping[name]=S/name
(N/'source-before').mkdir()
for name,p in mapping.items():
 shutil.copyfile(p,N/name);shutil.copyfile(p,N/'source-before'/name)
(N/'source-before.json').write_text(json.dumps([dict(path=str(p),candidate=str(N/n),sha256=sha(p)) for n,p in mapping.items()],indent=2))
(N/'DEFECT-LOCATION.md').write_text('''# Pre-change validation-only defect
The archived source paths and SHA-256 values are in source-before.json. All originals remain untouched.

monitor.ps1: Register-CimIndicationEvent creates local Win32_ProcessStartTrace / Win32_ProcessStopTrace subscriptions. Callback source is Microsoft.Management.Infrastructure.CimCmdlets.CimIndicationWatcher.CimIndicationArrived. PowerShell queues PSEventArgs in System.Management.Automation.PSEventArgsCollection, exposed through ExecutionContext.Events.ReceivedEvents; its enqueue notification is PSEventReceived. EventTap.AttachSource/AttachQueue observe these without consuming them.

Drain obtains Get-Event snapshots, serializes the selected PSEventArgs.SourceEventArgs.NewEvent using ConvertTo-Json and writes it using System.IO.File.AppendAllText. It then executes the defective destructive operation:

    Remove-Event -EventIdentifier $ev.EventIdentifier

This removes every matching external number, not just the successfully written object. The finally cleanup also pipes pending entries into Remove-Event. Both destructive numeric-key paths must disappear from the candidate. JARVIS runtime code is not involved.
''',encoding='utf-8')
print(N)
