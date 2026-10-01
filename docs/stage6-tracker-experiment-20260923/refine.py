import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parent
C=pathlib.Path(json.loads((R/'candidate.json').read_text())['code'])
p=C/'evidence_support.py';s=p.read_text()
backup=R/'first-tested-evidence_support.py';backup.write_text(s)
s=s.replace('acquiredQpc','captureEntryQpc')
old='  with self.lock:self.add(h.value,p.pid,os.getpid(),role,args)'
new='''  with self.lock:
   try:self.add(h.value,p.pid,os.getpid(),role,args)
   except BaseException:
    # Close only if add did not transfer ownership into retained handles.
    if h.value not in self.handles.values():
     if not K.CloseHandle(h.value):raise RuntimeError('Registration failure and handle-close failure')
    raise'''
assert s.count(old)==1;s=s.replace(old,new);p.write_text(s)
print(hashlib.sha256(p.read_bytes()).hexdigest())
