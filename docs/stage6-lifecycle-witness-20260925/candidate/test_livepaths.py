import unittest,pathlib,uuid,os,tempfile,json,errno,subprocess
from unittest.mock import patch
from workspace import CODE,new_run,run_dir,artifact,check_path,activate_temp
from finalize import finalize,accepted
from test_finalization import fixture
class LivePaths(unittest.TestCase):
 def setUp(self):self.root=new_run('paths-'+uuid.uuid4().hex)
 def test_all_critical_paths_are_d_and_contained(self):
  for n in ('heartbeat.jsonl','events.jsonl','collector-finished.json','workload-stop','ready.json','monitor-failure.json','probes.json','fine-trace.json','resources.json','evidence-manifest.json'):
   p=artifact(self.root,n);self.assertEqual(p.drive,'D:');self.assertTrue(p.is_relative_to(self.root));p.write_text('synthetic');self.assertEqual(p.read_text(),'synthetic')
 def test_no_c_fallback(self):
  for p in ('C:/Temp/heartbeat.jsonl','D:/outside/state.json'):
   with self.assertRaises(ValueError):check_path(pathlib.Path(p))
 def test_traversal(self):
  for n in ('..','../escape','x/../../escape','C:/escape','..\\escape','x:stream'):
   with self.assertRaises(ValueError):artifact(self.root,n)
  with self.assertRaises(ValueError):run_dir('../escape')
 def test_run_collision_and_stale_reuse(self):
  with self.assertRaises(FileExistsError):new_run(self.root.name)
  self.assertEqual(run_dir(self.root.name),self.root)
 def test_missing_workspace_no_fallback(self):
  with self.assertRaises(ValueError):run_dir('missing-'+uuid.uuid4().hex)
 def test_temp_ignores_c_environment(self):
  with patch.dict(os.environ,{'TEMP':'C:\\Temp','TMP':'C:\\Temp'}):
   activate_temp(self.root)
   with tempfile.NamedTemporaryFile() as f:self.assertTrue(pathlib.Path(f.name).is_relative_to(self.root/'temp'))
   self.assertEqual(pathlib.Path(os.environ['TEMP']).drive,'D:')
 def test_reparse_escape_rejected(self):
  link=self.root/'link';target=new_run('target-'+uuid.uuid4().hex)
  pwsh=r'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
  command="New-Item -ItemType Junction -Path '"+str(link)+"' -Target '"+str(target)+"' | Out-Null"
  p=subprocess.run([pwsh,'-NoProfile','-Command',command],capture_output=True,timeout=10)
  self.assertEqual(p.returncode,0,p.stderr.decode(errors='replace'))
  try:
   with self.assertRaises(ValueError):check_path(link/'escape.json')
  finally:
   self.assertTrue(link.is_junction());self.assertTrue(link.absolute().is_relative_to(self.root));os.rmdir(link)
 def test_workspace_access_denied(self):
  with patch.object(pathlib.Path,'mkdir',side_effect=PermissionError(errno.EACCES,'simulated inaccessible D workspace')):
   with self.assertRaises(PermissionError):new_run('denied-'+uuid.uuid4().hex)
 def test_archive_copy_denied_fails_closed(self):
  r=fixture()
  def fail(a,b):raise PermissionError('injected archive copy failure')
  with self.assertRaises(PermissionError):finalize(r,copy=fail)
  self.assertFalse(accepted(r,1))
 def test_probe_nonzero_rejected(self):
  r=fixture();(r/'probes.json').write_text(json.dumps([dict(pid=444,exit=17)]))
  with self.assertRaisesRegex(RuntimeError,'Probe failed'):finalize(r)
  self.assertFalse(accepted(r,1))
 def test_ambiguity_is_rejected(self):
  r=fixture();x=json.loads((r/'monitor-exit.json').read_text());x['identity']['created']='different';(r/'monitor-exit.json').write_text(json.dumps(x))
  with self.assertRaisesRegex(RuntimeError,'identity invalid'):finalize(r)
 def test_no_old_live_path_constants(self):
  for n in ('monitor.ps1','resources.ps1','collect.py','launch.ps1'):
   s=(CODE/n).read_text()
   self.assertNotIn('D:/JARVIS-STAGE6-EVENTDRAIN-20260920',s)
   self.assertNotIn('D:\\JARVIS-STAGE6-EVENTDRAIN-20260920',s)
   self.assertNotIn("journalVolume']=='C'",s)
   self.assertNotIn("$config.journalVolume -eq 'D'",s)
if __name__=='__main__':unittest.main(verbosity=2)
