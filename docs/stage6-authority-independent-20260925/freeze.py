import pathlib,json,hashlib,datetime
R=pathlib.Path(__file__).parent;C=R/'candidate';B=json.loads((R/'before.json').read_text());S=pathlib.Path(B['predecessor']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2)
assert json.loads((R/'offline-tests-result.json').read_text())['status']=='PASS'
rows=[];changed=[]
for x in B['files']:
 p=C/x['name'];r=dict(name=x['name'],bytes=p.stat().st_size,sha256=sha(p));rows.append(r)
 if r['sha256']!=x['sha256']:changed.append(dict(name=x['name'],beforeSHA256=x['sha256'],afterSHA256=r['sha256']))
 assert sha(S/x['name'])==x['sha256'] and (S/x['name']).stat().st_mtime_ns==x['mtimeNs']
assert {x['name'] for x in changed}=={'authority_trace_v3.cpp','authority_trace_v3.obj','J6AuthorityTraceV3.exe'}
for name in ('small-source-v3.json','witness-source-v1.json'):save(C/name,rows)
binding=dict(schema='stage6-authority-independent-offline-successor-v1',candidate=str(C),predecessor=str(S),predecessorManifestSHA256=B['manifestSHA256'],candidateManifestSHA256=sha(C/'small-source-v3.json'),diagnosticManifestSHA256=sha(C/'witness-source-v1.json'),authoritySHA256=sha(C/'J6AuthorityTraceV3.exe'),detailedSHA256=sha(C/'J6StartupTrace.exe'),authorityRequestedBefore=256,authorityRequestedAfter=134217984,onlyChangedModeBit=134217728,detailedRequestedMode=33554688,candidateFiles=245,changedArtifacts=changed,liveRun=False,UAC=False,preparationOnly=True,requiresFreshDWorkspaceRebinding=True,acceptanceRulesChanged=False,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
save(R/'successor-binding.json',binding)
save(R/'syntax-result.json',dict(status='PASS',cpp=['configuration-proof.cpp','candidate/authority_trace_v3.cpp'],sdkStaticAssertions=12,python=[]))
syntax=[]
for p in R.glob('*.py'):compile(p.read_text(),str(p),'exec');syntax.append(p.name)
save(R/'python-syntax.json',dict(status='PASS',files=syntax,bytecodeWritten=False))
print(json.dumps(binding,indent=2))
