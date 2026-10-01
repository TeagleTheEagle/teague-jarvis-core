import pathlib,json,hashlib,sys,os,unittest,zipfile
R=pathlib.Path(__file__).parent;P=R.parent/'stage6-small-rebind-20260925'
C=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\ea85ed4b4ef14769acbe0b5e750aaed2\code')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rec(p):
 s=p.stat();return dict(path=str(p),bytes=s.st_size,mtimeNs=s.st_mtime_ns,sha256=sha(p))
def write(n,v):
 with (R/n).open('x',encoding='utf8') as f:json.dump(v,f,indent=2)
def preserve():
 for x in read(P/'before.json')['inputs']:assert rec(pathlib.Path(x['path']))==x,x['path']
 for x in read(C/'small-source-v3.json'):assert (C/x['name']).stat().st_size==x['bytes'] and sha(C/x['name'])==x['sha256']
 assert rec(C/'small-source-v3.json')==read(P/'rebind.json')['manifest']
before=[rec(p) for p in P.rglob('*') if p.is_file()]
preserve();receipt=read(P/'archive-receipt.json');assert rec(pathlib.Path(receipt['archive']['path']))==receipt['archive']
with zipfile.ZipFile(receipt['archive']['path']) as z:
 assert len(z.namelist())==592 and z.testzip() is None
 for x in read(P/'archive-manifest.json'):assert hashlib.sha256(z.read(x['member'])).hexdigest()==x['sha256']
os.chdir(C);sys.path[0]=str(C)
import workspace_binding_v4 as b
policy=b.policy();dest=pathlib.Path(policy['preservationRoot']);assert dest==C.parent/'preservation-v4' and not dest.exists()
b.safe(dest,C.parent)
write('preflight.json',dict(policy=rec(C/'preservation-policy-v4.json'),destination=str(dest),priorArchiveMembers=592,historicalInputs=before,requiredBy='failure_preserve_v4.py target.mkdir(parents=False); no preexisting contents required'))
dest.mkdir(exist_ok=False);assert list(dest.iterdir())==[];b.safe(dest,C.parent)
write('directory-created.json',dict(path=str(dest),initiallyEmpty=True,reparse=False,sourceChanged=False))
runtime=b.runtime_policy();os.environ['PATH']=os.pathsep.join(dict.fromkeys(str(pathlib.Path(x['path']).parent) for x in runtime['executables'].values()));os.environ['PSModulePath']=os.pathsep.join(runtime['moduleRoots']);os.environ['PYTHONNOUSERSITE']='1';b.environment(runtime)
import test_binding_v4 as t
def tests(names,label):
 with (R/(label+'.txt')).open('x') as f:result=unittest.TextTestRunner(stream=f,verbosity=2).run(unittest.TestSuite(t.Tests(n) for n in names))
 out=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),passResult=result.wasSuccessful());write(label+'.json',out);print(label,out,flush=True)
 if not result.wasSuccessful():raise SystemExit('STOP: affected offline check failed')
tests(['test_22_fail_missing_sidecar_explicit','test_positive_failure_archive_integration'],'affected-two')
tests(['test_04_stale_path','test_05_old_cwd','test_07_old_manifest_path','test_08_reparse_escape','test_10_unapproved_root','test_21_pass_missing_sidecar','test_24_old_preservation','test_positive_pass_archive_integration','test_failure_never_pass','test_positive_binding','test_positive_dataset_local','test_positive_runtime_real','test_positive_native_dll_load_only','test_26_old_never_consulted','test_27_deadline_unchanged'],'focused-followup')
preserve()
for x in before:assert rec(pathlib.Path(x['path']))==x
write('post-verification.json',dict(status='PASS',sourceManifest='6a86a4f287388c8c58b3df4333792217b5205305f2157043a5a2ba5456c0b15b',successorManifest=rec(C/'small-source-v3.json'),candidateFiles=235,datasetFiles=12,datasetBytes=786432,preservedOriginalInputs=1227,priorReportUnchanged=True,liveRun=False))
