import pathlib,json,hashlib,shutil,os,ast,pefile
R=pathlib.Path(__file__).resolve().parent;plan=json.loads((R/'plan.json').read_text());D=pathlib.Path(plan['live_code'])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for p in (R/'candidate').iterdir():
 if p.suffix=='.py':ast.parse(p.read_text(),filename=str(p))
 shutil.copyfile(p,D/p.name)
rows=[dict(name=p.name,sha256=sha(p),size=p.stat().st_size) for p in sorted((R/'candidate').iterdir())]
with (R/'candidate-hashes.json').open('x') as f:json.dump(rows,f,indent=2)
images=[]
for name in ('J6ProbeNative.exe','J6ProbeToken.exe'):
 p=D/name;q=R/'images'/name
 if sha(p)!=sha(q):raise RuntimeError('C/D image mismatch')
 pe=pefile.PE(str(p));imports={m.dll.decode():[x.name.decode() if x.name else str(x.ordinal) for x in m.imports] for m in pe.DIRECTORY_ENTRY_IMPORT}
 images.append(dict(dPath=str(p),cPath=str(q),sha256=sha(p),imports=imports))
with (R/'helper-images.json').open('x') as f:json.dump(images,f,indent=2)
with (R/'environment-policy.json').open('x') as f:json.dump(dict(inheritsParent=True,perRunOverrides=['TEMP','TMP'],overridesVolume='D',recordedNonsecretValues={n:os.environ.get(n) for n in ('SystemRoot','ComSpec','PROCESSOR_ARCHITECTURE')},otherValues='NOT RECORDED; may contain credentials',dllSearch='normal Windows loader; no PATH/security change in probe launcher',workingDirectory=str(D)),f,indent=2)
print(json.dumps(dict(frozenFiles=len(rows),helperImages=images)))
