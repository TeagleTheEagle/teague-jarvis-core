"""Exclusive staging of final helper-identity-tested revision; preserve r1."""
from pathlib import Path
import ast,hashlib,json,shutil
ROOT=Path(__file__).parent
DEST=Path(r'D:\JARVIS-STAGE6-LIVE\cab9745de28a4cae8aa6f6f7a516bf54\code-r2')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
DEST.mkdir(exist_ok=False);rows=[]
for src in sorted((ROOT/'code').iterdir()):
    if not src.is_file() or src.suffix not in ('.py','.json'):raise ValueError('UNEXPECTED_FILE')
    if src.suffix=='.py':ast.parse(src.read_text(),filename=str(src))
    dst=DEST/src.name
    with src.open('rb') as a,dst.open('xb') as b:shutil.copyfileobj(a,b)
    if sha(src)!=sha(dst):raise ValueError('COPY_HASH')
    rows.append(dict(name=src.name,bytes=src.stat().st_size,sha256=sha(src)))
with (DEST/'source-manifest.json').open('x') as f:json.dump(rows,f,indent=2)
value=dict(stagedRoot=str(DEST),files=rows,manifestSHA256=sha(DEST/'source-manifest.json'))
with (ROOT/'new-source-manifest-r2.json').open('x') as f:json.dump(value,f,indent=2)
print(json.dumps(value))
