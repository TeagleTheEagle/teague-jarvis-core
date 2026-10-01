"""Fail-closed reconciliation of diagnostic ETW and retained-handle evidence."""
import json,pathlib,sys,collections
def reconcile(root):
 root=pathlib.Path(root);e=json.loads((root/'etw-result.json').read_text());ready=json.loads((root/'etw-ready.json').read_text());launcher=json.loads((root/'launcher.json').read_text());lr=json.loads((root/'launcher-result.json').read_text())
 errors=[];rows=e['rows'];freq=ready['frequency'];keys={};sequences={};out=[]
 for k in ('eventsLost','realtimeBuffersLost','buffersLost','faults','stopResult','flushResult','consumerResult'):
  if e[k]!=0:errors.append(f'{k}={e[k]}')
 if not e['requestedStop'] or not lr['exited'] or lr['exitCode']!=0:errors.append('Incomplete consumer shutdown')
 tree=json.loads((root/'tree-handles.json').read_text()) if (root/'tree-handles.json').exists() else dict(rows=[])
 retained={(r['pid'],r['created']):r for r in tree['rows']}
 for r in rows:
  key=(r['pid'],r['created']);seq=r['sequence']
  if key in keys or seq=='0' or seq in sequences:errors.append(f'Duplicate/missing identity {key}')
  keys[key]=r;sequences[seq]=r
 for r in rows:
  key=(r['pid'],r['created']);problems=[]
  if not r['stopQpc'] or not r['exitCodeKnown'] or int(r['exitFiletime'])<int(r['created']):problems.append('MISSING_EXIT')
  if not r['image'] or not r['handleClosed']:problems.append('MISSING_IMAGE_OR_UNCLOSED_HANDLE')
  if r['parentPid']==launcher['pid']:
   if int(r['created'])<int(launcher['creationFiletime']):problems.append('ROOT_CREATION_MISMATCH')
  else:
   p=sequences.get(r['parentSequence'])
   if not p or p['pid']!=r['parentPid'] or not int(p['created'])<=int(r['created'])<=int(p['exitFiletime']):problems.append('PARENT_IDENTITY_MISMATCH')
  t=retained.get(key)
  if t:
   if not t['closed'] or not t['signalObservedQpc'] or t['exitFiletime']!=r['exitFiletime'] or t['exitCode']!=r['exitCode']:problems.append('RETAINED_EXIT_MISMATCH')
  kept=bool(t) or r['handleRetained']
  if r['handleRetained']:
   if r['reason']!='RETAINED_MATCHING_KERNEL_CREATION' or not r['signalObservedQpc'] or r['metadataError']:problems.append('ETW_HANDLE_INCOMPLETE')
  why='RETAINED' if kept else 'UNKNOWN'
  if not kept and r['openError']==87 and r['stopQpc'] and r['handleAttemptQpc']>=r['stopQpc']:why='OPEN_ERROR_87_AFTER_KERNEL_EXIT'
  if why=='UNKNOWN':problems.append('UNEXPLAINED_NONRETENTION')
  errors.extend(f'{key}: {p}' for p in problems)
  out.append(dict(pid=r['pid'],created=r['created'],parentPid=r['parentPid'],sequence=r['sequence'],parentSequence=r['parentSequence'],image=r['image'],retained=kept,retentionReason=why,handleCoverage='COMPLETE' if kept else 'INCOMPLETE',kernelIdentityCoverage='COMPLETE' if not problems else 'INCOMPLETE',lifetimeSeconds=(int(r['exitFiletime'])-int(r['created']))/1e7,notificationDelaySeconds=(r['startCallbackQpc']-r['startQpc'])/freq,problems=problems))
 for key in retained:
  if key not in keys:errors.append(f'Retained process missing from ETW {key}')
 for p in root.glob('internal-*.jsonl'):
  lines=[json.loads(l) for l in p.read_text().splitlines()];pid=lines[0]['pid'];matches=[r for r in rows if r['pid']==pid]
  if len(matches)!=1:errors.append(f'Instrumented child missing/ambiguous {pid}')
  if lines[-1]['stage']!='return-main':errors.append(f'Incomplete internal trace {pid}')
 if (root/'explicit-launches.json').exists():
  for x in json.loads((root/'explicit-launches.json').read_text()):
   if 'times' not in x or (x['pid'],x.get('times',[''])[0]) not in keys:errors.append(f'Explicit launch missing {x["pid"]}')
 if (root/'stress-result.json').exists():
  sr=json.loads((root/'stress-result.json').read_text())
  if sr['primary_failure']:errors.append('Stress primary failure')
  for x in sr['launched']:
   if (x['pid'],x['created']) not in keys:errors.append(f'Explicit launch missing {x["pid"]}')
 if (root/'probe-timings.json').exists():
  for x in json.loads((root/'probe-timings.json').read_text()):
   if (x['pid'],x['initialKernelTimes'][0]) not in keys:errors.append(f'Probe missing {x["pid"]}')
 if (root/'tap.json').exists():
  taps=json.loads((root/'tap.json').read_text(encoding='utf-8-sig'))
  for x in taps:
   if x['stage']!='B-WMI-callback' or x['kind']!='start' or x['parentPid'] not in {r['pid'] for r in rows}:continue
   matches=[r for r in rows if r['pid']==x['pid'] and r['parentPid']==x['parentPid']]
   if len(matches)!=1:errors.append(f'WMI child missing/ambiguous in ETW {x["pid"]}')
 return dict(status='PASS' if not errors else 'FAIL',producerExit=lr['workExit'],producerStatus='PASS' if lr['workExit']==0 else 'FAILED_PRESERVED',observed=len(rows),retained=sum(r['retained'] for r in out),justifiedNonretained=sum(r['retentionReason']=='OPEN_ERROR_87_AFTER_KERNEL_EXIT' for r in out),unknown=sum(r['retentionReason']=='UNKNOWN' for r in out),errors=errors,rows=out,scope='Kernel identity/exit reconciliation only; producer failures are preserved separately. All scoped ETW descendants, including collector; not a universal guarantee against unobserved external/service helpers',eventLossCounters={k:e[k] for k in ('eventsLost','realtimeBuffersLost','buffersLost')})
if __name__=='__main__':
 r=pathlib.Path(sys.argv[1]);out=reconcile(r)
 with (r/'kernel-reconciliation.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps({k:v for k,v in out.items() if k!='rows'}))
