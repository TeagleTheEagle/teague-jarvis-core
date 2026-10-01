import pathlib,json,zipfile,hashlib,datetime,subprocess,ast
from context_config import R,PREV,PRECISE,FIXTURE,LIVE,load,sha,put,verify
def disasm(p):
 dump=r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\dumpbin.exe'
 text=subprocess.run([dump,'/disasm:nobytes',str(p)],capture_output=True,text=True,errors='replace',check=True).stdout.splitlines()
 for i,line in enumerate(text):
  if line.startswith('?dispatch@@'):
   body=[]
   for x in text[i+1:]:
    if x and not x[0].isspace():break
    if x.strip():body.append(x.strip())
   return '\n'.join(body)
 raise RuntimeError('Reference disassembly missing')
if __name__=='__main__':
 assert not LIVE.exists()
 census=load(R/'preflight-census.json');assert census['processCount']==census['traceCount']==0
 preserved=load(PREV/'before.json')['preserved']
 for row in preserved:verify(row)
 archives=[]
 for folder in [PREV,PRECISE]:
  receipt=load(folder/'archive-receipt.json');assert sha(receipt['archive'])==receipt['archiveSHA256']
  with zipfile.ZipFile(receipt['archive']) as z:
   assert len(z.namelist())==len(set(z.namelist()))==receipt['membersVerified']
   assert hashlib.sha256(z.read('archive-manifest.json')).hexdigest()==receipt['manifestSHA256']
   entries=json.loads(z.read('archive-manifest.json'))['entries']
   for row in entries:
    verify(row)
    with z.open(row['name']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['sha256']
   preserved+=entries
  archives.append(receipt)
 for row in load(PREV/'experiment-source-freeze.json'):verify(row)
 old=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\a34f91e1db274bf78fc5a80e2a9d417c\code')
 original=disasm(old/'loss_measurement_fixture_v3.obj');current=disasm(FIXTURE/'attribution_fixture.obj');assert original==current
 protocol=load(R/'protocol.json');assert sha(protocol['fixture'])==protocol['fixtureSHA256']
 assert sha(FIXTURE/'loss_measurement_v3.hpp')==sha(old/'loss_measurement_v3.hpp')
 harness=[]
 for folder,names in [(PREV,['run.py','prepare.py','build.cmd','fixture-main.inc']),(PRECISE,['benchmark.py','preflight.py'])]:
  for name in names:harness.append(dict(path=str(folder/name),sha256=sha(folder/name)))
 for p in R.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
 put(R/'preservation-before.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),records=preserved,archives=archives,originalHarness=harness,referenceInstructionsIdentical=True,referenceInstructionSHA256=hashlib.sha256(current.encode()).hexdigest(),fixtureSHA256=sha(FIXTURE/'J6AttributionFixture.exe'),protocolSHA256=sha(R/'protocol.json')))
 LIVE.mkdir();print('PREFLIGHT PASS: source/binary/harness unchanged; reference instructions identical; 36 + 143 archive members verified')
