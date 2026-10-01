import pathlib,json,hashlib,zipfile,shutil,datetime,difflib
R=pathlib.Path(__file__).parent
P=R.parent/'stage6-precise-overhead-20260924'
OLD=R.parent/'stage6-final-measurement-v3-20260924'
C=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\a34f91e1db274bf78fc5a80e2a9d417c\code')
W=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\component-attribution-20260924-7f29a680')
def load(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with pathlib.Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with pathlib.Path(p).open('x',encoding='utf8') as f:json.dump(x,f,indent=2)
def verify(row):
 p=pathlib.Path(row['path']);s=p.stat();assert not s.st_file_attributes&0x400
 assert sha(p)==row['sha256'];assert s.st_size==row['bytes']
 if 'mtimeNs' in row:assert s.st_mtime_ns==row['mtimeNs']
if __name__=='__main__':
 assert not W.exists()
 preserved=load(OLD/'candidate-artifact-manifest.json')['files']+load(OLD/'before.json')['inputs']+load(OLD/'historical-precheck.json')['evidence']
 for row in preserved:verify(row)
 receipt=load(P/'archive-receipt.json');assert sha(receipt['archive'])==receipt['archiveSHA256']
 with zipfile.ZipFile(receipt['archive']) as z:
  assert len(z.namelist())==len(set(z.namelist()))==143
  manifest=json.loads(z.read('archive-manifest.json'))
  for row in manifest['entries']:
   verify(row)
   with z.open(row['name']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['sha256']
  assert hashlib.sha256(z.read('archive-manifest.json')).hexdigest()==receipt['manifestSHA256']
  preserved+=manifest['entries']
 put(R/'before.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),preserved=preserved,archive=receipt))
 W.mkdir();(W/'build-temp').mkdir();(W/'raw').mkdir()
 shutil.copy2(C/'loss_measurement_v3.hpp',W/'loss_measurement_v3.hpp')
 source=(C/'loss_measurement_fixture_v3.cpp').read_text()
 begin=source.index('static void dispatch(');end=source.index('static void check(',begin)
 original=source[begin:end]
 branch=next(x for x in original.splitlines() if x.startswith(' if(tap.enabled)'))
 clock=original.replace('static void dispatch(','static void dispatch_clock(',1).replace(branch,' if(tap.enabled){auto completion=j6m::tick();(void)completion;}')
 storage=original.replace('static void dispatch(','static void dispatch_storage(',1).replace('v.completionQpc=j6m::tick();','v.completionQpc=arrival;')
 book=original.replace('static void dispatch(','static void dispatch_bookkeeping(',1).replace(branch,' if(tap.enabled){if(tap.enabled){++tap.attempted;if(tap.count==tap.capacity){++tap.overflow;}else{++tap.count;}}}')
 tbegin=source.index('static Trial trial(');tend=source.index('int main(',tbegin)
 generic=source[tbegin:tend].replace('static Trial trial(','static Trial attribution_trial(',1).replace('long long frequency){','long long frequency,void(*fn)(EVENT_RECORD*,j6m::LifecycleTap&)){',1).replace('dispatch(&e,tap)','fn(&e,tap)')
 prefix=source[:tend]+clock+storage+book+generic
 tail=(R/'fixture-main.inc').read_text()
 result=prefix+tail
 assert original in result and sha(W/'loss_measurement_v3.hpp')==sha(C/'loss_measurement_v3.hpp')
 (W/'attribution_fixture.cpp').write_text(result)
 (R/'fixture.diff').write_text(''.join(difflib.unified_diff(source.splitlines(True),result.splitlines(True),fromfile='unchanged_reference',tofile='BENCHMARK_ONLY_attribution_fixture')))
 put(W/'BENCHMARK_ONLY.json',dict(liveEligible=False,acceptanceInstrumentation=False,referenceHeaderSHA256=sha(C/'loss_measurement_v3.hpp'),referenceSourceSHA256=sha(C/'loss_measurement_fixture_v3.cpp'),originalDispatchTextSHA256=hashlib.sha256(original.encode()).hexdigest(),note='Partial variants are never usable as real diagnostic evidence'))
 print('Preservation PASS; new benchmark-only fixture generated; original recorder untouched')
