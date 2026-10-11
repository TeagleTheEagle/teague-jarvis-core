"""Select and scan nonsecret review evidence; no runtime/data/credential archive."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
frozen=json.loads((OUT/'source-final.json').read_text())
paths={ROOT/x['path'] for x in frozen['source']}
paths.add(ROOT/'docs/CORE-COMPLETION-CHECKLIST.md')
paths.add(ROOT/'docs/deployment-contract-20260916/REVIEW.md')
paths.update(p for p in OUT.rglob('*') if p.is_file() and p.suffix in ('.md','.py','.ps1','.txt','.json','.log','.diff') and p.name not in ('archive-manifest.json','archive-receipt.json'))
regressions=json.loads((OUT/'regressions-1d930927d3984283bac10f8527a675e0.json').read_text())
for row in regressions:
    text=Path(row['log']).read_text(errors='replace')
    for line in text.splitlines():
        if line.startswith('EVIDENCE '):
            p=Path(line[9:].strip())
            if p.is_file() and p.suffix=='.json' and p.is_relative_to(ROOT):paths.add(p)
    if row['name']=='response-commit':paths.add(Path(json.loads(text)['evidence']))
special=[ROOT/'docs/lifecycle-stage5-evidence/integrated-2dc1a02126b1480db0d1b07fc1ffc4e2.json',ROOT/'docs/lifecycle-stage4-evidence/client-state-media-ce4907b46aae4827a8d698a18b074a5b.json']
paths.update(special)
for row in json.loads(special[1].read_text())['records']:
    if row['case']=='actual client screenshot captured':paths.add(Path(row['file']))
def scan_json(value):
    if isinstance(value,dict):
        for key,v in value.items():
            if key in ('server_key','owner_key','client_key','clientKey','serverKey','authorization','proof','token','key') and isinstance(v,str) and re.fullmatch('[a-fA-F0-9]{32,128}',v):
                raise ValueError('Secret-like field denied: '+key)
            scan_json(v)
    elif isinstance(value,list):
        for v in value:scan_json(v)
entries=[]
for path in sorted(paths):
    assert path.is_relative_to(ROOT) and not path.is_symlink()
    assert '.env' not in path.parts and path.suffix not in ('.dpapi','.sqlite3','.dll','.exe','.node','.zip')
    content=path.read_bytes()
    if path.suffix!='.png':
        text=content.decode('utf-8-sig')
        assert not re.search(r'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}',text),'API key-like value'
        assert not re.search(r'^-----BEGIN [A-Z ]*PRIVATE KEY-----',text,re.M),'Private key header'
        if path.suffix=='.json':scan_json(json.loads(text))
    entries.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(content).hexdigest(),bytes=len(content)))
manifest=dict(mode='NONSECRET_REVIEW_ARCHIVE',source_root=str(ROOT),files=entries,excluded=['all credentials/DPAPI records','all canonical/runtime databases','runtime binaries/packages','profiles','model files','unrelated working-tree files'])
(OUT/'archive-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
print(json.dumps(dict(files=len(entries),bytes=sum(x['bytes'] for x in entries),manifest=str(OUT/'archive-manifest.json'))))
