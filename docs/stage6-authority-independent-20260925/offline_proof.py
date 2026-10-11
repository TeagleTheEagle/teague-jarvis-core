import pathlib,json,hashlib,re,unittest
R=pathlib.Path(__file__).parent;C=R/'candidate';B=json.loads((R/'before.json').read_text());S=pathlib.Path(B['predecessor'])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=b'p->LogFileMode=EVENT_TRACE_REAL_TIME_MODE;';new=b'p->LogFileMode=EVENT_TRACE_REAL_TIME_MODE|EVENT_TRACE_INDEPENDENT_SESSION_MODE;'
def save(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2)
def expr(p):return re.search(r'p->LogFileMode=([^;]+);',p.read_text()).group(1)
def reject(p):return re.search(r'return (!wrote\|\|!requested\|\|stop\|\|faults\|\|p->EventsLost\|\|p->RealTimeBuffersLost\?95:0);',p.read_text()).group(1)
class Isolation(unittest.TestCase):
 def test_01_exact_single_source_delta(self):self.assertEqual((C/'authority_trace_v3.cpp').read_bytes(),(S/'authority_trace_v3.cpp').read_bytes().replace(old,new))
 def test_02_authority_flag_present_once(self):self.assertEqual((C/'authority_trace_v3.cpp').read_text().count('EVENT_TRACE_INDEPENDENT_SESSION_MODE'),1)
 def test_03_detailed_flag_absent(self):self.assertNotIn('EVENT_TRACE_INDEPENDENT_SESSION_MODE',(C/'startup_trace.cpp').read_text())
 def test_04_authority_remaining_settings(self):
  for field in ('BufferSize','MinimumBuffers','MaximumBuffers','FlushTimer','ClientContext','EnableFlags'):
   pattern=r'\b'+field+r'=[^;]*;';self.assertEqual(re.findall(pattern,(C/'authority_trace_v3.cpp').read_text()),re.findall(pattern,(S/'authority_trace_v3.cpp').read_text()))
 def test_05_detailed_binary_source(self):
  for name in ('J6StartupTrace.exe','startup_trace.cpp'):self.assertEqual(sha(C/name),sha(S/name))
 def test_06_callback_body_unchanged(self):
  for name in ('authority_trace_v3.cpp','startup_trace.cpp'):
   self.assertEqual((C/name).read_text().split('int wmain')[0],(S/name).read_text().split('int wmain')[0])
 def test_07_diagnostic_files_unchanged(self):
  for x in B['files']:
   if 'witness' in x['name']:self.assertEqual(sha(C/x['name']),x['sha256'])
 def test_08_handoff_unchanged(self):
  for x in B['files']:
   if 'handoff' in x['name'].lower():self.assertEqual(sha(C/x['name']),x['sha256'])
 def test_09_loss_predicates_unchanged(self):
  for n in ('authority_trace_v3.cpp','startup_trace.cpp'):self.assertEqual(reject(C/n),reject(S/n))
 def test_10_checker_finalizer_unchanged(self):
  for x in B['files']:
   if 'check' in x['name'] or 'final' in x['name']:self.assertEqual(sha(C/x['name']),x['sha256'])
 def test_11_telemetry_unchanged(self):
  for x in B['files']:
   if 'telemetry' in x['name'] or 'loss_' in x['name']:self.assertEqual(sha(C/x['name']),x['sha256'])
 def test_12_launcher_deadline_policy_unchanged(self):
  for x in B['files']:
   if pathlib.Path(x['name']).suffix in ('.py','.ps1','.cs','.json'):self.assertEqual(sha(C/x['name']),x['sha256'])
 def test_13_only_three_artifacts_differ(self):
  changed={x['name'] for x in B['files'] if sha(C/x['name'])!=x['sha256']}
  self.assertEqual(changed,{'authority_trace_v3.cpp','authority_trace_v3.obj','J6AuthorityTraceV3.exe'})
 def test_14_dataset_exact(self):
  rows=[x for x in B['files'] if pathlib.PureWindowsPath(x['name']).parts[0]=='small-synthetic']
  self.assertEqual(len(rows),12);self.assertEqual(sum(x['bytes'] for x in rows),786432)
  for x in rows:self.assertEqual(sha(C/x['name']),x['sha256'])
 def test_15_predecessor_preserved(self):
  for x in B['files']:
   p=S/x['name'];self.assertEqual((sha(p),p.stat().st_size,p.stat().st_mtime_ns),(x['sha256'],x['bytes'],x['mtimeNs']))
 def test_16_historical_archives_preserved(self):
  for x in B['historicalArchives']:self.assertEqual(sha(pathlib.Path(x['archive'])),x['sha256'])
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Isolation))
 save(R/'offline-tests-result.json',dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),status='PASS' if result.wasSuccessful() else 'FAIL'))
 if not result.wasSuccessful():raise SystemExit(1)
 # Compile-only SDK proof uses the exact extracted configuration/rejection expressions.
 text='#define WIN32_LEAN_AND_MEAN\n#include <windows.h>\n#include <evntrace.h>\n'
 text+=f'constexpr ULONG oldMode={expr(S/"authority_trace_v3.cpp")};\nconstexpr ULONG newMode={expr(C/"authority_trace_v3.cpp")};\nconstexpr ULONG detailMode={expr(C/"startup_trace.cpp")};\n'
 text+='static_assert(oldMode==0x100);\nstatic_assert(newMode==0x08000100);\nstatic_assert((oldMode^newMode)==EVENT_TRACE_INDEPENDENT_SESSION_MODE);\nstatic_assert((detailMode&EVENT_TRACE_INDEPENDENT_SESSION_MODE)==0);\n'
 text+='struct Counters {ULONG EventsLost; ULONG RealTimeBuffersLost;};\n'
 for role,name in [('authority','authority_trace_v3.cpp'),('detailed','startup_trace.cpp')]:
  text+=f'constexpr int {role}(ULONG lost){{Counters c{{lost,0}};auto p=&c;bool wrote=true,requested=true;ULONG stop=0,faults=0;return {reject(C/name)};}}\n'
  text+=f'static_assert({role}(0)==0);\nstatic_assert({role}(1)==95);\nstatic_assert({role}(16)==95);\nstatic_assert({role}(136196)==95);\n'
 (R/'configuration-proof.cpp').write_text(text)
