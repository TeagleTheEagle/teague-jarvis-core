import pathlib,json,hashlib
R=pathlib.Path(__file__).parent
PREV=R.parent/'stage6-component-attribution-20260924'
PRECISE=R.parent/'stage6-precise-overhead-20260924'
FIXTURE=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\component-attribution-20260924-7f29a680')
LIVE=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\reference-precision-20260924-9f34d820')
def load(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with pathlib.Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with pathlib.Path(p).open('x',encoding='utf8') as f:json.dump(x,f,indent=2)
def verify(row):
 p=pathlib.Path(row['path']);s=p.stat();assert not s.st_file_attributes&0x400
 assert sha(p)==row['sha256'],str(p)
 if 'bytes' in row:assert s.st_size==row['bytes'],str(p)
 if 'mtimeNs' in row:assert s.st_mtime_ns==row['mtimeNs'],str(p)
