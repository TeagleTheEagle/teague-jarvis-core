"""Fabricated records only; never invokes the attribution fixture."""
import copy
import datetime as dt
import hashlib
import io
import json
import math
import pathlib
import tempfile
import unittest
import zipfile
import analyzer_v1 as a
import evidence_v1 as ev

RUN='1234567890abcdef1234567890abcdef'
def raw_rows():
    rows=[]
    for b in range(40):
        for p,s in enumerate(a.SCHEDULE[b%10]):
            v=ord(s)-65
            ns=[2000,2040,2010,2015,2005][v]
            rows.append(dict(block=b,position=p,variant=v,name=a.NAMES[v],callbacks=1000000,
                dispatcherCpu100ns=ns*10000,processCpu100ns=ns*10000,wallSeconds=3.,
                allocations=4000000,p50Ticks=1,p95Ticks=2,p99Ticks=3,sampledMaxTicks=4,
                frequency=10000000,peakWorkingSetBytes=4000000))
    return rows
def raw_bytes(rows):
    return b''.join(a.canonical(r)+b'\n' for r in rows)
def binding():
    return a.make_binding(RUN,a.run_workspace(RUN),a.read(a.ROOT/'candidate.json'),dt.datetime(2026,1,1,tzinfo=dt.timezone.utc))
def execution(b,raw):
    exe=next(x for x in b['candidate']['artifacts'] if x['role']=='fixtureExecutable')
    initial=dict(createdFILETIME=134200000000000000,exitFILETIME=0,kernel100ns=0,user100ns=0)
    final=dict(initial,exitFILETIME=134200000100000000,kernel100ns=1,user100ns=2)
    e=dict(mode='attribution',executable=exe['path'],sha256=exe['sha256'],cwd=str(pathlib.PureWindowsPath(exe['path']).parent),flags=0,UAC=False,pid=1,tid=2,
        initialProcess=initial,initialThread=initial,finalProcess=final,finalThread=final,
        exitCode=0,waitResult=0,closeErrors=[],elapsedSeconds=10.)
    ex=a.canonical(e)
    receipt=dict(schema='j6.blocked-attribution.execution.v1',runId=RUN,bindingSHA256=a.digest(a.canonical(b)),rawSHA256=a.digest(raw),exitSHA256=a.digest(ex),blocks=40,warmupPerArm=20000,warmupEvidence=a.contract()['warmupEvidence'],retries=0,replacements=0,extensions=0,referencePhases=0,interrupted=False,APIError=False,status='COMPLETE')
    return e,receipt,ex
def result():
    raw=raw_bytes(raw_rows())
    return a.analyze_rows(a.parse_rows(raw),a.digest(raw),'b'*64,RUN)
def review_for(r,**updates):
    return dict(schema='j6.blocked-attribution.inference-review.v1',runId=RUN,rawSHA256=r['rawSHA256'],bindingSHA256=r['bindingSHA256'],diagnosticsSHA256=r['diagnosticsSHA256'],assumptionsSupported=True,materialDriftOrDependence=False,basis='Synthetic constant records; this is only a unit-test inference fixture.',**updates)

class AnalyzerTests(unittest.TestCase):
    def test_exact_schedule(self):
        self.assertEqual(len(a.parse_rows(raw_bytes(raw_rows()))),200)
    def test_complete_execution(self):
        b=binding();raw=raw_bytes(raw_rows());e,r,ex=execution(b,raw);a.validate_execution(e,r,b,raw,ex)
    def test_binding_valid(self):
        b=binding();a.validate_binding(b,RUN,a.run_workspace(RUN),a.digest(a.canonical(b)),b['candidate'])
    def test_binding_hash_rejected(self):
        b=binding()
        with self.assertRaises(a.Rejected):a.validate_binding(b,RUN,a.run_workspace(RUN),'0'*64,b['candidate'])
    def test_raw_unchanged(self):
        raw=raw_bytes(raw_rows());before=raw[:];a.parse_rows(raw);self.assertEqual(raw,before)
    def test_all_seven_contrasts(self):
        r=result();expected=[40,25,10,10,5,15,15]
        for key,n in zip(a.WEIGHTS,expected):
            with self.subTest(key=key):
                self.assertAlmostEqual(r['contrasts'][key]['ns']['mean'],n)
                self.assertAlmostEqual(r['contrasts'][key]['percent']['mean'],n/20)
                self.assertEqual(len(r['contrasts'][key]['ns']['perBlock']),40)
    def test_denominator_uses_each_A(self):
        rows=raw_rows()
        for x in rows:
            if x['block']==1 and x['variant']==0:x['dispatcherCpu100ns']=10000000
        r=a.analyze_rows(rows,'a'*64,'b'*64,RUN)
        self.assertEqual(r['contrasts'][a.PRIMARY[0]]['percent']['perBlock'][:2],[1.25,2.5])
    def test_grouping(self):
        x=a.interval(list(range(40)),.95)
        self.assertEqual(x['grouped'],[1.5+4*i for i in range(10)])
        self.assertEqual(x['mean'],19.5)
    def test_t95_known(self):
        self.assertAlmostEqual(a.t9_quantile(.975),2.262157162798205,places=10)
    def test_t975_independent_numerical_integral(self):
        # Simpson integration of the t density, independent of the recurrence.
        t=a.t9_quantile(.9875);n=10000;h=t/n
        norm=math.gamma(5)/(math.sqrt(9*math.pi)*math.gamma(4.5))
        f=lambda x:norm*(1+x*x/9)**-5
        area=h/3*(f(0)+f(t)+sum((4 if i%2 else 2)*f(i*h) for i in range(1,n)))
        self.assertAlmostEqual(area+.5,.9875,places=11)
    def test_interval_halfwidth(self):
        x=a.interval([float(i//4) for i in range(40)],.95)
        self.assertAlmostEqual(x['halfwidth'],2.262157162798205*math.sqrt(9.166666666666666/10),places=9)
    def test_confidence_levels(self):
        for k,v in result()['contrasts'].items():self.assertEqual(v['percent']['confidence'],.975 if k in a.PRIMARY else .95)
    def test_strong_exact_remaining_boundary(self):
        self.assertEqual(a.classify(dict(lower=.500001,upper=2.,halfwidth=.75),dict(upper=.9)),'STRONGLY_SUPPORTED')
    def test_strict_clock_boundary(self):
        self.assertEqual(a.classify(dict(lower=.5,upper=.8,halfwidth=.15),dict(upper=.9)),'SUPPORTED_BUT_UNCERTAIN')
    def test_uncertain_remaining(self):
        self.assertEqual(a.classify(dict(lower=.6,upper=.8,halfwidth=.1),dict(upper=.900001)),'SUPPORTED_BUT_UNCERTAIN')
    def test_insufficient(self):
        self.assertEqual(a.classify(dict(lower=-.2,upper=.8,halfwidth=.5),dict(upper=1.)),'INSUFFICIENT')
    def test_disproven_inclusive_boundary(self):
        self.assertEqual(a.classify(dict(lower=.1,upper=.5,halfwidth=.2),dict(upper=1.)),'DISPROVEN')
    def test_disproven_requires_precision(self):
        self.assertEqual(a.classify(dict(lower=-.1,upper=.5,halfwidth=.3),dict(upper=1.)),'INSUFFICIENT')
    def test_full_width_not_gate(self):
        self.assertIsNone(a.contract()['targets']['FULL_OVERHEAD']);self.assertIsNone(a.contract()['referenceWidthPrerequisite'])
    def test_screen_not_qualification(self):
        r=result();self.assertEqual(r['finalScreenPercent'],1.);self.assertFalse(r['finalInstrumentationQualified'])
    def test_missing_review_inconclusive(self):self.assertEqual(result()['status'],'INCONCLUSIVE')
    def test_valid_review(self):
        r=result();x=a.analyze_rows(raw_rows(),r['rawSHA256'],r['bindingSHA256'],RUN,review_for(r));self.assertEqual(x['status'],'STRONGLY_SUPPORTED')
    def test_material_dependence_inconclusive(self):
        r=result();rev=review_for(r);rev['materialDriftOrDependence']=True
        self.assertEqual(a.analyze_rows(raw_rows(),r['rawSHA256'],r['bindingSHA256'],RUN,rev)['status'],'INCONCLUSIVE')
    def test_stale_review(self):
        r=result();rev=review_for(r);rev['rawSHA256']='0'*64
        with self.assertRaises(a.Rejected):a.analyze_rows(raw_rows(),r['rawSHA256'],r['bindingSHA256'],RUN,rev)
    def test_diagnostics_present(self):
        d=result()['diagnostics'];self.assertEqual(len(d['treatmentCenteredPositionNs']),5)
        for x in d['contrasts'].values():self.assertEqual(len(x['groupResiduals']),10);self.assertIn('halfDifference',x);self.assertIn('groupLag1',x)
    def test_noisy_values_retained(self):
        rows=raw_rows();rows[1]['dispatcherCpu100ns']*=5;rows[1]['processCpu100ns']*=5
        parsed=a.parse_rows(raw_bytes(rows));r=a.analyze_rows(parsed,'a'*64,'b'*64,RUN)
        self.assertEqual(r['excludedBlocks'],0);self.assertEqual(len(r['contrasts']['FULL_OVERHEAD']['ns']['perBlock']),40)
    def test_balanced_not_randomized(self):self.assertEqual(a.contract()['orderType'],'BALANCED_NOT_RANDOMIZED')
    def test_D_never_production_valid(self):self.assertFalse(result()['productionCompletionValid'])
    def test_no_runner_or_old_import(self):
        import ast
        tree=ast.parse(pathlib.Path(a.__file__).read_text());names=[]
        for n in ast.walk(tree):
            if isinstance(n,ast.Import):names.extend(x.name for x in n.names)
            if isinstance(n,ast.ImportFrom):names.append(n.module)
        self.assertFalse(set(names)&{'run','runpy','subprocess','ctypes','prepare'})
    def test_archive_integrity_and_corruption(self):
        with tempfile.TemporaryDirectory(dir=a.ROOT) as folder:
            p=pathlib.Path(folder)/'synthetic.zip';payload=b'synthetic'
            with zipfile.ZipFile(p,'x') as z:
                z.writestr('record',payload);z.writestr('archive-manifest.json',json.dumps(dict(entries=[dict(name='record',sha256=a.digest(payload))])))
            digest=a.sha(p);self.assertEqual(ev.verify_archive(p,digest),2)
            with p.open('ab') as f:f.write(b'bad')
            with self.assertRaises(a.Rejected):ev.verify_archive(p,digest)
    def test_census_zero_and_fail_closed(self):
        c=dict(processCount=0,traceCount=0,processes=[],traces=[],processQuerySucceeded=True,traceQuerySucceeded=True,utc='test',UAC=False)
        ev.verify_census(c)
        for field,value in [('processCount',1),('traceCount',1),('processes',[1]),('traces',['x']),('processQuerySucceeded',False),('traceQuerySucceeded',False)]:
            bad=dict(c);bad[field]=value
            with self.subTest(field=field),self.assertRaises(a.Rejected):ev.verify_census(bad)
    def test_historical_preservation(self):a.candidate()

def add_mutation_tests():
    raw_changes={
        'wrong_schedule':lambda x:x[0].update(variant=1),
        'missing_block':lambda x:x.__delitem__(slice(0,5)),
        'duplicate_treatment':lambda x:x.__setitem__(1,copy.deepcopy(x[0])),
        'wrong_callbacks':lambda x:x[0].update(callbacks=999999),
        'missing_statistic':lambda x:x[0].pop('frequency'),
        'bad_statistic':lambda x:x[0].update(dispatcherCpu100ns=-1),
        'bool_statistic':lambda x:x[0].update(position=False),
        'extra_block':lambda x:x.extend(copy.deepcopy(x[:5])),
        'incomplete_block':lambda x:x.pop(),
        'unsupported_schema':lambda x:x[0].update(newField=1),
        'wrong_position':lambda x:x[0].update(position=4),
        'wrong_allocations':lambda x:x[0].update(allocations=0),
    }
    for name,fn in raw_changes.items():
        def test(self,fn=fn):
            rows=raw_rows();fn(rows)
            with self.assertRaises(a.Rejected):a.parse_rows(raw_bytes(rows))
        setattr(AnalyzerTests,'test_reject_raw_'+name,test)
    binding_changes={
        'repeat':lambda b:b['contract'].update(repeats=5),
        'confidence':lambda b:b['contract']['confidence'].update(PRIMARY_CLOCK_REMOVAL_OPPORTUNITY=.95),
        'threshold':lambda b:b['contract']['classification'].update(strongSavingLowerStrict=.4),
        'old_gate':lambda b:b.update(schema='reference-gate-v0'),
        'schedule':lambda b:b['contract']['schedule'].__setitem__(0,'ABCDE'),
        'callback':lambda b:b['contract'].update(callbacksPerArm=1),
        'stale':lambda b:b.update(runId='0'*32),
        'workspace':lambda b:b.update(workspace='D:\\old'),
        'fixture':lambda b:b['candidate']['artifacts'][0].update(sha256='0'*64),
        'warmup':lambda b:b['contract'].update(warmupPerArm=0),
        'retry':lambda b:b['contract'].update(retries=1),
    }
    for name,fn in binding_changes.items():
        def test(self,fn=fn):
            b=binding();c=copy.deepcopy(b['candidate']);fn(b)
            with self.assertRaises(a.Rejected):a.validate_binding(b,RUN,a.run_workspace(RUN),a.digest(a.canonical(b)),c)
        setattr(AnalyzerTests,'test_reject_binding_'+name,test)
    for field,value in [('warmupPerArm',0),('retries',1),('extensions',1),('replacements',1),('referencePhases',1),('interrupted',True),('APIError',True),('blocks',41),('status','PARTIAL')]:
        def test(self,field=field,value=value):
            b=binding();raw=raw_bytes(raw_rows());e,r,ex=execution(b,raw);r[field]=value
            with self.assertRaises(a.Rejected):a.validate_execution(e,r,b,raw,ex)
        setattr(AnalyzerTests,'test_reject_execution_'+field,test)
    for name,fn in {
        'nonzero_exit':lambda e:e.update(exitCode=1),
        'process_instance':lambda e:e.update(finalProcess=dict(e['finalProcess'],createdFILETIME=1)),
        'old_creation':lambda e:e.update(initialProcess=dict(e['initialProcess'],createdFILETIME=1)),
        'wrong_image':lambda e:e.update(sha256='0'*64),
        'wait_timeout':lambda e:e.update(waitResult=258),
        'deadline':lambda e:e.update(elapsedSeconds=1201),
        'UAC':lambda e:e.update(UAC=True),
        'mode':lambda e:e.update(mode='reference'),
    }.items():
        def test(self,fn=fn):
            b=binding();raw=raw_bytes(raw_rows());e,r,ex=execution(b,raw);fn(e);ex=a.canonical(e);r['exitSHA256']=a.digest(ex)
            with self.assertRaises(a.Rejected):a.validate_execution(e,r,b,raw,ex)
        setattr(AnalyzerTests,'test_reject_process_'+name,test)

add_mutation_tests()
if __name__=='__main__':unittest.main(verbosity=2)
