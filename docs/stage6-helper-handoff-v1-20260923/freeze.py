import pathlib,json,hashlib,shutil
R=pathlib.Path(__file__).parent;config=json.loads((R/'before.json').read_text());C=pathlib.Path(config['candidate']);P=pathlib.Path(config['predecessor'])
for n in ('test_handoff_v1.py',):shutil.copy2(R/n,C/n)
names={r['name'] for r in json.loads((P/'small-source-v3.json').read_text())}
names.update(['helper_handoff_v1.py','helper_handoff_v1.hpp','test_handoff_v1.py','native_handoff_fixture.cpp','J6HandoffFixture.exe','native_handoff_fixture.obj'])
rows=[]
for n in sorted(names):
 p=C/n;rows.append(dict(name=n,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(C/'small-source-v3.json').write_text(json.dumps(rows,indent=2))
print('FROZEN',len(rows))
