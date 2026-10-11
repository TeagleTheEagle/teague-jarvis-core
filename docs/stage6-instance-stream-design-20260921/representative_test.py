import pathlib,json,hashlib,subprocess,ctypes as c,ctypes.wintypes as w
R=pathlib.Path(__file__).parent;plan=json.loads((R/'plan.json').read_text());root=pathlib.Path(plan['root'])/'representative-capacity';root.mkdir();exe=pathlib.Path(plan['root'])/'representative-code/J6StreamBench.exe'
args=[str(exe),str(root),'500000','100000','0','67108864','1000000','1073741824','288']
K=c.WinDLL('kernel32',use_last_error=True);K.GetProcessTimes.argtypes=[w.HANDLE]+[c.POINTER(w.FILETIME)]*4;K.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD]
p=subprocess.Popen(args,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);ts=[w.FILETIME() for _ in range(4)];assert K.GetProcessTimes(int(p._handle),*(c.byref(t) for t in ts));created=(ts[0].dwHighDateTime<<32)|ts[0].dwLowDateTime
rc=p.wait(timeout=13.6);signal=K.WaitForSingleObject(int(p._handle),0);p._handle.Close()
m=json.loads((root/'manifest.json').read_text());b=json.loads((root/'bench.json').read_text());seq=0;total=0;failure=None
try:
 assert rc==0 and signal==0 and m['fault']==0
 assert [s['name'] for s in m['segments']]==[f'trace-{i:05d}.jsonl' for i in range(len(m['segments']))]
 assert {p.name for p in root.glob('trace-*.jsonl')}=={s['name'] for s in m['segments']}
 for s in m['segments']:
  data=(root/s['name']).read_bytes();assert len(data)==s['bytes'] and hashlib.sha256(data).hexdigest()==s['sha256'];assert s['firstSequence']==seq+1 and data.endswith(b'\n')
  lines=data.splitlines();assert len(lines)==s['records']
  for line in lines:seq+=1;assert json.loads(line)['seq']==seq
  assert s['lastSequence']==seq;total+=len(data)
 assert seq==m['accepted']==m['persisted']==m['attempted']==500000 and total==m['bytes']
 assert b['recordsPerSecond']>=97212 and b['viewRows']==20000 and b['viewTruncated']==480000 and not b['viewAuthoritative']
except Exception as e:failure=repr(e)
out=dict(status='PASS' if failure is None else 'FAIL',failure=failure,pid=p.pid,created=str(created),args=args,exeSHA256=hashlib.sha256(exe.read_bytes()).hexdigest(),handleSignaled=signal==0,handleClosed=True,bench=b,manifest=m,verifiedRecords=seq,verifiedBytes=total,scope='Representative byte-size capacity only; larger-payload failure remains failed')
(R/'representative-result.json').write_text(json.dumps(out,indent=2));print(json.dumps(dict(status=out['status'],bench=b,segments=len(m['segments']),failure=failure)))
if failure:raise SystemExit(1)
