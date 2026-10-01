import pathlib,json,hashlib,uuid,shutil
ROOT=pathlib.Path(__file__).resolve().parent
R=ROOT/'stage6-native-control-20260920';R.mkdir(exist_ok=False)
OLD=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\fb8ef11d2c4d44cca4d352d4a9fdfc93\code')
CODE=pathlib.Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code'
DEST=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 NATIVE CONTROL DIAGNOSIS 20260920')
candidate=R/'candidate';candidate.mkdir();before=[]
for n in ('monitor.ps1','workspace.py','workspace.ps1','journal.py','event_queue.cs','LoopTiming.cs','EventTap.cs','workload.py','resources.ps1','J6Probe.exe','analyze.py','event_analysis.py','queue_tests.cs','test_queue.ps1','collect.py','probe_timing.py','probe_analysis.py','launch.ps1'):
 p=OLD/n;st=p.stat();before.append(dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),size=st.st_size,mtime_ns=st.st_mtime_ns));shutil.copyfile(p,candidate/n)
(R/'source-before.json').write_text(json.dumps(before,indent=2))
(R/'plan.json').write_text(json.dumps(dict(live_code=str(CODE),archive=str(DEST),c_image_dir=str(R/'images'),runs=[['idle',150,'idle1'],['disk',150,'reads1'],['sustained',150,'hash1'],['Dhash',150,'dhash1'],['idle',150,'idle2'],['disk',150,'reads2'],['sustained',150,'hash2']],acceptance=False),indent=2))
(R/'images').mkdir()
print(json.dumps(dict(report=str(R),live_code=str(CODE))))
