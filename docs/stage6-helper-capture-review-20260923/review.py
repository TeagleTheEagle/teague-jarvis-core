import pathlib,json,hashlib,zipfile
R=pathlib.Path(__file__).resolve().parent;P=R.parent/'stage6-integrated-loss-diagnostic-20260923'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cfg=read(P/'candidate.json');C=pathlib.Path(cfg['code']);run=pathlib.Path(read(P/'normal-run.json')['root'])
failed=read(P/'failed-identities.json');tree=read(run/'tree-handles.json')['rows'];metrics=read(P/'metrics.json');f=10000000
rows=[]
for x in failed:
 k=x['kernel'];matches=[r for r in tree if r['pid']==k['pid'] and r['created']==k['created']]
 rows.append(dict(pid=k['pid'],created=k['created'],sequence=k['sequence'],parentPid=k['parentPid'],parentSequence=k['parentSequence'],lifetimeSeconds=x['lifetimeSeconds'],eventToRecordedStartSeconds=x['eventToCallbackSeconds'],recordedStartToImageMicroseconds=(k['imageBeginQpc']-k['startCallbackQpc'])/10,imageCallMicroseconds=(k['imageEndQpc']-k['imageBeginQpc'])/10,imageAfterStopSeconds=x['imageQueryAfterStopSeconds'],tree=matches[0] if matches else None,treeRetentionBeforeStopSeconds=(k['stopQpc']-matches[0]['handleRetainedQpc'])/f if matches else None))
for x in cfg['files']:assert sha(C/x['name'])==x['sha256']
archive=read(P/'archive-receipt.json');assert sha(pathlib.Path(archive['archive']))==archive['archiveSHA256']
with zipfile.ZipFile(archive['archive']) as z:assert len(z.namelist())==archive['membersVerified']
sources=['authority_trace.cpp','evidence_support.py','small_check.py','small_coverage.py','owned_entry.cpp']
result=dict(status='REVIEW_COMPLETE_CORRECTION_NOT_IMPLEMENTED',rows=rows,maximumAuthorityCallbackSeconds=metrics['channels']['authority']['metrics']['callback']['maxSeconds'],candidateFilesVerified=len(cfg['files']),archiveSHA256=archive['archiveSHA256'],archiveMembers=archive['membersVerified'],sources=[dict(path=str(C/n),sha256=sha(C/n)) for n in sources])
with (R/'evidence.json').open('x') as out:json.dump(result,out,indent=2)
print(json.dumps(rows,indent=2))
