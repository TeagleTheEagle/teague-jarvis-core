"""Offline sacrificial tests; never run an observer, launcher, collector or UAC."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest
from unittest import mock
import uuid
import zipfile

import failure_preserve_v1 as p
import one_run_v1 as driver


ROOT = Path(__file__).parent.parent/'fixtures'


class FailurePreservation(unittest.TestCase):
    def setUp(self):
        self.home=ROOT/(self._testMethodName+'-'+uuid.uuid4().hex)
        self.base=self.home/'candidate'; self.base.mkdir(parents=True)
        self.out=self.home/'preservation'; self.out.mkdir()
        self.run=self.base/('protected-'+uuid.uuid4().hex); self.run.mkdir()
        self.policy=json.loads(Path(__file__).with_name('policy.json').read_text())
        self.policy.update(candidate=str(self.base),preservationRoot=str(self.out))
        self.failure=dict(classification='REJECTED',timestampUtc='2026-09-23T00:00:00+00:00',
                          qpc=200,component='collector',reason='COLLECTOR_FAILURE',observationOnly=True)
        for name in p.EXPECTED:
            self.put(name,{'run':self.run.name})
        self.put('small-declaration-v3.json',dict(run=self.run.name,sourceManifestSHA256=self.policy['sourceManifestSHA256']))
        self.put('cleanup-origin-v3.json',dict(run=self.run.name,cleanupEntryQpc=280,frequency=1,deadlineQpc=300))

    def put(self,name,value):
        file=self.run/name;file.parent.mkdir(parents=True,exist_ok=True)
        file.write_bytes(value if isinstance(value,bytes) else p.encode(value))

    def clean(self,run):
        return dict(run=run.name,evidenceRoot=str(run),available=True,processes=[],traces=[],
                    unknown=[],completedQpc=250,frequency=1,completedUtc=p.utc())

    def unknown(self,run):
        return dict(self.clean(run),available=False,processes=None,traces=None,unknown=['ACCESS_DENIED'])

    def preserve(self,**kwargs):
        return p.preserve(self.run,self.policy,self.out,self.failure,census=kwargs.pop('census',self.clean),**kwargs)

    def manifest(self,result):
        return json.loads((Path(result['directory'])/'FAILURE-MANIFEST.json').read_text())

    def files(self):
        return {x.relative_to(self.run).as_posix():(p.sha(x),x.stat().st_size,x.stat().st_mtime_ns)
                for x in self.run.rglob('*') if x.is_file()}

    def test_01_accepted_run_refuses_failure_archive(self):
        self.put('v3-archive-receipt.json',dict(state='ACCEPTED',status='SMALL_NORMAL_PASS'))
        with self.assertRaisesRegex(ValueError,'ACCEPTANCE_ARCHIVE'):self.preserve()
        self.assertEqual(list(self.out.iterdir()),[])

    def test_02_collector_failure_archive_complete(self):
        result=self.preserve(); self.assertEqual(result['status'],'FAILURE_EVIDENCE_COMPLETE')
        self.assertEqual(result['hashMismatches'],0)

    def partial_failure(self,component,reason):
        (self.run/'terminal-v3.json').unlink()  # synthetic setup only, never real failed evidence
        self.failure.update(component=component,reason=reason)
        result=self.preserve();m=self.manifest(result)
        self.assertEqual(result['status'],'FAILURE_EVIDENCE_PARTIAL')
        self.assertIn('terminal-v3.json',m['missingArtifacts'])
        self.assertEqual(m['firstFailureObserved']['reason'],reason)

    def test_03_observer_startup_partial(self):self.partial_failure('observer','STARTUP_FAILED')
    def test_04_uac_cancel_partial(self):self.partial_failure('observer','UAC_CANCELLED')
    def test_05_missing_terminal(self):self.partial_failure('launcher','TERMINAL_RECEIPT_MISSING')
    def test_06_helper_deadline(self):self.partial_failure('helper','HARD_DEADLINE')
    def test_07_checker_rejection(self):self.partial_failure('checker','REJECTED')
    def test_08_finalizer_refusal(self):self.partial_failure('normal-finalizer','INCOMPLETE_TERMINAL')

    def test_09_eventual_cleanup_never_pass(self):
        result=self.preserve();m=self.manifest(result)
        self.assertTrue(m['EVENTUAL_HOST_CLEANUP_PROVEN'])
        self.assertFalse(m['acceptance_seal']);self.assertEqual(m['runOutcome'],'REJECTED')

    def test_10_cleanup_after_deadline(self):
        result=self.preserve(census=lambda run:dict(self.clean(run),completedQpc=301))
        m=self.manifest(result);self.assertTrue(m['EVENTUAL_HOST_CLEANUP_PROVEN'])
        self.assertFalse(m['ACCEPTANCE_CLEANUP_TIMELY']);self.assertEqual(m['acceptanceDeadlineQpc'],300)

    def test_11_cleanup_unknown(self):
        result=self.preserve(census=self.unknown);m=self.manifest(result)
        self.assertEqual(result['status'],'CLEANUP_UNPROVEN');self.assertFalse(m['cleanupProven'])
        self.assertEqual(m['preserved'],[]);self.assertTrue(m['potentiallyMutable'])

    def test_12_active_writer_no_read(self):
        active=lambda run:dict(self.clean(run),processes=[dict(pid=55,created=123,image='synthetic-writer')])
        with mock.patch.object(p,'locked_read',side_effect=AssertionError('MUST_NOT_READ')):
            result=self.preserve(census=active)
        self.assertEqual(result['status'],'CLEANUP_UNPROVEN')

    def test_13_partial_set_explicit(self):
        (self.run/'observer-identities.json').unlink()
        m=self.manifest(self.preserve());self.assertIn('observer-identities.json',m['missingArtifacts'])
        self.assertEqual(m['knownObserverIDs'],'UNKNOWN')

    def test_14_malformed_bytes_unchanged(self):
        data=b'{broken\x00\xff\r\n';self.put('primary-failure.json',data)
        result=self.preserve();directory=Path(result['directory'])
        with zipfile.ZipFile(next(directory.glob('*.zip'))) as z:
            self.assertEqual(z.read('evidence/primary-failure.json'),data)
        self.assertEqual((self.run/'primary-failure.json').read_bytes(),data)

    def test_15_first_failure_preserved(self):
        self.put('rejected-v3.json',dict(run=self.run.name,qpc=100,reason='FIRST_TERMINAL_FAILURE'))
        self.put('launcher-failure.json',dict(run=self.run.name,qpc=150,reason='LATER_CLEANUP'))
        m=self.manifest(self.preserve())
        self.assertEqual(m['earliestTimestampedRunFailure']['value']['reason'],'FIRST_TERMINAL_FAILURE')
        self.assertEqual(len(m['preservedFailureRecords']),2)
        self.assertEqual(m['firstFailureObserved']['reason'],'COLLECTOR_FAILURE')

    def test_16_cross_run_excluded(self):
        self.put('terminal-v3.json',dict(binding=dict(run='protected-'+'f'*32)))
        result=self.preserve();m=self.manifest(result)
        self.assertIn('terminal-v3.json',m['missingArtifacts'])
        self.assertTrue(any('CROSS_RUN' in x['reason'] for x in m['exclusions']))
        with zipfile.ZipFile(next(Path(result['directory']).glob('*.zip'))) as z:
            self.assertNotIn('evidence/terminal-v3.json',z.namelist())

    def test_17_failure_naming(self):
        result=self.preserve();self.assertTrue(Path(result['directory']).name.startswith('FAILURE-EVIDENCE-'))
        self.assertEqual(result['label'],p.LABEL)

    def test_18_no_acceptance_seal(self):
        result=self.preserve();self.assertFalse(result['acceptance_seal'])
        self.assertFalse(self.manifest(result)['acceptance_seal'])
        self.assertFalse((self.run/'v3-seal.json').exists())

    def test_19_no_success_finalizer_dependency(self):
        import ast
        tree=ast.parse(Path(p.__file__).read_text())
        imports=[getattr(n,'module','') or '' for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
        self.assertFalse(any('finaliz' in name or 'check_v' in name for name in imports))
        self.assertEqual(self.manifest(self.preserve())['successFinalizerInvoked'],False)

    def test_20_corruption_detected(self):
        result=self.preserve();original=next(Path(result['directory']).glob('*.zip'))
        corrupt=self.home/'deliberately-corrupt.zip'
        with zipfile.ZipFile(original) as src,zipfile.ZipFile(corrupt,'x') as dst:
            for name in src.namelist():
                data=src.read(name)
                dst.writestr(name,data+b'bad' if name=='evidence/contract.json' else data)
        with self.assertRaisesRegex(ValueError,'ARCHIVE_HASH'):p.verify_archive(corrupt)

    def test_21_verifier_failure_state(self):
        result=self.preserve(verifier=mock.Mock(side_effect=ValueError('INJECTED_VERIFY_ERROR')))
        self.assertEqual(result['status'],'ARCHIVE_UNVERIFIED')
        self.assertTrue(next(Path(result['directory']).glob('*.zip')).exists())

    def test_22_no_archive_overwrite(self):
        result=self.preserve();path=next(Path(result['directory']).glob('*.zip'));old=p.sha(path)
        with self.assertRaises(FileExistsError):self.preserve()
        self.assertEqual(p.sha(path),old)

    def test_23_source_immutable(self):
        before=self.files();self.preserve();self.assertEqual(before,self.files())

    def test_24_frozen_candidate_hashes(self):
        p.verify_candidate(p.cli_policy())

    def test_25_historical_failure_fixture_not_pass(self):
        # Copy only preserved historical test artifacts, never rerun/reinterpret them.
        source=Path(r'D:\JARVIS-STAGE6-LIVE\2d922197cf7d4bb098d8da6e070cbff2\code\protected-8145cedf8db843959b8ba58dfd62717b')
        historical=self.base/source.name
        prior={str(x.relative_to(source)):(p.sha(x),x.stat().st_mtime_ns) for x in source.rglob('*') if x.is_file()}
        shutil.copytree(source,historical)
        result=p.preserve(historical,self.policy,self.out,self.failure,census=self.unknown)
        self.assertEqual(result['status'],'CLEANUP_UNPROVEN');self.assertFalse(result['acceptance_seal'])
        self.assertEqual(prior,{str(x.relative_to(source)):(p.sha(x),x.stat().st_mtime_ns) for x in source.rglob('*') if x.is_file()})

    def test_26_no_run_no_archive(self):
        empty=self.base/('protected-'+'e'*32);empty.mkdir()
        with self.assertRaisesRegex(ValueError,'NOTHING'):p.preserve(empty,self.policy,self.out,self.failure,census=self.clean)
        self.assertEqual(list(self.out.iterdir()),[])

    def test_27_path_escape_before_access(self):
        with self.assertRaisesRegex(ValueError,'UNAPPROVED_RUN_ROOT'):
            p.preserve(self.base/'..'/'protected-escape',self.policy,self.out,self.failure,census=self.clean)

    def test_28_hardlink_no_content_read(self):
        external=self.home/'external.bin';external.write_bytes(b'NOT_ARCHIVABLE')
        os.link(external,self.run/'primary-failure.json')
        m=self.manifest(self.preserve());self.assertTrue(any('HARDLINK' in x['reason'] for x in m['exclusions']))

    def test_29_unknown_file_and_env_excluded(self):
        self.put('.env',b'SYNTHETIC_SECRET_MUST_NOT_ARCHIVE');self.put('unexpected.bin',b'unknown')
        result=self.preserve()
        with zipfile.ZipFile(next(Path(result['directory']).glob('*.zip'))) as z:
            self.assertNotIn('evidence/.env',z.namelist());self.assertNotIn('evidence/unexpected.bin',z.namelist())

    def test_30_real_windows_writer_handle_conflict(self):
        with (self.run/'contract.json').open('r+b'):
            result=self.preserve()
        m=self.manifest(result)
        self.assertIn('contract.json',m['missingArtifacts']);self.assertTrue(m['potentiallyMutable'])

    def test_31_locked_source_denies_write(self):
        with p.locked_read(self.run/'contract.json'):
            with self.assertRaises(PermissionError):(self.run/'contract.json').open('wb')

    def test_32_source_addition_invalidates_verification(self):
        def verifier(path,manifest):
            self.put('primary-failure.json',b'late writer')
            return p.verify_archive(path,manifest)
        self.assertEqual(self.preserve(verifier=verifier)['status'],'ARCHIVE_UNVERIFIED')

    def test_33_census_binding_mismatch(self):
        result=self.preserve(census=lambda run:dict(self.clean(run),run='protected-'+'f'*32))
        self.assertEqual(result['status'],'CLEANUP_UNPROVEN')

    def test_34_source_declaration_mismatch(self):
        self.put('small-declaration-v3.json',dict(run=self.run.name,sourceManifestSHA256='wrong'))
        self.assertEqual(self.preserve()['status'],'ARCHIVE_UNVERIFIED')

    def test_35_manifest_corruption_rejected(self):
        result=self.preserve();archive=next(Path(result['directory']).glob('*.zip'))
        with self.assertRaisesRegex(ValueError,'MANIFEST_HASH'):p.verify_archive(archive,b'wrong')

    def test_36_duplicate_archive_member_rejected(self):
        result=self.preserve();archive=next(Path(result['directory']).glob('*.zip'))
        broken=self.home/'duplicate.zip'
        shutil.copyfile(archive,broken)
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            with zipfile.ZipFile(broken,'a') as z:z.writestr('NON-ACCEPTANCE.txt',p.LABEL+'\n')
        with self.assertRaisesRegex(ValueError,'DUPLICATE'):p.verify_archive(broken)

    def test_37_wrapper_never_retries_driver_failure(self):
        fake=mock.Mock(return_value=subprocess.CompletedProcess([],7));sink=mock.Mock(return_value={'status':'CLEANUP_UNPROVEN'})
        (self.run/'launcher-identity.json').unlink()
        with mock.patch.object(p,'verify_candidate'):
            result=driver.execute(self.run.name,self.policy,True,invoke=fake,preserve=sink)
        self.assertEqual(fake.call_count,1);self.assertEqual(sink.call_count,1)
        self.assertEqual(result['status'],'CLEANUP_UNPROVEN')

    def test_38_wrapper_success_never_preserves(self):
        fake=mock.Mock(return_value=subprocess.CompletedProcess([],0));sink=mock.Mock()
        (self.run/'launcher-identity.json').unlink()
        with mock.patch.object(p,'verify_candidate'):
            result=driver.execute(self.run.name,self.policy,True,invoke=fake,preserve=sink)
        self.assertEqual(fake.call_count,2);sink.assert_not_called()
        self.assertEqual(result['route'],'SUCCESS_FINALIZER_COMPLETED')

    def test_39_wrapper_finalizer_failure_preserved(self):
        fake=mock.Mock(side_effect=[subprocess.CompletedProcess([],0),subprocess.CompletedProcess([],9)])
        sink=mock.Mock(return_value={'status':'FAILURE_EVIDENCE_PARTIAL'})
        (self.run/'launcher-identity.json').unlink()
        with mock.patch.object(p,'verify_candidate'):
            driver.execute(self.run.name,self.policy,True,invoke=fake,preserve=sink)
        self.assertEqual(fake.call_count,2)
        self.assertEqual(sink.call_args.args[-1]['component'],'small_finalize_v3')

    def test_40_wrapper_requires_fresh_owner_approval(self):
        fake=mock.Mock()
        with self.assertRaisesRegex(ValueError,'APPROVAL'):
            driver.execute(self.run.name,self.policy,False,invoke=fake)
        fake.assert_not_called()

    def test_41_archive_write_failure(self):
        with mock.patch.object(p.zipfile,'ZipFile',side_effect=OSError('SIMULATED_DISK_FULL')):
            result=self.preserve()
        self.assertEqual(result['status'],'ARCHIVE_UNVERIFIED');self.assertFalse(result['acceptance_seal'])

    def test_42_census_becomes_uncertain(self):
        calls=iter([self.clean(self.run),self.clean(self.run),self.unknown(self.run)])
        result=self.preserve(census=lambda run:next(calls))
        self.assertEqual(result['status'],'ARCHIVE_UNVERIFIED')

    def test_43_deadline_not_trusted_without_original_formula(self):
        self.put('cleanup-origin-v3.json',dict(run=self.run.name,cleanupEntryQpc=280,frequency=1,deadlineQpc=9000))
        m=self.manifest(self.preserve())
        self.assertIsNone(m['ACCEPTANCE_CLEANUP_TIMELY'])
        self.assertIsNone(m['acceptanceDeadlineQpc'])

    def test_44_census_clock_mismatch_is_not_timely_proof(self):
        result=self.preserve(census=lambda run:dict(self.clean(run),frequency=999))
        self.assertIsNone(self.manifest(result)['ACCEPTANCE_CLEANUP_TIMELY'])

    def test_45_historical_bytes_offline_archive(self):
        source=Path(r'D:\JARVIS-STAGE6-LIVE\2d922197cf7d4bb098d8da6e070cbff2\code\protected-8145cedf8db843959b8ba58dfd62717b')
        historical=self.base/source.name;shutil.copytree(source,historical)
        policy=dict(self.policy)
        declaration=json.loads((historical/'small-declaration-v2.json').read_text())
        policy['sourceManifestSHA256']=declaration['sourceManifestSHA256']
        policy['artifactPatterns']=policy['artifactPatterns']+[r'small-declaration-v2\.json']
        result=p.preserve(historical,policy,self.out,self.failure,census=self.clean)
        self.assertIn(result['status'],('FAILURE_EVIDENCE_PARTIAL','FAILURE_EVIDENCE_COMPLETE'))
        m=self.manifest(result)
        self.assertGreater(len(m['preserved']),0)
        self.assertEqual(m['runOutcome'],'REJECTED');self.assertFalse(m['acceptance_seal'])
        for row in m['preserved']:
            self.assertEqual(row['sha256'],p.sha(source/row['path']))

    def test_46_live_exact_instance_prevents_cleanup_claim(self):
        # This ordinary unittest process is the harmless live instance. No new process.
        from ctypes import wintypes as w
        import ctypes
        k=ctypes.WinDLL('kernel32',use_last_error=True)
        k.GetCurrentProcess.restype=w.HANDLE
        k.GetProcessTimes.argtypes=[w.HANDLE,*([ctypes.POINTER(w.FILETIME)]*4)]
        values=[w.FILETIME() for _ in range(4)]
        self.assertTrue(k.GetProcessTimes(k.GetCurrentProcess(),*[ctypes.byref(x) for x in values]))
        created=(values[0].dwHighDateTime<<32)|values[0].dwLowDateTime
        self.put('etw-result.json',dict(run=self.run.name,rows=[dict(pid=os.getpid(),created=created)]))
        result=self.preserve();m=self.manifest(result)
        self.assertEqual(result['status'],'CLEANUP_UNPROVEN')
        self.assertEqual(m['recordedInstanceCensus']['rows'][0]['state'],'EXACT_INSTANCE_STILL_LIVE')

    def test_47_same_pid_different_creation_not_force_matched(self):
        result=p.instance_census({'etw-result.json':dict(rows=[dict(pid=os.getpid(),created=1)])})
        self.assertTrue(result['clean'])
        self.assertEqual(result['rows'][0]['state'],'PID_REUSED_RECORDED_INSTANCE_ABSENT')

    def test_48_malformed_identity_is_unproven(self):
        self.put('tree-handles.json',dict(run=self.run.name,rows=[dict(pid=22,created='bad')]))
        self.assertEqual(self.preserve()['status'],'CLEANUP_UNPROVEN')


if __name__=='__main__':unittest.main(verbosity=2)
