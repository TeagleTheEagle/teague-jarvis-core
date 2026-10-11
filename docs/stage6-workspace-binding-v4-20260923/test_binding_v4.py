"""Offline fixture coverage. Does not start tracers, probes, workers or ETW sessions."""
import unittest,unittest.mock as m,pathlib,json,os,sys,copy,uuid,hashlib,zipfile,subprocess,ctypes
import workspace_binding_v4 as b
from workspace import CODE
import evidence_format_v4 as ef
import small_finalize_v4 as fin
import failure_preserve_v4 as fp
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.runtime=b.runtime_policy()
  os.environ['PATH']=os.pathsep.join(dict.fromkeys(str(pathlib.Path(x['path']).parent) for x in cls.runtime['executables'].values()))
  os.environ['PSModulePath']=os.pathsep.join(cls.runtime['moduleRoots'])
  os.environ['PYTHONNOUSERSITE']='1'
  for k in ('PYTHONHOME','PYTHONPATH','PYTHONSTARTUP'):os.environ.pop(k,None)
  from small_binding_v3 import make
  cls.root=make('normal');cls.binding=b.prepare(cls.root)
  cls.history=CODE/('offline-fixtures-v4-'+uuid.uuid4().hex);cls.history.mkdir(exist_ok=False)
  cls.old=cls.history/'prior-candidate';cls.old.mkdir();(cls.old/'J6OwnedEntry.dll').write_bytes(b'old never load')
 def fixture(self):
  root=CODE/('protected-'+uuid.uuid4().hex);root.mkdir();(root/'detail').mkdir();(root/'temp').mkdir()
  for rel,(ch,ready,result) in ef.SIDECARS.items():
   session='TEST-'+ch+'-'+root.name
   b.write(root/ready,dict(session=session,frequency=10000000))
   b.write(root/result,dict(session=session,rows=[]))
   b.write(root/rel,dict(schema='stage6-loss-diagnostic-v2',diagnosticOnly=True,acceptanceSealed=False,run=root.name,session=session,channel=ch,frequency=10000000,samples=[],errors=9))
  b.write(root/b.NAME,dict(self.binding,run=root.name,evidenceRoot=str(root)))
  return root
 def bad(self,fn,reason=None):
  with self.assertRaises(ValueError) as e:fn()
  if reason:self.assertIn(reason,str(e.exception))
 def changed(self,key,value):
  v=copy.deepcopy(self.binding);v[key]=value
  with m.patch.object(b,'read',side_effect=lambda p:v if pathlib.Path(p)==self.root/b.NAME else self.original_read(p)):
   self.bad(lambda:b.verify(self.root),'BINDING')
 def setUp(self):self.original_read=b.read
 def test_01_missing_fresh_dependency_old_exists(self):
  self.assertTrue((self.old/'J6OwnedEntry.dll').exists());self.bad(lambda:b.local('absent.dll'),'MISSING')
 def test_02_missing_dataset_old_available(self):
  with m.patch.object(pathlib.Path,'is_file',return_value=False):self.bad(lambda:b.local('small-synthetic/00.bin'),'MISSING')
 def test_03_missing_local_dll_old_available(self):
  with m.patch.object(pathlib.Path,'is_file',return_value=False):self.bad(b.dll_path,'MISSING')
 def test_04_stale_path(self):
  self.bad(lambda:b.environment(self.runtime,env={'PATH':r'D:\JARVIS-STAGE6-LIVE\old\code'}),'OLD_WORKSPACE')
 def test_05_old_cwd(self):self.bad(lambda:b.environment(self.runtime,cwd=r'D:\JARVIS-STAGE6-LIVE\old\code'),'PATH_OUTSIDE')
 def test_06_old_environment(self):
  for key in ('TEMP','TMP','PYTHONHOME','PYTHONPATH','PSModulePath'):
   with self.subTest(key=key):self.bad(lambda:b.environment(self.runtime,env={key:r'D:\JARVIS-STAGE6-LIVE\old\code'}),'OLD_WORKSPACE')
 def test_07_old_manifest_path(self):self.bad(lambda:b.local(r'D:\JARVIS-STAGE6-LIVE\old\code\x.py'),'MANIFEST_ESCAPE')
 def test_08_reparse_escape(self):
  f=CODE/'J6OwnedEntry.dll';real=f.lstat()
  with m.patch.object(pathlib.Path,'lstat',return_value=type('Stat',(),{'st_file_attributes':real.st_file_attributes|0x400})()):self.bad(lambda:b.safe(f,CODE),'REPARSE')
 def test_09_candidate_hash(self):
  with m.patch.object(b,'sha',return_value='0'*64):self.bad(b.manifest,'SOURCE_HASH')
 def test_10_unapproved_root(self):self.bad(lambda:b.safe(pathlib.Path('C:/unapproved/x'),CODE),'PATH_OUTSIDE')
 def test_11_missing_record(self):
  root=CODE/('protected-'+uuid.uuid4().hex);root.mkdir();self.bad(lambda:b.verify(root),'MISSING_WORKSPACE')
 def test_12_schema(self):
  with m.patch.object(b,'read',return_value=dict(schema='old')):self.bad(lambda:b.verify(self.root),'BINDING_SCHEMA')
 def test_13_manifest_binding(self):self.changed('candidateManifestSHA256','0'*64)
 def test_14_dataset_binding(self):self.changed('datasetManifestSHA256','0'*64)
 def test_15_missing_runtime_identity(self):
  v=copy.deepcopy(self.runtime);v['executables']['python'].pop('version')
  with m.patch.object(b,'read',return_value=v):self.bad(b.runtime_policy,'RUNTIME_IDENTITY')
 def test_16_wrong_dll_hash(self):
  with m.patch.object(b,'sha',return_value='0'*64):self.bad(b.dll_path,'DLL_HASH')
 def test_17_loaded_module_mismatch(self):self.bad(lambda:b.assert_loaded(self.old/'J6OwnedEntry.dll'),'LOADED_MODULE')
 def test_18_sidecar_wrong_run(self):
  r=self.fixture();v=b.read(r/'loss-diagnostic-v2.json');v['run']='old';(r/'loss-diagnostic-v2.json').write_text(json.dumps(v));self.bad(lambda:ef.inspect(r),'SIDECAR_RUN')
 def test_19_sidecar_schema(self):
  r=self.fixture();v=b.read(r/'loss-diagnostic-v2.json');v['schema']='unknown';(r/'loss-diagnostic-v2.json').write_text(json.dumps(v));self.bad(lambda:ef.inspect(r),'SIDECAR_SCHEMA')
 def test_20_unknown_artifact(self):
  r=self.fixture();b.write(r/'loss-diagnostic-extra.json',{});self.bad(lambda:fin.inventory(r),'UNEXPECTED_ARTIFACT')
 def test_21_pass_missing_sidecar(self):
  r=self.fixture();(r/'detail/loss-diagnostic-v2.json').rename(r/'detail/absent.fixture')
  with m.patch('completed_v3.verify_complete',return_value={}),m.patch.object(fin,'verify_workspace',return_value=self.binding):self.bad(lambda:fin.finalize(r),'MISSING_SIDECAR')
  self.assertFalse((r/'v3-seal.json').exists())
 def preserve_fixture(self,r):
  policy=fp.cli_policy(r.name)
  clean=lambda _:dict(run=r.name,evidenceRoot=str(r),available=True,processes=[],traces=[],unknown=[],completedQpc=1,frequency=10000000)
  instances=lambda _:dict(clean=True,remaining=[],unknown=[],knownInstanceCount=0)
  failure=dict(classification='FAILED',reason='OFFLINE_FIXTURE_FIRST_FAILURE',qpc=1)
  with m.patch.object(b,'verify',return_value=self.binding):
   result=fp.preserve(r,policy,pathlib.Path(policy['preservationRoot']),failure,census=clean,instances=instances)
  return result,b.read(pathlib.Path(result['directory'])/'FAILURE-MANIFEST.json')
 def test_22_fail_missing_sidecar_explicit(self):
  r=self.fixture();(r/'detail/loss-diagnostic-v2.json').rename(r/'detail/missing.fixture');result,v=self.preserve_fixture(r)
  self.assertFalse(v['acceptance_seal']);self.assertFalse(v['archiveComplete']);self.assertIn('detail/loss-diagnostic-v2.json',v['missingArtifacts']);self.assertTrue(v['firstFailureObserved']['diagnosticAdmission']['errors'])
 def test_23_historical_input(self):
  v=copy.deepcopy(self.binding);v['entryPoints']=['analyze_medium.py']
  with m.patch.object(b,'read',side_effect=lambda p:v if pathlib.Path(p)==self.root/b.NAME else self.original_read(p)):self.bad(lambda:b.verify(self.root),'BINDING_MISMATCH')
 def test_24_old_preservation(self):
  v=b.policy();v['preservationRoot']=r'D:\JARVIS-STAGE6-LIVE\old\preservation'
  with m.patch.object(b,'read',return_value=v):self.bad(b.policy,'OLD_PRESERVATION')
 def test_25_ambient_tool(self):
  for tool in ('logman','powershell'):
   with self.subTest(tool=tool):self.bad(lambda:b.environment(self.runtime,env={},search=lambda n:'C:/stale/'+n if n==tool+'.exe' else None),'AMBIENT_TOOL')
 def test_26_old_never_consulted(self):
  opened=[];original=pathlib.Path.open
  def track(p,*args,**kwargs):opened.append(str(p));return original(p,*args,**kwargs)
  with m.patch.object(pathlib.Path,'open',track):v=b.verify(self.root)
  self.assertEqual(v['candidateRoot'],str(CODE));self.assertFalse(any(str(self.old) in x or '7f204e14c90a497a8476be0e9927e074' in x for x in opened))
 def test_27_deadline_unchanged(self):
  import coordination_v3 as c
  self.assertEqual(b.read(self.root/'small-declaration-v3.json')['cleanup'],20.0)
  original=(CODE/'small_launch_v3.ps1').read_text();new=(CODE/'small_launch_v4.ps1').read_text()
  self.assertEqual(original[original.index('$kernel=$null;'):],new[new.index('$kernel=$null;'):])
 def test_positive_dataset_local(self):
  self.assertEqual(len(self.binding['dataset']),12);self.assertEqual(sum(x['bytes'] for x in self.binding['dataset']),786432);self.assertTrue(all(pathlib.Path(x['path']).is_relative_to(CODE) for x in self.binding['dataset']))
 def test_positive_native_dll_load_only(self):
  dll=b.load_dll();self.assertTrue(dll._handle);self.assertEqual(b.sha(b.dll_path()),b.DLL_SHA)
 def test_positive_runtime_real(self):self.assertEqual(b.runtime_policy(),self.runtime)
 def test_positive_binding(self):self.assertEqual(b.verify(self.root),self.binding)
 def test_positive_diagnostic_not_authority(self):
  v=ef.inspect(self.fixture());self.assertTrue(v['complete']);self.assertFalse(v['acceptanceAuthority'])
 def test_positive_pass_archive_integration(self):
  r=self.fixture();b.write(r/'launcher-identity.json',dict(pid=1,created='1'))
  # Unit integration only: lifecycle predicates are controlled fixture dependencies,
  # never evidence that a real collector/observer completed.
  with m.patch('completed_v3.verify_complete',return_value={}),m.patch('small_check_v3.check',return_value=dict(status='SMALL_NORMAL_PASS_PENDING_ARCHIVE')),m.patch.object(fin,'verify_workspace',return_value=self.binding),m.patch.object(fin,'no_live_identities'):
   value=fin.finalize(r)
  self.assertEqual(value['state'],'ACCEPTED')
  with zipfile.ZipFile(r/'v3-evidence.zip') as z:
   for name in ef.SIDECARS:self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(),b.sha(r/name))
   self.assertIn(b.NAME,z.namelist())
 def test_positive_failure_archive_integration(self):
  r=self.fixture();result,v=self.preserve_fixture(r)
  self.assertFalse(v['acceptance_seal']);self.assertEqual(v['firstFailureObserved']['reason'],'OFFLINE_FIXTURE_FIRST_FAILURE')
  self.assertTrue(v['firstFailureObserved']['diagnosticAdmission']['complete']);self.assertEqual({x['path'] for x in v['preserved']} & set(ef.SIDECARS),set(ef.SIDECARS))
  self.assertTrue(result['verifiedArchiveMembers']>2)
 def test_failure_never_pass(self):
  r=self.fixture();b.write(r/'rejected-v3.json',dict(state='REJECTED'))
  self.bad(lambda:fin.finalize(r),'PRESERVED_FAILURE');self.assertFalse((r/'v3-seal.json').exists())
 def test_sidecar_wrong_session(self):
  r=self.fixture();v=b.read(r/'loss-diagnostic-v2.json');v['session']='other';(r/'loss-diagnostic-v2.json').write_text(json.dumps(v));self.bad(lambda:ef.inspect(r),'SIDECAR_SESSION')
 def test_no_decl_schema_change(self):self.assertEqual(set(b.read(self.root/'small-declaration-v3.json')),{'schema','run','code','source','sourceManifestSHA256','case','inventorySHA256','files','bytes','heartbeat','probe','observer','campaign','kernelCapture','cleanup','coordination','channels','classes'})
 def test_runtime_component_tamper(self):
  with m.patch.object(b,'sha',return_value='0'*64):self.bad(b.runtime_policy,'RUNTIME_HASH')
 def test_import_escape(self):self.bad(lambda:b.environment(self.runtime,env={},imports=[r'C:\unapproved\site-packages']),'PYTHON_IMPORT_ROOT')
 def test_child_environment_no_global_mutation(self):
  before=dict(os.environ);env=b.child_environment(self.root);self.assertEqual(before,dict(os.environ));self.assertEqual(env['TEMP'],str(self.root/'temp'));self.assertEqual(env['PSModulePath'],os.pathsep.join(self.runtime['moduleRoots']))
 def test_real_junction_rejection(self):
  link=self.history/('junction-'+uuid.uuid4().hex)
  p=subprocess.run([r'C:\Windows\System32\cmd.exe','/d','/c','mklink','/J',str(link),str(self.old)],capture_output=True,text=True)
  self.assertEqual(p.returncode,0,p.stderr);self.assertTrue(link.is_junction());self.bad(lambda:b.safe(link/'J6OwnedEntry.dll',CODE),'REPARSE')
if __name__=='__main__':unittest.main(verbosity=2)
