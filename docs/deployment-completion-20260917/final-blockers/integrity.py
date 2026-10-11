"""Verify immutable TEST payload, preserve exact accepted app source, check TEST DBs."""
from pathlib import Path
import hashlib,json,sqlite3
D=Path(__file__).resolve().parent;R=D.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
candidate=json.loads((D/'candidate.json').read_text());P=Path(candidate['package']['package'])
assert sha(P/'manifest.json')==candidate['package']['sha256']
manifest=json.loads((P/'manifest.json').read_text());copied=[]
for x in manifest['files']:
    assert sha(P/x['path'])==x['sha256'],x['path']
    if x['path'].startswith('app/'):
        target=D/'accepted-app'/x['path'][4:];target.parent.mkdir(parents=True,exist_ok=True)
        data=(P/x['path']).read_bytes()
        if target.exists():assert target.read_bytes()==data
        else:target.write_bytes(data)
        copied.append({'path':str(target.relative_to(D)),'sha256':sha(target)})
(D/'accepted-package-manifest.json').write_bytes((P/'manifest.json').read_bytes())
old=json.loads((D.parent/'readiness-publication-fix/source-hashes.json').read_text());source=[]
for x in old:
    p=R/x['path'];digest=sha(p)
    assert x['path']=='tests/lifecycle_stage4/fixtures.py' or digest==x['sha256']
    source.append({'path':x['path'],'before':x['sha256'],'after':digest})
dbs=[]
for row in json.loads((D/'final-cleanup.json').read_text())['roots']:
    root=Path(row['root'])
    for p in root.rglob('*.sqlite3'):
        con=sqlite3.connect(p.as_uri()+'?mode=ro',uri=True)
        try:result=con.execute('PRAGMA integrity_check').fetchall()
        finally:con.close()
        assert result==[('ok',)],str(p)
        dbs.append({'path':str(p),'integrity':'ok','classification':'intentionally retained synthetic TEST evidence'})
out={'package_manifest_sha256':sha(P/'manifest.json'),'package_files_verified':len(manifest['files']),'accepted_source':copied,'correction_source':source,'synthetic_databases':dbs,'production':'No production path opened or modified by this collector.'}
(D/'final-integrity.json').write_text(json.dumps(out,indent=2))
print(json.dumps({'package_files':len(manifest['files']),'source_files':len(copied),'synthetic_databases':len(dbs),'integrity':'PASS'}))
