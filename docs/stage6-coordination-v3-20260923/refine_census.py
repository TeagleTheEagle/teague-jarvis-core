import pathlib,json,hashlib,zipfile
R=pathlib.Path(__file__).resolve().parent;C=pathlib.Path(json.loads((R/'before.json').read_text())['candidate'])
old=json.loads((R/'candidate-frozen.json').read_text())
with zipfile.ZipFile(R/'draft-r1-source.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
 for row in old['files']:
  p=C/row['name'];assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'];z.write(p,row['name'])
 z.write(C/'small-source-v3.json','small-source-v3.json')
p=C/'terminal_control_v3.ps1';s=p.read_text()
a="   $known=@($expected|Where-Object {$_.pid -eq $p.ProcessId -and $_.created -ceq $p.CreationDate.ToUniversalTime().ToFileTimeUtc().ToString()})"
b="""   $nativeProcess=Get-Process -Id $p.ProcessId -ErrorAction Stop
   try{$nativeCreated=$nativeProcess.StartTime.ToUniversalTime().ToFileTimeUtc().ToString()}finally{$nativeProcess.Dispose()}
   $known=@($expected|Where-Object {$_.pid -eq $p.ProcessId -and $_.created -ceq $nativeCreated})"""
assert a in s;s=s.replace(a,b);p.write_text(s)
rows=[]
for row in old['files']:
 p=C/row['name'];rows.append(dict(name=row['name'],bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
# The first draft and its manifest remain archived; no historical/frozen input changes.
(C/'small-source-v3.json').write_text(json.dumps(rows,indent=2))
out=dict(candidate=str(C),revision=2,reason='CIM/native creation precision mismatch, confirmed read-only',sourceFiles=len(rows),manifestSHA256=hashlib.sha256((C/'small-source-v3.json').read_bytes()).hexdigest(),files=rows)
with (R/'candidate-final-r2.json').open('x') as f:json.dump(out,f,indent=2)
print('DRAFT_R1_PRESERVED_FINAL_R2_FROZEN')
