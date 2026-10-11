import pathlib,json,hashlib,uuid,shutil,difflib
R=pathlib.Path(__file__).resolve().parent;P=R.parent/'stage6-integrated-loss-diagnostic-20260923';old=json.loads((P/'candidate.json').read_text());O=pathlib.Path(old['code'])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for x in old['files']:assert sha(O/x['name'])==x['sha256']
C=O.parent.parent/uuid.uuid4().hex/'code';C.mkdir(parents=True)
for x in old['files']:
 p=C/x['name'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(O/x['name'],p)
def rep(s,a,b):assert s.count(a)==1,a;return s.replace(a,b)
p=C/'evidence_support.py';before=p.read_text();s=before
s=rep(s,'K.GetCurrentProcess.restype=w.HANDLE','K.GetCurrentProcess.restype=w.HANDLE\nK.GetProcessId.argtypes=[w.HANDLE];K.GetProcessId.restype=w.DWORD')
s=rep(s,' def __init__(self):\n  self.rows=', ' def __init__(self,collector_anchor=False):\n  self.anchor=None;self.anchorHandle=None;self.supporting=collector_anchor;self.capacity=8192\n  self.rows=')
s=rep(s,'self.thread.start()','\n  if collector_anchor:self.initialize_anchor()\n  try:self.thread.start()\n  except BaseException:\n   if self.anchorHandle:\n    if not K.CloseHandle(self.anchorHandle):raise RuntimeError("Anchor close failure after thread-start failure")\n    self.anchorHandle=None\n   raise')
s=rep(s,' def add(self,h,pid,parent,role,args=None):',(R/'anchor_methods.txt').read_text()+'\n def add(self,h,pid,parent,role,args=None):')
s=rep(s,"  ts=times(h);key=(pid,ts[0])","  if self.supporting and len(self.rows)>=self.capacity:\n   self.stop.set();raise RuntimeError('Supporting identity capacity exceeded')\n  ts=times(h);key=(pid,ts[0])")
s=rep(s,"  try:self.rows[key]['image']=image(h)","  if self.supporting:\n   capture=self.capture_image(h,pid,ts[0]);self.rows[key]['imageCapture']=capture;self.rows[key]['image']=capture['image']\n   if not capture['valid']:self.errors.append(dict(stage='supporting-image',pid=pid,created=ts[0]));self.stop.set()\n   return\n  try:self.rows[key]['image']=image(h)")
s=rep(s,"     parents=[r for r in self.rows.values() if r['pid']==parent]","     parents=[r for r in self.rows.values() if r['pid']==parent]\n     if self.anchor and self.anchor['pid']==parent:parents.append(self.anchor)")
s=rep(s,"   except BaseException:self.errors.append(dict(qpc=ticks(),error=traceback.format_exc()))","   except BaseException:\n    self.errors.append(dict(qpc=ticks(),error=traceback.format_exc()))\n    if self.supporting:self.stop.set()")
s=rep(s,'  with self.lock:\n   for key,h in self.handles.items():',"  if self.supporting and self.thread.is_alive():raise RuntimeError('Tracker join failed')\n  with self.lock:\n   for key,h in self.handles.items():")
s=rep(s,"  put(pathlib.Path(root)/'tree-handles.json',result);return result","  if self.supporting:result['supportingEvidenceValid']=self.finish_support(root,result)\n  put(pathlib.Path(root)/'tree-handles.json',result);return result")
p.write_text(s)
(R/'evidence_support.py.diff').write_text(''.join(difflib.unified_diff(before.splitlines(True),s.splitlines(True))))
p=C/'large_collect.py';before=p.read_text();s=rep(before,'tree=TreeTracker();','tree=TreeTracker(collector_anchor=True);');s=rep(s,"if not proof or not proof['allExited']","if not proof or not proof.get('supportingEvidenceValid',False) or not proof['allExited']");p.write_text(s)
(R/'large_collect.py.diff').write_text(''.join(difflib.unified_diff(before.splitlines(True),s.splitlines(True))))
files=[dict(name=x['name'],sha256=sha(C/x['name'])) for x in old['files']]
with (R/'candidate.json').open('x') as f:json.dump(dict(code=str(C),original=str(O),files=files,originalFiles=old['files'],integratedExecutionAuthorized=False),f,indent=2)
print(C)
