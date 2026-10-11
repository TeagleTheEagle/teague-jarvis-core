"""Normal exclusive byte copy + independent destination SHA-256; synthetic roots only."""
import pathlib,json,hashlib,os,sys,time,uuid,shutil,datetime,traceback
R=pathlib.Path(__file__).parent;P=R.parent/'stage6-large-revalidation-20260920'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=read(P/'candidate.json');C=pathlib.Path(plan['code']);O=pathlib.Path(plan['collector']);H=pathlib.Path(plan['diagnostic']);S=O/'large-synthetic';T=C/'large-synthetic'
assert C==pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\e23d36c0a24246c996aa28e5d5561863\code')
assert S==pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\1c1f5d0c390b42cc9ba9f4f6221dabc6\code\large-synthetic')
sys.path.insert(0,str(C));from workspace import check_path,new_run
check_path(T);assert not T.exists()
for root,rows in ((C,plan['hashes']),(O,read(O/'baseline-source.json')),(H,read(H/'hardening-hashes.json'))):
 for x in rows:assert sha(root/x['name'])==x['sha256']
receipt=read(P/'archive-verification.json');A=pathlib.Path(receipt['path']);assert sha(A/'evidence.zip')==receipt['zipSHA256'] and sha(A/'archive-manifest.json')==receipt['manifestSHA256']
cal=read(O/'calibration.json');expected={x['path']:x for x in cal['passes'][0]['files']};assert expected.keys()=={x['path'] for x in cal['created']}
assert {x['path']:x['sha256'] for x in cal['passes'][0]['files']}=={x['path']:x['sha256'] for x in cal['passes'][1]['files']}
def inventory(root):
 for p in (root,*root.parents):
  assert not p.lstat().st_file_attributes&0x400
 rows={};dirs=[]
 for d,ds,fs in os.walk(root,followlinks=False):
  for n in ds+fs:
   p=pathlib.Path(d)/n;assert not p.lstat().st_file_attributes&0x400
  for n in ds:dirs.append((pathlib.Path(d)/n).relative_to(root).as_posix())
  for n in fs:
   p=pathlib.Path(d)/n;s=p.stat();assert s.st_nlink==1
   rows[p.relative_to(root).as_posix()]=dict(bytes=s.st_size,mtime_ns=s.st_mtime_ns,fileId=s.st_ino,volume=s.st_dev,attributes=s.st_file_attributes)
 return dict(files=dict(sorted(rows.items())),directories=sorted(dirs))
before=inventory(S);assert before['files'].keys()==expected.keys()
for x in cal['created']:assert before['files'][x['path']]['bytes']==x['bytes'] and before['files'][x['path']]['mtime_ns']==x['mtime_ns']
assert shutil.disk_usage(C).free>cal['totalBytes']+2**30
run=new_run('rehome-'+uuid.uuid4().hex)
def put(n,v):
 with (run/n).open('x') as f:json.dump(v,f,indent=2);f.flush();os.fsync(f.fileno())
identity=dict(source=str(S),workspace=str(C),destination=str(T),fileCount=len(expected),totalBytes=cal['totalBytes'],calibration=str(O/'calibration.json'),calibrationSHA256=sha(O/'calibration.json'),run=str(run),freeBytes=shutil.disk_usage(C).free)
with (R/'copy-plan.json').open('x') as f:json.dump(identity,f,indent=2)
put('source-before.json',before);put('plan.json',identity);print(json.dumps(identity),flush=True)
copied=[];verified=[];start=time.monotonic()
try:
 T.mkdir()
 for d in before['directories']:check_path(T/d).mkdir()
 for name,meta in before['files'].items():
  src=S/name;dst=check_path(T/name);h=hashlib.sha256();begin=time.monotonic();count=0;notice=begin
  with src.open('rb',buffering=0) as f,dst.open('xb',buffering=0) as out:
   st=os.fstat(f.fileno());assert st.st_ino==meta['fileId'] and st.st_size==meta['bytes'] and st.st_mtime_ns==meta['mtime_ns']
   while block:=f.read(4*2**20):
    h.update(block);assert out.write(block)==len(block);count+=len(block)
    if time.monotonic()-notice>20:print(json.dumps(dict(phase='COPY_AND_SOURCE_HASH',file=name,bytes=count,total=meta['bytes'])),flush=True);notice=time.monotonic()
   out.flush();os.fsync(out.fileno());end=os.fstat(f.fileno());assert (end.st_ino,end.st_size,end.st_mtime_ns)==(st.st_ino,st.st_size,st.st_mtime_ns)
  assert count==meta['bytes'] and h.hexdigest()==expected[name]['sha256']
  os.utime(dst,ns=(st.st_atime_ns,st.st_mtime_ns));ds=dst.stat();assert ds.st_nlink==1 and ds.st_mtime_ns==meta['mtime_ns'] and ds.st_size==meta['bytes']
  assert not ds.st_file_attributes&0x400 and (ds.st_file_attributes&0x4800)==(meta['attributes']&0x4800) # compression/encryption unchanged
  copied.append(dict(path=name,bytes=count,sha256=h.hexdigest(),seconds=time.monotonic()-begin));put('copied-'+str(len(copied))+'.json',copied[-1]);print('COPIED '+name,flush=True)
 # All destination bytes are independently re-read; no source hash is reused as proof.
 for name,meta in before['files'].items():
  p=check_path(T/name);h=hashlib.sha256();begin=time.monotonic();notice=begin;count=0
  with p.open('rb',buffering=0) as f:
   while block:=f.read(4*2**20):
    h.update(block);count+=len(block)
    if time.monotonic()-notice>20:print(json.dumps(dict(phase='DESTINATION_HASH',file=name,bytes=count,total=meta['bytes'])),flush=True);notice=time.monotonic()
  assert count==meta['bytes'] and h.hexdigest()==expected[name]['sha256']
  verified.append(dict(path=name,bytes=count,sha256=h.hexdigest(),seconds=time.monotonic()-begin));put('verified-'+str(len(verified))+'.json',verified[-1]);print('VERIFIED '+name,flush=True)
 after=inventory(S);new=inventory(T);assert after==before and new['directories']==before['directories'] and new['files'].keys()==before['files'].keys()
 for n,a in before['files'].items():
  b=new['files'][n];assert (a['bytes'],a['mtime_ns'])==(b['bytes'],b['mtime_ns']);assert (a['volume'],a['fileId'])!=(b['volume'],b['fileId'])
 for d in reversed(before['directories']):
  st=(S/d).stat();os.utime(T/d,ns=(st.st_atime_ns,st.st_mtime_ns))
 st=S.stat();os.utime(T,ns=(st.st_atime_ns,st.st_mtime_ns))
 put('source-after.json',after);put('destination-inventory.json',new)
 manifest=dict(synthetic=True,root=str(T),files=[dict(path=n,fullPath=str(T/n),bytes=x['bytes'],mtime_ns=x['mtime_ns'],LastWriteTimeUtc=datetime.datetime.fromtimestamp(x['mtime_ns']/1e9,datetime.timezone.utc).isoformat(),sha256=expected[n]['sha256']) for n,x in new['files'].items()],totalBytes=cal['totalBytes'],sourceEquality=True)
 put('dataset-manifest.json',manifest)
 result=dict(status='COPY_VERIFIED',**identity,copyAndSourceHash=copied,destinationHash=verified,sourceUnchanged=True,newFileIdentities=True,noReparse=True,manifestSHA256=sha(run/'dataset-manifest.json'),seconds=time.monotonic()-start)
 put('copy-result.json',result)
 with (R/'copy-result.json').open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps(dict(status=result['status'],run=str(run),seconds=result['seconds'],manifestSHA256=result['manifestSHA256'])),flush=True)
except BaseException:
 put('copy-failure.json',dict(error=traceback.format_exc(),copied=copied,verified=verified,seconds=time.monotonic()-start));raise
