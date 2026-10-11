"""Seal complete diagnostic evidence in the context that can read it."""
import hashlib,json,os,pathlib,zipfile
R=pathlib.Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fail(e):raise e
if __name__=='__main__':
 old=R.parent/'stage6-heartbeat-decoupled-20260918';baseline=json.loads((R/'original-inventory.json').read_text());current=[]
 for base,dirs,files in os.walk(old,onerror=fail):
  for n in files:
   p=pathlib.Path(base)/n;s=p.stat();current.append({'path':str(p.relative_to(old)),'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'sha256':sha(p)})
 if sorted(current,key=lambda x:x['path'])!=baseline:raise RuntimeError('Original evidence changed')
 files=[]
 for base,dirs,names in os.walk(R,onerror=fail,followlinks=False):
  for n in dirs+names:
   if (pathlib.Path(base)/n).is_symlink():raise RuntimeError('Unexpected link')
  for n in names:
   if n.startswith('.env'):raise RuntimeError('Secret path refused')
   p=pathlib.Path(base)/n;files.append({'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
 files.sort(key=lambda x:x['path'])
 with (R/'archive-manifest.json').open('xb') as f:f.write(json.dumps({'purpose':'Sacrificial diagnosis, not monitor acceptance','files':files},indent=2,sort_keys=True).encode());f.flush();os.fsync(f.fileno())
 with zipfile.ZipFile(R/'evidence.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
  for row in files:z.write(R/row['path'],row['path'])
  z.write(R/'archive-manifest.json','archive-manifest.json')
 with (R/'evidence.zip').open('r+b') as f:os.fsync(f.fileno())
 with zipfile.ZipFile(R/'evidence.zip') as z:
  for row in files:
   if hashlib.sha256(z.read(row['path'])).hexdigest()!=row['sha256'] or sha(R/row['path'])!=row['sha256']:raise RuntimeError('Member mismatch')
 print(json.dumps({'payload_files':len(files),'zip_members':len(files)+1,'sha256':sha(R/'evidence.zip')}))
