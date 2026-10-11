import pathlib,json,hashlib,subprocess,time,ctypes,ctypes.wintypes as w,shutil
R=pathlib.Path(__file__).parent;P=json.loads((R/'plan.json').read_text());C=pathlib.Path(P['code']);T=pathlib.Path(P['root'])/'capacity';T.mkdir()
checks=[];runs=[]
def record():
 (R/'stream-tests.json').write_text(json.dumps(dict(checks=checks,runs=runs,scope='Standalone synthetic capacity only; not integrated application acceptance'),indent=2))
def ck(n,v):
 checks.append(dict(name=n,pass_=bool(v)));record();assert v,n
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def verify(root):
 m=read(root/'manifest.json');assert m['fault']==0;assert m['attempted']==m['accepted']==m['persisted'];seq=0;total=0
 assert len(m['segments'])<=16384
 assert [s['name'] for s in m['segments']]==[f'trace-{i:05d}.jsonl' for i in range(len(m['segments']))]
 assert {p.name for p in root.glob('trace-*.jsonl')}=={s['name'] for s in m['segments']}
 for s in m['segments']:
  p=root/s['name'];assert not p.is_symlink() and not p.is_junction();b=p.read_bytes();assert len(b)==s['bytes']<=8388608 and sha(p)==s['sha256'];assert b.endswith(b'\n')
  lines=b.splitlines();assert len(lines)==s['records'];assert s['firstSequence']==seq+1
  for line in lines:
   row=json.loads(line);seq+=1;assert row['seq']==seq
  assert s['lastSequence']==seq;total+=len(b)
 assert seq==m['persisted']<=m['recordBudget'];assert total==m['bytes']<=m['storageBudgetBytes'];return dict(records=seq,bytes=total,segments=len(m['segments']),sequenceGaps=0)
def rejects(root):
 try:verify(root)
 except (AssertionError,ValueError,OSError):return True
 return False
K=ctypes.WinDLL('kernel32',use_last_error=True);K.GetProcessTimes.argtypes=[w.HANDLE]+[ctypes.POINTER(w.FILETIME)]*4;K.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD]
def run(name,count,rate=0,fault=0,memory=67108864,limit=1000000,byteCap=1073741824,good=True):
 root=T/name;root.mkdir();exe=C/'J6StreamBench.exe';args=[str(exe),str(root),str(count),str(rate),str(fault),str(memory),str(limit),str(byteCap)]
 p=subprocess.Popen(args,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);times=[w.FILETIME() for _ in range(4)]
 assert K.GetProcessTimes(int(p._handle),*(ctypes.byref(t) for t in times));created=(times[0].dwHighDateTime<<32)|times[0].dwLowDateTime
 try:exit_=p.wait(timeout=13.6)
 except subprocess.TimeoutExpired:
  runs.append(dict(name=name,pid=p.pid,created=str(created),error='UNCHANGED_13_6_SECOND_LIMIT',args=args));record();raise
 signaled=K.WaitForSingleObject(int(p._handle),0)==0;p._handle.Close()
 data=read(root/'bench.json');m=read(root/'manifest.json');runs.append(dict(name=name,path=str(root),pid=p.pid,created=str(created),exeSHA256=sha(exe),args=args,exit=exit_,handleSignaled=signaled,handleClosed=True,bench=data,manifest=m));record()
 ck(name+' lifecycle exit',signaled);ck(name+' result',(exit_==0)==good and (m['fault']==0)==good)
 if good:
  v=verify(root);ck(name+' continuity',v['records']==count and v['sequenceGaps']==0);ck(name+' authoritative accepted/attempted',m['accepted']==m['attempted']==count)
 else:ck(name+' fail closed',rejects(root))
 return root,data,m
root,b,m=run('high-rate',625000,125000)
ck('sustained input rate at least measured peak',b['recordsPerSecond']>=97212)
ck('multiple segments at high rate',len(m['segments'])>2)
ck('bounded view truncates explicitly',b['viewRows']==20000 and b['viewTruncated']==605000 and not b['viewAuthoritative'])
ck('view does not limit authoritative records',m['persisted']==625000)
base,_,_=run('small-complete',25000,100000)
run('slow-writer-overflow',100000,0,4,65536,good=False)
run('output-failure',1000,0,1,good=False)
run('simulated-disk-full',1000,0,2,good=False)
run('segment-create-failure',1000,0,3,good=False)
run('segment-hash-failure',1000,0,5,good=False)
run('record-boundary',1000,0,0,limit=1000)
run('record-overflow',1001,0,0,limit=1000,good=False)
run('byte-budget',1000,0,0,byteCap=2000,good=False)
for name in ('missing','corrupt','seq-gap','seq-duplicate','seq-reorder','partial','omitted-manifest','duplicate-manifest'):
 root=T/name;shutil.copytree(base,root);m=read(root/'manifest.json');p=root/m['segments'][0]['name']
 if name=='missing':p.rename(root/'missing.evidence')
 elif name=='corrupt':p.write_bytes(p.read_bytes()+b'X')
 elif name=='omitted-manifest':m['segments'].pop()
 elif name=='duplicate-manifest':m['segments'][1]=m['segments'][0]
 else:
  lines=p.read_bytes().splitlines(keepends=True)
  if name=='seq-gap':lines[2]=lines[2].replace(b'"seq":3,',b'"seq":4,')
  elif name=='seq-duplicate':lines[2]=lines[2].replace(b'"seq":3,',b'"seq":2,')
  elif name=='seq-reorder':lines[2],lines[3]=lines[3],lines[2]
  elif name=='partial':lines[-1]=lines[-1][:-4]
  p.write_bytes(b''.join(lines));m['bytes']+=p.stat().st_size-m['segments'][0]['bytes'];m['segments'][0].update(bytes=p.stat().st_size,sha256=sha(p))
 (root/'manifest.json').write_text(json.dumps(m));ck(name+' rejected',rejects(root))
print(json.dumps(dict(checks=len(checks),passes=sum(x['pass_'] for x in checks),highRate=runs[0]['bench'],path=str(T))))
