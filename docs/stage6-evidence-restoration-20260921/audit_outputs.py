import pathlib,re,collections
from evidence_io import create_json
R=pathlib.Path(__file__).parent;rows=[]
for dirname in ('stage6-instance-stream-design-20260921','stage6-authoritative-integration-20260921'):
 for p in sorted((R.parent/dirname).iterdir()):
  if p.suffix not in ('.py','.ps1'):continue
  for line,text in enumerate(p.read_text(encoding='utf-8-sig').splitlines(),1):
   # Bounded source audit of writes, not arbitrary project contents.
   if not re.search(r'write_text\(|write_bytes\(|Set-Content|WriteAllText|\.open\([\x27\"](?:[wax]|r\+)|ZipFile\([^\n]*[\x27\"]x[\x27\"]|shutil.copy2\(',text):continue
   classification='UNKNOWN';reason='Review required before reuse'
   if re.search(r"\.open\(['\"]x[b]?['\"]\)|ZipFile\([^\n]*['\"]x['\"]",text):classification='SAFE_EXCLUSIVE_CREATE';reason='Exclusive file/archive creation'
   elif "open('r+b')" in text:classification='SAFE_UNIQUE_RUN_PATH';reason='Durability flush only of just exclusively created archive; no content write at this operation'
   elif 'shutil.copy2' in text or "(code/'trace_sink.hpp').write_text" in text or "(C/'stream_bench.cpp').write_text" in text:classification='SAFE_UNIQUE_RUN_PATH';reason='Destination is within a freshly mkdir-created sacrificial code directory; not finalized historical output'
   elif p.name in ('stream_tests.py','stream-tests-original-driver.py') and ("p.write_bytes" in text or "(root/'manifest.json').write_text" in text):classification='INTENTIONAL_MUTABLE_RUNTIME_FILE';reason='Deliberate corruption of disposable fault-test fixture, not accepted evidence'
   else:classification='UNSAFE_OVERWRITE';reason='write_text/Set-Content replaces finalized-looking result at fixed historical path; driver checkpoints also reuse that path'
   rows.append(dict(file=str(p),line=line,operation=text.strip(),classification=classification,reason=reason,disposition='FROZEN HISTORICAL SCRIPT; DO NOT REEXECUTE' if classification=='UNSAFE_OVERWRITE' else 'Historical source preserved'))
# Existing monitor files inspected by name only; no monitor execution or modification.
monitor=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\f469b94b665e4808af1c5bb6aa46b207\code\timed_monitor.ps1')
for line,text in enumerate(monitor.read_text().splitlines(),1):
 if 'WriteAllText' in text:
  rows.append(dict(file=str(monitor),line=line,operation=text.strip(),classification='UNKNOWN' if 'function Save' in text else 'SAFE_UNIQUE_RUN_PATH',reason='Save helper mixes intentional mutable app-health.json with final outputs; existing unique run bounds its use, but individual final writes are not exclusive. Frozen candidate must not change in this pass.',disposition='Documented broader hardening opportunity; not executed or modified'))
create_json(R/'output-audit.json',dict(scope='Two immediately relevant evidence/preflight/report directories plus frozen monitor output helper; not a production/global audit',operations=rows,counts=collections.Counter(x['classification'] for x in rows),policy='New hardened entry points only; historical scripts retained and retired from reuse'))
print(dict(operations=len(rows),counts=collections.Counter(x['classification'] for x in rows)))
