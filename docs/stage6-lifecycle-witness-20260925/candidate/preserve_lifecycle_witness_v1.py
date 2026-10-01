"""Post-quiescence NON-ACCEPTANCE archive, separate from frozen finalizers.

Only the four fixed sibling sidecars are eligible. Caller must first establish
observer exit and final cleanup; this module neither controls nor queries them.
Missing or malformed evidence remains incomplete, including on a failed run.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

SUFFIXES = ('authority-lifecycle-witness-v1.json', 'detailed-lifecycle-witness-v1.json',
            'authority-lifecycle-witness-export-failure-v1.json',
            'detailed-lifecycle-witness-export-failure-v1.json')

def plain(path):
    for p in (path, *path.parents):
        if p.exists() or p.is_symlink():
            s=p.lstat()
            if p.is_symlink() or getattr(s,'st_file_attributes',0)&0x400:
                raise ValueError('reparse path')

def preserve(run_root, archive, first_failure):
    run_root=Path(run_root).absolute();archive=Path(archive).absolute()
    if '..' in run_root.parts or '..' in archive.parts:
        raise ValueError('path traversal')
    plain(run_root);plain(archive)
    records=[];missing=[];data={}
    for suffix in SUFFIXES:
        p=run_root.with_name(run_root.name+'.'+suffix);plain(p)
        if not p.exists():
            missing.append(suffix);continue
        before=p.stat()
        if not p.is_file() or before.st_nlink!=1 or before.st_size>64*1024*1024:
            raise ValueError('nonregular/oversize sidecar')
        b=p.read_bytes();after=p.stat()
        if (before.st_size,before.st_mtime_ns,before.st_ino)!=(after.st_size,after.st_mtime_ns,after.st_ino) or len(b)!=before.st_size:
            raise ValueError('source mutation')
        data[suffix]=b
        records.append(dict(name=suffix,path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
    manifest=dict(schema='stage6-witness-preservation-v1',diagnosticOnly=True,acceptanceAuthority=False,
                  run=run_root.name,firstFailure=first_failure,files=records,missing=missing,
                  status='WITNESS_INCOMPLETE' if any(x in missing for x in SUFFIXES[:2]) or any(x in data for x in SUFFIXES[2:]) else 'DIAGNOSTIC_FILES_PRESERVED')
    encoded=json.dumps(manifest,sort_keys=True,indent=2).encode()
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        z.writestr('NON-ACCEPTANCE.txt','DIAGNOSTIC ONLY. This archive cannot accept a run or erase its first failure.')
        z.writestr('manifest.json',encoded)
        for name,b in data.items():z.writestr(name,b)
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None or z.read('manifest.json')!=encoded:raise ValueError('archive verification')
        for x in records:
            if hashlib.sha256(z.read(x['name'])).hexdigest()!=x['sha256']:raise ValueError('archive hash')
    for x in records:
        if hashlib.sha256(Path(x['path']).read_bytes()).hexdigest()!=x['sha256']:raise ValueError('source changed after archive')
    return dict(manifest,archive=str(archive),archiveSHA256=hashlib.sha256(archive.read_bytes()).hexdigest(),verifiedMembers=len(data)+2)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-root',required=True,type=Path);p.add_argument('--archive',required=True,type=Path);p.add_argument('--first-failure',required=True)
    a=p.parse_args();print(json.dumps(preserve(a.run_root,a.archive,a.first_failure),indent=2))
