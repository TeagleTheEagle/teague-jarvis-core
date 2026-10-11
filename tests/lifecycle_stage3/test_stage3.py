"""Windows TEST-only migration/rollback acceptance, no App or production services."""
import concurrent.futures
import errno
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
import unittest
import uuid

sys.path.insert(0, str(Path(__file__).absolute().parent))
import fixtures
import migration as m
import verify

RECORDS = []


class Tests(unittest.TestCase):
    def setUp(self):
        self.root, self.db = fixtures.create()
        self.addCleanup(self.db.close)
        self.expected = verify.inventory(self.root / 'source')

    def run_child(self, *args):
        return subprocess.Popen([sys.executable, '-I', str(Path(m.__file__)), str(self.root), *args],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                env={k: v for k, v in os.environ.items() if k.upper() in ('SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP')},
                                close_fds=True, creationflags=0x08000000)

    def check_source_mapping(self):
        self.assertEqual(m.read(self.root / 'mapping.json')['active'], 'source')

    def test_01_complete_all_tables_artifacts(self):
        self.assertEqual(m.migrate(self.root)['status'], 'ACTIVE_TEST_ONLY')
        self.assertEqual(verify.inventory(self.root / 'canonical'), self.expected)
        self.assertEqual(verify.inventory(self.root / 'backup'), self.expected)
        self.assertEqual(verify.inventory(self.root / 'source'), self.expected)
        self.assertEqual(verify.verify(self.root / 'canonical', self.expected)['tables'], 15)

    def test_02_wal_committed_uncheckpointed(self):
        self.assertGreater((self.root / 'source/jarvis.sqlite3-wal').stat().st_size, 32)
        self.db.execute("INSERT INTO messages(conversation,role,content,created) VALUES('wal','user','TEST WAL latest',3)")
        self.db.commit()
        expected = verify.inventory(self.root / 'source')
        m.migrate(self.root)
        self.assertEqual(verify.inventory(self.root / 'canonical'), expected)

    def test_03_uncommitted_write_refused(self):
        self.db.execute("UPDATE messages SET content='UNCOMMITTED TEST'")
        with self.assertRaises(sqlite3.OperationalError):
            m.migrate(self.root)
        self.db.rollback()
        self.check_source_mapping()

    def test_04_writer_blocked_at_backup_boundary(self):
        child = self.run_child('--fault', 'hold')
        try:
            deadline = time.monotonic() + 5
            while not (self.root / 'held.json').exists() and time.monotonic() < deadline:
                time.sleep(.02)
            self.assertTrue((self.root / 'held.json').exists())
            other = sqlite3.connect(self.root / 'source/jarvis.sqlite3', timeout=.05)
            try:
                with self.assertRaises(sqlite3.OperationalError):
                    other.execute("INSERT INTO settings VALUES('blocked','test')")
            finally:
                other.close()
            stdout, _ = child.communicate(timeout=8)
            self.assertEqual(child.returncode, 0)
        finally:
            if child.poll() is None:
                child.terminate()
                child.wait()

    def test_05_ephemeral_and_secrets_excluded(self):
        m.migrate(self.root)
        for name in ('runtime', 'secrets', 'cache'):
            self.assertFalse((self.root / 'canonical' / name).exists())
            self.assertTrue((self.root / 'source' / name).exists())
        self.assertFalse(m.migrate(self.root)['execution_authorized'])

    def test_06_corrupted_source(self):
        self.db.close()
        (self.root / 'source/jarvis.sqlite3').write_bytes(b'bad database')
        with self.assertRaises(sqlite3.DatabaseError):
            m.migrate(self.root)
        self.check_source_mapping()

    def test_07_schema_mismatch(self):
        self.db.execute('CREATE TABLE unexpected(value)')
        self.db.commit()
        with self.assertRaisesRegex(ValueError, 'SCHEMA'):
            m.migrate(self.root)

    def test_08_identity_mismatch(self):
        m.write(self.root / 'source/identity.json', {'mode': 'PRODUCTION'})
        with self.assertRaisesRegex(ValueError, 'IDENTITY'):
            m.migrate(self.root)

    def test_09_nonempty_destination(self):
        (self.root / 'canonical').mkdir()
        (self.root / 'canonical/keep.txt').write_text('TEST existing')
        with self.assertRaisesRegex(ValueError, 'DESTINATION'):
            m.migrate(self.root)
        self.assertEqual((self.root / 'canonical/keep.txt').read_text(), 'TEST existing')

    def test_10_outside_path(self):
        with self.assertRaisesRegex(ValueError, 'TEST_ROOT'):
            m.migrate(Path(__file__).parent.parent.parent / 'data')

    def test_11_hardlink_refused(self):
        os.link(self.root / 'source/persistent/personality.txt', self.root / 'source/persistent/linked.txt')
        with self.assertRaisesRegex(ValueError, 'HARDLINK'):
            m.migrate(self.root)

    def test_12_reparse_refused(self):
        # Junction target and link are both within this disposable TEST namespace.
        link = self.root / 'junction'
        p = subprocess.run(['cmd.exe', '/d', '/c', 'mklink', '/J', str(link), str(self.root / 'source/persistent')],
                           capture_output=True, creationflags=0x08000000)
        self.assertEqual(p.returncode, 0)
        with self.assertRaisesRegex(ValueError, 'REPARSE'):
            m.migrate(self.root)

    def test_13_disk_full_injected(self):
        with self.assertRaises(OSError) as error:
            m.migrate(self.root, fault='disk-full')
        self.assertEqual(error.exception.errno, errno.ENOSPC)
        self.check_source_mapping()

    def test_14_actual_permission_denied(self):
        import stat
        path = self.root / 'mapping.json'
        path.chmod(stat.S_IREAD)
        try:
            with self.assertRaises(PermissionError):
                m.migrate(self.root)
            self.check_source_mapping()
        finally:
            path.chmod(stat.S_IREAD | stat.S_IWRITE)

    def test_15_corrupted_candidate_independently_rejected(self):
        with self.assertRaises(sqlite3.DatabaseError):
            m.migrate(self.root, fault='corrupt-staging')
        self.check_source_mapping()

    def test_16_missing_artifact_independently_rejected(self):
        with self.assertRaisesRegex(ValueError, 'CONTENT'):
            m.migrate(self.root, fault='omit-artifact')
        self.check_source_mapping()

    def test_17_external_mutation_detected(self):
        with self.assertRaisesRegex(ValueError, 'SOURCE_CHANGED'):
            m.migrate(self.root, fault='artifact-race')
        self.check_source_mapping()

    def test_18_independent_database_tamper(self):
        m.migrate(self.root)
        with sqlite3.connect(self.root / 'canonical/jarvis.sqlite3') as db:
            db.execute("UPDATE messages SET content='TEST altered'")
        with self.assertRaisesRegex(ValueError, 'CONTENT'):
            verify.verify(self.root / 'canonical', self.expected)

    def test_19_idempotency_and_conflict(self):
        m.migrate(self.root)
        self.assertTrue(m.migrate(self.root)['idempotent'])
        with self.assertRaisesRegex(ValueError, 'CONFLICT'):
            m.migrate(self.root, 'another-operation')

    def test_20_repeated_process_contention(self):
        # Three fresh namespaces, four OS processes each; busy losers may retry only manually.
        for _ in range(3):
            root, db = fixtures.create()
            original = self.root
            self.root = root
            try:
                children = [self.run_child() for _ in range(4)]
                results = []
                for child in children:
                    out, err = child.communicate(timeout=10)
                    results.append(json.loads(out))
                self.assertEqual(sum(r.get('idempotent') is False for r in results), 1)
                self.assertEqual(m.read(root / 'journal.json')['phase'], 'ACTIVE')
                self.assertEqual(verify.inventory(root / 'canonical'), verify.inventory(root / 'source'))
            finally:
                self.root = original
                db.close()

    def test_21_pre_cutover_rollback(self):
        with self.assertRaises(RuntimeError):
            m.migrate(self.root, fault='backed-up')
        self.assertEqual(m.rollback(self.root)['status'], 'CANCELLED_BEFORE_CUTOVER')
        self.check_source_mapping()
        self.assertTrue((self.root / 'backup').exists())

    def test_22_no_new_writes_rollback(self):
        m.migrate(self.root)
        self.assertEqual(m.rollback(self.root)['status'], 'ROLLED_BACK_WITHOUT_NEW_WRITES')
        self.check_source_mapping()
        self.assertEqual(verify.inventory(self.root / 'source'), self.expected)

    def test_23_new_database_writes_rollback_refused(self):
        m.migrate(self.root)
        with sqlite3.connect(self.root / 'canonical/jarvis.sqlite3') as db:
            db.execute("INSERT INTO messages(conversation,role,content,created) VALUES('new','user','NEW TEST memory',4)")
        with self.assertRaisesRegex(ValueError, 'NEW_WRITES'):
            m.rollback(self.root)
        self.assertEqual(m.read(self.root / 'mapping.json')['active'], 'canonical')
        self.assertEqual(verify.database(self.root / 'canonical/jarvis.sqlite3')['tables']['messages']['rows'], 2)

    def test_24_new_artifact_writes_rollback_refused(self):
        m.migrate(self.root)
        (self.root / 'canonical/persistent/personality.txt').write_text('NEW TEST text')
        with self.assertRaisesRegex(ValueError, 'NEW_WRITES'):
            m.rollback(self.root)

    def test_25_stale_original_rollback_refused(self):
        m.migrate(self.root)
        self.db.execute("UPDATE messages SET content='TEST legacy writer'")
        self.db.commit()
        with self.assertRaisesRegex(ValueError, 'NEW_WRITES'):
            m.rollback(self.root)

    def test_26_crash_boundaries(self):
        for boundary in ('prepared', 'backup-copy', 'backed-up', 'verified', 'renamed', 'published', 'mapped'):
            with self.subTest(boundary=boundary):
                original = self.root
                root, db = fixtures.create()
                self.root = root
                try:
                    p = self.run_child('--fault', 'crash-' + boundary)
                    p.communicate(timeout=10)
                    self.assertEqual(p.returncode, 83)
                    with m.Lock(root):
                        pass  # OS lifetime lock released by process crash.
                    if boundary in ('verified', 'renamed', 'published', 'mapped'):
                        self.assertEqual(m.migrate(root, recover=True)['status'], 'ACTIVE_TEST_ONLY')
                    else:
                        with self.assertRaisesRegex(ValueError, 'RECOVERY_REQUIRED'):
                            m.migrate(root, recover=True)
                        self.assertEqual(m.rollback(root)['status'], 'CANCELLED_BEFORE_CUTOVER')
                    self.assertEqual(verify.inventory(root / 'source'), verify.inventory(root / 'canonical')
                                     if (root / 'canonical').exists() else verify.inventory(root / 'source'))
                finally:
                    self.root = original
                    db.close()

    def test_27_corrupt_journal(self):
        (self.root / 'journal.json').write_text('{')
        with self.assertRaises(ValueError):
            m.migrate(self.root, recover=True)
        self.check_source_mapping()

    def test_28_corrupt_reservation(self):
        self.db.execute('UPDATE project_budget_reservations SET used_core=999')
        self.db.commit()
        with self.assertRaisesRegex(ValueError, 'RESERVATION'):
            m.migrate(self.root)

    def test_29_stale_reservations_preserved_no_replay(self):
        m.migrate(self.root)
        self.assertEqual(verify.database(self.root / 'canonical/jarvis.sqlite3')['tables']['project_budget_reservations'],
                         self.expected['database']['tables']['project_budget_reservations'])
        self.assertIn('false', (self.root / 'canonical/persistent/recovery.json').read_text())

    def test_30_missing_source_no_empty_creation(self):
        self.db.close()
        path = self.root / 'source/jarvis.sqlite3'
        path.rename(path.with_suffix('.retained'))
        with self.assertRaises(sqlite3.OperationalError):
            m.migrate(self.root)
        self.assertFalse(path.exists())

    def test_31_unknown_artifact_class_refused(self):
        (self.root / 'source/unknown-record').write_text('TEST unknown')
        with self.assertRaisesRegex(ValueError, 'UNCLASSIFIED'):
            m.migrate(self.root)

    def test_32_postcrash_new_writes_refuse_recovery(self):
        p = self.run_child('--fault', 'crash-mapped')
        p.communicate(timeout=8)
        self.assertEqual(p.returncode, 83)
        with sqlite3.connect(self.root / 'canonical/jarvis.sqlite3') as db:
            db.execute("UPDATE messages SET content='TEST new after crash'")
        with self.assertRaisesRegex(ValueError, 'CONTENT'):
            m.migrate(self.root, recover=True)
        self.assertEqual(m.read(self.root / 'mapping.json')['active'], 'canonical')

    def test_33_destination_identity_tamper_recovery(self):
        with self.assertRaises(RuntimeError):
            m.migrate(self.root, fault='verified')
        m.write(self.root / 'staging/identity.json', {'data_id': 'TEST-wrong'})
        with self.assertRaisesRegex(ValueError, 'CONTENT'):
            m.migrate(self.root, recover=True)
        self.check_source_mapping()

    def test_34_mapping_identity_wrong(self):
        m.write(self.root / 'mapping.json', {'active': 'source', 'data_id': 'wrong'})
        with self.assertRaisesRegex(ValueError, 'MAPPING'):
            m.migrate(self.root)

    def test_35_schema_version_wrong(self):
        self.db.execute('PRAGMA user_version=2')
        self.db.commit()
        with self.assertRaisesRegex(ValueError, 'SCHEMA'):
            m.migrate(self.root)

    def test_36_nested_unclassified_secret_refused(self):
        (self.root / 'source/persistent/unapproved-secret.txt').write_text('TEST secret sentinel')
        with self.assertRaisesRegex(ValueError, 'UNCLASSIFIED'):
            m.migrate(self.root)
        self.assertFalse((self.root / 'backup').exists())

    def test_37_missing_artifact_refused(self):
        (self.root / 'source/persistent/repair-evidence.json').unlink()
        with self.assertRaisesRegex(ValueError, 'MISSING_ARTIFACT'):
            m.migrate(self.root)

    def test_38_budget_overspend_refused(self):
        self.db.execute('UPDATE project_budget_limits SET core_requests=0')
        self.db.commit()
        with self.assertRaisesRegex(ValueError, 'BUDGET_TOTAL'):
            m.migrate(self.root)

    def test_39_independent_direct_sql_and_bytes(self):
        # A second oracle: direct row/byte comparison, no verifier inventory or manifest.
        before = {name: self.db.execute('SELECT * FROM "' + name + '"').fetchall()
                  for (name,) in self.db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        artifacts = {p.name: p.read_bytes() for p in (self.root / 'source/persistent').iterdir()}
        m.migrate(self.root)
        dest = sqlite3.connect((self.root / 'canonical/jarvis.sqlite3').as_uri() + '?mode=ro', uri=True)
        try:
            self.assertEqual({n for (n,) in dest.execute("SELECT name FROM sqlite_master WHERE type='table'")}, set(before))
            for name, rows in before.items():
                self.assertEqual(sorted(map(repr, rows)), sorted(map(repr, dest.execute('SELECT * FROM "' + name + '"'))))
            self.assertEqual(dest.execute('PRAGMA integrity_check').fetchall(), [('ok',)])
        finally:
            dest.close()
        for name, content in artifacts.items():
            self.assertEqual((self.root / 'canonical/persistent' / name).read_bytes(), content)

    def test_40_disk_full_mid_backup_injected(self):
        with self.assertRaises(OSError) as error:
            m.migrate(self.root, fault='disk-full-backup')
        self.assertEqual(error.exception.errno, errno.ENOSPC)
        self.check_source_mapping()
        self.assertTrue((self.root / 'backup').exists())
        with self.assertRaisesRegex(ValueError, 'RECOVERY_REQUIRED'):
            m.migrate(self.root, recover=True)

    def test_41_migration_lock_handle_not_inherited(self):
        with m.Lock(self.root):
            child = subprocess.Popen([sys.executable, '-I', '-c', 'import time;time.sleep(2)'],
                                     close_fds=False, creationflags=0x08000000)
        try:
            self.assertIsNone(child.poll())
            with m.Lock(self.root):
                pass
        finally:
            child.terminate()
            child.wait(3)

    def test_42_source_changed_after_verified_refuses_resume(self):
        with self.assertRaises(RuntimeError):
            m.migrate(self.root, fault='verified')
        self.db.execute("UPDATE messages SET content='TEST new source'")
        self.db.commit()
        with self.assertRaisesRegex(ValueError, 'SOURCE_CHANGED'):
            m.migrate(self.root, recover=True)

    def test_43_rollback_concurrent_idempotent(self):
        m.migrate(self.root)
        children = [self.run_child('--rollback') for _ in range(4)]
        for child in children:
            out, _ = child.communicate(timeout=8)
            self.assertIn(json.loads(out)['status'], ('ROLLED_BACK_WITHOUT_NEW_WRITES', 'CANCELLED_BEFORE_CUTOVER', 'REFUSED'))
        self.check_source_mapping()
        self.assertEqual(verify.inventory(self.root / 'source'), self.expected)
        self.assertEqual(m.read(self.root / 'journal.json')['phase'], 'ROLLED_BACK_WITHOUT_NEW_WRITES')
        self.assertTrue(m.rollback(self.root)['idempotent'])


class Evidence(unittest.TextTestResult):
    def startTest(self, test):
        self.started = time.monotonic()
        super().startTest(test)

    def addSuccess(self, test):
        RECORDS.append({'case': test.id(), 'result': 'PASS', 'ms': round((time.monotonic()-self.started)*1000)})
        super().addSuccess(test)

    def addFailure(self, test, error):
        RECORDS.append({'case': test.id(), 'result': 'FAIL', 'reason': error[0].__name__})
        super().addFailure(test, error)

    def addError(self, test, error):
        RECORDS.append({'case': test.id(), 'result': 'ERROR', 'reason': error[0].__name__})
        super().addError(test, error)

    def addSubTest(self, test, subtest, error):
        RECORDS.append({'case': test.id(), 'variant': str(subtest.params), 'result': 'PASS' if error is None else 'FAIL'})
        super().addSubTest(test, subtest, error)


if __name__ == '__main__':
    start = time.monotonic()
    result = unittest.TextTestRunner(verbosity=2, resultclass=Evidence).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    path = m.BASE / ('run-' + uuid.uuid4().hex + '.json')
    m.write(path, {'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
                   'seconds': round(time.monotonic()-start, 3), 'records': RECORDS,
                   'production_access': False, 'scope': 'ISOLATED SYNTHETIC DATA ONLY'})
    print('EVIDENCE', path)
    sys.exit(not result.wasSuccessful())
