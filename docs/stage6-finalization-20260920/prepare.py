import pathlib,json,hashlib,uuid,shutil
R=pathlib.Path(__file__).resolve().parent;C=R/'candidate';C.mkdir(exist_ok=False)
old=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\ab1566cc23dd43cab43afef00cba5940\code');probe=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\fb8ef11d2c4d44cca4d352d4a9fdfc93\code')
names=[p.name for p in old.iterdir() if p.is_file() and p.suffix in ('.py','.ps1','.cs','.exe')];before=[]
for n in names:
 p=(probe/n) if n in ('collect.py','probe_timing.py','probe_analysis.py','launch.ps1') else old/n
 st=p.stat();before.append(dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),size=st.st_size,mtime_ns=st.st_mtime_ns));shutil.copyfile(p,C/n)
for n in ('probe_timing.py','probe_analysis.py'):
 if not (C/n).exists():
  p=probe/n;st=p.stat();before.append(dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),size=st.st_size,mtime_ns=st.st_mtime_ns));shutil.copyfile(p,C/n)
with (R/'source-before.json').open('x') as f:json.dump(before,f,indent=2)
plan=dict(live_code=str(pathlib.Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code'),archive=r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 FINALIZATION CORRECTION 20260920',quietSeconds=json.loads((R/'latency-summary.json').read_text())['quietSeconds'],finalizationDeadlineSeconds=45,collectorWaitSeconds=60,acceptance=False)
with (R/'plan.json').open('x') as f:json.dump(plan,f,indent=2)
print(json.dumps(plan))
