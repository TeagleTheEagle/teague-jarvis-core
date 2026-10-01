"""Bounded offline paired preparation. Never launches an observer."""
import os,sys,json,hashlib,subprocess,re,shutil,datetime,platform,stat,difflib
from pathlib import Path

HERE=Path(__file__).resolve().parent
DOCS=HERE.parent
CAND=Path(r'D:\JARVIS-STAGE6-LIVE\51faa5f9320b4b05b75cc522648621a7\code')
PYTHON=Path(sys.executable)
VS=Path(r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools')
AUTH='c405202381a2fed890512c553cc8b631cfc2f03e4d2ef955aa8f236d02949aef'
DETAIL='5225e63c654a63fff05e4002475e8caae5910d4d11822a13119bf2791fc35634'
KEYS=['INCLUDE','LIB','LIBPATH','PATH','CL','_CL_','LINK','VCToolsVersion','VCToolsInstallDir','VCINSTALLDIR','WindowsSdkDir','WindowsSDKVersion','WindowsSDKLibVersion','UniversalCRTSdkDir','UCRTVersion','VSCMD_ARG_HOST_ARCH','VSCMD_ARG_TGT_ARCH','TEMP','TMP','SystemRoot','SystemDrive','ComSpec']
def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def save(name,value):
    p=HERE/name
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')
def read(name):return json.loads((HERE/name).read_text(encoding='utf-8'))
def record(p):
    p=Path(p);s=p.stat()
    return {'path':str(p),'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'sha256':digest(p)}
def tree(root):
    root=Path(root)
    if not root.is_dir():raise RuntimeError('Required root unavailable: '+str(root))
    result=[]
    for base,dirs,files in os.walk(root,followlinks=False):
        for n in dirs+files:
            if (Path(base)/n).lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:raise RuntimeError('Reparse input: '+str(Path(base)/n))
        result.extend(record(Path(base)/n) for n in sorted(files))
    return sorted(result,key=lambda x:x['path'].casefold())
def verify(rows):
    bad=[]
    for r in rows:
        p=Path(r['path'])
        if not p.is_file() or record(p)!=r:bad.append(str(p))
    if bad:raise RuntimeError('Preservation/input drift: '+json.dumps(bad))
def initial():
    assert digest(CAND/'J6AuthorityTraceV3.exe')==AUTH
    assert digest(CAND/'J6StartupTrace.exe')==DETAIL
    manifest=json.loads((CAND/'small-source-v3.json').read_text())
    for r in manifest:
        p=CAND/r['name'];assert p.is_file() and digest(p)==r['sha256'] and p.stat().st_size==r['bytes'],r['name']
    roots=[CAND]+[DOCS/n for n in ['stage6-authority-independent-20260925','stage6-lifecycle-witness-20260925','stage6-witness-live-20260925','stage6-independent-live-20260925','stage6-independent-result-review-20260925']]
    rows={}
    for p in roots:
        for r in tree(p):rows[r['path']]=r
    save('preservation-before.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'roots':list(map(str,roots)),'files':list(rows.values()),'authoritySHA256':AUTH,'historicalDetailedSHA256':DETAIL,'sourceManifestSHA256':digest(CAND/'small-source-v3.json')})
    (HERE/'capture-env.cmd').write_text('@echo off\ncall "'+str(VS/'Common7/Tools/VsDevCmd.bat')+'" -arch=x64 -host_arch=x64 > "'+str(HERE/'environment-setup.log')+'" 2>&1\nif errorlevel 1 exit /b %errorlevel%\n"'+str(PYTHON)+'" -B "'+str(HERE/'prepare_pair.py')+'" env\n',encoding='utf-8')
    save('environment-capture-command.json',{'command':[str(Path(os.environ['SystemRoot'])/'System32/cmd.exe'),'/d','/c',str(HERE/'capture-env.cmd')],'script':record(HERE/'capture-env.cmd'),'setup':record(VS/'Common7/Tools/VsDevCmd.bat'),'python':record(PYTHON)})
    print('PRESERVATION_FROZEN',len(rows),'files; no build')
def env():save('initialized-environment.json',{k:os.environ.get(k,'') for k in KEYS})
if __name__=='__main__':
    if sys.argv[1]=='initial':initial()
    elif sys.argv[1]=='env':env()
