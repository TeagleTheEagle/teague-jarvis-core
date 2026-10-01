import copy,json,pathlib,unittest,hashlib,sys,tempfile
from diagnostic_review import verify,percentile_bounds,bind_external
R=pathlib.Path(__file__).parent;C=R/'candidate';O=pathlib.Path(json.loads((R/'before.json').read_text())['source'])
class DiagnosticTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.output=pathlib.Path(json.loads((R/'final-offline.json').read_text())['path']);cls.data=json.loads((cls.output/'normal.json').read_text())
 def check(self,v):return verify(v,run=self.data['run'],session=self.data['session'],channel='authority',frequency=self.data['frequency'])
 def reject(self,key,value):
  v=copy.deepcopy(self.data);v[key]=value
  with self.assertRaises(ValueError):self.check(v)
 def test_loss_transition(self):self.assertEqual([x['current'] for x in self.check(self.data)['lossTransitions']],[3,13])
 def test_multiple_increases(self):self.assertEqual(len(self.check(self.data)['lossTransitions']),2)
 def test_order(self):
  v=copy.deepcopy(self.data);v['samples'][1]['sequence']=1
  with self.assertRaises(ValueError):self.check(v)
 def test_aggregation(self):self.assertEqual(self.data['samples'][1]['callbackDelta'],2)
 def test_slow_timestamp(self):self.assertGreater(self.data['slowSpans'][0]['endQpc'],self.data['slowSpans'][0]['beginQpc'])
 def test_metadata(self):self.assertEqual(self.data['slowSpans'][0]['operation'],'metadata')
 def test_guard(self):self.assertEqual(self.data['slowSpans'][1]['operation'],'guardWait')
 def test_lag_quantiles(self):
  h=self.data['samples'][1]['deliveryLag']
  for q in (.5,.95,.99):self.assertEqual(percentile_bounds(h,q),[8,15])
 def test_channels(self):self.reject('channel','detail')
 def test_sessions(self):self.reject('session','another-session')
 def test_stale_run(self):self.reject('run','old-run')
 def test_clock(self):self.reject('frequency',self.data['frequency']+1)
 def test_queue_high_water(self):self.assertEqual((self.data['queueHighItems'],self.data['queueHighBytes']),(7,1200))
 def test_sample_bound(self):self.reject('sampleCapacity',1)
 def test_overflow(self):self.reject('overflow',1)
 def test_failure_no_pass(self):
  self.reject('errors',1);self.assertFalse(self.check(self.data)['liveEligibility'])
 def test_authoritative_unchanged(self):
  original=(O/'authority_trace_v3.cpp').read_text();successor=(C/'authority_trace_v3.cpp').read_text()
  self.assertIn('lifecycleSink->add(o.str())',successor)
  for line in original.splitlines():
   if '"source' in line or 'o<<"{\\"source' in line:self.assertIn(line.strip().replace('std::ostringstream o;',''),successor)
 def test_contract_unchanged(self):
  for n in ('small_launch_v3.ps1','terminal_control_v3.ps1'):
   self.assertEqual((C/n).read_bytes(),(O/n).read_bytes())
 def test_loss_semantics(self):
  for n in ('authority_trace_v3.cpp','startup_trace.cpp'):
   s=(C/n).read_text();self.assertIn('p->EventsLost',s);self.assertIn('p->RealTimeBuffersLost',s)
 def test_etw_configuration(self):
  for n in ('authority_trace_v3.cpp','startup_trace.cpp'):
   old=(O/n).read_text().splitlines();new=(C/n).read_text().splitlines()
   for line in old:
    if 'p->BufferSize=64' in line or 'EnableTraceEx2' in line:self.assertIn(line,new)
 def test_shutdown_order(self):
  for n in ('authority_trace_v3.cpp','startup_trace.cpp'):
   s=(C/n).read_text();old=(O/n).read_text()
   line=next(x for x in old.splitlines() if 'thread.join();CloseTrace' in x and 'beforeStop' in x)
   self.assertIn(line.replace('thread.join();CloseTrace','thread.join();j6d::diagnostic.stop();CloseTrace'),s)
 def test_historical_rejection(self):
  f=O/'protected-f117995dd9ef4ed1b33c1b44b1973293'
  self.assertEqual(json.loads((f/'etw-result.json').read_text())['eventsLost'],13)
  self.assertEqual(json.loads((f/'detail/etw-result.json').read_text())['eventsLost'],120281)
  self.assertFalse((f/'v3-seal.json').exists())
 def test_preserved_run(self):
  r=R.parent/'stage6-one-small-live-v3-20260923';f=O/'protected-f117995dd9ef4ed1b33c1b44b1973293'
  for row in json.loads((r/'failed-run-inventory.json').read_text())['files']:self.assertEqual(hashlib.sha256((f/row['path']).read_bytes()).hexdigest(),row['sha256'])
 def test_original_hashes(self):
  for row in json.loads((R/'before.json').read_text())['files']:self.assertEqual(hashlib.sha256((O/row['name']).read_bytes()).hexdigest(),row['sha256'])
 def test_concurrent_sampler(self):
  v=json.loads((self.output/'concurrent.json').read_text());result=verify(v,run=v['run'],session=v['session'],channel='detail',frequency=v['frequency'])
  self.assertTrue(result['telemetryValid']);self.assertGreaterEqual(len(v['samples']),4)
  self.assertTrue(all(x['consumerWaitState']==258 for x in v['samples']))
 def test_query_failure_explicit(self):
  v=json.loads((self.output/'query-failure.json').read_text());self.assertIsNone(v['samples'][-1]['eventsLost'])
  with self.assertRaises(ValueError):self.check(v)
 def test_original_checker_replay(self):
  sys.path.insert(0,str(O));import small_check_v3
  with self.assertRaises(Exception) as caught:small_check_v3.check(O/'protected-f117995dd9ef4ed1b33c1b44b1973293')
  self.assertNotIsInstance(caught.exception,ImportError)
 def test_buffer_loss_cannot_qualify(self):
  v=copy.deepcopy(self.data)
  for s in v['samples']:s['eventsLost']=0
  v['samples'][0]['realtimeBuffersLost']=1;self.assertFalse(self.check(v)['liveEligibility'])
 def test_external_binding(self):
  with tempfile.TemporaryDirectory(dir=R) as t:
   root=pathlib.Path(t);hz=self.data['frequency'];c={'frequency':hz,'cleanupEntryQpc':100,'deadlineQpc':100+20*hz};p=dict(c,binding={'run':self.data['run'],'kernelSession':self.data['session'],'frequency':hz})
   cp=root/'cleanup.json';pp=root/'phase.json';cp.write_text(json.dumps(c));pp.write_text(json.dumps(p));self.assertFalse(bind_external(self.data,cp,pp)['acceptanceSealed'])
   p['binding']['run']='prefix-'+self.data['run'];pp.write_text(json.dumps(p))
   with self.assertRaises(ValueError):bind_external(self.data,cp,pp)
 def test_admission_queue_side_effects(self):
  for n in ('trace_sink.hpp','durable_sink.hpp'):
   s=(C/n).read_text();self.assertIn('67108864',s);self.assertIn('137438953472',s);self.assertIn('196531200',s)
if __name__=='__main__':unittest.main(verbosity=2)
