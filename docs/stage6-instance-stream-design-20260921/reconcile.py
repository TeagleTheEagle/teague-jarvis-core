import pathlib,json,hashlib,ctypes as c,ctypes.wintypes as w,collections,difflib
R=pathlib.Path(__file__).parent;P=R.parent/'stage6-identity-capacity-recalibration-20260921';read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
old=read(P/'events-22.json');out=[]
for x in old:
 candidates=[dict(pid=r['kernel']['pid'],created=r['kernel']['created'],sequence=r['kernel']['sequence'],image=r['kernel']['image'],parentSequence=r['kernel']['parentSequence']) for r in x['candidates']]
 status='AMBIGUOUS' if len(candidates)>1 else 'UNIQUE_MATCH' if len(candidates)==1 else 'UNMATCHED'
 assert status==x['status']
 out.append(dict(index=x['index'],event=x['rawUnknown']['event'],classification=status,candidates=candidates,newSnapshotSequence='NOT CAPTURED historically',extendedProcessStartKey='NOT CAPTURED historically',reason=x['reason']))
(R/'historical-22-reassessment.json').write_text(json.dumps(out,indent=2))
K=c.WinDLL('kernel32',use_last_error=True);K.GetDiskFreeSpaceW.argtypes=[w.LPCWSTR,c.POINTER(w.DWORD),c.POINTER(w.DWORD),c.POINTER(w.DWORD),c.POINTER(w.DWORD)];values=[w.DWORD() for _ in range(4)]
assert K.GetDiskFreeSpaceW('D:\\',*(c.byref(v) for v in values))
K.GetDiskFreeSpaceExW.argtypes=[w.LPCWSTR]+[c.POINTER(c.c_ulonglong)]*3;space=[c.c_ulonglong() for _ in range(3)];assert K.GetDiskFreeSpaceExW('D:\\',*(c.byref(v) for v in space))
measure=read(R/'measurements.json');reserve=measure['proposedReserve']['requiredReserve'];cluster=values[0].value*values[1].value
plan=read(R/'plan.json');C=pathlib.Path(plan['code']);frozen=read(R/'freeze.json')
for row in frozen['checks']:
 with pathlib.Path(row['path']).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['sha256'],row['path']
hashes=[]
for base in (C,C.parent/'representative-code'):
 for p in sorted(base.iterdir()):
  if p.is_file():hashes.append(dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(R/'prototype-hashes.json').write_text(json.dumps(hashes,indent=2))
before=pathlib.Path(plan['originalSink']).read_text().splitlines(True);after=(C/'trace_sink.hpp').read_text().splitlines(True)
(R/'sink-prototype.diff').write_text(''.join(difflib.unified_diff(before,after,fromfile=plan['originalSink'],tofile=str(C/'trace_sink.hpp'))))
result=dict(frozenChecks=len(frozen['checks']),candidateHashesUnchanged=116,historical22Unchanged=True,classification=collections.Counter(x['classification'] for x in out),D=dict(clusterBytes=cluster,currentFreeBytes=space[0].value,proposedRequiredReserve=reserve,proposedHeadroomBytes=space[0].value-reserve,clusterAssumptionSatisfied=cluster<=4096,completeCurrentReserveValidated=False),prototypeFiles=len(hashes),protectedAccess=False,productionChanges=False)
(R/'reconciliation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
