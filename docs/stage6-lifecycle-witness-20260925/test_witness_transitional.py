import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile
import unittest

R=Path(__file__).parent; C=R/'candidate'
S=Path(r'D:\JARVIS-STAGE6-LIVE\ea85ed4b4ef14769acbe0b5e750aaed2\code')
spec=importlib.util.spec_from_file_location('analyzer',C/'analyze_lifecycle_witness_v1.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)

def fixture():
    binding=dict(run='fresh-run',session='J6-test-session',channel='authority',candidateSHA256='a'*64,observerSHA256='b'*64,frequency=10000000)
    record=dict(sequence=1,kind='START',eventQpc=110,callbackQpc=130,pid=20,parentPid=10,
                processSequence='7',parentSequence='6',decodedFields=31,validFields=31,
                parentKnown=True,instanceKnown=None,admitted=True,complete=True,
                disposition='ADMITTED',reason='NONE')
    w=dict(binding,schema=a.SCHEMA,diagnosticOnly=True,acceptanceAuthority=False,quiesced=True,
           capacity=65536,attempted=1,count=1,overflow=False,records=[record])
    t=dict(run='fresh-run',frequency=10000000,instances=[dict(role='sampler',pid=20,created='100000',exitFiletime='200000',
             identitySource='creator-retained-handle',identityEvidenceSHA256='c'*64,processSequence='7',eventWindows={'START':[100,120],'STOP':[190,220]})])
    loss=dict(run='fresh-run',session='J6-test-session',frequency=10000000,
              samples=[dict(beginQpc=90,endQpc=91,status=0,eventsLost=0),dict(beginQpc=230,endQpc=231,status=0,eventsLost=2)])
    return w,binding,t,loss

class AnalyzerTests(unittest.TestCase):
    def outcome(self,f,kind='START'):
        return a.analyze(*f)['instances'][0][kind]['outcome']
    def test_admitted_start(self):self.assertEqual(self.outcome(fixture()),'CALLBACK_ADMITTED')
    def test_unknown_parent(self):
        f=fixture();f[0]['records'][0].update(disposition='UNKNOWN_PARENT',reason='PARENT_NOT_KNOWN',admitted=False,parentKnown=False)
        self.assertEqual(self.outcome(f),'CALLBACK_REJECTED_UNKNOWN_PARENT')
    def test_admitted_stop(self):
        f=fixture();f[0]['records'][0].update(kind='STOP',eventQpc=200,parentKnown=None,instanceKnown=True)
        self.assertEqual(self.outcome(f,'STOP'),'CALLBACK_ADMITTED')
    def test_unknown_instance(self):
        f=fixture();f[0]['records'][0].update(kind='STOP',eventQpc=200,disposition='UNKNOWN_INSTANCE',reason='INSTANCE_NOT_KNOWN',admitted=False,parentKnown=None,instanceKnown=False)
        self.assertEqual(self.outcome(f,'STOP'),'CALLBACK_REJECTED_UNKNOWN_INSTANCE')
    def test_absence_not_payload_loss(self):
        f=fixture();r=a.analyze(*f);self.assertEqual(r['instances'][0]['STOP']['outcome'],'CALLBACK_NOT_OBSERVED');self.assertIn('does not identify',r['warning'])
    def test_other_rejections(self):
        for d in ['DUPLICATE','INVALID_IDENTITY','DECODE_FAILURE','OTHER_EXPLICIT_REJECTION']:
            with self.subTest(d=d):
                f=fixture();f[0]['records'][0].update(disposition=d,admitted=False);self.assertEqual(self.outcome(f),'CALLBACK_REJECTED_OTHER')
    def test_overflow(self):
        f=fixture();f[0].update(overflow=True,attempted=65537);self.assertEqual(self.outcome(f),'WITNESS_INCOMPLETE')
    def test_unquiesced(self):
        f=fixture();f[0]['quiesced']=False;self.assertEqual(self.outcome(f),'WITNESS_INCOMPLETE')
    def test_stale_bindings(self):
        for k in ['run','session','channel','candidateSHA256','observerSHA256','frequency']:
            with self.subTest(k=k):
                f=fixture();f[0][k]='stale'
                with self.assertRaises(ValueError):a.analyze(*f)
    def test_schema(self):
        f=fixture();f[0]['schema']='old'
        with self.assertRaises(ValueError):a.analyze(*f)
    def test_authority_forbidden(self):
        for k,v in [('diagnosticOnly',False),('acceptanceAuthority',True)]:
            f=fixture();f[0][k]=v
            with self.assertRaises(ValueError):a.analyze(*f)
    def test_sequence_gap(self):
        f=fixture();f[0]['records'][0]['sequence']=2
        with self.assertRaises(ValueError):a.analyze(*f)
    def test_partial_record(self):
        f=fixture();f[0]['records'][0]['complete']=False
        with self.assertRaises(ValueError):a.analyze(*f)
    def test_no_silent_drop(self):
        f=fixture();f[0]['attempted']=2
        with self.assertRaises(ValueError):a.analyze(*f)
    def test_pid_only_forbidden(self):
        f=fixture();del f[2]['instances'][0]['created']
        with self.assertRaises((ValueError,KeyError)):a.analyze(*f)
    def test_no_independent_window(self):
        f=fixture();del f[2]['instances'][0]['eventWindows']
        with self.assertRaises((ValueError,KeyError)):a.analyze(*f)
    def test_pid_reuse_overlap_unresolved(self):
        f=fixture();t=copy.deepcopy(f[2]['instances'][0]);t.update(created='100001',processSequence=None);f[2]['instances'].append(t)
        self.assertEqual(self.outcome(f),'CALLBACK_SEEN_IDENTITY_UNRESOLVED')
    def test_sequence_contradiction(self):
        f=fixture();f[0]['records'][0]['processSequence']='8'
        self.assertEqual(self.outcome(f),'CALLBACK_SEEN_IDENTITY_UNRESOLVED')
    def test_reused_pid_disjoint(self):
        f=fixture();t=copy.deepcopy(f[2]['instances'][0]);t.update(created='300000',exitFiletime='400000',eventWindows={'START':[300,320],'STOP':[390,420]});f[2]['instances'].append(t)
        self.assertEqual(self.outcome(f),'CALLBACK_ADMITTED');self.assertEqual(a.analyze(*f)['instances'][1]['START']['outcome'],'CALLBACK_NOT_OBSERVED')
    def test_duplicate_callback_unresolved(self):
        f=fixture();r=copy.deepcopy(f[0]['records'][0]);r['sequence']=2;f[0]['records'].append(r);f[0].update(count=2,attempted=2)
        self.assertEqual(self.outcome(f),'CALLBACK_SEEN_IDENTITY_UNRESOLVED')
    def test_loss_correlation(self):self.assertTrue(a.analyze(*fixture())['instances'][0]['START']['lossInSurroundingInterval'])
    def test_loss_coverage_unknown(self):
        f=fixture();f[3]['samples']=[];self.assertIsNone(a.analyze(*f)['instances'][0]['START']['lossInSurroundingInterval'])
    def test_loss_binding(self):
        f=fixture();f[3]['session']='other'
        with self.assertRaises(ValueError):a.analyze(*f)
    def test_diagnostic_only_result(self):
        r=a.analyze(*fixture());self.assertTrue(r['diagnosticOnly']);self.assertFalse(r['acceptanceAuthority']);self.assertEqual(r['historicalCause'],'UNCONFIRMED')
    def test_missing_roles_explicit(self):self.assertEqual(len(a.analyze(*fixture())['missingRoles']),7)
    def test_all_eight_roles(self):
        f=fixture();base=f[2]['instances'][0];f[2]['instances']=[]
        for i,role in enumerate(sorted(a.ROLES)):
            t=copy.deepcopy(base);t.update(role=role,pid=20+i);f[2]['instances'].append(t)
        self.assertEqual(a.analyze(*f)['missingRoles'],[])
    def test_actual_cpp_export_records(self):
        result=json.loads((R/'callback-replay-final.json').read_text());f=fixture();records=result['records']
        # Both channels replayed into one test buffer; validate one complete
        # synthetic export without treating it as a live observer sidecar.
        f[0].update(records=records,count=len(records),attempted=len(records));a.validate(f[0],f[1])

class IntegrationTests(unittest.TestCase):
    def test_original_candidate_unchanged(self):
        for x in json.loads((R/'before.json').read_text()):
            p=Path(x['path']);self.assertEqual((p.stat().st_size,p.stat().st_mtime_ns,hashlib.sha256(p.read_bytes()).hexdigest()),(x['bytes'],x['mtimeNs'],x['sha256']))
    def test_only_two_existing_sources_changed(self):
        changed=[]
        for x in json.loads((R/'predecessor-manifest.json').read_text()):
            if hashlib.sha256((C/x['name']).read_bytes()).hexdigest()!=x['sha256']:changed.append(x['name'])
        self.assertEqual(set(changed),{'authority_trace_v3.cpp','startup_trace.cpp','J6AuthorityTraceV3.exe','J6StartupTrace.exe','authority_trace_v3.obj','preservation-policy-v4.json'})
    def test_no_witness_callback_cost_sources(self):
        h=(C/'lifecycle_witness_v1.hpp').read_text().split('// Serialization')[0]
        for forbidden in ['QueryPerformanceCounter(', 'TdhGet','OpenProcess(', 'GetProcessTimes(', 'CreateFile', 'WriteFile', 'new ', 'malloc(', 'mutex', 'lock(', 'ControlTrace']:
            self.assertNotIn(forbidden,h)
    def test_no_additional_qpc_tdh_or_process_queries(self):
        for name in ['authority_trace_v3.cpp','startup_trace.cpp']:
            old=(S/name).read_text();new=(C/name).read_text()
            for token in ['Q()', 'QueryPerformanceCounter(', 'TdhGetProperty(', 'TdhGetPropertySize(', 'OpenProcess(', 'GetProcessTimes(', 'ParentKnown(', 'rows.emplace(', 'rows.find(']:
                self.assertEqual(old.count(token),new.count(token),(name,token))
    def test_export_after_join(self):
        for name in ['authority_trace_v3.cpp','startup_trace.cpp']:
            s=(C/name).read_text();self.assertGreater(s.index('j6w::exportWitness('),s.index('thread.join();'))
    def test_events_lost_rules_unchanged(self):
        for name in ['authority_trace_v3.cpp','startup_trace.cpp']:
            select=lambda s:[l for l in s.splitlines() if 'EventsLost' in l]
            self.assertEqual(select((S/name).read_text()),select((C/name).read_text()))
    def test_provider_buffers_unchanged(self):
        for name in ['authority_trace_v3.cpp','startup_trace.cpp']:
            select=lambda s:[l for l in s.splitlines() if any(v in l for v in ['EnableTraceEx2(', 'p->BufferSize=', 'p->LogFileMode='])]
            self.assertEqual(select((S/name).read_text()),select((C/name).read_text()))
    def test_frozen_checker_finalizer_handoff_telemetry_unchanged(self):
        names=[x['name'] for x in json.loads((R/'predecessor-manifest.json').read_text()) if any(k in x['name'].lower() for k in ['checker','finaliz','handoff','telemetry','loss_diagnostic'])]
        self.assertGreater(len(names),5)
        for n in names:self.assertEqual((S/n).read_bytes(),(C/n).read_bytes(),n)
    def test_detailed_outer_only_timestamp_pass_changed(self):
        def outer(s):return s[s.index('static void WINAPI Event('):s.index('static void Sample()')]
        self.assertEqual(outer((S/'startup_trace.cpp').read_text()).replace('LifecycleEvent(e);','LifecycleEvent(e,timing.begin);'),outer((C/'startup_trace.cpp').read_text()))
    def test_fixed_capacity_and_overflow(self):
        s=(C/'lifecycle_witness_v1.hpp').read_text();self.assertIn('capacity=65536',s);self.assertIn('overflow=true;return nullptr;',s)
    def test_both_actual_export_bindings(self):
        base=R/'export-offline';exe=base/'WitnessExportOffline.exe'
        for channel,path in [('authority',base/'fresh-channel-run/authority-lifecycle-witness-v1.json'),('detailed',base/'fresh-channel-run/detail/detailed-lifecycle-witness-v1.json')]:
            w=json.loads(path.read_text());self.assertEqual(w['run'],'fresh-channel-run');self.assertEqual(w['channel'],channel)
            self.assertEqual(w['candidateSHA256'],hashlib.sha256((base/'witness-source-v1.json').read_bytes()).hexdigest())
            self.assertEqual(w['observerSHA256'],hashlib.sha256(exe.read_bytes()).hexdigest());self.assertTrue(w['quiesced'])
            self.assertTrue(w['diagnosticOnly']);self.assertFalse(w['acceptanceAuthority'])
    def test_export_failures_no_overwrite(self):
        for channel in ['authority','detailed']:
            self.assertEqual((R/('export-'+channel+'.log')).read_text().strip(),'first=1 duplicate=0 missing=0')
    def test_preservation_policy_exact_extension(self):
        old=json.loads((S/'preservation-policy-v4.json').read_text());new=json.loads((C/'preservation-policy-v4.json').read_text())
        names=['authority-lifecycle-witness-v1.json','detail/detailed-lifecycle-witness-v1.json','lifecycle-witness-export-failure-v1.json','detail/lifecycle-witness-export-failure-v1.json']
        self.assertEqual(new['artifactPatterns'],old['artifactPatterns']+[re.escape(n) for n in names])
        for n in names:self.assertTrue(any(re.fullmatch(p,n) for p in new['artifactPatterns']))
        new['artifactPatterns']=old['artifactPatterns'];self.assertEqual(old,new)
    def test_missing_witness_preserves_incomplete_output(self):
        directory=R/'missing-sidecar-test';directory.mkdir(exist_ok=True)
        output=directory/'result.json'
        # Exclusive output; each execution gets a fresh output identity.
        import uuid
        output=directory/(uuid.uuid4().hex+'.json')
        cmd=[__import__('sys').executable,'-B',str(C/'analyze_lifecycle_witness_v1.py')]
        for k in ['witness','binding','targets','loss']:cmd+=['--'+k,str(directory/'absent.json')]
        cmd+=['--output',str(output)]
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=10);self.assertEqual(p.returncode,2)
        result=json.loads(output.read_text());self.assertEqual(result['status'],'WITNESS_INCOMPLETE');self.assertFalse(result['acceptanceAuthority'])
    def test_failure_archive_roundtrip(self):
        # Archive actual offline sidecars; this is a preservation test, not a
        # success seal and not execution of a frozen acceptance finalizer.
        import io
        paths=[R/'export-offline/fresh-channel-run/authority-lifecycle-witness-v1.json',R/'export-offline/fresh-channel-run/detail/detailed-lifecycle-witness-v1.json']
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('NON-ACCEPTANCE.txt','OFFLINE WITNESS TEST ONLY')
            for p in paths:z.writestr(p.name,p.read_bytes())
        with zipfile.ZipFile(stream) as z:
            self.assertIsNone(z.testzip())
            for p in paths:self.assertEqual(hashlib.sha256(z.read(p.name)).hexdigest(),hashlib.sha256(p.read_bytes()).hexdigest())

if __name__=='__main__':unittest.main(verbosity=2)
