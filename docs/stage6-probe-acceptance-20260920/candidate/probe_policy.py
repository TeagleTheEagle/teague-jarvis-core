"""Owner-approved 2026-09-20 sacrificial policy. No production authority."""
WARNING_SECONDS=5.0
HARD_SECONDS=13.6
SLICE_SECONDS=.05
class ProbeFailure(RuntimeError):pass
class HardDeadline(ProbeFailure):pass

def wait_tracked(*,clock,origin,campaign_deadline,wait,identity,health,warning,exit_elapsed):
 """Relative handle waits never reset absolute monotonic acceptance deadlines.
 State 0 = signaled; 258 = running; any other value fails closed.
 All callbacks are the actual integration operations, injected in boundary tests.
 """
 deadline=min(origin+HARD_SECONDS,campaign_deadline)
 warned=False;checks=0
 def warn(elapsed,reason):
  nonlocal warned
  if not warned:
   warning(dict(kind='SLOW_PROBE_WARNING',observedElapsed=elapsed,threshold=WARNING_SECONDS,reason=reason));warned=True
 while True:
  health();identity();checks+=1;now=clock()
  if now>=deadline:raise HardDeadline('PROBE_HARD_DEADLINE: fixed launch/campaign deadline reached')
  state=wait(0)
  if state not in (0,258):raise ProbeFailure('Retained process handle failed')
  if state==0:
   health();identity();now=clock()
   if now>=deadline:raise HardDeadline('PROBE_HARD_DEADLINE: exit confirmation too late')
   elapsed=exit_elapsed()
   if elapsed is None or elapsed<0 or elapsed>=HARD_SECONDS:raise HardDeadline('PROBE_HARD_DEADLINE: invalid/late exit evidence')
   if elapsed>WARNING_SECONDS:warn(now-origin,'kernel-exit estimate exceeds five seconds')
   # Warning persistence/identity collection cannot push a completion beyond the deadline.
   if clock()>=deadline:raise HardDeadline('PROBE_HARD_DEADLINE: completion evidence late')
   return dict(status='ELIGIBLE_PENDING_LIFECYCLE',warning=warned,confirmedElapsed=now-origin,exitElapsedEstimate=elapsed,healthChecks=checks,hardSeconds=HARD_SECONDS,warningSeconds=WARNING_SECONDS)
  if now-origin>=WARNING_SECONDS:warn(now-origin,'retained handle still running at threshold check')
  now=clock()
  if now>=deadline:raise HardDeadline('PROBE_HARD_DEADLINE: health/warning operation exceeded deadline')
  seconds=min(SLICE_SECONDS,deadline-now)
  if now<origin+WARNING_SECONDS:seconds=min(seconds,origin+WARNING_SECONDS-now)
  state=wait(max(1,int(seconds*1000)))
  if state not in (0,258):raise ProbeFailure('Retained process handle failed while waiting')

def validate_lifecycle(rows,events,handles):
 """Warning eligibility never substitutes for actual retained exits/START/STOP."""
 if not rows or len(rows)!=len(handles):raise ProbeFailure('Missing probe/retained identity')
 if len({x['pid'] for x in rows})!=len(rows):raise ProbeFailure('Duplicate PID')
 if len(events)!=2*len(rows):raise ProbeFailure('Lifecycle count mismatch')
 by={x['pid']:x for x in handles}
 if len(by)!=len(handles):raise ProbeFailure('Ambiguous retained handles')
 for row in rows:
  p=row.get('policy',{});h=by.get(row['pid']);ts=row.get('finalKernelTimes')
  if p.get('status')!='ELIGIBLE_PENDING_LIFECYCLE' or row.get('hardDeadlineFailure') or row.get('timedOut'):raise ProbeFailure('Probe failed policy')
  if p.get('hardSeconds')!=HARD_SECONDS or p.get('warningSeconds')!=WARNING_SECONDS or not 0<=p.get('confirmedElapsed',HARD_SECONDS)<HARD_SECONDS or not 0<=p.get('exitElapsedEstimate',HARD_SECONDS)<HARD_SECONDS:raise ProbeFailure('Unapproved/late deadline evidence')
  if not h or not ts or ts[0]!=h['times'][0] or ts[1]!=h['times'][1] or int(ts[1])<=int(ts[0]) or h['exit']!=0 or row.get('actualExitCode')!=0 or row.get('finalHandleState')!=0:raise ProbeFailure('Identity/cleanup/orphan failure')
  if p['exitElapsedEstimate']>WARNING_SECONDS and not p.get('warning'):raise ProbeFailure('Missing slow warning')
  for kind in ('start','stop'):
   if sum(e['pid']==row['pid'] and e['kind']==kind for e in events)!=1:raise ProbeFailure('Missing/duplicate lifecycle record')
