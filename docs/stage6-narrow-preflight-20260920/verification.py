"""Report-only integrity verification; never follows archive source-path fields."""
import pathlib,json,hashlib,zipfile
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def verify_hash(path,expected):
 raw=pathlib.Path(path).read_bytes()
 if sha_bytes(raw)!=expected:raise ValueError('Hash mismatch: '+str(path))
 return raw
def verify_archive(root,receipt):
 root=pathlib.Path(root)
 verify_hash(root/'evidence.zip',receipt['zipSHA256'])
 raw=verify_hash(root/'archive-manifest.json',receipt['manifestSHA256']);m=json.loads(raw)
 names=[x['name'] for x in m['files']]
 if len(names)!=len(set(names)):raise ValueError('Duplicate manifest members')
 with zipfile.ZipFile(root/'evidence.zip') as z:
  if len(z.namelist())!=receipt['members'] or len(z.namelist())!=len(names)+1 or set(z.namelist())!=set(names)|{'archive-manifest.json'}:raise ValueError('Archive member set mismatch')
  for x in m['files']:
   # x['source'] is provenance only. DO NOT stat, open, resolve or traverse it.
   data=z.read(x['name'])
   if sha_bytes(data)!=x['sha256'] or ('bytes' in x and len(data)!=x['bytes']):raise ValueError('Archive member mismatch')
  if z.read('archive-manifest.json')!=raw:raise ValueError('Embedded manifest mismatch')
 return m
def verify_candidate(root,rows):
 names=[]
 for x in rows:
  n=x['name']
  if pathlib.PureWindowsPath(n).name!=n or n in ('.','..') or ':' in n or '/' in n or '\\' in n or n.casefold() in names:raise ValueError('Invalid candidate member')
  names.append(n.casefold());verify_hash(pathlib.Path(root)/n,x['sha256'])
 return len(rows)
def verify_calibration(paths):
 return [json.loads(verify_hash(p,h)) for p,h in paths]
def verify_safety(v):
 if v['processes'] or v['traces'] or v['traceExit']!=0:raise ValueError('Process/trace preflight failed')
 return True
