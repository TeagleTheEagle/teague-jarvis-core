from contextlib import closing
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
import zipfile
from unittest.mock import patch
import recovery


class RecoveryTests(unittest.TestCase):
    def test_wearable_sources_and_phone_restore_without_secrets_or_builds(self):
        names=['wearables/contracts.py','wearables/mock_device.py','phone/phone.html','docs/glasses/SETUP.md']
        excluded=['wearables/.env.local','wearables/build/generated.py','phone/private.key','wearables/cache.bin']
        for name in names+excluded:
            path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('fixture')
        backup=self.manager.create();manifest=recovery.verify(self.manager.archive(backup['id']))
        for name in names:self.assertIn('app/'+name,manifest['files'])
        for name in excluded:self.assertNotIn('app/'+name,manifest['files'])
        self.assertEqual(self.manager.rehearse(backup['id'])['status'],'restore_rehearsal_passed')

    def test_verification_uses_backup_folder_not_environment_temp(self):
        backup=self.manager.create()
        real=recovery.tempfile.TemporaryDirectory
        def local_only(*args,**kwargs):
            self.assertEqual(Path(kwargs['dir']),self.manager.folder)
            return real(*args,**kwargs)
        with patch('recovery.tempfile.TemporaryDirectory',side_effect=local_only):
            self.assertEqual(self.manager.rehearse(backup['id'])['status'],'restore_rehearsal_passed')

    def test_permission_error_identifies_recovery_stage(self):
        with patch('recovery.verify',side_effect=PermissionError(13,'private path')):
            with self.assertRaises(PermissionError) as caught:self.manager.rehearse('a'*32)
        self.assertEqual(caught.exception.recovery_stage,'verify archive and database snapshot')

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name)
        self.root=self.base/'jarvis';self.data=self.root/'data';self.data.mkdir(parents=True)
        (self.root/'static').mkdir();(self.root/'desktop').mkdir()
        (self.root/'server.py').write_text('print("never execute backups")')
        (self.root/'.env').write_text('secret-placeholder')
        (self.root/'static/app.js').write_text('app code')
        for name in ['generated','inspection-archive','development','update-history','speech-models']:
            (self.data/name).mkdir();(self.data/name/'saved.txt').write_text(name)
        with closing(sqlite3.connect(self.data/'jarvis.sqlite3')) as db:
            db.execute('PRAGMA journal_mode=WAL');db.execute('CREATE TABLE messages(text)');db.execute("INSERT INTO messages VALUES ('saved conversation')");db.commit()
        self.manager=recovery.Recovery(self.root,self.data)

    def tearDown(self):self.temp.cleanup()

    def test_complete_backup_and_recovery_preserve_live_data(self):
        result=self.manager.create();archive=self.manager.archive(result['id'])
        manifest=recovery.verify(archive)
        self.assertNotIn('app/.env',manifest['files'])
        self.assertFalse(any('speech-models' in p for p in manifest['files']))
        for name in ['generated','inspection-archive','development','update-history']:
            self.assertIn('data/'+name+'/saved.txt',manifest['files'])
        live=recovery.digest(self.data/'jarvis.sqlite3')
        self.assertEqual(self.manager.rehearse(result['id'])['status'],'restore_rehearsal_passed')
        copied=self.manager.restore_copy(result['id']);destination=Path(copied['path'])
        self.assertEqual(recovery.check_database(destination/'data/jarvis.sqlite3'),{'messages':1})
        self.assertTrue((destination/'server.py').exists());self.assertFalse((destination/'.env').exists())
        self.assertEqual(recovery.digest(self.data/'jarvis.sqlite3'),live)
        with self.assertRaises(ValueError):self.manager.restore_copy(result['id'])

    def test_committed_wal_is_included(self):
        db=sqlite3.connect(self.data/'jarvis.sqlite3')
        try:
            db.execute("INSERT INTO messages VALUES ('WAL content')");db.commit()
            self.assertEqual(self.manager.create()['database_counts']['messages'],2)
        finally:db.close()

    def test_tampered_archive_never_restores(self):
        result=self.manager.create();path=self.manager.archive(result['id'])
        with zipfile.ZipFile(path) as z:contents={n:z.read(n) for n in z.namelist()}
        contents['app/server.py']=b'tampered'
        with zipfile.ZipFile(path,'w') as z:
            for n,v in contents.items():z.writestr(n,v)
        with self.assertRaises(ValueError):self.manager.restore_copy(result['id'])
        self.assertFalse((self.manager.folder/('recovered-'+result['id'])).exists())

    def test_unsafe_names_and_ids(self):
        for name in ['../outside','app/../../outside','app/C:/file','app/CON.txt','app/a//b','app/a\\b','data/x.']:
            with self.subTest(name=name),self.assertRaises(ValueError):recovery.safe_name(name)
        for ident in ['../x','C:/x','']:
            with self.assertRaises(ValueError):self.manager.archive(ident)

    def test_failure_does_not_publish_partial_backup(self):
        with patch('recovery.verify',side_effect=ValueError('simulated corrupt copy')):
            with self.assertRaises(ValueError):self.manager.create()
        self.assertEqual(self.manager.listing()['backups'],[])
        self.assertTrue((self.data/'jarvis.sqlite3').exists())

    def test_default_backup_folder_is_never_inside_program_files(self):
        self.assertEqual(recovery.default_folder(self.root,self.data),(self.base/'jarvis-backups').resolve())  # development: beside the app
        home=self.base/'home';app=home/'releases'/'1.0.0-abc'/'app'
        self.assertEqual(recovery.default_folder(app,home/'data'),(home/'data-backups').resolve())  # installed: beside the data

    def test_installed_release_backs_up_the_owner_configuration_not_the_shipped_defaults(self):
        (self.root/'personality.txt').write_text('shipped default')
        selected,_=recovery.inventory(self.root,self.data)
        self.assertEqual(selected['app/personality.txt'],self.root/'personality.txt')  # development: beside the code
        home=self.base/'home';app=home/'releases'/'1.0.0-abc'/'app';(home/'config').mkdir(parents=True)
        shutil.copytree(self.root,app);(app.parent/'manifest.json').write_text('{"product":"JARVIS"}')  # an installed release's layout
        (home/'config'/'personality.txt').write_text('owner personality');(home/'config'/'preferences.json').write_text('{"owner":true}')
        selected,_=recovery.inventory(app,self.data)
        self.assertEqual(selected['app/personality.txt'],home/'config'/'personality.txt')
        self.assertEqual(selected['app/desktop/preferences.json'],home/'config'/'preferences.json')
        backup=recovery.Recovery(app,self.data,home/'data-backups').create()
        with zipfile.ZipFile(home/'data-backups'/(backup['id']+'.zip')) as z:
            self.assertEqual(z.read('app/personality.txt'),b'owner personality')

    def test_backup_works_while_a_core_runs_and_never_saves_its_state_logs_or_session_token(self):
        import core_lock
        (self.data/'logs').mkdir();(self.data/'logs'/'core.log').write_text('log lines')
        (self.data/'.jarvis-session.json').write_text('{"token":"not-a-real-secret"}')
        (self.data/core_lock.CONNECTION_NAME).write_text('{"origin":"http://127.0.0.1:1","token":"not-a-real-secret"}')
        held=core_lock.CoreLock(self.data)  # a running Core holds the lock file open
        try: result=self.manager.create()
        finally: held.release()
        manifest=recovery.verify(self.manager.archive(result['id']))
        for name in ('data/logs/core.log','data/.jarvis-session.json','data/'+core_lock.CONNECTION_NAME,'data/'+core_lock.LOCK_NAME,'data/'+core_lock.OWNER_NAME):
            self.assertNotIn(name,manifest['files'])
        self.assertIn('logs',manifest['excluded_cache_folders'])
        self.assertIn('data/jarvis.sqlite3',manifest['files'])

    def test_concurrent_operation_rejected(self):
        recovery.LOCK.acquire()
        try:
            with self.assertRaises(ValueError):self.manager.create()
        finally:recovery.LOCK.release()


if __name__=='__main__':unittest.main()
