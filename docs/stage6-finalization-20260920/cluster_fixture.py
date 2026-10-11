from pathlib import Path
R=Path(__file__).parent/'candidate'
p=R/'collect.py';s=p.read_text();a=s.index("   measured_probe=Probe(R/'J6Probe.exe');");b=s.index("  if time.monotonic()-began>duration+15",a)
old=s[a:b];tail=old[old.index("   p=measured_probe.process"):]
# Launch first batch before waiting, retain all handles immediately. Same five-second wait.
tail=tail.replace(";handles.append(p)","")
tail='\n'.join(' '+line if line else line for line in tail.split('\n'))
s=s[:a]+"""   cluster=config.get('cluster',1) if not measured else 1
   if type(cluster) is not int or not 1<=cluster<=8:raise RuntimeError('Bounded cluster fixture required')
   batch=[]
   for _ in range(cluster):
    item=Probe(R/'J6Probe.exe');measured.append(item);handles.append(item.process);batch.append(item)
   for measured_probe in batch:
"""+tail+s[b:];p.write_text(s)
p=R/'launch.ps1';s=p.read_text().replace("[string]$Label)","[string]$Label,[ValidateRange(1,8)][int]$Cluster=1)").replace("duration=$Duration;threshold=10", "duration=$Duration;cluster=$Cluster;threshold=10");p.write_text(s)
print('Optional bounded first-batch concurrent probe fixture added')
