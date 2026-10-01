import json,subprocess,uuid,hashlib,time,sys
from pathlib import Path
R=Path(__file__).parent;C=Path(json.loads((R/'candidate.json').read_text())['code'])
campaign=C/('durability-'+uuid.uuid4().hex);campaign.mkdir();results=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,o):
 with p.open('x') as f:json.dump(o,f,indent=2)
def verify(root):
 m=json.loads((root/'durable-manifest.json').read_text());seal=json.loads((root/'durable-seal.json').read_text());assert seal['manifestSHA256']==sha(root/'durable-manifest.json')
 expected=1;count=0
 for i,s in enumerate(m['segments']):
  p=root/s['name'];assert s['number']==i and p.stat().st_size==s['bytes'] and sha(p)==s['sha256'];rows=[json.loads(x) for x in p.read_text().splitlines()]
  assert s['first']==expected and len(rows)==s['records'] and s['states']==[0,1,2,3,4]
  for row in rows:assert row['seq']==expected;expected+=1
  assert rows[-1]['seq']==s['last'];count+=len(rows)
 assert count==m['accepted']==seal['accepted'];return count
for fault in ([0] if sys.argv[1:] == ['normal'] else range(1,15)):
 root=campaign/('case-'+str(fault));root.mkdir();t=time.monotonic()
 p=subprocess.Popen([str(C/'J6DurableTest.exe'),str(root),str(fault),'12000'],cwd=C,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 try:out,err=p.communicate(timeout=15)
 except subprocess.TimeoutExpired:
  save(root/'blocked.json',dict(reason='process exceeded unchanged 15-second observation',pid=p.pid));raise
 save(root/'process.json',dict(pid=p.pid,exit=p.returncode,elapsed=time.monotonic()-t,stdout=out,stderr=err))
 try:
  stats=json.loads(out);v=stats['result'];assert v['threadsExited'] and v['remaining']==0
  assert v['peakPending']<=2 and v['peakPendingBytes']<=2*v['segmentBytes'] and v['peakQueueItems']<=65536
  if not fault:
   assert p.returncode==0 and v['fault']==0 and verify(root)==12000
   assert len(v['segments'])>2 and all(s['states']==[0,1,2,3,4,5] for s in v['segments'])
   assert v['progressedWhileFinalizing']>0
  else:
   assert p.returncode!=0 and v['fault']!=0 and not (root/'durable-seal.json').exists()
  results.append(dict(fault=fault,status='PASS',run=str(root),statistics=stats))
 except Exception as exc:
  results.append(dict(fault=fault,status='FAIL',run=str(root),error=repr(exc)));save(campaign/'results.json',results);raise
save(campaign/'results.json',results)
save(R/('durability-results-'+uuid.uuid4().hex+'.json'),dict(campaign=str(campaign),cases=results))
print(json.dumps(dict(campaign=str(campaign),passed=len(results))))
