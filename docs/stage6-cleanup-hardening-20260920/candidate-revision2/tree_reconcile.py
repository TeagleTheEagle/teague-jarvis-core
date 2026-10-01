"""Event timestamps are observation/provider timestamps, not kernel process times."""
import pathlib
def match_child(start,rows,events):
 # Retained identity was established from a live Toolhelp parent link + kernel creation time.
 # Do not reinterpret WMI TIME_CREATED as a process creation/exit time.
 candidates=[r for r in rows if r['pid']==start['pid']]
 matched=[r for r in candidates if r['parentPid']==start['parentPid'] and pathlib.PureWindowsPath(r['image']).name.lower()==start['name'].lower()]
 if len(candidates)!=1:matched=[] # Any recorded PID reuse makes event-only association ambiguous.
 stops=[r for r in events if r['stage']=='B-WMI-callback' and r['kind']=='stop' and r['pid']==start['pid'] and r['name'].lower()==start['name'].lower() and int(r['nativeTime'])>=int(start['nativeTime'])]
 starts=[r for r in events if r['stage']=='B-WMI-callback' and r['kind']=='start' and r['pid']==start['pid']]
 if len(starts)!=1:matched=[]
 return dict(start=start,retainedMatches=len(matched),stopMatches=len(stops),identityBasis='retained handle/kernel creation/observed parent link; no PID reuse; WMI time not kernel time')
