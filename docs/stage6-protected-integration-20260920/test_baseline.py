import unittest,pathlib,uuid,json,os,time,subprocess,sys,copy
from unittest.mock import patch
import baseline_contract as b,baseline_hash_worker as w,baseline_finalize as f
from workspace import CODE,new_run,activate_temp
class Health:
 def __init__(self):self.samples=[]
 def check(self):self.samples.append(dict(age=0))
class Baseline(unittest.TestCase):
 def setUp(self):
  self.source=CODE/('test-source-'+uuid.uuid4().hex);self.source.mkdir();(self.source/'nested').mkdir();(self.source/'one.vdi').write_bytes(b'a'*8192);(self.source/'nested'/'two.xml').write_bytes(b'xml')
  a=b.read(CODE/'baseline-allowlist.json');a['syntheticRoots'].append(str(self.source));(CODE/'baseline-allowlist.json').write_text(json.dumps(a))
  self.root=b.prepare(self.source);self.v=b.load(self.root)
 def snapshot(self,number=1,h=None):return w.snapshot(self.root,self.v,h or Health(),number,time.monotonic()+30)
 def closed(self):
  while b.state(self.root)['phase']!='OBSERVERS_CLOSED':
   p=b.state(self.root)['phase'];b.advance(self.root,p,b.PHASES[b.PHASES.index(p)+1])
  b.save(self.root/'source-hashes.json',[]);b.save(self.root/'hash-pass-2.json',dict(files={}))
 def test_recursive_mixed_extensions(self):self.assertEqual(list(self.v['inventory']),['nested/two.xml','one.vdi'])
 def test_two_hash_passes(self):self.assertEqual(self.snapshot(),self.snapshot(2))
 def test_metadata_unchanged(self):before=b.inventory(self.source);self.snapshot();self.assertEqual(before,b.inventory(self.source))
 def test_full_and_relative_paths(self):
  for k,v in self.v['inventory'].items():self.assertEqual(v['relativePath'],k);self.assertEqual(v['fullPath'],str(self.source/k));self.assertIn('LastWriteTimeUtc',v)
 def test_real_vm_blocked_before_read(self):
  with patch.object(pathlib.Path,'exists',side_effect=AssertionError('no filesystem read')):
   with self.assertRaises(ValueError):b.approved(r'C:\Users\jonny\VirtualBox VMs\JARVIS-CLEAN-WIN11')
 def test_real_config_blocked_before_read(self):
  with patch.object(pathlib.Path,'exists',side_effect=AssertionError('no filesystem read')):
   with self.assertRaises(ValueError):b.approved(r'C:\Users\jonny\.VirtualBox')
 def test_unapproved_root(self):
  with self.assertRaises(ValueError):b.approved(CODE.parent)
 def test_traversal(self):
  with self.assertRaises(ValueError):b.approved(self.source/'..')
 def test_duplicate_path(self):
  actual=list(os.walk(self.source))
  with patch.object(os,'walk',return_value=[(str(self.source),[],['one.vdi','one.vdi'])]):
   with self.assertRaises(ValueError):b.inventory(self.source)
 def test_source_missing(self):
  (self.source/'one.vdi').rename(self.source/'renamed.vdi')
  with self.assertRaises(ValueError):b.load(self.root)
 def test_source_content_change(self):
  self.snapshot();p=self.source/'one.vdi';st=p.stat();p.write_bytes(b'b'*8192);os.utime(p,ns=(st.st_atime_ns,st.st_mtime_ns));self.assertNotEqual(b.read(self.root/'hash-pass-1.json')['files'],self.snapshot(2))
 def test_source_metadata_change(self):
  p=self.source/'one.vdi';s=p.stat();os.utime(p,ns=(s.st_atime_ns,s.st_mtime_ns+10000000))
  with self.assertRaises(ValueError):b.load(self.root)
 def test_unreadable_injected(self):
  with patch.object(w,'checked_open',side_effect=PermissionError('injected unreadable')):
   with self.assertRaises(PermissionError):self.snapshot()
  self.assertFalse((self.root/'hash-pass-1.json').exists())
 def test_evidence_write_failure(self):
  with patch.object(w,'save',side_effect=OSError('injected evidence failure')):
   with self.assertRaises(OSError):self.snapshot()
 def test_heartbeat_failure(self):
  h=Health();h.check=lambda:(_ for _ in ()).throw(RuntimeError('stale'))
  with self.assertRaises(RuntimeError):self.snapshot(h=h)
 def test_deadline_expiry(self):
  with self.assertRaises(TimeoutError):w.snapshot(self.root,self.v,Health(),1,time.monotonic()-1)
 def test_cancel(self):
  (self.root/'workload-stop').touch()
  with self.assertRaises(RuntimeError):self.snapshot()
 def test_disk_full_preparation(self):
  with patch.object(b.shutil,'disk_usage',return_value=type('D',(),dict(free=0))()):
   with self.assertRaises(RuntimeError):b.prepare(self.source)
 def test_altered_limits(self):
  self.v['thresholds']['heartbeat']=11
  with self.assertRaises(ValueError):b.validate(self.root,self.v)
 def test_wrong_mode(self):
  self.v['mode']='sacrificial'
  with self.assertRaises(ValueError):b.validate(self.root,self.v)
 def test_contract_inventory_injection(self):
  self.v['inventory']['../../escape']=self.v['inventory']['one.vdi']
  with self.assertRaises(ValueError):b.validate(self.root,self.v)
 def test_hardlink_rejected(self):
  os.link(self.source/'one.vdi',self.source/'alias')
  with self.assertRaises(ValueError):b.inventory(self.source)
 def test_open_handle_escape(self):
  with patch.object(w,'opened_path',return_value=CODE/'elsewhere'):
   with self.assertRaises(ValueError):self.snapshot()
 def test_identity_replacement(self):
  m=copy.deepcopy(self.v['inventory']['one.vdi']);m['fileId']+=1
  with self.assertRaises(ValueError):w.checked_open(self.source/'one.vdi',self.source,m)
 def test_worker_write_guard(self):
  # Fresh subprocess; persistent audit hook cannot contaminate the test runner.
  code="import pathlib,baseline_contract as b;from workspace import run_dir;r=run_dir("+repr(self.root.name)+");b.install_write_guard(r);p=pathlib.Path("+repr(str(self.source/'one.vdi'))+");\ntry:p.write_bytes(b'bad')\nexcept PermissionError:print('DENIED')\nelse:raise RuntimeError('source write permitted')"
  q=subprocess.run([sys.executable,'-B','-c',code],cwd=CODE,capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr);self.assertIn('DENIED',q.stdout);self.assertEqual((self.source/'one.vdi').stat().st_size,8192)
 def test_finalizer_requires_closed_observers(self):
  with self.assertRaises(RuntimeError):f.finalize(self.root)
 def test_manifest_cannot_be_created_on_missing_evidence(self):
  while b.state(self.root)['phase']!='OBSERVERS_CLOSED':
   p=b.state(self.root)['phase'];b.advance(self.root,p,b.PHASES[b.PHASES.index(p)+1])
  with self.assertRaises((RuntimeError,OSError)):f.finalize(self.root)
  self.assertFalse((self.root/'baseline-manifest.json').exists())
 def test_source_open_mode_readonly(self):
  real=pathlib.Path.open;modes=[]
  def record(p,*a,**kw):
   if p.is_relative_to(self.source):modes.append(a[0] if a else kw.get('mode','r'))
   return real(p,*a,**kw)
  with patch.object(pathlib.Path,'open',record):self.snapshot()
  self.assertTrue(modes);self.assertEqual(set(modes),{'rb'})
 def test_worker_failure_prevents_manifest(self):
  self.closed();b.save(self.root/'hash-failure.json',dict(error='injected worker crash'))
  with self.assertRaises(RuntimeError):f.finalize(self.root)
  self.assertFalse((self.root/'baseline-manifest.json').exists())
 def test_observer_failure_prevents_manifest(self):
  self.closed();b.save(self.root/'stress-result.json',dict(status='DIAGNOSTIC_COMPLETE',primary_failure=None));b.save(self.root/'launcher-result.json',dict(workExit=0))
  with patch.object(f,'evaluate',return_value=dict(status='FAIL',errors=['observer lost'])):
   with self.assertRaises(RuntimeError):f.finalize(self.root)
  self.assertFalse((self.root/'baseline-manifest.json').exists())
 def test_archive_failure(self):
  self.closed()
  with patch.object(f,'require_ready',return_value=dict(status='PASS')),patch.object(f.zipfile,'ZipFile',side_effect=OSError('archive failure')):
   with self.assertRaises(OSError):f.finalize(self.root)
  self.assertFalse((self.root/'integration-result.json').exists())
 def test_manifest_write_failure(self):
  self.closed();real=f.save
  def fail(p,v):
   if p.name=='baseline-manifest.json':raise OSError('manifest failure')
   return real(p,v)
  with patch.object(f,'require_ready',return_value=dict(status='PASS')),patch.object(f,'save',side_effect=fail):
   with self.assertRaises(OSError):f.finalize(self.root)
  self.assertFalse((self.root/'evidence.zip').exists())
 def test_source_disappears_at_open(self):
  real=w.checked_open
  def removed(p,base,meta):
   p.unlink();return real(p,base,meta)
  with patch.object(w,'checked_open',side_effect=removed):
   with self.assertRaises(FileNotFoundError):self.snapshot()
  self.assertFalse((self.root/'hash-pass-1.json').exists())
 def test_metadata_changes_during_hash(self):
  h=Health();p=self.source/'one.vdi';calls=0
  def mutate():
   nonlocal calls
   calls+=1
   if calls==2:
    s=p.stat();os.utime(p,ns=(s.st_atime_ns,s.st_mtime_ns+10000000))
  h.check=mutate
  with self.assertRaises((ValueError,RuntimeError)):self.snapshot(h=h)
 def test_reparse_junction(self):
  target=CODE/('junction-target-'+uuid.uuid4().hex);target.mkdir();(target/'unrelated').write_bytes(b'outside')
  link=self.source/'junction'
  # Fixed generated synthetic paths only. Retain the junction as negative-test evidence.
  ps=r'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
  command="New-Item -ItemType Junction -Path '"+str(link)+"' -Target '"+str(target)+"' -ErrorAction Stop | Out-Null"
  q=subprocess.run([ps,'-NoProfile','-Command',command],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
  with self.assertRaises(ValueError):b.inventory(self.source)
 def test_unique_fresh_state(self):self.assertNotEqual(self.root,b.prepare(self.source))
 def test_no_ads_path_admitted(self):
  with patch.object(os,'walk',return_value=[(str(self.source),[],['one.vdi:stream'])]):
   with self.assertRaises((ValueError,OSError)):b.inventory(self.source)
if __name__=='__main__':unittest.main()
