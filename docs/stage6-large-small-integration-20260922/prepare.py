import pathlib,json,hashlib,uuid,shutil,difflib,os
R=pathlib.Path(__file__).parent
OLD=R.parent/'stage6-health-journal-candidate-20260922'
rows=json.loads((OLD/'candidate-frozen.json').read_text())['files']
base=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\e55504d627d24f24a6f56f9e2435230b\code')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert all(sha(pathlib.Path(x['path']))==x['sha256'] for x in rows)
assert shutil.disk_usage(base).free>300*2**30,'Both trace hard caps plus archival reserve required'
C=base.parent.parent/uuid.uuid4().hex/'code';C.mkdir(parents=True)
for x in rows:
 p=pathlib.Path(x['path']);dst=C/p.relative_to(base);dst.parent.mkdir(exist_ok=True,parents=True);shutil.copy2(p,dst)
changed=[]
for name in ('dry_health.py','small_binding.py','small_launch.ps1','small_check.py','test_small_binding.py'):
 p=C/name;old=p.read_text() if p.exists() else '';new=(R/name).read_text().replace('@CODE@',str(C).replace('\\','\\\\'))
 p.write_text(new,encoding='utf8');changed.append(dict(name=name,before=hashlib.sha256(old.encode()).hexdigest() if old else None,after=sha(p)))
 (R/(name+'.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='frozen/'+name,tofile='candidate/'+name)))
old=(C/'traced_collect.py').read_text();new=old.replace("  result=collector.main(root)","  from baseline_contract import advance\n  advance(root,'PREPARED','OBSERVERS_READY')\n  result=collector.main(root)")
assert new!=old
(C/'traced_collect.py').write_text(new)
changed.append(dict(name='traced_collect.py',before=hashlib.sha256(old.encode()).hexdigest(),after=sha(C/'traced_collect.py')))
(R/'traced_collect.py.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True))))
coverage=(C/'medium-checker'/'coverage.py').read_text()
coverage=coverage.replace("'OS_CONSOLE_HELPER','APPLICATION_OBSERVER')", "'OS_CONSOLE_HELPER','APPLICATION_OBSERVER','DETAIL_OBSERVER')")
(C/'small_coverage.py').write_text(coverage)
changed.append(dict(name='small_coverage.py',before=None,after=sha(C/'small_coverage.py')))
data=C/'small-synthetic';data.mkdir()
for i in range(12):
 with (data/f'{i:02}.bin').open('xb') as f:f.write(bytes([i])*65536);f.flush();os.fsync(f.fileno())
for name,value in [('baseline-allowlist.json',dict(syntheticRoots=[str(data)],approvedProtectedRoots=[],realProtectedAccess=False)),('baseline-limits.json',dict(campaign=90.0,monitor=180.0,hold=0.0,heartbeat=10.0,probe=13.6,observer=15.0))]:
 (C/name).write_text(json.dumps(value,indent=2))
files=[dict(name=str(p.relative_to(C)),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(C.rglob('*')) if p.is_file()]
(C/'small-source.json').write_text(json.dumps(files,indent=2))
(R/'candidate.json').write_text(json.dumps(dict(code=str(C),source=str(data),changes=changed,files=files,priorFiles=len(rows)),indent=2))
print(C)
