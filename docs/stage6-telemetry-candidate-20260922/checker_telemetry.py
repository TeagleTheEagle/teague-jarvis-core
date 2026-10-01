"""Versioned TEST composition: existing identity rules PLUS mandatory telemetry.

No legacy fallback. The v3 compatibility view removes ONLY already-verified new
measurement fields; original raw lifecycle/identity evidence is never altered.
"""
import copy,collections,json,sys
from pathlib import Path
import checker_medium as legacy
import telemetry
VERSION='stage6-checker-telemetry-v4'
POLICY=dict(schema='stage6-telemetry-policy-v1',telemetrySchema=telemetry.SCHEMA,snapshotCapacity=65536,slowHeartbeatWarnings='NOT CONFIGURED',heartbeatFailureSeconds=10)
def compatibility_view(bundle):
 b=copy.deepcopy(bundle)
 for key in ('manifest','writer'):
  del b[key]['telemetry']
  for s in b[key]['segments']:del s['timing']
 return b
def rules(bundle,measurements,declaration):
 result=telemetry.validate(measurements,bundle['manifest'],bundle['writer'])
 b=compatibility_view(bundle)
 payload=legacy.adapter.validate(b,declaration=declaration)
 e=dict(schema=legacy.VERSION,contract=legacy.CONTRACT,adapter='stage6-medium-combined-v1',runId=Path(b['root']).name,evidenceRoot=b['root'],payload=payload,bundle=b)
 old=legacy.rules(e,declaration=declaration)
 return dict(schema=VERSION,status='RULES_SATISFIED_NOT_ACCEPTANCE',lifecycle=old,telemetry=result)
def evaluate():
 from fresh_binding import verify_intake
 code=Path(__file__).parent.parent;root,d,intake=verify_intake(code)
 legacy.need(legacy.load(code/'telemetry-policy.json')==POLICY,'TELEMETRY_POLICY')
 b=legacy.adapter.read_bundle(root,root/'analysis',root/'final-host-state.json')
 # This verifies the exact on-disk telemetry/manifest/result binding before view adaptation.
 verified=telemetry.verify(root)
 measurements=telemetry.load(root/'kernel-authority-telemetry.json')
 declared=legacy.load(root/'process-identities.json')
 required={(x['pid'],x['created']) for x in declared if x['role'] in ('worker','application')}
 legacy.need(len(required)==2 and required<={(x['pid'],x['created']) for x in b['kernel']['rows']},'DECLARED_INFRASTRUCTURE_MISSING')
 probes=legacy.load(root/'identity-probes.json')['rows']
 legacy.need(len(probes)==d['directProbes'] and dict(collections.Counter(p['case'] for p in probes))=={p['name']:p['groups']*p['width'] for p in d['cases']},'DECLARED_CASES_MISSING')
 result=rules(b,measurements,d);legacy.need(result['telemetry']==verified,'TELEMETRY_RECOMPUTATION')
 verify_intake(code)
 return dict(schema=VERSION,status='EVIDENCE_VALIDATED_PENDING_ARCHIVE',acceptance=False,runId=root.name,intakeSHA256=legacy.sha(root/'intake-manifest.json'),policy=POLICY,rules=result)
if __name__=='__main__':
 try:
  sys.path.insert(0,str(Path(__file__).parent.parent));legacy.need(sys.argv[1:]==['--evaluate-medium'],'EXPLICIT_MODE_REQUIRED');print(json.dumps(evaluate(),allow_nan=False))
 except Exception as e:print(json.dumps(dict(status='REJECT',reason=str(e))));raise SystemExit(1)
