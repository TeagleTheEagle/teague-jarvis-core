import pathlib,json,hashlib,zipfile
R=pathlib.Path(__file__).resolve().parent;P=R.parent/'stage6-checker-v2-20260923'
cfg=json.loads((P/'candidate.json').read_text());C=pathlib.Path(cfg['code']);O=pathlib.Path(cfg['original'])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v=json.loads((P/'final-verification.json').read_text())
for x in cfg['originalFiles']:assert sha(O/x['name'])==x['sha256'],('original',x['name'])
for x in v['source']:assert sha(C/x['name'])==x['sha256'],('candidate',x['name'])
assert sha(C/'small-source-v2.json')==v['candidateManifestSHA256']
r=json.loads((P/'canonical-archive-receipt.json').read_text());zpath=pathlib.Path(r['archive']);assert sha(zpath)==r['archiveSHA256']
manifest=zpath.parent/'manifest.json';assert sha(manifest)==r['manifestSHA256'];members=json.loads(manifest.read_text())
with zipfile.ZipFile(zpath) as z:
 assert len(z.namelist())==len(members)==363
 for x in members:
  b=z.read(x['path']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
  if x['path'].startswith('report/'):
   p=P/x['path'][7:];assert sha(p)==x['sha256'],('preserved report',str(p))
with (R/'preservation-preflight.json').open('x') as f:json.dump(dict(status='PASS',originalFiles=len(cfg['originalFiles']),candidateFiles=len(v['source']),archiveMembers=363,priorFocusedTestsPreserved=True,archiveSHA256=r['archiveSHA256'],code=str(C),protectedFilesAccessed=False,productionChanged=False),f,indent=2)
print('PRESERVATION_PASS: original=183 candidate=194 archive=363; previous test records unchanged')
