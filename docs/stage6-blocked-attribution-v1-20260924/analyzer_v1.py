"""Offline conditional attribution only. Never launches a process or imports old gates."""
import argparse
import datetime as dt
import hashlib
import json
import math
import ntpath
import pathlib
import statistics as st
import uuid

ROOT = pathlib.Path(__file__).resolve().parent
SCHEMA = 'j6.blocked-attribution.analysis.v1'
NAMES = ['BASELINE_DISABLED', 'FULL_ENABLED_REFERENCE', 'CLOCK_ONLY', 'STORAGE_ONLY', 'BOOKKEEPING_ONLY']
SCHEDULE = ['ABECD', 'BCADE', 'CDBEA', 'DECAB', 'EADBC', 'DCEBA', 'EDACB', 'AEBDC', 'BACED', 'CBDAE']
WEIGHTS = {
    'FULL_OVERHEAD': [-1, 1, 0, 0, 0],
    'PRIMARY_CLOCK_REMOVAL_OPPORTUNITY': [0, 1, 0, -1, 0],
    'CLOCK_ONLY_CONTRAST': [-1, 0, 1, 0, 0],
    'RECORD_STORE_CONTRIBUTION': [0, 0, 0, 1, -1],
    'BOOKKEEPING_CONTRIBUTION': [-1, 0, 0, 0, 1],
    'REMAINING_PACKAGE_OVERHEAD': [-1, 0, 0, 1, 0],
    'INTERACTION_RESIDUAL': [1, 1, -1, -1, 0],
}
PRIMARY = ('PRIMARY_CLOCK_REMOVAL_OPPORTUNITY', 'REMAINING_PACKAGE_OVERHEAD')
TARGETS = dict(zip(WEIGHTS, [None, .20, .30, .30, .30, .20, .40]))

class Rejected(ValueError):
    pass

def require(ok, reason):
    if not ok:
        raise Rejected(reason)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def sha(path):
    with pathlib.Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()

def strict_json(data):
    def pairs(items):
        d = {}
        for k, v in items:
            require(k not in d, 'duplicate JSON key')
            d[k] = v
        return d
    def invalid(x):
        raise Rejected('nonfinite JSON constant')
    try:
        return json.loads(data, object_pairs_hook=pairs, parse_constant=invalid)
    except (ValueError, TypeError) as e:
        raise Rejected('malformed JSON: ' + str(e)) from e

def read(path):
    return strict_json(pathlib.Path(path).read_text(encoding='utf-8-sig'))

def write_new(path, value):
    with pathlib.Path(path).open('x', encoding='utf8') as f:
        f.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')

def contract():
    value = dict(schema=SCHEMA, purpose='PROFILING_ONLY', variants=NAMES,
        schedule=SCHEDULE, orderType='BALANCED_NOT_RANDOMIZED', repeats=4, blocks=40,
        callbacksPerArm=1000000, warmupPerArm=20000, warmupEvidence='PINNED_SOURCE_AND_RUN_DECLARATION_NOT_EMITTED_PER_ARM',
        measuredCallbacks=200000000, excludedWarmupCallbacks=4000000, launcherBoundSeconds=1200,
        weights=WEIGHTS, groupSize=4, groups=10, df=9,
        confidence={k: .975 if k in PRIMARY else .95 for k in WEIGHTS}, targets=TARGETS,
        classification=dict(strongSavingLowerStrict=.5, strongRemainingUpperInclusive=.9,
            disprovenSavingUpperInclusive=.5, disprovenHalfwidthInclusive=.2,
            order=['STRONGLY_SUPPORTED','DISPROVEN','SUPPORTED_BUT_UNCERTAIN','INSUFFICIENT']),
        finalScreenPercent=1.0, finalInstrumentationQualified=False, productionCompletionValid=False,
        referenceWidthPrerequisite=None, referenceUse='EXTERNAL_ONLY_NOT_POOLED',
        fixedSample=True, retries=0, replacements=0, extensions=0, referencePhases=0,
        estimator='MEAN_WITHIN_BLOCK_CONTRAST_THEN_FOUR_BLOCK_GROUP_T_INTERVAL',
        invalidRules=['identity','schema','malformed','missing','duplicate','order','count','warmup','API','process','interruption','exit','statistics'],
        noisyBlocks='KEEP_ALL_NO_TRIMMING_NO_WINSORIZATION',
        inference='RUN_BOUND_REVIEW_REQUIRED; material drift/dependence -> INCONCLUSIVE; no estimator switching',
        meaning='Conditional compiled-software contrasts, not pure hardware costs; residual is not independent; reconstruction is not additivity')
    return strict_json(canonical(value))

def t9_cdf(x):
    # Integral of cos(theta)^8, t=3*tan(theta), df=9. No external dependency.
    theta = math.atan(x / 3)
    integ = theta
    for n in (2, 4, 6, 8):
        integ = math.sin(theta) * math.cos(theta)**(n-1) / n + (n-1) / n * integ
    return .5 + math.gamma(5) / (math.sqrt(math.pi)*math.gamma(4.5)) * integ

def t9_quantile(p):
    require(.5 < p < 1, 'invalid quantile')
    lo, hi = 0., 100.
    for _ in range(80):
        mid = (lo+hi)/2
        if t9_cdf(mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo+hi)/2

def interval(values, confidence):
    require(len(values) == 40 and all(math.isfinite(x) for x in values), 'contrast dimensions')
    groups = [st.mean(values[i:i+4]) for i in range(0,40,4)]
    critical = t9_quantile((1+confidence)/2)
    mean = st.mean(groups)
    half = critical * st.stdev(groups) / math.sqrt(10)
    return dict(perBlock=values, grouped=groups, mean=mean, lower=mean-half, upper=mean+half,
        halfwidth=half, confidence=confidence, critical=critical, df=9)

def classify(clock, remaining):
    if clock['lower'] > .5 and remaining['upper'] <= .9:
        return 'STRONGLY_SUPPORTED'
    if clock['halfwidth'] <= .2 and clock['upper'] <= .5:
        return 'DISPROVEN'
    if clock['lower'] > 0:
        return 'SUPPORTED_BUT_UNCERTAIN'
    return 'INSUFFICIENT'

def run_workspace(run_id):
    require(isinstance(run_id,str) and len(run_id)==32 and uuid.UUID(hex=run_id).hex==run_id, 'run ID')
    return 'D:\\JARVIS-STAGE6-LIVE\\blocked-attribution-v1-' + run_id

def candidate():
    c = read(ROOT/'candidate.json')
    require(c['schema']=='j6.blocked-attribution.candidate.v1', 'candidate schema')
    for row in c['artifacts']:
        require(sha(row['path'])==row['sha256'], 'candidate/source/history drift: '+row['role'])
    return c

def make_binding(run_id, workspace, c, now=None):
    require(workspace==run_workspace(run_id), 'workspace mismatch')
    return dict(schema=SCHEMA, runId=run_id, workspace=workspace,
        createdUtc=(now or dt.datetime.now(dt.timezone.utc)).isoformat(),
        candidateSHA256=sha(ROOT/'candidate.json'), analyzerSHA256=sha(__file__),
        candidate=c, contract=contract(), benchmarkAuthorized=False)

def validate_binding(b, expected_run, expected_workspace, expected_hash, c):
    require(set(b)=={'schema','runId','workspace','createdUtc','candidateSHA256','analyzerSHA256','candidate','contract','benchmarkAuthorized'}, 'binding fields')
    require(digest(canonical(b))==expected_hash, 'binding hash mismatch')
    require(b['schema']==SCHEMA, 'unsupported/old binding schema')
    require(b['runId']==expected_run and b['workspace']==expected_workspace==run_workspace(expected_run), 'stale binding/workspace')
    require(b['candidate']==c and b['candidateSHA256']==sha(ROOT/'candidate.json'), 'wrong candidate/fixture')
    require(b['analyzerSHA256']==sha(__file__), 'analyzer drift')
    require(canonical(b['contract'])==canonical(contract()), 'contract mismatch')
    require(b['benchmarkAuthorized'] is False, 'binding cannot authorize execution')
    when = dt.datetime.fromisoformat(b['createdUtc'])
    require(when.tzinfo is not None, 'binding timestamp timezone')

def contained_file(path, workspace):
    p, root = pathlib.Path(path), pathlib.Path(workspace)
    require(ntpath.commonpath([ntpath.abspath(str(p)),ntpath.abspath(str(root))]).casefold()==ntpath.abspath(str(root)).casefold(), 'evidence path escape')
    for part in (p, *p.parents):
        if part.exists():
            require(not (part.stat().st_file_attributes & 0x400), 'reparse point')
    require(p.is_file(), 'missing evidence file')
    return p

FIELDS = {'block','position','variant','name','callbacks','dispatcherCpu100ns','processCpu100ns','wallSeconds','allocations','p50Ticks','p95Ticks','p99Ticks','sampledMaxTicks','frequency','peakWorkingSetBytes'}

def parse_rows(raw):
    require(isinstance(raw,bytes) and raw.endswith(b'\n'), 'incomplete raw stream')
    lines=raw.splitlines();require(len(lines)==200, 'missing/extra arms or blocks')
    rows=[]
    for i,line in enumerate(lines):
        r=strict_json(line)
        require(isinstance(r,dict) and set(r)==FIELDS, 'unsupported raw schema/missing statistics')
        b,pos=divmod(i,5);v=ord(SCHEDULE[b%10][pos])-65
        require(r['block']==b and r['position']==pos and r['variant']==v and r['name']==NAMES[v], 'wrong schedule/duplicate/missing arm')
        require(r['callbacks']==1000000, 'callback count')
        for key in FIELDS-{'name','wallSeconds'}:
            require(type(r[key]) is int and r[key]>=0, 'malformed integer statistic')
        require(type(r['wallSeconds']) in (float,int) and math.isfinite(r['wallSeconds']) and r['wallSeconds']>0, 'wall statistic')
        require(r['dispatcherCpu100ns']>0 and r['processCpu100ns']>=r['dispatcherCpu100ns'] and r['frequency']>0 and r['peakWorkingSetBytes']>0, 'CPU API/statistic')
        require(r['allocations']==4000000 and 0<=r['p50Ticks']<=r['p95Ticks']<=r['p99Ticks']<=r['sampledMaxTicks'], 'work/statistic mismatch')
        rows.append(r)
    require(len({r['frequency'] for r in rows})==1, 'frequency drift')
    return rows

def validate_execution(e, receipt, binding, raw, exit_bytes):
    expected={'schema':'j6.blocked-attribution.execution.v1', 'runId':binding['runId'],
        'bindingSHA256':digest(canonical(binding)), 'rawSHA256':digest(raw), 'exitSHA256':digest(exit_bytes),
        'blocks':40, 'warmupPerArm':20000, 'warmupEvidence':contract()['warmupEvidence'],
        'retries':0,'replacements':0,'extensions':0,'referencePhases':0,'interrupted':False,'APIError':False,'status':'COMPLETE'}
    require(canonical(receipt)==canonical(expected), 'execution declaration/count/warmup/retry/identity mismatch')
    artifacts={a['role']:a for a in binding['candidate']['artifacts']}
    exe=artifacts['fixtureExecutable']
    require(e['mode']=='attribution' and e['executable']==exe['path'] and e['sha256']==exe['sha256'], 'wrong execution identity')
    require(e['cwd']==str(pathlib.PureWindowsPath(exe['path']).parent) and e['flags']==0 and e['UAC'] is False, 'launch context')
    require(e['exitCode']==0 and e['waitResult']==0 and e['closeErrors']==[], 'exit/handle failure')
    require(type(e['pid']) is int and e['pid']>0 and type(e['tid']) is int and e['tid']>0, 'process/thread ID')
    require(math.isfinite(e['elapsedSeconds']) and 0<e['elapsedSeconds']<=1200, 'interruption/launcher bound')
    boundary=(dt.datetime.fromisoformat(binding['createdUtc']).timestamp()+11644473600)*10000000
    for kind in ['Process','Thread']:
        a,z=e['initial'+kind],e['final'+kind]
        require(a['createdFILETIME']==z['createdFILETIME'] and a['createdFILETIME']>=boundary and a['exitFILETIME']==0 and z['exitFILETIME']>=z['createdFILETIME'], 'stale/contradictory process instance')
        for key in ('kernel100ns','user100ns'):
            require(type(a[key]) is int and type(z[key]) is int and 0<=a[key]<=z[key], 'CPU identity counters')

def lag1(values):
    mean=st.mean(values);den=sum((x-mean)**2 for x in values)
    return sum((values[i]-mean)*(values[i-1]-mean) for i in range(1,len(values)))/den if den else None

def diagnostics(rows, contrasts):
    blocks=[]
    for b in range(40):
        blocks.append({r['variant']:r['dispatcherCpu100ns']*100/1000000 for r in rows[b*5:b*5+5]})
    result={}
    for name,data in contrasts.items():
        vals=data['percent']['perBlock'];g=data['percent']['grouped'];m=st.mean(vals)
        result[name]=dict(first20=st.mean(vals[:20]),last20=st.mean(vals[20:]),halfDifference=st.mean(vals[20:])-st.mean(vals[:20]),
            orderSlope=sum((i-19.5)*(x-m) for i,x in enumerate(vals))/sum((i-19.5)**2 for i in range(40)),
            groupResiduals=[v-st.mean(g) for v in g], groupLag1=lag1(g))
    position={}
    for v in range(5):
        vm=st.mean(d[v]-st.mean(d.values()) for d in blocks)
        position[NAMES[v]]={str(p):st.mean(blocks[b][v]-st.mean(blocks[b].values())-vm for b in range(40) if ord(SCHEDULE[b%10][p])-65==v) for p in range(5)}
    return dict(contrasts=result,treatmentCenteredPositionNs=position,
        limitations=['Balanced not randomized','Grouping does not guarantee independence','No measured component power guarantee','No automatic drift cutoff invented'],
        requiredReview='Assess order/position/temporal drift and grouped dependence; material issue or unresolved assumptions => INCONCLUSIVE')

def analyze_rows(rows, raw_hash, binding_hash, run_id, review=None):
    blocks=[{r['variant']:r['dispatcherCpu100ns']*100/r['callbacks'] for r in rows[i:i+5]} for i in range(0,200,5)]
    contrasts={}
    for name,weights in WEIGHTS.items():
        vals=[sum(weights[v]*d[v] for v in range(5)) for d in blocks]
        conf=.975 if name in PRIMARY else .95
        pct=interval([100*x/d[0] for x,d in zip(vals,blocks)],conf)
        contrasts[name]=dict(ns=interval(vals,conf),percent=pct,planningHalfwidth=TARGETS[name],
            planningTargetMet=None if TARGETS[name] is None else pct['halfwidth']<=TARGETS[name])
    diag=diagnostics(rows,contrasts);diag_hash=digest(canonical(diag))
    conditional=classify(contrasts[PRIMARY[0]]['percent'],contrasts[PRIMARY[1]]['percent'])
    status='INCONCLUSIVE'; reason='Inference review missing'
    if review is not None:
        require(set(review)=={'schema','runId','rawSHA256','bindingSHA256','diagnosticsSHA256','assumptionsSupported','materialDriftOrDependence','basis'}, 'review schema')
        require(review['schema']=='j6.blocked-attribution.inference-review.v1' and review['runId']==run_id and review['rawSHA256']==raw_hash and review['bindingSHA256']==binding_hash and review['diagnosticsSHA256']==diag_hash, 'stale inference review')
        require(type(review['assumptionsSupported']) is bool and type(review['materialDriftOrDependence']) is bool and isinstance(review['basis'],str) and len(review['basis'].strip())>=20, 'inference review incomplete')
        if review['assumptionsSupported'] and not review['materialDriftOrDependence']:
            status=conditional;reason='Explicit run-bound inference assessment'
        else:
            reason='Material drift/dependence or unresolved assumptions'
    return dict(schema=SCHEMA,status=status,reason=reason,conditionalClassification=conditional,
        finalInstrumentationQualified=False,finalScreenPercent=1.0,productionCompletionValid=False,
        contrasts=contrasts,diagnostics=diag,diagnosticsSHA256=diag_hash,rawSHA256=raw_hash,
        runId=run_id,bindingSHA256=binding_hash,referenceEvidence='External consistency only; not pooled; point difference is not defect',
        invalidBlocks=0,excludedBlocks=0,retries=0,extensions=0,
        warning='D uses arrival time; no production optimization authorization. Conditional software effects, not pure component costs.')

def external_consistency(full, references):
    return [dict(id=r['id'],sha256=r['sha256'],priorMean=r['mean'],priorInterval=[r['lower'],r['upper']],
        overlaps=full['upper']>=r['lower'] and full['lower']<=r['upper'],
        meaning='External check only; not pooled; non-overlap requires review, not automatic defect') for r in references]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='action',required=True)
    b=sub.add_parser('bind');b.add_argument('--run-id',required=True);b.add_argument('--workspace',required=True);b.add_argument('--output',required=True)
    a=sub.add_parser('analyze')
    for k in ('binding','binding-sha','run-id','workspace','raw','exit','receipt','output'):
        a.add_argument('--'+k,required=True)
    a.add_argument('--review')
    args=p.parse_args();c=candidate()
    if args.action=='bind':
        value=make_binding(args.run_id,args.workspace,c)
        workspace=pathlib.Path(args.workspace)
        require(workspace.is_dir() and not any(workspace.iterdir()), 'workspace must be new and empty')
        for part in (workspace,*workspace.parents):
            if part.exists():
                require(not part.stat().st_file_attributes & 0x400,'workspace reparse point')
        write_new(args.output,value);print(digest(canonical(value)));return
    b=read(args.binding);validate_binding(b,args.run_id,args.workspace,args.binding_sha,c)
    raw=contained_file(args.raw,args.workspace).read_bytes();ex=contained_file(args.exit,args.workspace).read_bytes()
    receipt=read(contained_file(args.receipt,args.workspace))
    validate_execution(strict_json(ex),receipt,b,raw,ex)
    rows=parse_rows(raw)
    result=analyze_rows(rows,digest(raw),args.binding_sha,args.run_id,read(args.review) if args.review else None)
    result['historicalReferences']=c['historicalReferences']
    refs=[]
    for ref in c['historicalReferences']:
        p=read(ref['path'])['primary']
        refs.append(dict(ref,mean=p['mean'],lower=p['lower'],upper=p['upper']))
    result['externalConsistency']=external_consistency(result['contrasts']['FULL_OVERHEAD']['percent'],refs)
    if not all(r['overlaps'] for r in result['externalConsistency']):
        result.update(status='INCONCLUSIVE',reason='External consistency requires separate review; no reproducibility defect inferred')
    require(sha(args.raw)==digest(raw),'raw mutated during analysis')
    candidate()
    write_new(args.output,result)
    print(result['status'])

if __name__=='__main__':
    try:
        main()
    except (Rejected,KeyError,TypeError,ValueError,OSError) as e:
        raise SystemExit('REJECTED: '+str(e))
