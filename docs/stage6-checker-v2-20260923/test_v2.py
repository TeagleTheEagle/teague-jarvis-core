import unittest,copy,json,pathlib,uuid,sys,hashlib,os
from unittest.mock import patch
from workspace import CODE,new_run,check_path
sys.path.insert(0,str(CODE/'medium-checker'))
import qualification as q
import small_coverage as oldcov,small_coverage_v2 as cov
import small_binding_v2 as binding
import tracker_adapter_v2 as adapter
import small_finalize_v2 as fin
from fixture_support import fixture

ROOT=new_run('v2-focused-'+uuid.uuid4().hex)
def folder():
 p=ROOT/uuid.uuid4().hex;p.mkdir();return p
def put(p,v):p.write_text(json.dumps(v))
BASE=json.loads((CODE/'medium-checker/positive-fixture.json').read_text())['bundle']

class Authority(unittest.TestCase):
 def test_original_coverage_preserved(self):
  self.assertEqual(cov.coverage(**BASE['coverage']),oldcov.coverage(**BASE['coverage']))
  self.assertEqual(cov.coverage(**BASE['coverage'])['status'],'PASS')
 def test_actual_qualifier(self):self.assertEqual(q.qualify(**BASE['structural'])['status'],'PASS')
 def test_kernel_mutations(self):
  for field,value in [('eventsLost',1),('buffersLost',1),('faults',1),('requestedStop',False)]:
   with self.subTest(field=field):
    x=copy.deepcopy(BASE['structural']);x['kernel'][field]=value
    with self.assertRaises(ValueError):q.qualify(**x)
 def test_native_contradiction(self):
  x=copy.deepcopy(BASE['structural']);x['natives'][0]['fault']=True
  with self.assertRaises(ValueError):q.qualify(**x)
 def test_direct_cannot_use_tracker(self):
  x=copy.deepcopy(BASE['coverage']);h=next(h for h in x['handles'] if h['source']=='creator-owned-handle');h.update(source='independent-tree-handle-v1',trackerVerified=True,originalTracer={'a':1},trackerEvidence={'b':1})
  self.assertEqual(cov.coverage(**x)['status'],'FAIL')
 def test_image31_still_fails(self):
  x=copy.deepcopy(BASE['coverage']);ids={oldcov.identity(e) for e in x['expected'] if e['role']=='OS_CONSOLE_HELPER'}
  h=next(h for h in x['handles'] if oldcov.identity(h) in ids and h['retained']);h.update(image='',imageError=31)
  self.assertEqual(cov.coverage(**x)['status'],'FAIL')
 def stream(self):
  p=folder();events=BASE['events'];data=b''.join((json.dumps(dict(seq=i+1,raw=e))+'\n').encode() for i,e in enumerate(events));(p/'segment.jsonl').write_bytes(data)
  seg=dict(name='segment.jsonl',number=0,first=1,last=len(events),states=[0,1,2,3,4],records=len(events),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
  m=dict(format='durable-segments-v1',segments=[seg],accepted=len(events),bytes=len(data));put(p/'kernel-authority-manifest.json',m)
  put(p/'kernel-authority-seal.json',dict(manifestSHA256=q.sha(p/'kernel-authority-manifest.json'),segments=1,accepted=len(events)))
  put(p/'kernel-authority-result.json',dict(fault=0,threadsExited=True,remaining=0,written=len(events),accepted=len(events),attempted=len(events),segments=[dict(seg,states=[0,1,2,3,4,5])]))
  return p
 def test_serialized_stream(self):self.assertEqual(q.stream(self.stream(),'kernel-authority')[0],BASE['events'])
 def test_segment_tamper(self):
  p=self.stream();(p/'segment.jsonl').write_bytes(b'{}\n')
  with self.assertRaises(ValueError):q.stream(p,'kernel-authority')
 def test_missing_segment(self):
  p=self.stream();m=json.loads((p/'kernel-authority-manifest.json').read_text());m['segments'][0]['name']='missing.jsonl';put(p/'kernel-authority-manifest.json',m)
  s=json.loads((p/'kernel-authority-seal.json').read_text());s['manifestSHA256']=q.sha(p/'kernel-authority-manifest.json');put(p/'kernel-authority-seal.json',s)
  with self.assertRaises(ValueError):q.stream(p,'kernel-authority')
 def test_sequence_gap_resealed(self):
  p=self.stream();lines=(p/'segment.jsonl').read_text().splitlines();a=json.loads(lines[0]);a['seq']=2;lines[0]=json.dumps(a);data=('\n'.join(lines)+'\n').encode();(p/'segment.jsonl').write_bytes(data)
  m=json.loads((p/'kernel-authority-manifest.json').read_text());m['segments'][0].update(bytes=len(data),sha256=q.sha(p/'segment.jsonl'));m['bytes']=len(data);put(p/'kernel-authority-manifest.json',m)
  s=json.loads((p/'kernel-authority-seal.json').read_text());s['manifestSHA256']=q.sha(p/'kernel-authority-manifest.json');put(p/'kernel-authority-seal.json',s)
  with self.assertRaises(ValueError):q.stream(p,'kernel-authority')

class Adapter(unittest.TestCase):
 def setUp(self):
  self.p=folder();self.doc=fixture()[0];self.bind=dict(kernelSession='session',frequency=100);self.doc['binding']=self.bind
  self.doc['anchor']['capture'].update(acquisitionBeginQpc=8,acquisitionReturnedQpc=9)
  self.r=self.doc['descendants'][0];self.r['capture'].update(acquisitionBeginQpc=28,acquisitionReturnedQpc=29)
  self.expected=[dict(pid=1,created='100',sequence=1,parentSequence=0,parentPid=9,startQpc=1,stopQpc=100,exitFiletime='400',exitCode=0,image='D:\\fixture.exe',role='DIRECT_WORKER'),dict(pid=2,created='200',sequence=2,parentSequence=1,parentPid=1,startQpc=20,stopQpc=70,exitFiletime='300',exitCode=0,image='D:\\fixture.exe',role='OS_CONSOLE_HELPER')]
  self.h=dict(pid=2,created='200',handleCreated='200',source='tracer-opened-handle',retained=True,closed=True,exited=True,exitFiletime='300',exitCode=0,image='',imageError=31)
 def run_adapter(self):
  put(self.p/'tree-image-support.json',self.doc)
  with patch.object(adapter,'binding',return_value=self.bind):return adapter.adapt(self.p,self.expected,[self.h],{'session':'session'},{},(1,'100'))
 def test_helper_supplement_preserves_original(self):
  h=self.run_adapter()[0];self.assertEqual(h['source'],'independent-tree-handle-v1');self.assertEqual(h['originalTracer']['imageError'],31);self.assertEqual(self.h['imageError'],31)
 def test_contradictions(self):
  for change in ('time','parent','image','exit','creation','session','binding','missing'):
   with self.subTest(change=change):
    self.setUp()
    if change=='time':self.r['capture']['acquisitionReturnedQpc']=99
    if change=='parent':self.expected[1]['parentSequence']=999
    if change=='image':self.h.update(image='D:\\wrong.exe',imageError=0)
    if change=='exit':self.h['exitFiletime']='301'
    if change=='creation':self.h['handleCreated']='201'
    if change=='session':self.bind['kernelSession']='other'
    if change=='binding':self.doc['binding']={}
    if change=='missing':del self.r['capture']['acquisitionBeginQpc']
    with self.assertRaises((ValueError,KeyError)):self.run_adapter()
 def test_other_class_never_supplemented(self):
  self.expected[1]['role']='APPLICATION_OBSERVER';self.assertEqual(self.run_adapter()[0],self.h)

class Binding(unittest.TestCase):
 def test_producer_binding_session_and_artifacts(self):
  from journal import frequency
  p=binding.make('normal');put(p/'etw-ready.json',dict(pid=10,rootPid=20,rootCreated='200',frequency=frequency(),session='synthetic-session'))
  put(p/'observer-identities.json',dict(etw=dict(pid=10,created='100')));put(p/'launcher-identity.json',dict(pid=20,created='200'))
  bound=adapter.binding(p,30,'300');self.assertEqual(bound['run'],p.name);self.assertEqual(bound['producer'],dict(pid=30,created='300'))
  put(p/'etw-ready.json',dict(pid=11,rootPid=20,rootCreated='200',frequency=frequency(),session='synthetic-session'))
  with self.assertRaises(ValueError):adapter.binding(p,30,'300')
 def test_stale_producer_digest(self):
  p=binding.make('normal');v=json.loads((p/'small-declaration-v2.json').read_text());(p/'contract.json').write_text((p/'contract.json').read_text()+' ')
  with self.assertRaises(ValueError):binding.validate(p,v)
 def test_real_small_declaration(self):
  p=binding.make('normal');v=json.loads((p/'small-declaration-v2.json').read_text());self.assertEqual(binding.validate(p,v),v)
  for key,value in [('run','old'),('sourceManifestSHA256','0'*64),('inventorySHA256','0'*64),('case','large'),('probe',14),('bytes',59665402098)]:
   w=dict(v);w[key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):binding.validate(p,w)
 def test_path_escape(self):
  with self.assertRaises(ValueError):check_path(CODE/'..'/'elsewhere')
 def test_reparse_path(self):
  p=folder()
  with patch.object(pathlib.Path,'is_junction',return_value=True),self.assertRaises(ValueError):check_path(p)

class Finalizer(unittest.TestCase):
 def setup_root(self):
  p=folder();put(p/'state.json',{'phase':'WORKLOAD_CLOSED'});(p/'detail').mkdir();put(p/'detail/trace-00000.jsonl',{'fixture':True});return p
 def call(self,p,check=None,census=None):
  import small_check_v2
  with patch.object(fin,'frozen'),patch.object(small_check_v2,'check',side_effect=check or (lambda r:dict(status='SMALL_NORMAL_PASS_PENDING_ARCHIVE'))),patch.object(fin,'no_live_identities',side_effect=census):return fin.finalize(p)
 def test_nested_archive(self):
  p=self.setup_root();r=self.call(p);self.assertEqual(r['status'],'SMALL_NORMAL_PASS');self.assertEqual(r['members'],5)
  with self.assertRaises(ValueError):self.call(p)
 def test_unknown_file(self):
  p=self.setup_root();(p/'unexpected').write_text('bad')
  with self.assertRaises(ValueError):self.call(p)
 def test_mutation(self):
  p=self.setup_root()
  def check(r):(r/'detail/trace-00000.jsonl').write_text('changed');return dict(status='SMALL_NORMAL_PASS_PENDING_ARCHIVE')
  with self.assertRaises(ValueError):self.call(p,check)
 def test_missing_nested_during_check(self):
  p=self.setup_root()
  def check(r):
   (r/'detail/trace-00000.jsonl').rename(r/'detail/trace-00001.jsonl');return dict(status='SMALL_NORMAL_PASS_PENDING_ARCHIVE')
  with self.assertRaises(ValueError):self.call(p,check)
 def test_controlled_failure_disposition(self):
  p=self.setup_root();put(p/'primary-failure.json',{'injected':True})
  r=self.call(p,lambda r:dict(status='CONTROLLED_FAILURE_REJECTED_PENDING_ARCHIVE'));self.assertEqual(r['status'],'CONTROLLED_FAILURE_REJECTION_VALIDATED')
 def test_cleanup_failure(self):
  with self.assertRaises(RuntimeError):self.call(self.setup_root(),census=RuntimeError('live identity'))
 def test_preserved_failure(self):
  p=self.setup_root();put(p/'primary-failure.json',{'failure':'preserve'})
  with self.assertRaises(ValueError):self.call(p)
 def test_archive_write_failure(self):
  p=self.setup_root()
  with patch.object(fin.zipfile,'ZipFile',side_effect=OSError('injected archive failure')),self.assertRaises(OSError):self.call(p)
  self.assertFalse((p/'v2-archive-receipt.json').exists())
 def test_durable_failure(self):
  p=self.setup_root()
  with patch.object(fin.os,'fsync',side_effect=OSError('injected fsync failure')),self.assertRaises(OSError):self.call(p)
  self.assertFalse((p/'v2-archive-receipt.json').exists())

if __name__=='__main__':
 print('FOCUSED_EVIDENCE '+str(ROOT));unittest.main(verbosity=2)
