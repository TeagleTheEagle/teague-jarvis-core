import copy,json,pathlib,unittest
from support_verifier import structural,cross_channel,Rejected

def fixture():
 def cap(pid,created,t):
  return dict(pid=pid,created=created,source='independent-tree-handle-v1',handlePid=pid,
   handleCreated=created,creationAfter=created,valid=True,imageError=0,stateBefore=258,
   stateAfter=258,handleIdentity=str(pid+100),frequency=100,captureEntryQpc=t,
   stateBeforeQpc=t+1,queryBeginQpc=t+2,queryEndQpc=t+3,stateAfterQpc=t+4,image='D:\\fixture.exe')
 a=dict(pid=1,created='100',capture=cap(1,'100',10),closed=True,scopeOnly=True,
        exitFiletime=None,exitProof='EXTERNAL_NATIVE_OBSERVER_REQUIRED',stateAtClose=258,closeQpc=80)
 r=dict(pid=2,created='200',parentPid=1,capture=cap(2,'200',30),closed=True,exitFiletime='300',exitCode=0)
 d=dict(schema='stage6-independent-tree-support-v1',supportingOnly=True,kernelQualification='NOT_PERFORMED',
        valid=True,errors=[],anchor=a,descendants=[r],capacity=8192)
 k=dict(run='fresh',lost=0,complete=True,segmentsVerified=True,sequence=[1,2,3,4],rows=[
  dict(pid=1,created='100',startQpc=1,stopQpc=100,exitFiletime='400',frequency=100),
  dict(pid=2,created='200',startQpc=20,stopQpc=70,exitFiletime='300',frequency=100,parentIdentity=[1,'100'])])
 i=dict(run='fresh',rows=[dict(pid=x['pid'],created=x['created'],handleSignaled=True,nativeEntryVerified=True,
   image='D:\\fixture.exe',exitFiletime=x['exitFiletime'],entryQpc=x['startQpc']+1) for x in k['rows']])
 return [d,'a'*64,dict(run='fresh',supportSHA256='a'*64),'fresh',k,i]

class Tests(unittest.TestCase):
 def test_positive_synthetic(self):self.assertEqual(cross_channel(*fixture()),'FIXTURE_PREDICATES_PASS_NOT_ACCEPTANCE')
 def test_preserved_real_structure_only(self):
  root=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\978b5ce769244ec9a580fb0846f9bfdc\code\tracker-focused-b02e8f30c0ab4a9bbd39936b1c2c84be')
  count=0
  for p in root.rglob('tree-image-support.json'):
   try:d=json.loads(p.read_text())
   except json.JSONDecodeError:continue # preserved explicit collision fixture
   if d['valid']:self.assertGreater(len(structural(d)),1);count+=1
  self.assertGreater(count,0)

def mutation(path,value,delete=False):
 def test(self):
  args=fixture();v=args
  for key in path[:-1]:v=v[key]
  if delete:del v[path[-1]]
  else:v[path[-1]]=value
  with self.assertRaises(Rejected):cross_channel(*args)
 return test

cases={
 'missing_capture':([0,'descendants',0,'capture'],None),
 'missing_timing':([0,'descendants',0,'capture','queryEndQpc'],None),
 'reversed_timing':([0,'descendants',0,'capture','queryEndQpc'],1),
 'post_exit_query':([0,'descendants',0,'capture','stateAfter'],0),
 'query_error':([0,'descendants',0,'capture','imageError'],31),
 'pid_reuse':([0,'descendants',0,'capture','handlePid'],9),
 'creation_reuse':([0,'descendants',0,'capture','creationAfter'],'201'),
 'missing_handle':([0,'descendants',0,'capture','handleIdentity'],'0'),
 'relative_image':([0,'descendants',0,'capture','image'],'fixture.exe'),
 'traversal_image':([0,'descendants',0,'capture','image'],'D:\\..\\fixture.exe'),
 'unclosed_handle':([0,'descendants',0,'closed'],False),
 'missing_exit':([0,'descendants',0,'exitFiletime'],None),
 'missing_parent':([0,'descendants',0,'parentPid'],99),
 'self_parent':([0,'descendants',0,'parentPid'],2),
 'vacuous':([0,'descendants'],[]),
 'overflow':([0,'capacity'],0),
 'collector_self_exit':([0,'anchor','exitFiletime'],'400'),
 'collector_close_failure':([0,'anchor','closed'],False),
 'collector_early_close':([0,'anchor','closeQpc'],1),
 'error_record':([0,'errors'],['thread join failure']),
 'false_qualification':([0,'kernelQualification'],'PASS'),
 'stale_run':([2,'run'],'old'),
 'wrong_digest':([2,'supportSHA256'],'b'*64),
 'channel_stale':([5,'run'],'old'),
 'loss':([4,'lost'],1),
 'incomplete':([4,'complete'],False),
 'segment_missing':([4,'segmentsVerified'],False),
 'sequence_gap':([4,'sequence'],[1,2,4]),
 'missing_kernel_identity':([4,'rows'],[]),
 'missing_independent_identity':([5,'rows'],[]),
 'kernel_lifetime':([4,'rows',1,'stopQpc'],32),
 'kernel_clock':([4,'rows',1,'frequency'],10),
 'kernel_parent_reuse':([4,'rows',1,'parentIdentity'],[1,'101']),
 'kernel_exit':([4,'rows',1,'exitFiletime'],'301'),
 'retained_unsignaled':([5,'rows',1,'handleSignaled'],False),
 'missing_native':([5,'rows',1,'nativeEntryVerified'],False),
 'native_after_exit':([5,'rows',1,'entryQpc'],99),
 'independent_image':([5,'rows',1,'image'],'D:\\other.exe'),
 'independent_exit':([5,'rows',1,'exitFiletime'],'301'),
}
for name,(path,value) in cases.items():setattr(Tests,'test_reject_'+name,mutation(path,value))

def duplicate_test(self):
 args=fixture();args[0]['descendants'].append(copy.deepcopy(args[0]['descendants'][0]))
 with self.assertRaises(Rejected):cross_channel(*args)
Tests.test_duplicate=duplicate_test
def ambiguous_test(self):
 args=fixture();p=copy.deepcopy(args[0]['anchor']);p.update(created='150',parentPid=1,exitFiletime='350',exitCode=0)
 p['capture'].update(created='150',handleCreated='150',creationAfter='150')
 args[0]['descendants'].append(p)
 with self.assertRaises(Rejected):structural(args[0])
Tests.test_ambiguous_parent=ambiguous_test

if __name__=='__main__':unittest.main(verbosity=2)
