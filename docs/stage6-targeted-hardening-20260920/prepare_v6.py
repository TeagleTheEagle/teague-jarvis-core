import pathlib,json,hashlib,shutil,uuid
R=pathlib.Path(__file__).parent;old=json.loads((R/'candidate-v5.json').read_text());O=pathlib.Path(old['code'])
for x in old['hashes']:assert hashlib.sha256((O/x['name']).read_bytes()).hexdigest()==x['sha256']
D=pathlib.Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code';D.mkdir(parents=True)
for p in O.iterdir():
 if p.is_file() and p.name!='hardening-hashes.json':shutil.copyfile(p,D/p.name)
p=D/'lineage.py';s=p.read_text();s=s.replace("   if stamp<int(r['created']) or (upper is not None and stamp>=upper):continue","""   # A delayed notification does not itself prove which same-image incarnation
   # owns it. Never exclude an earlier incarnation just because another PID
   # incarnation existed before notification time. Multiple candidates UNKNOWN.
   if stamp<int(r['created']):continue""");p.write_text(s)
p=D/'test_hardening_scope.py';s=p.read_text();s=s.replace("self.assertEqual(set(v['bound']),{'a','b'})","self.assertEqual(set(v['bound']),{'a'});self.assertEqual(len(v['unknown']),1)")
p.write_text(s)
p=D/'test_hardening_boundary.py';s=p.read_text();s+='''
 def test_delayed_stop_cannot_transfer_to_reused_pid(self):
  a=row(7,10,20,'a');b=row(7,100,120,'b');e=ev(7,121,'stop',received=200)
  v=associate([a,b],[e],{'a','b'});self.assertFalse(v['bound']);self.assertEqual(len(v['unknown']),1)
 def test_delayed_start_cannot_transfer_to_reused_pid(self):
  a=row(7,10,20,'a');b=row(7,100,120,'b');e=ev(7,101,'start',received=200)
  v=associate([a,b],[e],{'a','b'});self.assertFalse(v['bound']);self.assertEqual(len(v['unknown']),1)
''';p.write_text(s)
manifest=[dict(name=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(D.iterdir()) if p.is_file()]
(D/'hardening-hashes.json').write_text(json.dumps([x for x in manifest if x['name'] not in old['generatedRegressionOutputs']],indent=2))
with (R/'candidate-v6.json').open('x') as f:json.dump(dict(code=str(D),previous=str(O),hashes=manifest,generatedRegressionOutputs=old['generatedRegressionOutputs'],correction='Conservative fail-closed handling of delayed notification spanning same-image PID reuse; monitor/sampler/probe code unchanged from combined v5 run.'),f,indent=2)
print(D)
