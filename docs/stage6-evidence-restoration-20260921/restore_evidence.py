"""One explicitly authorized restoration. Fixed target; no general overwrite API."""
import datetime,hashlib,json,pathlib,sys,uuid,zipfile
from evidence_io import create_bytes,create_json
R=pathlib.Path(__file__).parent
P=R.parent/'stage6-instance-stream-design-20260921'
I=R.parent/'stage6-authoritative-integration-20260921'
TARGET=P/'final-host-state.json'
ORIGINAL='c01b96eecf05c4b29723b900d0543d104fe0f514487886339f080d3d709b17cb'
OVERWRITTEN='d95aefe75a1815037f2c1dc184ed4e91373686cc3fb465974b1784c06d58de12'
MEMBER='report/final-host-state.json'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def metadata(p):
    s=p.stat()
    return dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,LastWriteTimeUtc=datetime.datetime.fromtimestamp(s.st_mtime_ns/1e9,datetime.timezone.utc).isoformat(),sha256=sha(p))
def snapshot():
    return {str(p):metadata(p) for base in (P,I) for p in sorted(base.rglob('*')) if p.is_file()}
def archives():
    result=[];original=None
    for recordfile,expected,count in [(P/'archive-verification.json','46dddb7c33c87154325778989f51fda265e9833f8f50d550b9506fdc770dc1a5',143),(I/'archive-verification.json','a18270f1aee8510ba0895d794fb66a95f0c52f473477b1db3f5f836c06c7bec1',8)]:
        receipt=load(recordfile);path=pathlib.Path(receipt['path'])/'evidence.zip'
        assert sha(path)==expected,'RESTORATION_EVIDENCE_CONFLICT: archive'
        members=[]
        with zipfile.ZipFile(path) as z:
            assert len(z.namelist())==len(set(z.namelist()))==count
            manifest_bytes=z.read('manifest.json');manifest=json.loads(manifest_bytes)
            for x in manifest['files']:
                with z.open(x['name']) as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
                assert digest==x['sha256'],x['name']
                members.append(dict(name=x['name'],sha256=digest,bytes=z.getinfo(x['name']).file_size))
            members.append(dict(name='manifest.json',sha256=hashlib.sha256(manifest_bytes).hexdigest(),bytes=len(manifest_bytes)))
            if count==143:
                original=z.read(MEMBER)
                assert hashlib.sha256(original).hexdigest()==ORIGINAL
                assert manifest['utc'] < load(I/'preservation-incident.json')['newHostCheck']['utc'],'Archive chronology conflict'
                chronology=dict(manifestFinalizedUtc=manifest['utc'],accidentalCheckUtc=load(I/'preservation-incident.json')['newHostCheck']['utc'])
            result.append(dict(archive=metadata(path),members=members))
    for x in load(P/'freeze.json')['checks']:assert sha(pathlib.Path(x['path']))==x['sha256'],x['path']
    assert sha(I/'original-host-state-from-verified-archive.json')==ORIGINAL
    assert sha(I/'new-host-state-after-accidental-overwrite.json')==OVERWRITTEN
    return result,original,chronology
def freeze():
    assert sha(TARGET)==OVERWRITTEN,'RESTORATION_EVIDENCE_CONFLICT: current local file'
    a,b,c=archives()
    state=load(R/'final'/(R/'initial-run-id.txt').read_text()/'final-host-state.json')
    assert state['status']=='PASS' and state['matchingProcessCount']==state['diagnosticTraceCount']==0
    assert load(I/'preservation-incident.json')['localEvidenceMismatches'][0]['actual']==OVERWRITTEN
    out=dict(status='AUTHORITATIVE_RESTORATION_SOURCE_CONFIRMED',target=metadata(TARGET),archives=a,originalMember=MEMBER,originalMemberSHA256=ORIGINAL,originalMemberBytes=len(b),chronology=c,candidateHashes=116,additionalFrozenChecks=6,beforeDirectoryState=snapshot(),hostPreflight=state,knownConflictingOriginal=False)
    create_json(R/'freeze.json',out)
    print(json.dumps({k:v for k,v in out.items() if k not in ('archives','beforeDirectoryState','hostPreflight')}))
def restore():
    frozen=load(R/'freeze.json');assert frozen['status']=='AUTHORITATIVE_RESTORATION_SOURCE_CONFIRMED'
    assert snapshot()==frozen['beforeDirectoryState'],'RESTORATION_EVIDENCE_CONFLICT: directory drift'
    a,original,c=archives();assert a==frozen['archives'],'RESTORATION_EVIDENCE_CONFLICT: archive metadata drift'
    current=TARGET.read_bytes();assert hashlib.sha256(current).hexdigest()==OVERWRITTEN
    incident=R/'incident';incident.mkdir(exist_ok=False)
    backup=incident/('final-host-state.overwritten.'+uuid.uuid4().hex+'.json')
    create_bytes(backup,current);assert backup.read_bytes()==current
    materialized=incident/'authoritative-original.json';create_bytes(materialized,original)
    assert sha(materialized)==ORIGINAL
    create_json(R/'restoration-intent.json',dict(target=str(TARGET),source=metadata(materialized),preservedOverwritten=metadata(backup),overwrittenOriginalMetadata=frozen['target'],method='Fixed single target r+b; verify current handle bytes, write original, truncate to original length, fsync; no directory extraction'))
    # The sole authorized exception to exclusive-create. Never exported as general helper.
    with TARGET.open('r+b') as stream:
        assert hashlib.sha256(stream.read()).hexdigest()==OVERWRITTEN
        stream.seek(0);stream.write(original);stream.truncate(len(original));stream.flush();__import__('os').fsync(stream.fileno())
    assert TARGET.read_bytes()==original and sha(TARGET)==ORIGINAL
    after=snapshot();before=frozen['beforeDirectoryState']
    assert set(after)==set(before),'RESTORATION_SIDE_EFFECT: filenames changed'
    assert [p for p in before if before[p]!=after[p]]==[str(TARGET)],'RESTORATION_SIDE_EFFECT: neighbors changed'
    archives()
    create_json(R/'restoration-result.json',dict(status='RESTORED_CONTENT_MATCH_PASS',target=metadata(TARGET),preservedOverwritten=metadata(backup),source=metadata(materialized),byteEquality=True,changedExistingPaths=[str(TARGET)],directoryPreservation=True,timestampPolicy='New local filesystem timestamp recorded separately; historical timestamp not recreated',historicalArchiveUnchanged=True,incidentArchiveUnchanged=True,candidateHashesUnchanged=116))
    print(json.dumps(load(R/'restoration-result.json'),indent=2))
def verify():
    result=load(R/'restoration-result.json');assert sha(TARGET)==ORIGINAL
    a,original,c=archives();assert TARGET.read_bytes()==original
    before=load(R/'freeze.json')['beforeDirectoryState'];after=snapshot()
    assert set(before)==set(after)
    assert all(before[p]==after[p] for p in before if p!=str(TARGET))
    assert metadata(TARGET)==result['target']
    create_json(R/'final-preservation.json',dict(restoredHash=sha(TARGET),restoredBytes=len(original),byteEquality=True,candidateHashesUnchanged=116,additionalFrozenChecks=6,archiveMembersVerified=[143,8],onlyHistoricalChange=str(TARGET),unrelatedMutations=0,protectedAccess=False,productionChanged=False))
    print('FINAL_PRESERVATION_PASS')
if __name__=='__main__': {'freeze':freeze,'restore':restore,'verify':verify}[sys.argv[1]]()
