"""Deployment review preflight: read-only source/runtime metadata, no Core launch.

Writes only this review's nonsecret evidence. No package activation, DB access,
credential read, registry/ACL mutation, enrollment or production inspection.
"""
import configparser, datetime, hashlib, importlib.metadata, importlib.util, json, pathlib, sys
OUT=pathlib.Path(__file__).resolve().parent;ROOT=OUT.parents[1]
sys.path.insert(0,str(ROOT))
import stage4_runtime as runtime
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,v):(OUT/n).write_text(json.dumps(v,indent=2),encoding='utf-8')
checks=[]
def check(name,ok,**fields):
    checks.append(dict(check=name,passed=bool(ok),**fields));write('preflight-results.json',checks)
    assert ok,name
accepted=load(ROOT/'docs/lifecycle-stage5-evidence/source-final.json')
frozen=[dict(path=x['path'],expected=x['sha256'],sha256=sha(ROOT/x['path'])) for x in accepted]
check('all 31 accepted source/executable hashes unchanged',len(frozen)==31 and all(x['expected']==x['sha256'] for x in frozen))
write('accepted-source-verification.json',frozen)
selected=['tests/lifecycle_stage1/harness.py','tests/lifecycle_stage2/bootstrap.py','tests/lifecycle_stage2/pipe_transport.py','stage4_runtime.py','stage4_client.cjs','stage4_native/peer_identity.cc','stage4_native/CMakeLists.txt','tests/lifecycle_stage4/fixtures.py','desktop/main.cjs','desktop/backend.cjs','desktop/local-updates.cjs','desktop/package.json','desktop/preload.cjs','intelligence/main.cjs','intelligence/package.json','requirements.txt','tests/lifecycle_stage3/migration.py','tests/lifecycle_stage3/verify.py']
write('inspected-source.json',[dict(path=p,sha256=sha(ROOT/p),bytes=(ROOT/p).stat().st_size) for p in selected])
candidate=OUT/'uncreated-relocated-release'/'state'/('TEST-STAGE4-'+'a'*32)
try:runtime.validate_root(candidate)
except ValueError as exc:
    check('current root guard rejects independent relocated state path',str(exc)=='TEST namespace required',candidate=str(candidate),error=str(exc),candidate_created=False)
else:check('current root guard rejects independent relocated state path',False)
check('Core allowed TEST base is source-derived',runtime.exclusion.BASE==ROOT/'tests/lifecycle_stage1/evidence',base=str(runtime.exclusion.BASE))
check('Python client source has mirrored source-derived root restriction',"path.resolve(__dirname,'tests/lifecycle_stage1/evidence')" in (ROOT/'stage4_client.cjs').read_text())
check('native addon dependency is outside application root',"path.resolve(__dirname,'../stage4-toolchain/peer-build/Release/peer_identity.node')" in (ROOT/'stage4_client.cjs').read_text())
check('Core child command uses inherited native interpreter and fixed venv path',"sys._base_executable" in (ROOT/'stage4_runtime.py').read_text() and "REPO/'.venv/Lib/site-packages'" in (ROOT/'stage4_runtime.py').read_text())
cfg=configparser.ConfigParser();cfg.read_string('[venv]\n'+(ROOT/'.venv/pyvenv.cfg').read_text())
check('venv depends on developer runtime and system site packages',cfg['venv'].getboolean('include-system-site-packages') and pathlib.Path(cfg['venv']['home']).is_absolute())
check('client fixture launch depends on external Node cache',"Path(os.environ['USERPROFILE'])/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'" in (ROOT/'tests/lifecycle_stage4/fixtures.py').read_text())
check('desktop and intelligence package versions are preview 0.1.0',all(load(ROOT/p)['version']=='0.1.0' for p in ('desktop/package.json','intelligence/package.json')))
check('existing manifests have no installer/update scripts',all(set(load(ROOT/p)['scripts'])=={'start','test'} for p in ('desktop/package.json','intelligence/package.json')))
check('legacy Desktop owns backend process',"await backend?.quit()" in (ROOT/'desktop/main.cjs').read_text() and "function startBackend" in (ROOT/'desktop/backend.cjs').read_text())
check('legacy Intelligence reads desktop session discovery',"desktop','.jarvis-session.json'" in (ROOT/'intelligence/main.cjs').read_text())
check('TEST enrollment pins executable without persistent install binding',"peer['exe_digest']==entry['exe_digest']" in (ROOT/'tests/lifecycle_stage2/bootstrap.py').read_text())
for name in ('TEAGUE-PRODUCTION-'+'a'*32,r'\\other-machine\pipe\TEAGUE-TEST-'+'a'*32):
    try:runtime.transport.endpoint(name)
    except runtime.transport.Rejected as exc:check('TEST endpoint rejects out-of-scope destination',str(exc)=='TEST_ENDPOINT_ONLY',destination=name)
    else:check('TEST endpoint rejects out-of-scope destination',False)
check('valid TEST pipe name resolves without opening pipe',runtime.transport.endpoint('TEAGUE-TEST-'+'a'*32)==r'\\.\pipe\TEAGUE-TEST-'+'a'*32)
dependencies=[]
for module,distribution in [('pypdf','pypdf'),('docx','python-docx'),('reportlab','reportlab'),('PIL','Pillow'),('openwakeword','openwakeword'),('playwright','playwright'),('numpy','numpy')]:
    spec=importlib.util.find_spec(module)
    try:version=importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:version=None
    dependencies.append(dict(module=module,distribution=distribution,version=version,origin=spec.origin if spec else None))
native=ROOT.parent/'stage4-toolchain/peer-build/Release/peer_identity.node'
write('dependencies.json',dict(python_version=sys.version,python_executable=sys.executable,base_executable=sys._base_executable,base_executable_sha256=sha(pathlib.Path(sys._base_executable)),base_prefix=sys.base_prefix,venv_home=cfg['venv']['home'],include_system_site_packages=cfg['venv'].getboolean('include-system-site-packages'),electron=load(ROOT/'desktop/node_modules/electron/package.json')['version'],native_bridge=dict(path=str(native),sha256=sha(native),bytes=native.stat().st_size),resolved_sample_modules=dependencies,complete_dependency_lock=False))
write('summary.json',dict(timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),checks=len(checks),all_preflight_checks_passed=all(x['passed'] for x in checks),deployment_contract_validated=False,status='REVIEW REQUIRED — installation-root and persistent-enrollment bindings require scoped architecture approval',cores_launched=0,databases_opened=0,credentials_read=False,packages_built=0,source_modified=False,production_modified=False,tests='Read-only boundary/preflight checks only; no installation, relocation, enrollment or update runtime acceptance executed.'))
print(json.dumps(load(OUT/'summary.json')))
