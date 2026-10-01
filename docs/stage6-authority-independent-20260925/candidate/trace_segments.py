"""Read-only validation of the complete bounded trace. No missing/tampered segment accepted."""
import json,hashlib,pathlib
def verify(root):
 root=pathlib.Path(root);manifest=json.loads((root/'startup-events.json').read_text());assert manifest['format']=='segmented-jsonl-v1'
 assert manifest['fault']==0 and manifest['accepted']==manifest['persisted']
 segments=manifest['segments'];assert len(segments)<=16384
 assert {p.name for p in root.glob('trace-*.jsonl')}=={x['name'] for x in segments}
 count=0;total=0;expectedNames=[f'trace-{i:05d}.jsonl' for i in range(len(segments))];assert [x['name'] for x in segments]==expectedNames
 for x in segments:
  p=root/x['name'];assert not p.is_symlink() and not p.is_junction()
  b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'];assert b.endswith(b'\n')
  rows=b.splitlines();assert len(rows)==x['records'];count+=len(rows);total+=len(b)
  for row in rows:assert isinstance(json.loads(row),dict)
 assert count==manifest['persisted'] and total==manifest['bytes'];assert count<=manifest['recordBudget'] and total<=manifest['storageBudgetBytes']
 return dict(records=count,bytes=total,segments=len(segments),fault=0)
