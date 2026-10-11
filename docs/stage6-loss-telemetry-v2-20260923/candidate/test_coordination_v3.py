"""Offline evidence fixtures. PASS here is not live lifecycle/timing qualification."""
import unittest,copy,tempfile,pathlib,json
import coordination_v3 as c
def fixture():
 b=dict(schema=c.SCHEMA,run='protected-'+'1'*32,declarationSHA256='a'*64,sourceManifestSHA256='b'*64,kernelSession='J6-fixed-fixture',observerSHA256='c'*64,frequency=100)
 collector=dict(pid=10,created='1000',image=r'D:\python.exe');observer=dict(pid=20,created='900',image=r'D:\J6AuthorityTraceV3.exe')
 helper=dict(pid=11,created='1001',image=r'C:\Windows\System32\conhost.exe',role='OS_CONSOLE_HELPER',parent=collector,localClosed=True,localCloseQpc=1020,stateAtClose=258)
 p=dict(binding=b,state=c.STATES[3],collector=collector,authorityObserver=observer,helpers=[helper],cleanupEntryQpc=1000,deadlineQpc=3000,admissionsStopped=True,localDurable=True,trackerStopped=True,localHandlesClosed=True,cleanupPass=False,acceptance=False,completedQpc=1030)
 rows=[]
 for x,seq,parent,stop in ((collector,'41',1,1100),(helper,'42',10,1110)):
  rows.append(dict(pid=x['pid'],created=x['created'],sequence=seq,parentPid=parent,parentSequence='41' if parent==10 else '40',handleImage=x['image'],handleCreated=x['created'],handleRetained=True,imageError=0,metadataError=0,startQpc=100,handleAttemptQpc=200,imageBeginQpc=210,imageEndQpc=220,stopQpc=stop,stopCallbackQpc=stop+1,signalObservedQpc=stop+2,exitFiletime='2000',exitCode=0,kernelExitFiletime='2000',kernelExitCode=0))
 r=dict(schema=c.SCHEMA,kind='workload-terminal',sequence=1,binding=copy.deepcopy(b),phaseASHA256='d'*64,observer=observer,cleanupEntryQpc=1000,deadlineQpc=3000,capturedQpc=1120,coordinationOnly=True,acceptance=False,faults=0,eventsLost=0,buffersLost=0,rows=rows)
 n=dict(pid=10,created='1000',entryQpc=150,exitCode=0,exitFiletime='2000',finalWait=0,fault=False,deadlineExceeded=False)
 census=dict(kind='workload-only',binding=b,available=True,unknown=[],workloadRemaining=[],matchingProcesses=[observer],expectedManagement=[observer],completedQpc=1130)
 closure=dict(binding=b,completedQpc=2100,launcherExitVerified=True,launcherExitCode=0,observers={role:dict(exitVerified=True,exitCode=0,drained=True,exitQpc=1500+i*100) for i,role in enumerate(('application','detail','authority'))},durableComplete=True,authoritativeContradictions=[],allRequiredHandlesClosed=True)
 final=dict(binding=b,completedQpc=2200,available=True,unknown=[],workloadRemaining=[],matchingProcesses=[],traceSessions=[],launcherExitVerified=True,observerExitsVerified=True)
 return p,r,n,census,closure,final
def evaluate(v):
 p,r,n,pre,exits,final=v
 c.terminal(p,r,'d'*64,1125,n);c.census(p,pre);c.closure(p,exits);c.census(p,final,True)
 return True
class Tests(unittest.TestCase):
 def setUp(self):self.v=fixture()
 def reject(self,mutate):
  mutate(self.v)
  with self.assertRaises((c.Rejected,KeyError,TypeError)):evaluate(self.v)
 def test_01_helper_before_collector(self):
  self.v[1]['rows'][1].update(stopQpc=1050,stopCallbackQpc=1051,signalObservedQpc=1052);self.assertTrue(evaluate(self.v))
 def test_02_helper_after_collector(self):self.assertTrue(evaluate(self.v))
 def test_03_helper_after_deadline(self):self.reject(lambda v:v[1]['rows'][1].update(stopQpc=3001))
 def test_04_helper_never_exits(self):self.reject(lambda v:v[1]['rows'][1].update(signalObservedQpc=0))
 def test_05_collector_crash(self):self.reject(lambda v:v[1]['rows'][0].update(exitCode=1))
 def test_06_missing_phase(self):self.reject(lambda v:v[0].clear())
 def test_07_authority_crash(self):self.reject(lambda v:v[4]['observers']['authority'].update(exitCode=1))
 def test_08_application_crash(self):self.reject(lambda v:v[4]['observers']['application'].update(exitCode=1))
 def test_09_detail_crash(self):self.reject(lambda v:v[4]['observers']['detail'].update(exitCode=1))
 def test_10_missing_stop(self):self.reject(lambda v:v[1]['rows'][1].update(stopQpc=0))
 def test_11_handle_contradiction(self):self.reject(lambda v:v[1]['rows'][1].update(kernelExitCode=1))
 def test_12_native_contradiction(self):self.reject(lambda v:v[2].update(exitFiletime='other'))
 def test_13_reused_pid(self):self.reject(lambda v:v[1]['rows'][1].update(created='1002'))
 def test_14_handle_creation(self):self.reject(lambda v:v[1]['rows'][1].update(handleCreated='1002'))
 def test_15_full_image(self):self.reject(lambda v:v[1]['rows'][1].update(handleImage=r'D:\conhost.exe'))
 def test_16_parent(self):self.reject(lambda v:v[1]['rows'][1].update(parentSequence='999'))
 def test_17_stale_receipt(self):self.reject(lambda v:v[1].update(phaseASHA256='e'*64))
 def test_18_wrong_run(self):self.reject(lambda v:v[1]['binding'].update(run='old'))
 def test_19_wrong_observer(self):
  self.v[1]['observer']=dict(pid=21,created='900',image=r'D:\J6AuthorityTraceV3.exe')
  with self.assertRaises(c.Rejected):evaluate(self.v)
 def test_20_partial_publication(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'partial.json';p.write_text('{"schema":')
   with self.assertRaises(ValueError):c.load(p)
 def test_21_wrong_version(self):self.reject(lambda v:v[1].update(schema='future'))
 def test_22_receipt_late(self):
  with self.assertRaises(c.Rejected):c.terminal(self.v[0],self.v[1],'d'*64,3000,self.v[2])
 def test_23_observers_in_workload_census(self):self.assertTrue(c.census(self.v[0],self.v[3]))
 def test_24_workload_remains(self):self.reject(lambda v:v[3].update(workloadRemaining=[11]))
 def test_25_shutdown_before_receipt(self):
  m=c.Machine(self.v[0]['binding'])
  with self.assertRaises(c.Rejected):m.advance('OBSERVER_SHUTDOWN_ALLOWED','launcher',dict(binding=m.binding))
  self.assertEqual(m.state,'REJECTED')
 def test_26_shutdown_before_census(self):
  m=c.Machine(self.v[0]['binding']);m.state='TERMINAL_EVIDENCE_COMPLETE'
  with self.assertRaises(c.Rejected):m.advance('OBSERVER_SHUTDOWN_ALLOWED','launcher',dict(binding=m.binding))
 def test_27_application_drain(self):self.reject(lambda v:v[4]['observers']['application'].update(drained=False))
 def test_28_detail_drain(self):self.reject(lambda v:v[4]['observers']['detail'].update(drained=False))
 def test_29_authority_drain(self):self.reject(lambda v:v[4]['observers']['authority'].update(drained=False))
 def test_30_launcher_crash(self):self.reject(lambda v:v[4].update(launcherExitCode=1))
 def test_31_controller_unavailable(self):self.reject(lambda v:v[5].clear())
 def test_32_launcher_exit_unproven(self):self.reject(lambda v:v[4].update(launcherExitVerified=False))
 def test_33_census_unavailable(self):self.reject(lambda v:v[5].update(available=False))
 def test_34_census_unknown(self):self.reject(lambda v:v[5].update(unknown=[10]))
 def test_35_process_remains(self):self.reject(lambda v:v[5].update(matchingProcesses=[10]))
 def test_36_trace_remains(self):self.reject(lambda v:v[5].update(traceSessions=['J6-left']))
 def test_37_shutdown_deadline(self):self.reject(lambda v:v[4].update(completedQpc=3000))
 def test_38_census_deadline(self):self.reject(lambda v:v[5].update(completedQpc=3000))
 def test_39_deadline_reset_collector(self):self.reject(lambda v:v[0].update(deadlineQpc=4000))
 def test_40_deadline_reset_receipt(self):self.reject(lambda v:v[1].update(deadlineQpc=4000))
 def test_41_later_contradiction(self):self.reject(lambda v:v[4].update(authoritativeContradictions=['lost']))
 def test_42_complete(self):self.assertTrue(evaluate(self.v))
 def test_43_failed_replay(self):
  m=c.Machine(self.v[0]['binding'])
  with self.assertRaises(c.Rejected):m.reject('preserved failed run')
  with self.assertRaises(c.Rejected):m.advance('RUN_ACTIVE','launcher',dict(binding=m.binding))
  self.assertEqual(m.state,'REJECTED')
 def test_duplicate_key(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'x.json';p.write_text('{"a":1,"a":2}')
   with self.assertRaises(c.Rejected):c.load(p)
 def test_late_handoff(self):self.reject(lambda v:v[1]['rows'][1].update(handleAttemptQpc=1021))
 def test_late_creation_verification(self):self.reject(lambda v:v[1]['rows'][1].update(imageBeginQpc=1021,imageEndQpc=1022))
 def test_local_durability(self):self.reject(lambda v:v[0].update(localDurable=False))
 def test_authority_durability(self):self.reject(lambda v:v[4].update(durableComplete=False))
 def test_receipt_cannot_accept(self):self.reject(lambda v:v[1].update(acceptance=True))
 def test_shutdown_order(self):self.reject(lambda v:v[4]['observers']['authority'].update(exitQpc=1400))
 def test_source_binding(self):self.reject(lambda v:v[1]['binding'].update(sourceManifestSHA256='f'*64))
 def test_phase_schema(self):self.reject(lambda v:v[0].update(state='PASS'))
 def test_handle_closed_final(self):self.reject(lambda v:v[4].update(allRequiredHandlesClosed=False))
 def test_exclusive_publication(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'receipt.json';c.write_once(p,{'first':True});old=p.read_bytes()
   with self.assertRaises(OSError):c.write_once(p,{'second':True})
   self.assertEqual(old,p.read_bytes())
if __name__=='__main__':unittest.main(verbosity=2)
