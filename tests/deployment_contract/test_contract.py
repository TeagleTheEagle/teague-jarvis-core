"""Focused policy tests only. Dummy package files are never executed."""
import hashlib
import io
import json
from pathlib import Path
import secrets
import sys
import tempfile
import unittest
import uuid
from unittest import mock

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from deployment_test import contract as c, enrollment as e

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.parent=Path(tempfile.mkdtemp(prefix='TEST-DEPLOYMENT-POLICY-'))
        self.install=c.private_directory(self.parent/('TEST-INSTALL-'+uuid.uuid4().hex))
        c.private_directory(self.install/'state');c.private_directory(self.install/'releases')
        self.state=c.private_directory(self.install/'state'/('TEST-STAGE4-'+uuid.uuid4().hex))
        for name in ('enrollment','owner-intents','updates'):c.private_directory(self.state/name)
        (self.state/'TEST_ONLY').write_text('NO PRODUCTION SERVICES')
        release=c.private_directory(self.install/'releases'/'test-policy-fixture')
        for name in ('python','electron','app'):c.private_directory(release/name)
        for name in ('python/python.exe','electron/electron.exe'):(release/name).write_bytes(b'NONEXECUTABLE POLICY TEST FIXTURE')
        files=[dict(path=p.relative_to(release).as_posix(),bytes=p.stat().st_size,sha256=c.digest(p)) for p in release.rglob('*') if p.is_file()]
        c.exclusive_json(release/'manifest.json',dict(mode=c.MODE,version=2,application_version=1,enrollment_format=1,bootstrap_contract=2,build='a'*32,protocol=[2,3],data_schema=1,files=files,capabilities={'policy_fixture_only':True}))
        record=dict(schema=c.SCHEMA,mode=c.MODE,installation_id=self.install.name,data_id='TEST-'+uuid.uuid4().hex,owner_sid=c.current_sid(),
            install_root=str(self.install),state_root=str(self.state),release_root=str(release),package_hash=c.digest(release/'manifest.json'),protocol=[2,3],data_schema=1)
        c.write_protected(self.install/'binding.dpapi',record)
        self.b=c.Binding(self.install/'binding.dpapi');self.key=secrets.token_bytes(32)
        c.write_protected(self.install/'initial-owner.dpapi',dict(binding=self.b.seal,owner_key=self.key.hex(),intent='NEW_SYNTHETIC_TEST'))
    def init(self):
        return e.initialize(self.b,e.signed_request(self.b,self.key,'initialize',{'intent':'NEW_SYNTHETIC_TEST'}),lambda:None)
    def test_binding_resolves_explicit_roots(self):
        self.assertEqual(self.b.check_root(self.state),self.state);self.assertNotEqual(self.b.release,self.state)
    def test_missing_root(self):
        with self.assertRaises(FileNotFoundError):c.safe_path(self.parent/'missing')
    def test_relative_root(self):
        with self.assertRaisesRegex(ValueError,'ABSOLUTE_LOCAL'):c.safe_path('relative')
    def test_remote_path(self):
        with self.assertRaisesRegex(ValueError,'ABSOLUTE_LOCAL'):c.safe_path(r'\\server\share\test')
    def test_ambiguous_json(self):
        p=self.state/'ambiguous.json';p.write_text('{"a":1,"a":2}')
        with self.assertRaisesRegex(ValueError,'AMBIGUOUS'):c.read_json(p)
    def test_conflicting_root(self):
        with self.assertRaisesRegex(ValueError,'CONFLICTING'):self.b.check_root(self.parent)
    def test_copied_binding(self):
        clone=c.private_directory(self.parent/('TEST-INSTALL-'+uuid.uuid4().hex));(clone/'binding.dpapi').write_bytes(self.b.descriptor.read_bytes())
        with self.assertRaisesRegex(ValueError,'COPIED_BINDING'):c.Binding(clone/'binding.dpapi')
    def test_package_identity(self):
        # These are intentionally non-executable policy files; actual PE/native checks run in the installed campaign.
        with mock.patch('deployment_test.native.verify_native'):
            self.assertEqual(self.b.verify_package()['mode'],c.MODE)
    def test_modified_runtime_rejected(self):
        (self.b.release/'python/python.exe').write_bytes(b'MODIFIED NONEXECUTABLE FIXTURE')
        with self.assertRaisesRegex(ValueError,'PACKAGE_FILE_IDENTITY'):self.b.verify_package()
    def test_unmanifested_code_rejected(self):
        (self.b.release/'app/extra.py').write_text('# unexpected module')
        with self.assertRaisesRegex(ValueError,'UNMANIFESTED'):self.b.verify_package()
    def test_manifest_modified_rejected(self):
        (self.b.release/'manifest.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'PACKAGE_PIN'):self.b.verify_package()
    def test_no_generic_process_role(self):
        with self.assertRaisesRegex(ValueError,'BOOTSTRAP_ROLE'):self.b.python_command('--execute-arbitrary-code')
    def test_explicit_owner_init(self):
        self.assertEqual(self.init()['result'],'INITIALIZED');self.assertEqual(e.current(self.b)['version'],1)
    def test_no_silent_second_init(self):
        self.init()
        with self.assertRaisesRegex(ValueError,'ALREADY_COMMITTED'):self.init()
    def test_wrong_owner_proof(self):
        req=e.signed_request(self.b,secrets.token_bytes(32),'initialize',{'intent':'NEW_SYNTHETIC_TEST'})
        with self.assertRaisesRegex(ValueError,'OWNER_PROOF'):e.initialize(self.b,req,lambda:None)
        self.assertFalse((self.state/'initialized.json').exists())
    def test_expired_owner_intent(self):
        req=e.signed_request(self.b,self.key,'initialize',{'intent':'NEW_SYNTHETIC_TEST'});req['body']['expires']=0
        with self.assertRaisesRegex(ValueError,'OWNER_EXPIRY'):e.initialize(self.b,req,lambda:None)
    def test_owner_intent_one_use(self):
        self.init();req=e.signed_request(self.b,self.key,'inspect',{})
        e.authorize(self.b,req)
        with self.assertRaises(FileExistsError):e.authorize(self.b,req)
    def test_wrong_installation_intent(self):
        req=e.signed_request(self.b,self.key,'initialize',{'intent':'NEW_SYNTHETIC_TEST'});req['body']['installation']='OTHER'
        with self.assertRaisesRegex(ValueError,'OWNER_TARGET'):e.initialize(self.b,req,lambda:None)
    def test_ordinary_has_no_management(self):
        self.init();record=e.current(self.b)
        self.assertNotIn('lifecycle',record['entries']['teague']['scopes']);self.assertIn('lifecycle',record['entries']['controller']['scopes'])
    def test_persistent_enrollment_reopen(self):
        self.init();again=c.Binding(self.b.descriptor)
        self.assertEqual(e.current(self.b),e.current(again))
    def test_incomplete_enrollment_generation_fails_closed(self):
        self.init();(self.state/'enrollment/generation-000002.dpapi').write_bytes(b'incomplete')
        with self.assertRaises(OSError):e.current(self.b)
    def test_skipped_generation_rejected(self):
        self.init();c.write_protected(self.state/'enrollment/generation-000003.dpapi',{})
        with self.assertRaisesRegex(ValueError,'ENROLLMENT_GAP'):e.current(self.b)
    def test_copied_enrollment_rejected(self):
        self.init();record=e.current(self.b)
        record['binding']='0'*64
        c.write_protected(self.state/'enrollment/generation-000002.dpapi',{**record,'version':2})
        with self.assertRaisesRegex(ValueError,'ENROLLMENT_GENERATION'):e.current(self.b)
    def test_partial_initialization_cannot_reinitialize_or_start(self):
        original=e.write_protected
        def interrupt(path,value):
            if path.name.startswith('generation-'):raise OSError('TEST interrupted generation publication')
            return original(path,value)
        with mock.patch.object(e,'write_protected',interrupt):
            with self.assertRaisesRegex(OSError,'TEST interrupted'):self.init()
        with self.assertRaisesRegex(ValueError,'ENROLLMENT_HISTORY'):e.core_configuration(self.b)
        with self.assertRaisesRegex(ValueError,'ALREADY_COMMITTED'):self.init()
        self.assertFalse((self.state/'initialized.json').exists())
    def test_pending_restore_fence_denies_operational_binding(self):
        c.exclusive_json(self.state/'deployment-fence.json',{'action':'prepare-restore','operation':'a'*32})
        with self.assertRaisesRegex(ValueError,'DEPLOYMENT_FENCED'):c.Binding(self.b.descriptor)
    def test_complete_authenticated_reinstall_binding_is_operational(self):
        c.exclusive_json(self.state/'deployment-fence.json',{'action':'prepare-uninstall','operation':'a'*32})
        c.write_protected(self.state/'reinstall-ready.dpapi',dict(binding=self.b.seal,operation='a'*32,package_hash=self.b.record['package_hash'],revision=2))
        self.assertEqual(c.Binding(self.b.descriptor).state,self.state)

if __name__=='__main__':
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ContractTests))
    out=ROOT/'docs/deployment-completion-20260916'/('policy-'+uuid.uuid4().hex+'.json')
    out.write_text(json.dumps(dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
        output=stream.getvalue(),actual_core_execution=False,fixture_packages_nonexecutable=True),indent=2),encoding='utf8')
    print(stream.getvalue());print('Evidence:',out);sys.exit(not result.wasSuccessful())
