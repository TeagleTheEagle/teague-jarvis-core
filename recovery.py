"""Local, verified backups and non-destructive restore rehearsals. Never run archives."""
from contextlib import closing
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sqlite3
import stat
import tempfile
import threading
import time
import uuid
import zipfile

LOCK = threading.Lock()
MAX_BYTES = 2 * 1024**3
MAX_FILES = 20000
EXCLUSIONS = ['API credentials (.env); keep/reconfigure separately', 'Python/Node runtimes and installed dependencies; reinstall from requirements/lockfile', 'Downloaded speech/wake model caches; recreate with setup scripts', 'Temporary captures, logs and review/test artifacts outside saved data', 'Windows shortcuts and Electron/browser cache; recreate on recovery']


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()


def publish_backup(source,destination):
    # TemporaryDirectory is owner-only on Windows. Moving its ZIP preserves
    # that ACL, preventing the desktop user from reading sandbox-made backups.
    # Create a NEW sibling file with the backup folder's inherited permissions.
    pending=destination.with_name(destination.name+'.publishing-'+uuid.uuid4().hex)
    try:
        with source.open('rb') as src,pending.open('xb') as dst:
            shutil.copyfileobj(src,dst)
        verify(pending)
        pending.rename(destination)
    finally:
        if pending.exists():pending.unlink()


def default_folder(root, data):
    """Backups live beside the app in development and beside the data folder in an installed
    release (docs/RELEASE-DESIGN.md), never inside the release's program files."""
    root, data = Path(root).resolve(), Path(data).resolve()
    return root.parent/'jarvis-backups' if data == root/'data' else data.parent/(data.name+'-backups')


def safe_name(name):
    p = PurePosixPath(name)
    if not name or '\x00' in name or '\\' in name or ':' in name or p.is_absolute() or p.as_posix()!=name or any(x in ('..','.') or x.endswith((' ','.')) for x in name.split('/')):
        raise ValueError('Unsafe archive path.')
    if any(re.fullmatch(r'(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?',x,re.I) for x in p.parts):
        raise ValueError('Reserved archive path.')
    if p.parts[0] not in ('app','data'): raise ValueError('Unexpected archive root.')
    return p


def tree_files(folder):
    if not folder.exists(): return
    for base, dirs, files in os.walk(folder, followlinks=False):
        for name in dirs + files:
            p=Path(base)/name
            if p.is_symlink() or (hasattr(p,'is_junction') and p.is_junction()):
                raise ValueError('Backup refuses linked files/directories.')
        dirs[:] = [d for d in dirs if d not in ('node_modules','.venv','__pycache__','.git')]
        for name in files:
            p=Path(base)/name
            if not name.startswith('.env') and p.suffix not in ('.pyc',): yield p


def owner_config(root):
    """The owner's personality and desktop preferences when they live outside the program
    (installed release, config folder). In development they are already under root."""
    import runtime_paths
    config=runtime_paths.config_dir()
    if not runtime_paths.installed() or config.resolve()==Path(root).resolve(): return {}
    files=(('app/personality.txt','personality.txt'),('app/desktop/preferences.json','preferences.json'))
    return {name:config/file for name,file in files if (config/file).is_file()}


def inventory(root, data):
    selected={}
    for p in root.iterdir():
        if p.is_file() and (p.suffix in ('.py','.md','.ps1','.cmd','.cjs') or p.name in ('requirements.txt','requirements-local-voice.txt','requirements-wearables.txt','personality.txt','release-notes.json')):
            if p.is_symlink(): raise ValueError('Linked source file.')
            selected['app/'+p.name]=p
    for folder in ('static','desktop','phone','wearables','docs/glasses'):
        for p in tree_files(root/folder):
            if folder in ('phone','wearables','docs/glasses'):
                if any(part in ('build','dist','release') for part in p.relative_to(root/folder).parts): continue
                if p.suffix not in ('.py','.md','.js','.css','.html'): continue
            if folder=='desktop' and p.name not in ('package.json','pnpm-lock.yaml','preferences.json','tray.png') and p.suffix not in ('.cjs','.js','.css','.html','.md'): continue
            selected['app/'+p.relative_to(root).as_posix()]=p
    for name,source in owner_config(root).items():  # the owner's copies replace the shipped defaults
        if source.is_symlink(): raise ValueError('Linked configuration file.')
        selected[name]=source
    excluded=[]
    for p in data.iterdir():
        if p.name in ('jarvis.sqlite3','jarvis.sqlite3-wal','jarvis.sqlite3-shm'): continue
        if p.name in ('speech-models','wake-models'):
            excluded.append(p.name);continue
        if p.is_symlink() or (hasattr(p,'is_junction') and p.is_junction()): raise ValueError('Linked data path.')
        paths=tree_files(p) if p.is_dir() else [p]
        for entry in paths:
            if entry.name.startswith('.env'): raise ValueError('Unexpected credential file in saved data.')
            selected['data/'+entry.relative_to(data).as_posix()]=entry
    return selected,excluded


def check_database(path):
    with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as db:
        db.execute('PRAGMA trusted_schema=OFF')
        if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok': raise ValueError('Database integrity failed.')
        tables=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        counts={name:db.execute('SELECT COUNT(*) FROM "'+name.replace('"','""')+'"').fetchone()[0] for name in tables}
    return counts


def verify(archive):
    with zipfile.ZipFile(archive) as z:
        infos=z.infolist()
        names=[i.filename for i in infos]
        if len(infos)>MAX_FILES or len(set(n.lower() for n in names))!=len(names) or sum(i.file_size for i in infos)>MAX_BYTES: raise ValueError('Archive limits or duplicate paths.')
        if 'manifest.json' not in names or z.getinfo('manifest.json').file_size>8*1024**2: raise ValueError('Missing/oversized manifest.')
        manifest=json.loads(z.read('manifest.json'))
        if manifest.get('format')!=1 or set(names)!=set(manifest.get('files',{}))|{'manifest.json'}: raise ValueError('Manifest does not match archive.')
        if 'data/jarvis.sqlite3' not in names: raise ValueError('Missing database snapshot.')
        for info in infos:
            if info.filename=='manifest.json': continue
            safe_name(info.filename)
            if stat.S_ISLNK(info.external_attr>>16) or info.is_dir(): raise ValueError('Links and directory entries are not supported.')
            h=hashlib.sha256()
            with z.open(info) as f:
                for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
            expected=manifest['files'][info.filename]
            if h.hexdigest()!=expected['sha256'] or info.file_size!=expected['bytes']:raise ValueError('Backup checksum mismatch.')
        with tempfile.TemporaryDirectory(prefix='jarvis-db-check-',dir=Path(archive).parent) as temp:
            dbpath=Path(temp)/'snapshot.sqlite3'
            with z.open('data/jarvis.sqlite3') as src,dbpath.open('wb') as dest:shutil.copyfileobj(src,dest)
            counts=check_database(dbpath)
            if counts!=manifest['database_counts']:raise ValueError('Database counts mismatch.')
    return manifest


class Recovery:
    def __init__(self,root,data,folder=None):
        self.root,self.data=Path(root).resolve(),Path(data).resolve()
        self.folder=Path(folder).resolve() if folder else self.root.parent/'jarvis-backups'
        if self.folder.is_relative_to(self.data) or self.root.is_relative_to(self.folder):raise ValueError('Backup location must be separate from application/data.')
        self.folder.mkdir(parents=True,exist_ok=True)

    def archive(self,ident):
        if not isinstance(ident,str) or not re.fullmatch(r'[a-f0-9]{32}',ident):raise ValueError('Invalid backup ID.')
        p=self.folder/(ident+'.zip')
        if p.is_symlink():raise ValueError('Linked backup refused.')
        return p

    def listing(self):
        rows=[]
        for p in sorted(self.folder.glob('*.zip'),key=lambda p:p.stat().st_mtime,reverse=True):
            if re.fullmatch(r'[a-f0-9]{32}',p.stem) and not p.is_symlink():rows.append({'id':p.stem,'created':p.stat().st_mtime,'bytes':p.stat().st_size})
        return {'backups':rows[:100],'location':str(self.folder),'exclusions':EXCLUSIONS,'privacy':'Local unencrypted backups contain saved personal data. No upload occurs.'}

    def create(self):
        if not LOCK.acquire(False):raise ValueError('A recovery operation is already running.')
        ident=uuid.uuid4().hex
        try:
            with tempfile.TemporaryDirectory(prefix='.building-',dir=self.folder) as temp:
                temp=Path(temp);dbpath=temp/'jarvis.sqlite3'
                # A separate write reservation blocks SQLite mutations while the read
                # connection makes its snapshot. No write is made to the live database.
                gate=sqlite3.connect(self.data/'jarvis.sqlite3',timeout=2)
                try:
                    gate.execute('BEGIN IMMEDIATE')
                    selected,excluded=inventory(self.root,self.data)
                    before={name:digest(p) for name,p in selected.items()}
                    with closing(sqlite3.connect((self.data/'jarvis.sqlite3').as_uri()+'?mode=ro',uri=True)) as source,closing(sqlite3.connect(dbpath)) as target:
                        deadline=time.monotonic()+20
                        def progress(*_):
                            if time.monotonic()>deadline:raise ValueError('Backup snapshot timed out.')
                        source.backup(target,pages=256,progress=progress)
                    selected['data/jarvis.sqlite3']=dbpath
                    if len(selected)>MAX_FILES-1 or sum(p.stat().st_size for p in selected.values())>MAX_BYTES:raise ValueError('Backup exceeds size limit.')
                    manifest={'format':1,'id':ident,'created_at':time.time(),'exclusions':EXCLUSIONS,'excluded_cache_folders':excluded,'files':{},'database_counts':check_database(dbpath)}
                    pending=temp/'backup.zip'
                    with zipfile.ZipFile(pending,'w',zipfile.ZIP_DEFLATED) as z:
                        for name,p in selected.items():
                            safe_name(name);z.write(p,name)
                            manifest['files'][name]={'sha256':digest(p),'bytes':p.stat().st_size}
                        current,_=inventory(self.root,self.data)
                        if set(current)!=set(before) or any(digest(p)!=before[name] for name,p in current.items()):raise ValueError('Files changed during backup. Retry when idle.')
                        if any(manifest['files'][n]['sha256']!=h for n,h in before.items()):raise ValueError('Files changed during backup.')
                        z.writestr('manifest.json',json.dumps(manifest,indent=2))
                finally:
                    gate.rollback();gate.close()
                verify(pending)
                publish_backup(pending,self.archive(ident))
            return {'status':'backup_verified','id':ident,'files':len(manifest['files']),'bytes':self.archive(ident).stat().st_size,'database_counts':manifest['database_counts'],'exclusions':EXCLUSIONS}
        finally:LOCK.release()

    def rehearse(self,ident):
        if not LOCK.acquire(False):raise ValueError('A recovery operation is already running.')
        stage='verify archive and database snapshot'
        try:
            archive=self.archive(ident);manifest=verify(archive)
            stage='create temporary restore folder'
            with tempfile.TemporaryDirectory(prefix='.restore-test-',dir=self.folder) as temp:
                target=Path(temp)
                stage='extract and check saved files'
                with zipfile.ZipFile(archive) as z:
                    for name in manifest['files']:
                        p=target.joinpath(*safe_name(name).parts);p.parent.mkdir(parents=True,exist_ok=True)
                        with z.open(name) as src,p.open('xb') as out:shutil.copyfileobj(src,out)
                        if digest(p)!=manifest['files'][name]['sha256']:raise ValueError('Restored file mismatch.')
                stage='check restored database'
                counts=check_database(target/'data/jarvis.sqlite3')
                if counts!=manifest['database_counts']:raise ValueError('Restored database mismatch.')
                stage='remove temporary restore folder'
            result={'status':'restore_rehearsal_passed','id':ident,'checked_at':time.time(),'files':len(manifest['files']),'database_counts':counts,'scope':'Extracted and hash-checked every saved file in a disposable folder; SQLite integrity and table counts match. Live app untouched. Restored code was not executed; dependencies, credentials and hardware not tested.'}
            stage='save restore-test receipt'
            receipt=self.folder/(ident+'.restore-check.json');receipt.write_text(json.dumps(result,indent=2),encoding='utf-8')
            return result
        except OSError as exc:
            exc.recovery_stage=stage
            raise
        finally:LOCK.release()

    def restore_copy(self,ident):
        """Recover into a NEW directory. No live replacement or execution."""
        if not LOCK.acquire(False):raise ValueError('A recovery operation is already running.')
        try:
            archive=self.archive(ident);manifest=verify(archive)
            destination=self.folder/('recovered-'+ident)
            if destination.exists():raise ValueError('Recovered directory already exists; it will not be overwritten.')
            with tempfile.TemporaryDirectory(prefix='.restore-copy-',dir=self.folder) as temp:
                stage=Path(temp)/'jarvis';stage.mkdir()
                with zipfile.ZipFile(archive) as z:
                    for name,entry in manifest['files'].items():
                        parts=safe_name(name).parts
                        p=stage.joinpath(*(parts[1:] if parts[0]=='app' else parts))
                        p.parent.mkdir(parents=True,exist_ok=True)
                        with z.open(name) as src,p.open('xb') as out:shutil.copyfileobj(src,out)
                        if digest(p)!=entry['sha256']:raise ValueError('Restored file mismatch.')
                if check_database(stage/'data/jarvis.sqlite3')!=manifest['database_counts']:raise ValueError('Database mismatch.')
                stage.rename(destination)
            return {'status':'restored_to_separate_folder','path':str(destination),'id':ident,'scope':'Saved files restored and verified. Nothing launched. Reinstall dependencies and configure credentials before using this copy. Original app unchanged.'}
        finally:LOCK.release()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['create','list','verify','rehearse','restore'])
    parser.add_argument('--id');parser.add_argument('--root',default=str(Path(__file__).parent))
    parser.add_argument('--data',help='saved-data folder (default: the installed data folder, else <root>/data)')
    args=parser.parse_args();root=Path(args.root).resolve()
    import runtime_paths
    data=Path(args.data).resolve() if args.data else (runtime_paths.data_dir() if runtime_paths.installed() else root/'data')
    recovery=Recovery(root,data,default_folder(root,data))
    if args.action=='create':result=recovery.create()
    elif args.action=='list':result=recovery.listing()
    elif args.action=='rehearse':result=recovery.rehearse(args.id)
    elif args.action=='restore':result=recovery.restore_copy(args.id)
    else:
        m=verify(recovery.archive(args.id));result={'status':'backup_verified','id':m['id'],'files':len(m['files'])}
    print(json.dumps(result,indent=2))
