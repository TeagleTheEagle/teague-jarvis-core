"""Read-only diagnostic replay. Never an acceptance result or checker mutation."""
import json,copy,sys
from pathlib import Path
R=Path(__file__).parent;C=Path(json.loads((R/'candidate.json').read_text())['code']);root=Path(json.loads((R/'run.json').read_text())['path']);sys.path[:0]=[str(C/'medium-checker'),str(C)]
import checker_telemetry as ct
import checker_medium as old
import fresh_binding as fb
fb.verify_intake(C);b=old.adapter.read_bundle(root,root/'analysis',root/'final-host-state.json');measurement=ct.telemetry.verify(root);d=old.load(C/'medium-declaration.json')
assert b['qualification']['writer']==b['writer'],'Nested writer is NOT an exact copy; stop diagnosis'
view=ct.compatibility_view(b)
# Diagnostic in-memory normalization of the independently proven identical copy.
# Frozen source, original evidence and failed acceptance disposition stay unchanged.
view['qualification']['writer']=copy.deepcopy(view['writer'])
payload=old.adapter.validate(view,declaration=d)
envelope=dict(schema=old.VERSION,contract=old.CONTRACT,adapter='stage6-medium-combined-v1',runId=root.name,evidenceRoot=str(root),payload=payload,bundle=view)
rules=old.rules(envelope,declaration=d);fb.verify_intake(C)
result=dict(status='DIAGNOSTIC_REPLAY_ONLY_NOT_ACCEPTANCE',acceptance=False,exactFailure='SCHEMA_FIELDS:$.bundle.qualification.writer',nestedWriterEqualsRawWriter=True,cause='The new compatibility projection omitted the duplicate writer under qualification. Its strict legacy schema rejects the new telemetry reference and per-segment timing fields.',proposedCorrection='In a separately versioned candidate, require the nested raw writer to equal the authoritative raw writer, then apply the same reviewed projection to that exact duplicate. Add a positive fixture produced by the actual analyzer and negative nested-writer substitution tests. Preserve this run as rejected.',telemetry=measurement,diagnosticRules=rules)
with (R/'checker-diagnosis.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(dict(status=result['status'],cause=result['cause'],telemetry=measurement)))
