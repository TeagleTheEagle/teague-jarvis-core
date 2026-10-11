import pathlib,json,hashlib,difflib
R=pathlib.Path(__file__).resolve().parent;plan=json.loads((R/'plan.json').read_text(encoding='utf-8-sig'));C=pathlib.Path(plan['live_code']);OLD=pathlib.Path(plan['previous'])
for n in ('evidence_support.py','trace_fixture.py','test_hardening.py','collect_hardened.py'):(C/n).write_bytes((R/n).read_bytes())
# The reviewed collector boundary now delegates to the hardened diagnostic collector.
(C/'collect.py').write_text('"""Diagnostic-only hardened candidate; original candidate preserved separately."""\nimport collect_hardened\n')
s=(OLD/'monitor.ps1').read_text();s=s.replace('$producerClosed=$false;$proofRead=$false;', '$producerFailed=$false;$producerClosed=$false;$proofRead=$false;')
s=s.replace("$proof.status -ne 'LIVE_MONITOR_HEALTHY' -or -not $proof.allHandlesExited", "($proof.status -notin @('LIVE_MONITOR_HEALTHY','FAILED_CLOSED')) -or -not $proof.allHandlesExited")
s=s.replace("$gate.ConfirmExits([int[]]", "$producerFailed=($proof.status -eq 'FAILED_CLOSED')\n   $gate.ConfirmExits([int[]]")
s=s.replace("$gate.Dispose()", "$gate.Dispose()\nif($producerFailed){Save 'monitor-failure.json' @{error='Producer failed; late events drained and flushed; no acceptance';qpc=[Diagnostics.Stopwatch]::GetTimestamp()};exit 1}")
(C/'monitor.ps1').write_text(s)
s=(OLD/'finalize.py').read_text().replace("('collector-failure.json','monitor-failure.json'", "('primary-failure.json','collector-failure.json','monitor-failure.json'")
s=s.replace("  (root/'finalization-failure.json').write_text(json.dumps({'traceback':traceback.format_exc()}));raise", "  from evidence_support import Ledger\n  Ledger(root).fail('finalization/archive')\n  raise")
(C/'finalize.py').write_text(s)
s=(OLD/'diagnostic_launch.ps1').read_text().replace("'A','B','C','D','E','F'","'A','B','C','D','E'").replace("$Run='ladder-'", "$Run='harden-'").replace("'diagnose.py'", "'collect.py'")
(C/'diagnostic_launch.ps1').write_text(s)
rows=[];diff=[]
for p in sorted(C.iterdir()):
 if p.is_file() and p.suffix in ('.py','.ps1','.cs','.c','.exe','.json','.obj'):
  rows.append(dict(path=str(p),name=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),size=p.stat().st_size))
  old=OLD/p.name
  if p.suffix in ('.py','.ps1','.cs','.c') and (not old.exists() or old.read_bytes()!=p.read_bytes()):diff.extend(difflib.unified_diff(old.read_text().splitlines(True) if old.exists() else [],p.read_text().splitlines(True),fromfile='previous/'+p.name,tofile='candidate/'+p.name))
(R/'candidate-diff.patch').write_text(''.join(diff));(R/'candidate-source.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(dict(sourceFiles=len(rows),code=str(C))))
