import pathlib,json,hashlib,shutil,ast
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'plan.json').read_text())['code']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
shutil.copy2(R/'integration_verify.py',C/'integration_verify.py')
names={x['name'] for x in json.loads((R/'plan.json').read_text())['preChangeHashes']}|{'trace_sink.hpp','sink_test.cpp','trace_segments.py','native_bridge.py','traced_sampler_worker.py','owned_entry.cpp','J6OwnedEntry.dll','J6SinkTest.exe','python_marker_probe.py','integration_verify.py'}
for n in names:
 if n.endswith('.py'):ast.parse((C/n).read_text(),filename=n)
rows=[dict(name=n,sha256=sha(C/n)) for n in sorted(names)]
(C/'run-source.json').write_text(json.dumps(rows,indent=2));(R/'candidate-hashes.json').write_text(json.dumps(rows,indent=2))
assert shutil.disk_usage(C).free>137438953472+10*1024**3
print('Frozen artifacts',len(rows),'syntax PASS; storage headroom PASS')
