"""Fixed additive file copy only; no subprocesses or live validation."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).parent
DEST=Path(r'D:\JARVIS-STAGE6-LIVE\cab9745de28a4cae8aa6f6f7a516bf54')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,v):
    with p.open('x') as f:json.dump(v,f,indent=2)
verification=json.loads((ROOT/'post-source-verification.json').read_text())
if verification['errors']:raise ValueError('PRESERVATION_FAILED')
DEST.mkdir(exist_ok=False);(DEST/'code').mkdir();(DEST/'preservation').mkdir()
rows=[]
for src in sorted((ROOT/'code').iterdir()):
    if not src.is_file() or src.suffix not in ('.py','.json'):raise ValueError('UNEXPECTED_FILE')
    dst=DEST/'code'/src.name
    with src.open('rb') as a,dst.open('xb') as b:shutil.copyfileobj(a,b)
    if sha(src)!=sha(dst):raise ValueError('COPY_HASH')
    rows.append(dict(name=src.name,bytes=src.stat().st_size,sha256=sha(src)))
write(DEST/'code'/'source-manifest.json',rows)
write(ROOT/'new-source-manifest.json',dict(stagedRoot=str(DEST/'code'),files=rows,manifestSHA256=sha(DEST/'code'/'source-manifest.json')))
print(json.dumps(dict(stagedFiles=len(rows),manifestSHA256=sha(DEST/'code'/'source-manifest.json'))))
