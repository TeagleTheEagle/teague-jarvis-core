"""Read-only predecessor/history verification and evidence-only accounting."""
import ast,datetime,difflib,json,pathlib,statistics
from prepare import R,D,P,C,load,sha,record,write

def unchanged(row):
    now=record(row['path'])
    assert now['sha256']==row['sha256'],row['path']
    assert now['bytes']==row['bytes'] and now['mtimeNs']==row['mtimeNs'],row['path']

before=load(R/'before.json')
for row in before['inputs']:unchanged(row)
hist=load(R/'historical-precheck.json')
for row in hist['evidence']:unchanged(row)
assert sha(hist['archive'])==hist['archiveSHA256']
old=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\f469b94b665e4808af1c5bb6aa46b207\code')
freeze=load(D/'stage6-identity-capacity-recalibration-20260921'/'freeze.json')
for row in freeze['candidateHashes']:assert sha(old/row['name'])==row['sha256'],row['name']
syntax=[]
for p in sorted(R.glob('*.py')):
    ast.parse(p.read_text(encoding='utf8'),filename=str(p))
    syntax.append(dict(path=str(p),sha256=sha(p),result='PASS',method='ast.parse; no module execution or bytecode'))
write('syntax-results.json',syntax)
changed=[];patch=[];expected=load(P/'small-source-v3.json')
for row in expected:
    p=C/row['name'];assert p.is_file()
    if sha(p)!=row['sha256']:
        assert row['name'] in ['baseline-allowlist.json','preservation-policy-v4.json']
        changed.append(dict(name=row['name'],before=row['sha256'],after=sha(p)))
        patch.extend(difflib.unified_diff((P/row['name']).read_text().splitlines(True),p.read_text().splitlines(True),fromfile='predecessor/'+row['name'],tofile='successor/'+row['name']))
for name in ['loss_measurement_v3.hpp','loss_measurement_fixture_v3.cpp']:
    assert sha(R/name)==sha(C/name)
    patch.extend(difflib.unified_diff([], (C/name).read_text().splitlines(True),fromfile='/dev/null',tofile='successor/'+name))
with (R/'implementation.diff').open('x',encoding='utf8') as f:f.writelines(patch)
source=[record(p) for p in sorted(C.rglob('*')) if p.is_file()]
write('candidate-artifact-manifest.json',dict(status='INCOMPLETE_NOT_LIVE_ELIGIBLE',purpose='Partial recorder feasibility successor; not an acceptance source manifest',files=source))
write('preservation-postcheck.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),predecessorAndEvidenceFiles=len(before['inputs']),historicalEvidenceFiles=len(hist['evidence']),historicalCandidateFiles=len(freeze['candidateHashes']),historicalArchiveUnchanged=True,allUnchanged=True,copiedCandidateFiles=len(expected),changedCopiedFiles=changed,frozenCheckerUnchanged=True,productionAccess=False,protectedVMAccess=False,scope='Only explicit diagnostic/evidence paths accessed; protected files intentionally not inspected'))
bench=load(R/'screen-result.json');pairs=bench['pairs'];off=[p['off'] for p in pairs];on=[p['on'] for p in pairs]
write('benchmark-summary.json',dict(status=bench['status'],pairs=len(pairs),callbacks=sum(p['callbacks'] for p in off+on),cpuPercent=bench['meanAdditionalCpuPercent'],paired95Interval=bench['paired95PercentInterval'],minTrialCpuSeconds=min(p['dispatcherCpu100ns']/1e7 for p in off+on),allocationDelta=sum(p['allocationDelta'] for p in pairs),offCallbacksPerSecond=sum(p['callbacks'] for p in off)/sum(p['wallSeconds'] for p in off),onCallbacksPerSecond=sum(p['callbacks'] for p in on)/sum(p['wallSeconds'] for p in on),maxSampledCallbackOffUs=max(p['sampledLatencyTicks']['max']/p['frequency']*1e6 for p in off),maxSampledCallbackOnUs=max(p['sampledLatencyTicks']['max']/p['frequency']*1e6 for p in on),peakWorkingSetBytes=max(p['peakWorkingSetBytes'] for p in off+on),limitation='Early unknown-parent START branch screen; no integrated observer/coordination/other lifecycle-path benchmark. Callback maxima are sampled, not exhaustive. Stop rule prevents further integration.'))
print(json.dumps(dict(preservation='PASS',syntax=len(syntax),candidateFiles=len(source),status=bench['status'])))
