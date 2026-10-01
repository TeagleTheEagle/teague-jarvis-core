from pathlib import Path
R=Path(__file__).parent;P=R.parent/'stage6-required-coverage-20260921'
s=(P/'coverage.py').read_text().replace("'parent')","'parent','source','capture')")
for a,b in [('probe','DIRECT_PROBE'),('worker','DIRECT_WORKER'),('console','OS_CONSOLE_HELPER'),('infrastructure','APPLICATION_OBSERVER')]:s=s.replace("'"+a+"'","'"+b+"'")
s=s.replace("role in ('OS_CONSOLE_HELPER','APPLICATION_OBSERVER')","role=='OS_CONSOLE_HELPER'")
needle="  need_native=role in ('DIRECT_PROBE','DIRECT_WORKER')"
assert needle in s
s=s.replace(needle,'''  direct=role in ('DIRECT_PROBE','DIRECT_WORKER')
  source='creator-owned-handle' if direct else 'tracer-opened-handle'
  check('source',bool(h.get('source')),h.get('source')==source)
  absolute=bool(h.get('image')) and PureWindowsPath(h['image']).is_absolute() and '\\x00' not in h['image'] and '..' not in PureWindowsPath(h['image']).parts
  if direct:
   good=h.get('handlePid')==key[0] and h.get('creatorPid')==x.get('parentPid') and h.get('processState')==258 and h.get('success') is True and bool(h.get('handleIdentity'))
   good=good and x['startQpc']<=h.get('handleAcquiredQpc',0)<=h.get('queryBeginQpc',0)<=h.get('queryEndQpc',0)<h.get('identityPersistedQpc',0)<n.get('entryQpc',0)<=x['stopQpc'] and absolute
  else:
   good=qualified or (absolute and x['startQpc']<=h.get('queryBeginQpc',0)<=h.get('queryEndQpc',0)<x['stopQpc'])
  check('capture',bool(hs),good)
'''+needle)
with (R/'coverage.py').open('x') as f:f.write(s)
t=(P/'test_coverage.py').read_text()
for a,b in [('probe','DIRECT_PROBE'),('worker','DIRECT_WORKER'),('console','OS_CONSOLE_HELPER')]:t=t.replace("'"+a+"'","'"+b+"'")
t=t.replace("exitCode=0,parentVerified=True","exitCode=0,parentPid=500,parentVerified=True")
t=t.replace("imageError=0,retained=True", "imageError=0,source='tracer-opened-handle' if role=='OS_CONSOLE_HELPER' else 'creator-owned-handle',handlePid=i,creatorPid=500,processState=258,success=True,handleIdentity='123',handleAcquiredQpc=11,queryBeginQpc=12,queryEndQpc=13,identityPersistedQpc=14,retained=True")
t=t.replace("C:\\\\untrusted\\\\probe.exe","C:\\\\untrusted\\\\DIRECT_PROBE.exe")
needle="with (R/'coverage-tests.json').open('x')"
extra='''
for label,error in [('access denied',5),('invalid handle',6),('already exited',31),('insufficient buffer',122),('unexpected error',999)]:
 case(label,lambda d,e=error:d['handles'][0].update(image='',imageError=e,success=False),'FAIL')
case('malformed relative path',lambda d:d['handles'][0].update(image='DIRECT_PROBE.exe'),'FAIL')
case('NUL image',lambda d:d['handles'][0].update(image='D:\\\\test\\\\x\\x00.exe'),'FAIL')
case('query after exit',lambda d:d['handles'][0].update(queryBeginQpc=51,queryEndQpc=52),'FAIL')
case('persist after native entry',lambda d:d['handles'][0].update(identityPersistedQpc=21),'FAIL')
case('direct source cannot be tracer',lambda d:d['handles'][0].update(source='tracer-opened-handle'),'FAIL')
case('helper tracer source missing',lambda d:d['handles'][2].update(source=''),'FAIL')
case('helper image absent is not NA',lambda d:d['handles'][2].update(image=''),'FAIL')
case('helper live image query after exit',lambda d:d['handles'][2].update(queryBeginQpc=51,queryEndQpc=52),'FAIL')
case('other helper not implicitly console',lambda d:d['expected'][2].update(role='OTHER_INDIRECT_HELPER'),'FAIL')
case('creator PID differs',lambda d:d['handles'][0].update(creatorPid=999),'FAIL')
case('handle PID differs',lambda d:d['handles'][0].update(handlePid=999),'FAIL')
case('creation mismatches',lambda d:d['handles'][0].update(handleCreated='999'),'FAIL')
case('probe already signaled at capture',lambda d:d['handles'][0].update(processState=0),'FAIL')
'''
t=t.replace(needle,extra+'\n'+needle)
with (R/'test_coverage.py').open('x') as f:f.write(t)
