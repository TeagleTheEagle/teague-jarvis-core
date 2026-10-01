import pathlib,json,hashlib,shutil,uuid
R=pathlib.Path(__file__).resolve().parent;P=R.parent/'stage6-tracker-experiment-20260923'
O=pathlib.Path(json.loads((P/'candidate.json').read_text())['code']);rows=json.loads((P/'final-source.json').read_text())['files']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for r in rows:assert sha(O/r['name'])==r['sha256']
C=pathlib.Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code';C.mkdir(parents=True)
for r in rows:
 p=C/r['name'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(O/r['name'],p)
def change(s,a,b):
 assert a in s,a
 return s.replace(a,b)
s=(C/'small_binding.py').read_text().replace('stage6-small-large-integration-v1','stage6-small-tracker-integration-v2').replace('small-source.json','small-source-v2.json').replace('small-declaration.json','small-declaration-v2.json')
s=change(s,"case=v.get('case'),files=12","case=v.get('case'),inventorySHA256=sha(root/'contract.json'),files=12")
s=change(s,'case=case,files=12',"case=case,inventorySHA256=sha(root/'contract.json'),files=12")
s=change(s," if v!=expected", " check_path(root)\n if v!=expected")
(C/'small_binding_v2.py').write_text(s)
s=(C/'small_coverage.py').read_text()
s=change(s,"  source='creator-owned-handle' if direct else 'tracer-opened-handle'", "  tracker=(role=='OS_CONSOLE_HELPER' and h.get('source')=='independent-tree-handle-v1' and h.get('trackerVerified') is True and bool(h.get('originalTracer')) and bool(h.get('trackerEvidence')))\n  source='creator-owned-handle' if direct else ('independent-tree-handle-v1' if tracker else 'tracer-opened-handle')")
(C/'small_coverage_v2.py').write_text(s)
s=(C/'small_check.py').read_text().replace('from small_coverage import','from small_coverage_v2 import').replace('from small_binding import','from small_binding_v2 import').replace('small-declaration.json','small-declaration-v2.json').replace('small-check-result.json','small-check-result-v2.json')
s=change(s," cov=coverage(expected,events,handles,native,mapping)"," from tracker_adapter_v2 import adapt\n handles=adapt(root,expected,handles,kernel,mapping,collector)\n cov=coverage(expected,events,handles,native,mapping)")
(C/'small_check_v2.py').write_text(s)
s=(C/'evidence_support.py').read_text()
s=change(s,'def __init__(self,collector_anchor=False):','def __init__(self,collector_anchor=False,run_root=None):')
s=change(s,'  if collector_anchor:self.initialize_anchor()', '''  self.runBinding=None
  if collector_anchor:
   self.initialize_anchor()
   if run_root is not None:
    try:
     from tracker_adapter_v2 import binding
     self.runBinding=binding(run_root,self.anchor['pid'],self.anchor['created'])
    except BaseException:
     K.CloseHandle(self.anchorHandle);self.anchorHandle=None;raise''')
s=change(s,'def capture_image(self,h,pid,created):','def capture_image(self,h,pid,created,acquisition=None):')
s=change(s,"  try:\n   record['handlePid']", "  if acquisition is not None:record.update(acquisitionBeginQpc=acquisition[0],acquisitionReturnedQpc=acquisition[1])\n  try:\n   record['handlePid']")
s=change(s,"h=w.HANDLE();me=K.GetCurrentProcess()","h=w.HANDLE();me=K.GetCurrentProcess();acq=ticks()")
s=change(s,'  self.anchorHandle=h.value','  acquired=ticks();self.anchorHandle=h.value')
s=change(s,'self.capture_image(h.value,os.getpid(),created)','self.capture_image(h.value,os.getpid(),created,(acq,acquired))')
s=change(s,"value=dict(schema='stage6-independent-tree-support-v1',","value=dict(binding=self.runBinding,schema='stage6-independent-tree-support-v1',")
s=change(s,'def add(self,h,pid,parent,role,args=None):','def add(self,h,pid,parent,role,args=None,acquisition=None):')
s=change(s,'self.capture_image(h,pid,ts[0])','self.capture_image(h,pid,ts[0],acquisition)')
s=change(s,'h=w.HANDLE();selfhandle=K.GetCurrentProcess()','h=w.HANDLE();selfhandle=K.GetCurrentProcess();acq=ticks()')
s=change(s,'  with self.lock:\n   try:self.add(h.value,p.pid,os.getpid(),role,args)','  acquired=ticks()\n  with self.lock:\n   try:self.add(h.value,p.pid,os.getpid(),role,args,(acq,acquired))')
s=change(s,'     h=K.OpenProcess(0x100000|0x1000,False,pid)','     acq=ticks();h=K.OpenProcess(0x100000|0x1000,False,pid);acquired=ticks()')
s=change(s,"self.add(h,pid,parent,'descendant:'+name)","self.add(h,pid,parent,'descendant:'+name,acquisition=(acq,acquired))")
(C/'evidence_support.py').write_text(s)
s=(C/'large_collect.py').read_text().replace('TreeTracker(collector_anchor=True)','TreeTracker(collector_anchor=True,run_root=root)');(C/'large_collect.py').write_text(s)
s=(C/'small_launch.ps1').read_text().replace('small_binding.py','small_binding_v2.py').replace('small-declaration.json','small-declaration-v2.json')
s=s.replace('D:\\\\JARVIS-STAGE6-LIVE\\\\693f0cd17ff4419aaf404604a23edc5f\\\\code',str(C).replace('\\','\\\\'))
(C/'small_launch_v2.ps1').write_text(s)
shutil.copy2(R.parent/'stage6-support-verifier-20260923'/'support_verifier.py',C/'support_verifier.py')
for name in ('tracker_adapter_v2.py','small_finalize_v2.py'):shutil.copy2(R/name,C/name)
# Only the known tiny source/allowlist is rebound. No protected/large source allowed.
allow=C/'baseline-allowlist.json';a=json.loads(allow.read_text());a['syntheticRoots']=[str(C/'small-synthetic')];a['approvedProtectedRoots']=[];a['realProtectedAccess']=False;allow.write_text(json.dumps(a,indent=2))
with (R/'candidate.json').open('x') as f:json.dump(dict(code=str(C),original=str(O),originalFiles=rows),f,indent=2)
print(C)
