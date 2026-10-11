import pathlib,json,subprocess,hashlib
R=pathlib.Path(__file__).resolve().parent;repo=R.parent.parent
state={}
for name,args in [('head',['rev-parse','HEAD']),('branch',['branch','--show-current']),('status',['status','--porcelain=v1','-unormal'])]:
 p=subprocess.run(['git','-C',str(repo),*args],capture_output=True,text=True);state[name]=dict(exit=p.returncode,stdout=p.stdout,stderr=p.stderr)
p=subprocess.run(['git','-C',str(repo),'ls-files','-z'],capture_output=True,check=True)
state['trackedApplication']=[dict(path=n,sha256=hashlib.sha256((repo/n).read_bytes()).hexdigest()) for n in p.stdout.decode().split('\0') if n and not n.startswith(('docs/','.env')) and (repo/n).is_file()]
with (R/'repository-before.json').open('x') as f:json.dump(state,f,indent=2)
print(len(state['trackedApplication']))
