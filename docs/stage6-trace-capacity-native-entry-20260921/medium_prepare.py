import pathlib,json,hashlib,shutil,uuid
R=pathlib.Path(__file__).parent;B=R/'batched-candidate';p=json.loads((B/'plan.json').read_text());O=pathlib.Path(p['code']);sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest();rows=json.loads((B/'candidate-hashes.json').read_text())
for x in rows:assert sha(O/x['name'])==x['sha256']
C=pathlib.Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code';C.mkdir(parents=True)
for x in rows:shutil.copy2(O/x['name'],C/x['name'])
source=C/'small-sacrificial';source.mkdir()
for x in p['files']:shutil.copy2(pathlib.Path(p['source'])/x['name'],source/x['name'])
(C/'baseline-allowlist.json').write_text(json.dumps(dict(approvedProtectedRoots=[],realProtectedAccess=False,syntheticRoots=[str(source)]),indent=2))
limits=json.loads((C/'baseline-limits.json').read_text());limits.update(campaign=150,monitor=240,hold=90);(C/'baseline-limits.json').write_text(json.dumps(limits,indent=2))
file=C/'traced_launch.ps1';file.write_text(file.read_text().replace(str(O).replace('\\','\\\\'),str(C).replace('\\','\\\\')))
file=C/'integration_verify.py';s=file.read_text();needle='  if markers:\n';assert s.count(needle)==1
s=s.replace(needle,"  if k['image'].lower().endswith('python.exe'):assert markers,('Missing Python supplemental marker',n['pid'],n['created'])\n"+needle);file.write_text(s)
M=R/'medium-candidate';M.mkdir();(M/'plan.json').write_text(json.dumps(dict(p,code=str(C),source=str(source),limits=limits),indent=2))
hashes=[dict(name=x['name'],sha256=sha(C/x['name'])) for x in rows];(C/'run-source.json').write_text(json.dumps(hashes,indent=2));(M/'candidate-hashes.json').write_text(json.dumps(hashes,indent=2))
print(json.dumps(dict(code=str(C),limits=limits,hashes=len(hashes))))
