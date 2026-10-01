"""Fixed one-run TEST driver. Never invokes the finalizer or retries a run."""
import subprocess,sys,pathlib,time,os,ctypes,json
from workspace import CODE,run_dir,activate_temp
from journal import ticks,frequency
from coordination_v3 import *
from small_binding_v3 import validate
from workspace_binding_v4 import verify as verify_workspace,tool,child_environment
from evidence_support import K,times,image
PWSH=r'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'

def final_census(root,p,launcher,observations):
 # Same host-context read-only census policy; no UAC and no protected-file reads.
 script=r'''$ErrorActionPreference='Stop';$all=@(Get-CimInstance Win32_Process);$found=@($all|Where-Object{$_.ProcessId -ne $PID -and $_.ProcessId -ne CONTROLLER_PID -and ($_.Name -match '^(VBox|VirtualBox|J6)' -or ($_.Name -match '^(python|pwsh|powershell)' -and $_.CommandLine -like '*D:\JARVIS-STAGE6-LIVE*'))}|Select-Object ProcessId,CreationDate,ExecutablePath);$tr=@(& 'C:\Windows\System32\logman.exe' query -ets 2>&1|ForEach-Object{"$_"});if($LASTEXITCODE -ne 0){throw 'TRACE_CENSUS_UNAVAILABLE'};@{processes=$found;traces=@($tr|Where-Object{$_ -match '(?i)J6|JARVIS|Stage6'})}|ConvertTo-Json -Depth 5 -Compress'''.replace('CONTROLLER_PID',str(os.getpid()))
 started=ticks();left=before(p,started)/p['binding']['frequency']
 result=subprocess.run([PWSH,'-NoProfile','-Command',script],capture_output=True,text=True,timeout=min(10,left),creationflags=0x08000000)
 need(result.returncode==0,'FINAL_CENSUS_UNAVAILABLE');raw=json.loads(result.stdout)
 v=dict(kind='final-cleanup',binding=p['binding'],available=True,unknown=[],workloadRemaining=[],matchingProcesses=raw['processes'],traceSessions=raw['traces'],launcherExitVerified=launcher,observerExitsVerified=observations,startedQpc=started,completedQpc=ticks())
 census(p,v,True);write_once(root/'final-census-v3.json',v);return v

def main(run,approved=False):
 need(approved is True,'SEPARATE_OWNER_LIVE_APPROVAL_REQUIRED')
 root=run_dir(run);activate_temp(root);validate(root,load(root/'small-declaration-v3.json'))
 need(not any((root/n).exists() for n in ('launcher-identity.json','phase-a-v3.json','rejected-v3.json')),'RUN_ALREADY_USED')
 verify_workspace(root)
 me=K.GetCurrentProcess();write_once(root/'external-controller-v3.json',dict(pid=os.getpid(),created=times(me)[0],image=image(me),qpc=ticks()))
 proc=None;p=None
 try:
  with (root/'driver-stdout-v3.bin').open('xb') as out,(root/'driver-stderr-v3.bin').open('xb') as err:
   proc=subprocess.Popen([PWSH,'-NoProfile','-File',str(CODE/'small_launch_v4.ps1'),'-Run',run],cwd=CODE,stdout=out,stderr=err,creationflags=0x08000000,close_fds=True,env=child_environment(root))
   launcher=dict(pid=proc.pid,created=times(int(proc._handle))[0],image=image(int(proc._handle)))
   gates=set()
   while proc.poll() is None:
    for ready,gate in (('etw-ready.json','allow-detail-prompt'),('detail/etw-ready.json','allow-app-prompt')):
     if gate not in gates and (root/ready).is_file():write_once(root/gate,dict(run=run,existingSequentialPrompt=True));gates.add(gate)
    if (root/'phase-a-v3.json').exists():p=load(root/'phase-a-v3.json');before(p,ticks())
    elif (root/'cleanup-origin-v3.json').exists():
     origin=load(root/'cleanup-origin-v3.json');need(origin['frequency']==frequency() and origin['deadlineQpc']==origin['cleanupEntryQpc']+20*frequency() and ticks()<origin['deadlineQpc'],'ABSOLUTE_DEADLINE')
    time.sleep(min(.01,max(0,(p['deadlineQpc']-ticks())/frequency())) if p is not None else .01)
   exit_qpc=ticks();need(proc.returncode==0,'LAUNCHER_FAILED')
   need(int(K.WaitForSingleObject(int(proc._handle),0))==0 and times(int(proc._handle))[0]==launcher['created'],'LAUNCHER_INSTANCE_EXIT')
   need(p is not None,'MISSING_PHASE_A');before(p,exit_qpc)
   observed=load(root/'launcher-identity.json');need(identity(observed)==identity(launcher) and norm(observed['image'])==norm(launcher['image']),'LAUNCHER_IDENTITY')
   obs=load(root/'observer-exits-v3.json');need(obs['error'] is None,'OBSERVER_FAILURE')
   identities=load(root/'observer-identities.json')
   for role,name in (('application','app'),('detail','detail'),('authority','etw')):
    need(identity(obs['observers'][role])==identity(identities[name]),'OBSERVER_REUSE')
   app=load(root/'app-result.json');detail=load(root/'detail'/'etw-result.json');kernel=load(root/'etw-result.json')
   obs['observers']['application']['drained']=bool(app['success'] and app['durableFinalization'] and app['queue']['remaining']==0)
   for role,row in (('detail',detail),('authority',kernel)):
    obs['observers'][role]['drained']=bool(row['requestedStop'] and all(row[f]==0 for f in ('faults','eventsLost','realtimeBuffersLost','buffersLost','flushResult','stopResult','consumerResult')))
   v=dict(binding=p['binding'],launcher=launcher,launcherExitQpc=exit_qpc,launcherExitVerified=True,launcherExitCode=proc.returncode,observers=obs['observers'],durableComplete=all(x['drained'] for x in obs['observers'].values()),authoritativeContradictions=[],allRequiredHandlesClosed=all(x['handleClosed'] for x in kernel['rows']),completedQpc=ticks())
   closure(p,v);write_once(root/'external-exits-v3.json',v)
   final_census(root,p,True,True)
   from completed_v3 import verify_complete
   verify_complete(root)
   states=[dict(state=s,owner=OWNERS[i],binding=p['binding']) for i,s in enumerate(STATES[:12])]
   write_once(root/'coordination-states-v3.json',dict(kind='evidence-reconciled-state-sequence',states=states,evidence={n:digest(root/n) for n in ('phase-a-v3.json','terminal-v3.json','workload-census-v3.json','integration-launcher.json','external-exits-v3.json','final-census-v3.json')}))
   print('COMPLETED_EVIDENCE_PENDING_CHECKER_AND_ARCHIVE')
 except BaseException as exc:
  if not (root/'rejected-v3.json').exists():write_once(root/'rejected-v3.json',dict(state='REJECTED',reason=type(exc).__name__+': '+str(exc),qpc=ticks()))
  raise
 finally:
  if proc is not None and hasattr(proc,'_handle'):proc._handle.Close()
if __name__=='__main__':
 need(len(sys.argv)==3 and sys.argv[2]=='--owner-approved-one-small-run','EXPLICIT_ONE_RUN_APPROVAL_REQUIRED')
 main(sys.argv[1],True)
