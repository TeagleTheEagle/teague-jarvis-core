from pathlib import Path
R=Path(__file__).parent/'candidate'
p=R/'probe_timing.py';s=p.read_text().replace('Observation only: original five-second wait remains authoritative.','Revised sacrificial wait: 5 s warning, fixed 13.6 s launch deadline.')
s=s.replace('from journal import ticks,frequency','from journal import ticks,frequency\nfrom probe_policy import wait_tracked,HardDeadline')
s=s.replace("  self.row['initialKernelTimes']=process_times(self.process);self.row['identityCapturedQpc']=ticks()", "  try:self.row['initialKernelTimes']=process_times(self.process);self.row['identityCapturedQpc']=ticks()\n  except BaseException as ex:self.row['startupIdentityError']=repr(ex)")
a=s.index(' def wait_original(self):');b=s.index(' def finish_observation(self):',a)
s=s[:a]+''' def wait_approved(self,health,warning,campaign_deadline):
  self.row['mainWaitEnteredQpc']=ticks();self.row['slowWarnings']=[]
  origin=self.row['launchRequestedQpc']/self.row['frequency']
  def identity():
   if self.row.get('startupIdentityError'):raise RuntimeError('Initial process identity unavailable')
   if process_times(self.process)[0]!=self.row['initialKernelTimes'][0]:raise RuntimeError('Probe creation identity mismatch')
  def emit(v):
   v.update(pid=self.process.pid,created=self.row['initialKernelTimes'][0],qpc=ticks())
   self.row['slowWarnings'].append(v);warning(v)
  def exit_elapsed():
   ts=process_times(self.process);b=bridge();f=self.row['frequency']
   q=(b['qpcBefore']+b['qpcAfter'])/2+(int(ts[1])-int(b['filetime']))*f/1e7
   self.row['exitConfirmationBridge']=b
   return (q-self.row['launchRequestedQpc'])/f
  try:
   self.row['policy']=wait_tracked(clock=lambda:ticks()/self.row['frequency'],origin=origin,campaign_deadline=campaign_deadline,wait=lambda ms:int(K.WaitForSingleObject(int(self.process._handle),ms)),identity=identity,health=health,warning=emit,exit_elapsed=exit_elapsed)
   code=self.process.poll()
   if code is None:raise RuntimeError('Signaled retained handle did not provide exit code')
   self.row['mainWaitReturnedQpc']=ticks();self.row['timedOut']=False;self.row['hardDeadlineFailure']=False
   return code
  except BaseException as ex:
   self.row['failureCaughtQpc']=ticks();self.row['hardDeadlineFailure']=isinstance(ex,HardDeadline);self.row['timedOut']=isinstance(ex,HardDeadline)
   self.row['policyFailure']=repr(ex);self.row['immediateHandleState']=int(K.WaitForSingleObject(int(self.process._handle),0))
   if isinstance(ex,HardDeadline):self.row['timeoutCaughtQpc']=ticks()
   raise
''' + s[b:];p.write_text(s)
p=R/'collect.py';s=p.read_text().replace('PublisherWatch,ticks','PublisherWatch,ticks,frequency')
needle="try:\n if mode!='idle':"
replacement="""def health():
 if (out/'monitor-failure.json').exists():raise RuntimeError('Monitor failure')
 before=ticks()
 try:v=reader.poll()
 except BaseException:
  save('rejected-poll.json',dict(before=before,after=ticks(),last=reader.last,traceback=traceback.format_exc()));raise
 if v['age']>=10:raise RuntimeError('Heartbeat must remain below ten seconds')
 if not reader.last.get('subscriberHealthy') or reader.last.get('queueFailure'):raise RuntimeError('Subscriber/queue unhealthy')
 samples.append(dict(v,qpc=before,pollEnd=ticks(),phase=mode))
def warning(v):
 with (out/'slow-probe-warnings.jsonl').open('a',encoding='utf-8') as f:
  f.write(json.dumps(v)+'\\n');f.flush()
try:
 if mode!='idle':"""
assert needle in s;s=s.replace(needle,replacement)
s=s.replace("save('phases.json',[phase]);began=time.monotonic();last=-1", "save('phases.json',[phase]);began=time.monotonic();campaign_deadline=ticks()/frequency()+duration+15;last=-1")
a=s.index("  if (out/'monitor-failure.json').exists():raise RuntimeError('Monitor failure')",s.index(' while (child'));b=s.index('  if time.monotonic()-began-last>=1:',a)
s=s[:a]+"  health()\n"+s[b:]
s=s.replace("    item=Probe(R/'J6Probe.exe');", "    health()\n    if ticks()/frequency()+13.6>=campaign_deadline:break\n    item=Probe(R/'J6Probe.exe');")
s=s.replace('code=measured_probe.wait_original();ts=times(p)','code=measured_probe.wait_approved(health,warning,campaign_deadline);ts=times(p)')
s=s.replace(" reader.poll();phase.update(status='COMPLETE'", " health();phase.update(status='COMPLETE'")
# Keep timing evidence on unsuccessful cleanup as well.
s=s.replace("  verified=[]\n save('collector-finished.json'", "  verified=[]\n  save('probe-timings.json',[m.row for m in measured])\n save('collector-finished.json'")
p.write_text(s)
p=R/'monitor.ps1';s=p.read_text()
s=s.replace("Mark 'health.begin';if([EventTap]", "Mark 'health.begin';if(@(Get-EventSubscriber|Where-Object SourceIdentifier -in $ids).Count -ne 2){throw 'Event subscriber lost'};if($exact.Failed){throw 'Event queue failed'};if([EventTap]")
s=s.replace("state='ACTIVE';violations=$violations;events=$count", "state='ACTIVE';violations=$violations;events=$count;subscriberHealthy=$true;queueFailure=$exact.Failed")
p.write_text(s)
p=R/'accept_run.py';s=p.read_text().replace('from workspace import run_dir','from workspace import run_dir\nfrom probe_policy import validate_lifecycle')
s=s.replace(" result=finalize(R)"," validate_lifecycle(read('probe-timings.json'),[json.loads(x) for x in (R/'events.jsonl').read_text().splitlines()],h)\n result=finalize(R)")
p.write_text(s)
p=R/'probe_analysis.py';s=p.read_text().replace("No timeout is converted to success; no acceptance is attempted.","New owner-approved model: 5 s warning, 13.6 s hard deadline; no historical result changed.")
s=s.replace("timeoutCount=sum(x['timedOut'] for x in measurements)","timeoutCount=sum(x['timedOut'] for x in measurements),slowWarningCount=sum(bool(x.get('slowWarnings')) for x in rows)")
p.write_text(s)
p=R/'launch.ps1';s=p.read_text().replace("purpose='bounded finalization sacrificial validation'","purpose='owner-approved revised probe model';probeWarning=5.0;probeHardDeadline=13.6")
p.write_text(s)
print('New isolated candidate updated; predecessor unchanged')
