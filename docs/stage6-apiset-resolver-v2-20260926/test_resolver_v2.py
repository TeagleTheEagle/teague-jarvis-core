import unittest,struct,tempfile,json,copy
from pathlib import Path
from resolver_v2 import *

HERE=Path(__file__).resolve().parent
PREV=HERE.parent/'stage6-prospective-pair-20260926'
NAME='api-ms-win-core-errorhandling-l1-1-3'
REQUEST='api-ms-win-core-errorhandling-l1-1-0.dll'
UNAVAILABLE=lambda _: {'status':'UNAVAILABLE'}

def fixture(entries=None):
 entries=entries or [(NAME,[('', 'example-default.dll')])]
 count=len(entries);buf=bytearray(28+count*24+count*8);entryoff=28;hashoff=28+count*24
 struct.pack_into('<7I',buf,0,6,0,0,count,entryoff,hashoff,31)
 def text(s):
  raw=s.encode('utf-16le');off=len(buf);buf.extend(raw);return off,len(raw)
 hashes=[]
 for i,(name,values) in enumerate(entries):
  no,nl=text(name);hashed=name.rfind('-')*2;vo=len(buf);buf.extend(bytes(20*len(values)))
  for j,(alias,host) in enumerate(values):
   ao,al=text(alias);ho,hl=text(host);struct.pack_into('<5I',buf,vo+j*20,0,ao,al,ho,hl)
  struct.pack_into('<6I',buf,entryoff+24*i,0,no,nl,hashed,vo,len(values))
  hashes.append((hash_name(name[:hashed//2],31),i))
 for i,(h,index) in enumerate(sorted(hashes)):struct.pack_into('<2I',buf,hashoff+8*i,h,index)
 struct.pack_into('<I',buf,4,len(buf));return bytes(buf)

class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.folder=Path(tempfile.mkdtemp(prefix='offline-tests-',dir=HERE)).resolve()
  assert cls.folder.is_relative_to(HERE)
  cls.importer=cls.folder/'consumer.dll';cls.importer.write_bytes(b'synthetic importer')
 def schema(self,entries=None):return SchemaV6(fixture(entries))
 def resolve(self,contract=REQUEST,entries=None,importer='consumer.dll',query=UNAVAILABLE):
  return resolve_contract(self.schema(entries),contract,importer,query)
 def test_01_exact_name_preserved(self):self.assertEqual(self.resolve()['exact_contract'],REQUEST)
 def test_02_case_normalization(self):self.assertEqual(self.resolve(REQUEST.upper())['normalized_name'],REQUEST[:-4])
 def test_03_optional_extension(self):self.assertEqual(self.resolve(REQUEST[:-4])['host'],self.resolve()['host'])
 def test_04_import_kind(self):
  for kind in ['NORMAL','DELAY']:
   self.assertEqual(import_evidence(self.importer,{'exact_name':REQUEST,'import_kind':kind,'symbols':[]},'BUILD_TOOL_RUNTIME_DEPENDENCY')['import_kind'],kind)
 def test_05_current_revision_case(self):self.assertEqual(self.resolve()['selection']['selected_entry']['name'],NAME)
 def test_06_hashed_fields(self):
  e=self.schema().entries[0];self.assertEqual(e['hashed_name'],'api-ms-win-core-errorhandling-l1-1');self.assertEqual(e['hashed_length'],68)
 def test_07_default(self):self.assertEqual(self.resolve()['host'],'example-default.dll')
 def test_08_importer_override(self):
  self.assertEqual(self.resolve(entries=[(NAME,[('', 'default.dll'),('consumer.dll','override.dll')])])['host'],'override.dll')
 def test_09_unmatched_importer_default(self):
  self.assertEqual(self.resolve(entries=[(NAME,[('', 'default.dll'),('other.dll','override.dll')])])['host'],'default.dll')
 def test_10_absent_contract(self):
  with self.assertRaises(Unresolved):self.resolve('api-ms-win-other-l1-1-0.dll')
 def test_11_ambiguous_entry(self):
  with self.assertRaises(Ambiguous):self.resolve(entries=[(NAME,[('','a.dll')]),(NAME,[('','b.dll')])])
 def test_12_empty_mapping(self):
  with self.assertRaises(Unresolved):self.resolve(entries=[(NAME,[('','')])])
 def test_13_malformed_entry(self):
  b=bytearray(fixture());struct.pack_into('<I',b,28+12,3)
  with self.assertRaises(ProvenanceError):SchemaV6(b)
 def test_14_out_of_bounds(self):
  b=bytearray(fixture());struct.pack_into('<I',b,28+4,0xfffffff0)
  with self.assertRaises(ProvenanceError):SchemaV6(b)
 def test_15_unsupported_version(self):
  b=bytearray(fixture());struct.pack_into('<I',b,0,4)
  with self.assertRaises(SchemaUnsupported):SchemaV6(b)
 def test_16_query_success(self):self.assertEqual(self.resolve(query=lambda _: {'status':'SUCCESS','host':'example-default.dll'})['method'],'DOCUMENTED_QUERY_SCHEMA_AGREEMENT')
 def test_17_query_unavailable(self):self.assertEqual(self.resolve()['documented_query']['status'],'UNAVAILABLE')
 def test_18_query_notimpl(self):self.assertEqual(self.resolve(query=lambda _: {'status':'E_NOTIMPL','hresult':0x80004001})['method'],'OFFLINE_SCHEMA_V6_HASH_INDEX')
 def test_19_hash_corruption_rejected(self):
  b=bytearray(fixture());struct.pack_into('<I',b,52,0)
  with self.assertRaises(ProvenanceError):SchemaV6(b)
 def test_20_forward_destination_separate(self):
  r=self.resolve();g=partition([{'classification':'CORROBORATIVE_ONLY','function_destination':'different.dll'},{'classification':'BUILD_TOOL_RUNTIME_DEPENDENCY','resolution':r}])
  self.assertEqual(g['BUILD_TOOL_RUNTIME_DEPENDENCY'][0]['resolution']['host'],'example-default.dll')
 def test_21_physical_resolves(self):
  f=self.folder/'ordinary.dll';f.write_bytes(b'ordinary fixture');self.assertEqual(resolve_physical('ordinary.dll',self.importer,self.folder,self.folder),identity(f))
 def test_22_missing_physical_fails(self):
  with self.assertRaises(Unresolved):resolve_physical('missing.dll',self.importer,self.folder,self.folder)
 def test_23_schema_drift(self):
  f=self.folder/'schema.bin';f.write_bytes(fixture());r=identity(f);f.write_bytes(b'changed')
  with self.assertRaises(ProvenanceError):verify_identity(r)
 def test_24_host_hash_drift(self):
  f=self.folder/'host.dll';f.write_bytes(b'first');r=identity(f);f.write_bytes(b'second')
  with self.assertRaises(ProvenanceError):verify_identity(r)
 def test_25_os_binding(self):
  expected=json.loads((HERE/'host-before.json').read_text());check_binding(host_binding(expected['schema_path']),expected)
  other=copy.deepcopy(expected);other['os']['UBR']+=1
  with self.assertRaises(ProvenanceError):check_binding(expected,other)
 def test_26_tool_runtime_class(self):self.assertEqual(import_evidence(self.importer,{'exact_name':REQUEST},'BUILD_TOOL_RUNTIME_DEPENDENCY')['classification'],'BUILD_TOOL_RUNTIME_DEPENDENCY')
 def test_27_output_class(self):self.assertEqual(import_evidence(self.importer,{'exact_name':REQUEST},'OUTPUT_RUNTIME_DEPENDENCY')['classification'],'OUTPUT_RUNTIME_DEPENDENCY')
 def test_28_no_input_enlargement(self):
  rows=[import_evidence(self.importer,{'exact_name':REQUEST},c) for c in ['BUILD_TOOL_RUNTIME_DEPENDENCY','OUTPUT_RUNTIME_DEPENDENCY']]
  self.assertEqual(partition(rows)['BUILD_INPUT_REQUIRED'],[])
 def test_29_deterministic(self):self.assertEqual(json.dumps(self.resolve(),sort_keys=True),json.dumps(self.resolve(),sort_keys=True))
 def test_30_predecessor_unchanged(self):
  rows=json.loads((PREV/'archive-manifest.json').read_text())['members']
  for r in rows:self.assertEqual(sha(PREV/r['name']),r['sha256'])
 def test_31_query_error_no_fallback(self):
  with self.assertRaises(Unresolved):self.resolve(query=lambda _: {'status':'ERROR','hresult':0x80004005})
 def test_32_query_contradiction(self):
  with self.assertRaises(Unresolved):self.resolve(query=lambda _: {'status':'SUCCESS','host':'wrong.dll'})
 def test_33_duplicate_default(self):
  with self.assertRaises(Ambiguous):self.resolve(entries=[(NAME,[('','a.dll'),('','b.dll')])])
 def test_34_duplicate_override(self):
  with self.assertRaises(Ambiguous):self.resolve(entries=[(NAME,[('','a.dll'),('consumer.dll','b.dll'),('CONSUMER.DLL','b.dll')])])
 def test_35_empty_override_no_fallback(self):
  with self.assertRaises(Unresolved):self.resolve(entries=[(NAME,[('','a.dll'),('consumer.dll','')])])
 def test_36_query_with_override(self):
  r=self.resolve(entries=[(NAME,[('','a.dll'),('consumer.dll','b.dll')])],query=lambda _: {'status':'SUCCESS','host':'a.dll'})
  self.assertEqual(r['host'],'b.dll');self.assertEqual(r['method'],'DOCUMENTED_DEFAULT_WITH_SCHEMA_IMPORTER_OVERRIDE')
 def test_37_no_nearest_matching(self):
  with self.assertRaises(Unresolved):self.resolve('api-ms-win-core-errorhandling-l1-2-0.dll')
 def test_38_bad_module_path(self):
  with self.assertRaises(ProvenanceError):self.resolve(entries=[(NAME,[('','../escape.dll')])])
 def test_39_unsupported_name(self):
  for name in ['../'+REQUEST,'api-win-alias','plain.dll','api-x-l1-1-0.dll.dll']:
   with self.assertRaises(Unresolved):self.resolve(name)
 def test_40_actual_schema_and_ucrt(self):
  binding=json.loads((HERE/'host-before.json').read_text());schema=SchemaV6.from_file(binding['schema_path'])
  row=next(x for x in PE(Path(binding['schema_path']).parent/'ucrtbase.dll').imports() if x['exact_name'].lower()==REQUEST)
  self.assertEqual(row['import_kind'],'NORMAL');self.assertIn({'name':'GetLastError'},row['symbols'])
  result=resolve_contract(schema,REQUEST,'ucrtbase.dll',UNAVAILABLE)
  self.assertEqual(result['selection']['selected_entry']['name'],NAME)
  self.assertEqual(result['selection']['selected_value']['alias'],'')
  self.assertEqual(result['host'].lower(),'kernelbase.dll') # Recorded host-specific regression, not resolver mapping.

if __name__=='__main__':unittest.main(verbosity=2)
