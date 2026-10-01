import pathlib,json,hashlib,ast
R=pathlib.Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=json.loads((R/'source-before.json').read_text(encoding='utf-8-sig'));checks={}
for row in before:
 p=pathlib.Path(row['Path']);target=R/'collect-original.py' if p.name=='collect.py' else p
 checks[p.name]=sha(target)==row['Hash'].lower()
assert all(checks.values()),checks
prior=R.parent/'stage6-heartbeat-journal-20260918'
checks['preserved_old_monitor']=sha(prior/'monitor.ps1')=='33b772b6a629ca838a919b844a49e70bd6e2a30dbb1fc38335e67fb2ee841398'
checks['journal_reader_unchanged']=sha(R/'journal.py')==sha(prior/'journal.py')
assert all(checks.values())
sources=[p for p in sorted(R.iterdir()) if p.suffix in ('.py','.ps1')]
for p in sources:
 if p.suffix=='.py':ast.parse(p.read_text())
event_results={}
for name in ('stepped','isolation','volume-d'):
 d=R/name;probes=json.loads((d/'probes.json').read_text());events=[json.loads(s) for s in (d/'events.jsonl').read_text().splitlines()]
 assert len({p['pid'] for p in probes})==len(probes)
 for p in probes:
  assert p['exit']==0
  for kind in ('start','stop'):assert sum(e['pid']==p['pid'] and e['kind']==kind for e in events)==1
 event_results[name]={'starts_expected':len(probes),'stops_expected':len(probes),'events_captured':len(events)}
cleanup=json.loads((R/'cleanup.json').read_text(encoding='utf-8-sig'));assert cleanup['query_succeeded'] and cleanup['helper_count']==0 and cleanup['virtualbox_count']==0
result={'status':'DIAGNOSTIC_EVIDENCE_VERIFIED_NOT_MONITOR_ACCEPTANCE','source_checks':checks,'python_syntax_files':sum(p.suffix=='.py' for p in sources),'source_hashes':{p.name:sha(p) for p in sources},'events':event_results,'protected_retry':'NOT_JUSTIFIED','historical_14_second_cause':'UNCONFIRMED','historical_13_7_second_cause':'UNCONFIRMED','historical_stage1_cause':'UNCONFIRMED'}
(R/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
