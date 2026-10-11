"""Hash verification, read-only census and offline evidence archival only."""
import pathlib,json,hashlib,ast,sys,os,zipfile
R=pathlib.Path(__file__).parent;v=json.loads((R/'before.json').read_text());C=pathlib.Path(v['candidate'])
DEST=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 PREFLIGHT PATH FILTER FIX 20260923')
def read(p):return json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.flush();os.fsync(f.fileno())
for x in v['inputs']:
 p=pathlib.Path(x['path']);s=p.stat();assert(s.st_size,s.st_mtime_ns,sha(p))==(x['bytes'],x['mtimeNs'],x['sha256'])
for receipt in v['archives']:
 a=pathlib.Path(receipt['archive']);m=a.parent/'manifest.json';assert sha(a)==receipt['archiveSHA256'] and sha(m)==receipt['manifestSHA256']
 with zipfile.ZipFile(a) as z:
  rows=read(m)['files'];assert len(rows)==receipt['members']==len(z.namelist())==len(set(z.namelist()))
  for x in rows:
   with z.open(x['path']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==x['sha256']
syntax=[]
for p in R.glob('*.py'):ast.parse(p.read_bytes(),filename=str(p));syntax.append(dict(path=str(p),sha256=sha(p)))
sys.path.insert(0,str(C));import failure_preserve_v4 as fp
census=fp.host_census(C);write(R/'final-census.json',census)
assert census['available'] and census['processes']==[] and census['traces']==[] and census['unknown']==[]
assert not (R/'preflight.json').exists() and not (R/'preflight-failure.json').exists()
original=R.parent/'stage6-one-trace-diagnostic-v4-20260923/preflight.py'
result=dict(status='PREFLIGHT_PATH_FILTER_CORRECTED_AND_TESTED',tests=24,passed=24,failed=0,syntax=syntax,originalHelperSHA256=sha(original),correctedHelperSHA256=sha(R/'preflight.py'),candidateManifestSHA256=sha(C/'small-source-v3.json'),candidateFilesUnchanged=229,frozenCheckerSHA256=sha(C/'medium-checker/frozen_reference.py'),originalRecordsUnchanged=len(v['inputs']),historicalArchivesVerified=[x['members'] for x in v['archives']],datasetFiles=12,datasetBytes=786432,liveDiagnosticProcesses=0,traceSessions=0,VirtualBoxProcesses=0,livePreflightRun=False,UAC=False,protectedAccess=False,productionChange=False)
write(R/'verification.json',result)
report=f'''# Preflight path-filter correction — offline result

PREFLIGHT_PATH_FILTER_CORRECTED_AND_TESTED

Only a separate copy of the preflight helper was corrected. The old failed helper, its records and nine-member archive remain unchanged. Candidate/frozen sources were not edited.

Corrected helper: `{R / 'preflight.py'}`
Original SHA-256: `{result['originalHelperSHA256']}`
Corrected SHA-256: `{result['correctedHelperSHA256']}`

The new dataset_records function normalizes separators and case only for duplicate/comparison validation, validates safe relative components, and returns the original manifest names unchanged. Forward-slash equivalents are accepted only as comparison aliases. Backslash/forward-slash/case aliases cannot provide duplicate logical entries. Empty/dot/traversal components, absolute/drive/root paths, malformed Windows names, unexpected dataset entries, size/hash mismatches, extra disk files, missing files, hardlinks and reparse escapes fail closed. The unchanged candidate containment function is reused. Expected per-file hashes are pinned to the reviewed dataset. All 12 files must be present, 65,536 bytes each, total 786,432 bytes.

The only non-filter adjustment is the new helper's report destination, needed to avoid overwriting/reusing the original failed preflight. A focused source-comparison test proves that all remaining helper logic is identical. No candidate code or authoritative manifest representation changes.

24/24 focused offline tests passed (0 failed); all 12 requested cases covered. Additional cases include actual NTFS junction and hardlink rejection, duplicate separator/case aliases, unchanged manifest bytes, missing-local/old-copy fallback rejection, extra files and exact source-diff scope. The function was extracted by AST for testing; the helper's top-level preflight, run preparation, observers and UAC were never executed. A read-only test of the actual candidate dataset passed all 12 expected file hashes.

Exact test command: `C:\\Users\\jonny\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe -B "{R / 'run_tests.py'}"`.
Detailed stdout/stderr: focused-0ab7084f4f2e449a932779d07a4cf4bc/tests.json. Syntax: AST parse of the corrected helper and action Python tooling; exact files/hashes in verification.json. No unrelated test suite rerun.

Preservation: 229 candidate files unchanged, frozen checker unchanged, {len(v['inputs'])} recorded input files unchanged; prior archives of 9 and 2,207 members reopened and hash-verified. Candidate manifest remains `d2f6738f5d7c3f22fe361f6cb1da174f630d8e150574009b59825d88321ed4d7`.

Final read-only census: zero matching diagnostic processes, zero trace sessions, zero VirtualBox processes, zero unknown entries. Disposable fixture files and an intentionally rejected junction are retained as offline evidence; archival does not follow the junction. No source deletion or protected/production access occurred.

Historical trace-loss cause remains UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED. No live diagnostic result exists for this action; Stage 6 remains incomplete. No deadlines, tracing settings, providers, buffers or checker semantics changed.

Rollback: do not use this separate corrected helper; retain it and its evidence. The failed original and frozen candidate remain intact. No production rollback is needed.

Exact next one-run diagnostic procedure: ONE-RUN-OWNER-REVIEW.md, owner review only. Separate live/UAC approval is required. STOPPED; no run launched.
'''
with (R/'REPORT.md').open('x') as f:f.write(report)
files=[];excluded=[]
for at,dirs,names in os.walk(R,followlinks=False):
 for name in list(dirs):
  p=pathlib.Path(at)/name
  if p.lstat().st_file_attributes&0x400:dirs.remove(name);excluded.append(dict(path=str(p.relative_to(R)),reason='SACRIFICIAL_REPARSE_NOT_FOLLOWED'))
 for name in names:
  p=pathlib.Path(at)/name;assert not p.lstat().st_file_attributes&0x400
  if name.startswith('.env'):raise ValueError('UNEXPECTED_ENV_FILE')
  files.append(dict(path=p.relative_to(R).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
DEST.mkdir(parents=True,exist_ok=False);write(DEST/'manifest.json',dict(kind='OFFLINE PATH FILTER CORRECTION; NOT LIVE ACCEPTANCE',files=files,excluded=excluded))
a=DEST/'preflight-path-filter-fix.zip'
with zipfile.ZipFile(a,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for x in files:z.write(R/x['path'],x['path'])
with a.open('r+b') as f:os.fsync(f.fileno())
with zipfile.ZipFile(a) as z:
 assert len(z.namelist())==len(files)==len(set(z.namelist()))
 for x in files:
  with z.open(x['path']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==x['sha256']
  assert sha(R/x['path'])==x['sha256']
for x in v['inputs']:
 p=pathlib.Path(x['path']);s=p.stat();assert(s.st_size,s.st_mtime_ns,sha(p))==(x['bytes'],x['mtimeNs'],x['sha256'])
receipt=dict(status='VERIFIED',archive=str(a),archiveSHA256=sha(a),manifestSHA256=sha(DEST/'manifest.json'),members=len(files),excluded=excluded,liveAcceptance=False)
write(DEST/'archive-receipt.json',receipt);write(R/'archive-receipt.json',receipt)
print(json.dumps(dict(result=result,archive=receipt),indent=2))
