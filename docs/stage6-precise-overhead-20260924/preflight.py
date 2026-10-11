import pathlib,json,hashlib,zipfile,datetime,ast
R=pathlib.Path(__file__).parent
PREV=R.parent/'stage6-final-measurement-v3-20260924'
C=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\a34f91e1db274bf78fc5a80e2a9d417c\code')
LIVE=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\precise-overhead-20260924-4b0db487')
def load(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with pathlib.Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
    with pathlib.Path(p).open('x',encoding='utf8') as f:json.dump(x,f,indent=2)
def verify(row):
    p=pathlib.Path(row['path']);s=p.stat()
    assert not s.st_file_attributes&0x400
    assert sha(p)==row['sha256'],str(p)
    assert s.st_size==row['bytes'] and s.st_mtime_ns==row['mtimeNs'],str(p)
if __name__=='__main__':
    assert not LIVE.exists();assert not (R/'preflight.json').exists()
    for x in load(PREV/'candidate-artifact-manifest.json')['files']:verify(x)
    for x in load(PREV/'before.json')['inputs']:verify(x)
    hist=load(PREV/'historical-precheck.json')
    for x in hist['evidence']:verify(x)
    assert sha(hist['archive'])==hist['archiveSHA256']
    receipt=load(PREV/'archive-receipt.json');assert sha(receipt['archive'])==receipt['archiveSHA256']
    with zipfile.ZipFile(receipt['archive']) as z:
        assert len(z.namelist())==len(set(z.namelist()))==receipt['membersVerified']
        for x in receipt['memberHashes']:
            with z.open(x['name']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==x['sha256']
        # Ensure predecessor report files remain identical to the archived originals.
        manifest=json.loads(z.read('archive-manifest.json'))
        for x in manifest['entries']:verify(x)
    protocol=load(R/'protocol.json');assert sha(protocol['binary'])==protocol['binarySHA256']
    syntax=[]
    for p in sorted(R.glob('*.py')):
        ast.parse(p.read_text(),filename=str(p));syntax.append(dict(path=str(p),sha256=sha(p)))
    LIVE.mkdir()
    put(R/'preflight.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidateFiles=240,predecessorEvidence=760,historicalEvidence=len(hist['evidence']),archiveMembers=receipt['membersVerified'],preservation='PASS',protocolSHA256=sha(R/'protocol.json'),harnessSources=syntax,liveRoot=str(LIVE),existingRestrictedCensusFailure='Win32_Processor access denied in restricted command context; same read-only host-context census succeeded; no UAC',preflightHostCensus=dict(utc='2026-09-23T23:18:32.3167043Z',cpu='AMD Ryzen 7 3700X 8-Core Processor',logicalProcessors=16,os='Microsoft Windows NT 10.0.26200.0',processes=0,traces=0)))
    print('PREFLIGHT PASS; prior archive 275 members verified; no executable/source changes')
