import unittest,pathlib,tempfile,json,shutil,threading,time,subprocess,sys,os
from finalize import finalize,accepted,sync_file
R=pathlib.Path(__file__).parent
def fixture():
 root=pathlib.Path(tempfile.mkdtemp(prefix='final-test-',dir=R));identity={'run':root.name,'pid':123,'created':'456','frequency':1000}
 def put(n,v):(root/n).write_text(json.dumps(v))
 put('ready.json',identity);put('collector-finished.json',{'status':'LIVE_MONITOR_HEALTHY'})
 put('monitor-result.json',{'status':'LIVE_COLLECTION_CLOSED','journalDurableFlush':True,'run':root.name,'sequences':2,'violations':0,'events':2})
 put('monitor-exit.json',{'exit_code':0,'identity':identity});put('collector-samples.json',[{'age':.2}]);put('resources.json',[{'synthetic_test':True}]);put('probes.json',[{'pid':444,'exit':0}])
 (root/'events.jsonl').write_text('\n'.join(json.dumps({'pid':444,'kind':k,'name':'J6Probe.exe'}) for k in ('start','stop'))+'\n')
 (root/'heartbeat.jsonl').write_text(''.join(json.dumps(dict(identity,seq=i,pump=i,ticks=100000+i*1000,utc='synthetic',state='ACTIVE',violations=0))+'\n' for i in (1,2)))
 return root
class Finalization(unittest.TestCase):
 def test_no_durable_flush_in_live_loop(self):
  s=(R/'monitor.ps1').read_text();loop=s.split('while($clock.Elapsed.TotalSeconds -lt 600){')[1].split('if($clock.Elapsed.TotalSeconds -ge 600)')[0]
  self.assertIn('$stream.Flush($false)',loop);self.assertNotIn('Flush($true)',loop)
  self.assertIn("Mark 'collection.freeze';Mark 'durable.flush.begin';$stream.Flush($true)",s)
 def test_success_real_fsync_and_archive(self):
  r=fixture();result=finalize(r);self.assertEqual(result['status'],'EVIDENCE_DURABLY_FINALIZED');self.assertTrue(accepted(r,0));self.assertFalse(accepted(r))
 def test_final_flush_failure(self):
  r=fixture()
  def fail(p):raise OSError('Injected final flush failure')
  with self.assertRaises(OSError):finalize(r,sync=fail)
  self.assertFalse(accepted(r,1));self.assertFalse((r/'EVIDENCE-DURABLY-FINALIZED.json').exists())
 def test_delayed_finalization_is_not_accepted_early(self):
  r=fixture();entered=threading.Event();release=threading.Event();errors=[]
  def delayed(p):entered.set();release.wait(3);sync_file(p)
  def worker():
   try:finalize(r,sync=delayed)
   except BaseException as e:errors.append(str(e))
  t=threading.Thread(target=worker);t.start();self.assertTrue(entered.wait(1));self.assertFalse(accepted(r,0));release.set();t.join(5);self.assertFalse(t.is_alive());self.assertFalse(errors);self.assertTrue(accepted(r,0))
 def test_copy_hash_failure(self):
  r=fixture()
  def corrupt(a,b):shutil.copyfile(a,b);b.write_bytes(b'corrupt')
  with self.assertRaisesRegex(RuntimeError,'hash mismatch'):finalize(r,copy=corrupt)
  self.assertFalse(accepted(r,1))
 def test_tamper_after_finalization(self):
  r=fixture();finalize(r);self.assertTrue(accepted(r,0));(r/'events.jsonl').write_text('changed');self.assertFalse(accepted(r,0))
 def test_partial_record_refused(self):
  r=fixture()
  with (r/'heartbeat.jsonl').open('ab') as f:f.write(b'{')
  with self.assertRaisesRegex(RuntimeError,'Incomplete'):finalize(r)
  self.assertFalse(accepted(r,1))
 def test_truncation_refused(self):
  r=fixture();(r/'heartbeat.jsonl').write_bytes(b'')
  with self.assertRaises(RuntimeError):finalize(r)
 def test_monitor_crash_missing_close_record(self):
  r=fixture();(r/'monitor-result.json').unlink()
  with self.assertRaises(FileNotFoundError):finalize(r)
  self.assertFalse(accepted(r,1))
 def test_nonzero_monitor_exit_refused(self):
  r=fixture();v=json.loads((r/'monitor-exit.json').read_text());v['exit_code']=17;(r/'monitor-exit.json').write_text(json.dumps(v))
  with self.assertRaises(RuntimeError):finalize(r)
 def test_finalizer_process_crash(self):
  r=fixture();p=subprocess.Popen([sys._base_executable,'-B',str(R/'test_finalization.py'),'crash',r.name]);p.wait(timeout=10)
  self.assertEqual(p.returncode,17);self.assertFalse(accepted(r,p.returncode))
 def test_failed_live_run_cannot_finalize(self):
  r=fixture();(r/'collector-finished.json').write_text(json.dumps({'status':'FAILED_CLOSED'}))
  with self.assertRaises(RuntimeError):finalize(r)
 def test_failed_event_counts_refused(self):
  r=fixture();(r/'events.jsonl').write_text('')
  with self.assertRaises(RuntimeError):finalize(r)
 def test_receipt_without_successful_worker_not_accepted(self):
  r=fixture();finalize(r);self.assertFalse(accepted(r,17));self.assertFalse(accepted(r,None))
if __name__=='__main__':
 if len(sys.argv)>1 and sys.argv[1]=='crash':
  root=R/sys.argv[2]
  assert root.parent==R and root.name.startswith('final-test-')
  def crash_sync(p):sync_file(p);os._exit(17)
  finalize(root,sync=crash_sync)
 else:unittest.main(verbosity=2)
