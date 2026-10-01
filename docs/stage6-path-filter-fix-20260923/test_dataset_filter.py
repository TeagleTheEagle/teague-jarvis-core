"""Focused offline tests only. Extract one pure validation function; no preflight execution."""
import ast,pathlib,json,hashlib,copy,unittest,uuid,shutil,sys,subprocess,os
from unittest import mock
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'before.json').read_text())['candidate'])
sys.path.insert(0,str(C));import workspace_binding_v4 as b
tree=ast.parse((R/'preflight.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='dataset_records')
ns=dict(pathlib=pathlib,b=b,sha=b.sha);exec(compile(ast.Module(body=[fn],type_ignores=[]),str(R/'preflight.py'),'exec'),ns)
validate=ns['dataset_records']
ROWS=json.loads((C/'small-source-v3.json').read_text())
DATA=[r for r in ROWS if pathlib.PureWindowsPath(r['name']).parts[0]=='small-synthetic']
FIX=R/('fixtures-'+uuid.uuid4().hex);FIX.mkdir()
class Tests(unittest.TestCase):
 def fixture(self,omit=None,change=None):
  root=FIX/(self._testMethodName+'-'+uuid.uuid4().hex);d=root/'small-synthetic';d.mkdir(parents=True)
  for row in DATA:
   name=pathlib.PureWindowsPath(row['name']).name
   if name==omit:continue
   data=(C/'small-synthetic'/name).read_bytes()
   if change and name==change[0]:data=change[1](data)
   (d/name).write_bytes(data)
  return root,copy.deepcopy(DATA)
 def fail(self,rows,root,reason):
  with self.assertRaisesRegex(ValueError,reason):validate(rows,root)
 def test_01_canonical_windows_paths_pass(self):
  root,rows=self.fixture();self.assertEqual(validate(rows,root),rows)
 def test_02_forward_slashes_explicit_comparison_only(self):
  root,rows=self.fixture()
  for r in rows:r['name']=r['name'].replace('\\','/')
  before=copy.deepcopy(rows);self.assertEqual(validate(rows,root),before);self.assertEqual(rows,before)
 def test_03_mixed_separators_deterministic(self):
  root,rows=self.fixture()
  for r in rows[::2]:r['name']=r['name'].replace('\\','/')
  self.assertEqual(validate(rows,root),rows)
  rows[0]['name']='small-synthetic/\\00.bin';self.fail(rows,root,'MALFORMED')
 def test_04_missing_file_fails(self):
  root,rows=self.fixture(omit='00.bin');self.fail(rows,root,'DISK_INVENTORY')
 def test_05_wrong_content_hash_fails(self):
  root,rows=self.fixture(change=('00.bin',lambda x:bytes([x[0]^1])+x[1:]));self.fail(rows,root,'DATASET_HASH')
 def test_06_wrong_disk_size_fails(self):
  root,rows=self.fixture(change=('00.bin',lambda x:x[:-1]));self.fail(rows,root,'DATASET_SIZE')
 def test_07_absolute_path_fails(self):
  root,rows=self.fixture()
  for name in (r'C:\data\small-synthetic\00.bin',r'\\server\share\small-synthetic\00.bin',r'\small-synthetic\00.bin','/small-synthetic/00.bin',r'C:small-synthetic\00.bin'):
   with self.subTest(name=name):
    x=copy.deepcopy(rows);x[0]['name']=name;self.fail(x,root,'ABSOLUTE')
 def test_08_traversal_fails(self):
  root,rows=self.fixture()
  for name in ('small-synthetic/../00.bin',r'small-synthetic\..\00.bin',r'..\small-synthetic\00.bin',r'small-synthetic\.\00.bin'):
   with self.subTest(name=name):
    x=copy.deepcopy(rows);x[0]['name']=name;self.fail(x,root,'MALFORMED')
 def test_09_old_workspace_path_fails(self):
  root,rows=self.fixture();rows[0]['name']=r'D:\JARVIS-STAGE6-LIVE\old\code\small-synthetic\00.bin';self.fail(rows,root,'ABSOLUTE')
 def test_10_duplicate_normalized_path_fails(self):
  root,rows=self.fixture()
  for alias in ('small-synthetic/00.bin',r'SMALL-SYNTHETIC\00.BIN',r'small-synthetic\00.bin'):
   with self.subTest(alias=alias):
    x=copy.deepcopy(rows);x.append(dict(rows[0],name=alias));self.fail(x,root,'DUPLICATE_NORMALIZED')
 def test_11_all_twelve_exact_files_pass(self):
  root,rows=self.fixture();result=validate(rows,root);self.assertEqual(len(result),12);self.assertEqual({pathlib.PureWindowsPath(x['name']).name for x in result},{f'{i:02}.bin' for i in range(12)})
 def test_12_total_bytes_exact(self):
  root,rows=self.fixture();self.assertEqual(sum(x['bytes'] for x in validate(rows,root)),786432)
 def test_13_wrong_manifest_size_fails(self):
  root,rows=self.fixture();rows[0]['bytes']=65535;self.fail(rows,root,'DATASET_SIZE')
 def test_14_wrong_manifest_hash_fails(self):
  root,rows=self.fixture();rows[0]['sha256']='0'*64;self.fail(rows,root,'EXPECTED_HASH')
 def test_15_extra_disk_file_fails(self):
  root,rows=self.fixture();(root/'small-synthetic/12.bin').write_bytes(b'extra');self.fail(rows,root,'DISK_INVENTORY')
 def test_16_extra_manifest_file_fails(self):
  root,rows=self.fixture();rows.append(dict(rows[0],name=r'small-synthetic\12.bin'));self.fail(rows,root,'UNEXPECTED_DATASET')
 def test_17_missing_manifest_entry_fails(self):
  root,rows=self.fixture();self.fail(rows[:-1],root,'MANIFEST_COUNT')
 def test_18_malformed_relative_paths_fail(self):
  root,rows=self.fixture()
  for name in ('',r'small-synthetic\\00.bin','small-synthetic/00.bin/','small-synthetic/00.bin.','small-synthetic/00.bin ','small-synthetic/00.bin:stream','small-synthetic/\x00.bin'):
   with self.subTest(name=name):
    x=copy.deepcopy(rows);x[0]['name']=name;self.fail(x,root,'MALFORMED')
 def test_19_missing_local_never_uses_old_copy(self):
  old,_=self.fixture();root,rows=self.fixture(omit='00.bin');self.assertTrue((old/'small-synthetic/00.bin').is_file())
  original=pathlib.Path.open
  def checked(p,*args,**kwargs):
   self.assertFalse(p.is_relative_to(old),'OLD_DATASET_CONSULTED');return original(p,*args,**kwargs)
  with mock.patch.object(pathlib.Path,'open',checked):self.fail(rows,root,'DISK_INVENTORY')
 def test_20_real_junction_escape_rejected(self):
  target,rows=self.fixture();root=FIX/('junction-'+uuid.uuid4().hex);root.mkdir()
  p=subprocess.run([r'C:\Windows\System32\cmd.exe','/d','/c','mklink','/J',str(root/'small-synthetic'),str(target/'small-synthetic')],capture_output=True,text=True)
  self.assertEqual(p.returncode,0,p.stderr);self.assertTrue((root/'small-synthetic').is_junction());self.fail(rows,root,'REPARSE')
 def test_21_real_candidate_read_only(self):
  before=b.sha(C/'small-source-v3.json');result=validate(ROWS,C)
  self.assertEqual(result,DATA);self.assertEqual(b.sha(C/'small-source-v3.json'),before)
 def test_22_only_filter_and_evidence_destination_change(self):
  original=R.parent/'stage6-one-trace-diagnostic-v4-20260923/preflight.py'
  expected=original.read_text().replace(str(original.parent),str(R),1)
  expected=expected.replace(" dataset=[dict(name=x['name'],sha256=x['sha256'],bytes=x['bytes']) for x in rows if x['name'].startswith('small-synthetic/')]",' dataset=dataset_records(rows,C)',1)
  actual=(R/'preflight.py').read_text();snippet=(R/'dataset-filter-snippet.py').read_text()
  self.assertEqual(actual.replace(snippet+'\n','',1),expected)
 def test_23_no_preflight_top_level_executed(self):
  self.assertFalse((R/'preflight.json').exists());self.assertFalse((R/'preflight-failure.json').exists())
 def test_24_hardlinked_dataset_file_rejected(self):
  root,rows=self.fixture(omit='00.bin');external=FIX/('file-'+uuid.uuid4().hex);external.write_bytes((C/'small-synthetic/00.bin').read_bytes());os.link(external,root/'small-synthetic/00.bin');self.fail(rows,root,'LINKED')
if __name__=='__main__':unittest.main(verbosity=2)
