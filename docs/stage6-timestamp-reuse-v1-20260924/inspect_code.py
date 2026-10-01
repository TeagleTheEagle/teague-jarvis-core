from prepare import *
streams=[]
for root,names in [(C,['fixture.asm','authority_trace_v3.asm','startup_trace.asm']),(C.parent/'reference',['fixture.asm'])]:
 for name in names:
  # MSVC /Fa: emitted a directory named stream. Preserve it verbatim as a normal archiveable file.
  source=pathlib.Path(str(root)+':'+name);target=root/name
  with source.open('rb') as f:content=f.read()
  with target.open('xb') as f:f.write(content)
  assert sha(source)==sha(target)
  streams.append(dict(source=str(source),copy=rec(target)))
write(R/'assembly-stream-preservation.json',streams)
for root,label in [(C,'reuse'),(C.parent/'reference','reference')]:
 text=(root/'fixture.asm').read_text(errors='replace')
 lines=text.splitlines()
 out=[];active=False
 for line in lines:
  if ('clock_path PROC' in line) or ('??1CallbackScope' in line and ' PROC' in line):active=True
  if active:out.append(line)
  if active and ' ENDP' in line:active=False
 (R/f'assembly-{label}-extract.txt').write_text('\n'.join(out))
 print(label,[(x.strip()) for x in out if 'call' in x and not x.lstrip().startswith(';')])
