import pathlib,json,hashlib,uuid,shutil,ast,difflib
R=pathlib.Path(__file__).parent;pre=json.loads((R/'preflight.json').read_text());host=json.loads((R/'host-preflight.json').read_text(encoding='utf-8-sig'));assert pre['status']=='PASS_PENDING_HOST_CHECK' and not host['processes'] and not host['traces'] and host['traceExit']==0
H=pathlib.Path(pre['diagnostic']);C=pathlib.Path(pre['collector']);D=pathlib.Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code';D.mkdir(parents=True)
for x in json.loads((H/'hardening-hashes.json').read_text()):
 assert hashlib.sha256((H/x['name']).read_bytes()).hexdigest()==x['sha256'];shutil.copyfile(H/x['name'],D/x['name'])
for n in ('baseline_collect.py','baseline_contract.py','baseline_hash_worker.py','baseline_finalize.py','baseline-limits.json','baseline-allowlist.json'):
 assert (D/n).read_bytes()==(C/n).read_bytes()
for n in ('secondary_sampling.py','test_wiring.py'):shutil.copyfile(R/n,D/n)
s=(D/'baseline_collect.py').read_text().replace('from journal import ticks,frequency','from journal import ticks,frequency\nfrom secondary_sampling import SecondarySampler')
s=s.replace('health=None;worker=None;probes=[]','health=None;worker=None;sampler=None;probes=[]')
s=s.replace("  worker=Managed(","  sampler=SecondarySampler(root,tree,launched,ledger)\n  worker=Managed(",1)
s=s.replace("   health.check()\n   if ticks()", "   health.check()\n   if ledger.primary:raise RuntimeError('Required diagnostic evidence failed')\n   if ticks()")
s=s.replace("  proof=secondary('tree-cleanup'", "  if sampler:secondary('sampler-close',sampler.close)\n  proof=secondary('tree-cleanup'")
s=s.replace("producer='baseline_collect.py'","producer='large_collect.py'");ast.parse(s);(D/'large_collect.py').write_text(s)
(R/'collector-wiring.diff').write_text(''.join(difflib.unified_diff((C/'baseline_collect.py').read_text().splitlines(True),s.splitlines(True),fromfile=str(C/'baseline_collect.py'),tofile=str(D/'large_collect.py'))))
s=(D/'baseline_launch.ps1').read_text().replace("'baseline-source.json'","'run-source.json'").replace("'baseline_monitor.ps1'","'timed_monitor.ps1'").replace("'baseline_collect.py'","'large_collect.py'")
s=s.replace(" Ready $etw 'etw-ready.json'", """ Ready $etw 'etw-ready.json';Write-Output ('KERNEL_READY '+$root)
 $gateClock=[Diagnostics.Stopwatch]::StartNew()
 while(!(Test-Path -LiteralPath (Join-Path $root 'allow-app-prompt'))){if($etw.HasExited -or $gateClock.Elapsed.TotalSeconds -gt 120){throw 'Second observer prompt gate expired'};Start-Sleep -Milliseconds 100}""")
# Finalization is invoked only after independent timing, sampler and source-ACL checks.
s=s[:s.index('& $py -B (Join-Path $PSScriptRoot \'baseline_finalize.py\')')]+"Write-Output ('OBSERVERS_CLOSED_PENDING_INDEPENDENT_REVIEW '+$root)\n"
(D/'large_launch.ps1').write_text(s)
manifest=[dict(name=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(D.iterdir()) if p.is_file()]
(D/'run-source.json').write_text(json.dumps(manifest,indent=2))
with (R/'candidate.json').open('x') as f:json.dump(dict(code=str(D),source=str(pre['source']),collector=str(C),diagnostic=str(H),hashes=manifest,thresholds=json.loads((D/'baseline-limits.json').read_text()),changes=['large_collect.py: orchestration only','secondary_sampling.py: fixed bounded query supervisor','large_launch.ps1: selects validated observers; finalization gated on independent review','test_wiring.py']),f,indent=2)
print(D)
