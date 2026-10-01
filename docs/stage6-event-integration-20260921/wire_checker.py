import pathlib,json,hashlib,difflib
from evidence_io import create_bytes,create_json
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'active-workspace.json').read_text())['code']);out=[]
for name in ('application_authority.py','process_instances.py'):create_bytes(C/name,(R/name).read_bytes())
def edit(name,transform):
 p=C/name;b=p.read_bytes();s=b.decode('utf-8-sig');a=transform(s).encode();assert b!=a
 create_bytes(R/(name+'.before'),b);p.write_bytes(a);create_bytes(R/(name+'.diff'),''.join(difflib.unified_diff(s.splitlines(True),a.decode().splitlines(True),fromfile='frozen/'+name,tofile=str(p))).encode());out.append(dict(name=name,before=hashlib.sha256(b).hexdigest(),after=hashlib.sha256(a).hexdigest()))
def checker(s):
 s=s.replace('from lineage import associate,parent_valid','from lineage import associate,parent_valid\nfrom application_authority import load_inputs,verify as verify_authority\nfrom process_instances import InstanceTable')
 s=s.replace("return dict(kernel=read('etw-result.json')","tap,events,receipts=load_inputs(root)\n mirrored=[json.loads(l) for l in (root/'app-events.jsonl').read_text(encoding='utf-8-sig').splitlines()]\n if events!=mirrored or receipts!=read('app-receipts.json'):raise ValueError('AUTHORITATIVE_MIRROR_MISMATCH')\n return dict(authoritative=verify_authority(root),kernel=read('etw-result.json')")
 s=s.replace("events=[json.loads(l) for l in (root/'app-events.jsonl').read_text(encoding='utf-8-sig').splitlines()],receipts=read('app-receipts.json'),tap=read('app-tap.json')","events=events,receipts=receipts,tap=tap")
 s=s.replace("association=associate(rows,events,scope)","association=associate(rows,events,scope)\n table=InstanceTable(rows,d['ready']['session'])\n enrichments=[table.correlate(e) for e in events if e['pid'] in pids]\n if any(e['result']!='UNIQUE_MATCH' for e in enrichments):fail('INDEPENDENT_EVENT_INSTANCE_IDENTITY_UNPROVEN')")
 s=s.replace("return dict(status='PASS' if not errors", "return dict(authoritative=d['authoritative'],identityEnrichment=enrichments,status='PASS' if not errors")
 return s
edit('cleanup_checker.py',checker)
def finalizer(s):
 s=s.replace("synthetic=contract['synthetic'],scenario=", "authoritativeApplication=result['authoritative'],identityEnrichment=result['identityEnrichment'],synthetic=contract['synthetic'],scenario=")
 return s
edit('baseline_finalize.py',finalizer)
create_json(R/'integration-changes-step2.json',out)
print(json.dumps(out))
