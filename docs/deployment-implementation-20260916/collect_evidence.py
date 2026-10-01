"""Inspect only named TEST evidence, package imports and recorded process IDs."""
import hashlib,json,os,re,subprocess,sys,uuid
import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tests/lifecycle_stage2'))
import pipe_transport as t
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
sources=[OUT/'installed-0630e4345f8f4975bf5bab5a6ab07c23.json',
 ROOT/'docs/lifecycle-stage5-evidence/integrated-2dc1a02126b1480db0d1b07fc1ffc4e2.json',
 ROOT/'docs/lifecycle-stage4-evidence/client-state-media-ce4907b46aae4827a8d698a18b074a5b.json']
identities={};summary=[];waited_exits=set()
def walk(value):
    if isinstance(value,dict):
        if {'pid','created','exe_digest'}<=set(value):
            peer={k:value[k] for k in ('pid','created','exe_digest')};peer['created']=int(peer['created'])
            identities[(peer['pid'],peer['created'],peer['exe_digest'])]=peer
        for v in value.values():walk(v)
    elif isinstance(value,list):
        for v in value:walk(v)
for path in sources:
    data=json.loads(path.read_text());walk(data)
    records=data['records'];summary.append(dict(path=str(path.relative_to(ROOT)),sha256=digest(path),checks=len(records),failures=sum(not x['passed'] for x in records)))
    for row in records:
        if row.get('case')=='coordinator exit recorded' and row.get('passed') and row.get('exit') in (0,93):
            peer=row['identity'];waited_exits.add((peer['pid'],int(peer['created']),peer['exe_digest']))
cleanup=[]
census=json.loads((OUT/'cleanup-process-census.json').read_text(encoding='utf-8-sig'))
assert set(census['queriedPids'])=={p['pid'] for p in identities.values()}
current_processes={x['ProcessId']:x for x in census['processes']}
for peer in identities.values():
    if peer['pid'] not in current_processes:
        cleanup.append(dict(identity=peer,result='ABSENT_FROM_CURRENT_PROCESS_CENSUS'))
        continue
    observed=current_processes[peer['pid']]
    creation=datetime.datetime.fromisoformat(observed['CreationDate'])
    epoch=datetime.datetime(1601,1,1,tzinfo=datetime.timezone.utc)
    delta=creation.astimezone(datetime.timezone.utc)-epoch
    observed_ticks=(delta.days*86400+delta.seconds)*10000000+delta.microseconds*10
    if abs(observed_ticks-peer['created'])>10:
        cleanup.append(dict(identity=peer,result='PID_REUSED_DIFFERENT_CREATION_TIME',
                            observed_created=observed_ticks,method='CIM creation time; no executable access or process control'))
        continue
    try:
        now=t.identity(peer['pid'])
        result='STILL_LIVE' if now==peer else 'PID_REUSED_DIFFERENT_IDENTITY'
    except t.Rejected as exc:
        result='EXITED' if str(exc)=='PROCESS_DEAD' else 'UNCONFIRMED:'+str(exc)
    except OSError as exc:
        result='EXITED' if exc.errno in (87,1168) else 'UNCONFIRMED:'+str(exc)
    cleanup.append(dict(identity=peer,result=result))
corroboration=json.loads((OUT/'cleanup-cim-corroboration.json').read_text(encoding='utf-8-sig'))
for row in cleanup:
    peer=row['identity'];key=(peer['pid'],peer['created'],peer['exe_digest'])
    if row['result'].startswith('UNCONFIRMED:') and peer['pid'] in corroboration['queriedPids'] and not corroboration['processes'] and key in waited_exits:
        row['native_inspection']=row['result']
        row['result']='EXIT_CONFIRMED_PARENT_WAIT_AND_CIM_ABSENCE'
allowed={'EXITED','PID_REUSED_DIFFERENT_IDENTITY','PID_REUSED_DIFFERENT_CREATION_TIME','EXIT_CONFIRMED_PARENT_WAIT_AND_CIM_ABSENCE','ABSENT_FROM_CURRENT_PROCESS_CENSUS'}
if not all(x['result'] in allowed for x in cleanup):
    failure=dict(error='TEST_CLEANUP_REVIEW',cleanup=cleanup)
    (OUT/('cleanup-inspection-failure-'+uuid.uuid4().hex+'.json')).write_text(json.dumps(failure,indent=2),encoding='utf8')
    print(json.dumps([x for x in cleanup if x['result'] not in allowed],indent=2))
    raise AssertionError('TEST_CLEANUP_REVIEW')
installed=json.loads(sources[0].read_text());package=Path(installed['package']['package'])
manifest=json.loads((package/'manifest.json').read_text())
frozen=json.loads((OUT/'source-final.json').read_text())
entries={x['path']:x for x in manifest['files']}
for row in frozen['source']:
    if 'app/'+row['path'] in entries:assert row['after_sha256']==entries['app/'+row['path']]['sha256']
assert digest(package/'manifest.json')==installed['package']['sha256']
dump=Path(r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\dumpbin.exe')
dependencies=[]
for item in manifest['files']:
    file=package/item['path']
    if file.suffix.lower() not in ('.exe','.dll','.pyd','.node'):continue
    result=subprocess.run([str(dump),'/dependents',str(file)],capture_output=True,text=True)
    assert result.returncode==0
    imports=sorted(set(re.findall(r'^\s+([^\s]+\.(?:dll|exe))\s*$',result.stdout,re.M|re.I)))
    dependencies.append(dict(path=item['path'],sha256=item['sha256'],imports=imports))
allnames={Path(x['path']).name.lower() for x in manifest['files']}
host_names=sorted(set(x.lower() for item in dependencies for x in item['imports'])-allnames)
host=[]
for name in host_names:
    file=Path(os.environ['SystemRoot'])/'System32'/name
    host.append(dict(name=name,api_set=name.startswith(('api-ms-','ext-ms-')),system_file_present=file.is_file(),system_file_sha256=digest(file) if file.is_file() else None))
result=dict(campaigns=summary,cleanup=cleanup,cleanup_counts={k:sum(x['result']==k for x in cleanup) for k in set(x['result'] for x in cleanup)},
 package_manifest_sha256=digest(package/'manifest.json'),package_matches_final_source=True,package_files=len(manifest['files']),
 native_imports=dependencies,unbundled_import_names=host,limitations=['PE import names are not a trace of actual Windows DLL resolution','same-host relocation, not clean-machine validation'])
(OUT/'independent-final.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps(dict(campaigns=summary,identities=len(cleanup),cleanup=result['cleanup_counts'],native_binaries=len(dependencies),unbundled_non_system_api_set=[x['name'] for x in host if not x['api_set']]),indent=2))
