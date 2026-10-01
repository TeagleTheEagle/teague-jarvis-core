import pathlib,hashlib,json,sys
R=pathlib.Path(__file__).parent;name,which=sys.argv[1:];assert name in ('dry1','dry2') and which in ('before','after')
source=R.parent/'stage6-heartbeat-journal-20260918'/'sacrificial';result={}
files=sorted(source.iterdir());assert len(files)==12
for p in files:
 assert p.is_file() and p.suffix=='.bin'
 s=p.stat();h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(4194304):h.update(b)
 end=p.stat();assert s.st_size==end.st_size and s.st_mtime_ns==end.st_mtime_ns
 result[p.name]={'size':s.st_size,'mtime_ns':s.st_mtime_ns,'sha256':h.hexdigest()}
(R/name/f'source-{which}.json').write_text(json.dumps(result,sort_keys=True,indent=2))
