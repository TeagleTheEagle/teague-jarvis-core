import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import time
import xml.etree.ElementTree as ET

OUT = Path(__file__).parent
MON = OUT / 'run2'
ROOT = Path(r'C:\Users\jonny\VirtualBox VMs\JARVIS-CLEAN-WIN11')
CONFIG = Path(r'C:\Users\jonny\.VirtualBox')
def utc(): return dt.datetime.now(dt.timezone.utc).isoformat()
def write(name, value):
    target = OUT / name
    raw = (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + '\n').encode()
    with target.open('xb') as f: f.write(raw)
    return hashlib.sha256(raw).hexdigest()
def monitor():
    if (MON/'monitor-failure.json').exists(): raise RuntimeError('Monitor failure; see preserved monitor evidence')
    h = json.loads((MON/'monitor-heartbeat.json').read_text(encoding='utf-8-sig'))
    age = (dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(h['Utc'].replace('Z','+00:00'))).total_seconds()
    if age > 10 or h['Violations'] or h['State'] != 'ACTIVE': raise RuntimeError('Monitoring heartbeat stale or violation')
    return h
def inventory(root):
    result = []
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            p = Path(directory)/name
            s = p.lstat()
            if s.st_file_attributes & 0x400: raise RuntimeError('Reparse point in protected inventory: '+str(p))
        for name in files:
            p=Path(directory)/name; s=p.stat()
            result.append(dict(full_path=str(p),relative_path=str(p.relative_to(root)),size=s.st_size,
                mtime_ns=s.st_mtime_ns,LastWriteTimeUtc=dt.datetime.fromtimestamp(s.st_mtime,dt.timezone.utc).isoformat(),
                windows_last_write_ticks=s.st_mtime_ns//100+116444736000000000))
    return sorted(result,key=lambda r:r['relative_path'].lower())
def digest(row,phase):
    monitor(); p=Path(row['full_path']); h=hashlib.sha256(); count=0; tick=0
    print(phase+' '+row['relative_path'],flush=True)
    with p.open('rb') as f:
        while True:
            if time.monotonic()-tick > .25: monitor(); tick=time.monotonic()
            chunk=f.read(4*1024*1024)
            if not chunk: break
            h.update(chunk);count+=len(chunk)
    monitor();s=p.stat()
    if count!=row['size'] or s.st_size!=row['size'] or s.st_mtime_ns!=row['mtime_ns']: raise RuntimeError('Mutation during hash: '+str(p))
    return h.hexdigest()
def tag(e): return e.tag.rsplit('}',1)[-1]
def tree(e): return {'tag':tag(e),'attributes':dict(sorted(e.attrib.items())),'children':[tree(c) for c in e]}
def topology(path):
    top=ET.parse(path).getroot(); machine=next(e for e in top if tag(e)=='Machine')
    parents={c:p for p in top.iter() for c in p}
    def ancestor(e,kind):
        p=parents.get(e)
        while p is not None:
            if tag(p)==kind:return p
            p=parents.get(p)
        return None
    scopes=[]
    for scope in [machine]+[e for e in machine.iter() if tag(e)=='Snapshot']:
        parent=ancestor(scope,'Snapshot')
        hardware=next((c for c in scope if tag(c)=='Hardware'),None)
        networks=[];nvram=[];controllers=[]
        if hardware is not None:
            networks=[tree(c) for c in hardware if tag(c)=='Network']
            nvram=[dict(e.attrib) for e in hardware.iter() if tag(e)=='NVRAM']
        for c in scope:
            if tag(c)=='StorageControllers':controllers.append(tree(c))
        scopes.append({'kind':tag(scope),'uuid':scope.get('uuid'),'name':scope.get('name'),
            'parent_snapshot':None if parent is None else parent.get('uuid'),
            'snapshot_time':scope.get('timeStamp'),'state_file':scope.get('stateFile'),
            'network':networks,'nvram':nvram,'storage_controllers':controllers})
    disks=[];external_media=[]
    for e in top.iter():
        if tag(e)=='HardDisk':
            parent=ancestor(e,'HardDisk');loc=e.get('location');p=(ROOT/loc).resolve()
            if not p.is_relative_to(ROOT) or not p.is_file():raise RuntimeError('Unresolved protected disk reference')
            disks.append({'attributes':dict(e.attrib),'parent_uuid':None if parent is None else parent.get('uuid'),'resolved_path':str(p)})
        elif tag(e)=='Image' and e.get('location'):
            external_media.append(dict(e.attrib))
    return {'machine_uuid':machine.get('uuid'),'current_snapshot':machine.get('currentSnapshot'),
        'snapshot_folder':machine.get('snapshotFolder'),'scopes':scopes,'disk_chain':disks,
        'external_media_references_not_hashed':external_media,
        'nvram_files':[r['relative_path'] for r in inventory(ROOT) if r['relative_path'].lower().endswith('.nvram')],
        'current_nvram_note':'No explicit current-machine NVRAM element; machine-named NVRAM file inventoried, not inferred as a new XML reference.'}

started=utc()
try:
    monitor()
    original=inventory(ROOT); normal=inventory(CONFIG)
    if len(original)!=12:raise RuntimeError('Expected exactly 12 protected files')
    write('inventory-before.json',{'protected':original,'normal_configuration_tree':normal})
    relationships=topology(ROOT/'JARVIS-CLEAN-WIN11.vbox')
    prior_relationships=topology(ROOT/'JARVIS-CLEAN-WIN11.vbox-prev')
    nat=[e for e in ET.parse(ROOT/'JARVIS-CLEAN-WIN11.vbox').iter() if tag(e)=='NAT']
    if len(nat)!=3 or any(e.get('localhost-reachable')!='true' for e in nat):raise RuntimeError('Unexpected post-incident network state')
    first=[];normal_first=[]
    for rows, destination in ((original,first),(normal,normal_first)):
        for row in rows:destination.append(dict(row,SHA256=digest(row,'CAPTURE')))
    write('first-pass.json',{'protected':first,'normal_configuration_tree':normal_first})
    if inventory(ROOT)!=original or inventory(CONFIG)!=normal:raise RuntimeError('Inventory mutation before verification')
    for row in first+normal_first:
        if digest(row,'VERIFY')!=row['SHA256']:raise RuntimeError('Second-pass hash mismatch: '+row['full_path'])
    if inventory(ROOT)!=original or inventory(CONFIG)!=normal:raise RuntimeError('Inventory mutation after verification')
    manifest={'baseline_type':'NEW POST-INCIDENT PROTECTED BASELINE','capture_started_utc':started,'capture_completed_utc':utc(),
        'protected_root':str(ROOT),'protected_count':len(first),'protected_total_bytes':sum(r['size'] for r in first),
        'protected_artifacts':first,'normal_configuration_root':str(CONFIG),'normal_configuration_artifacts':normal_first,
        'relationships_current':relationships,'relationships_vbox_prev':prior_relationships,
        'networking':{'protected_post_incident_LocalhostReachable':1,'historical_pre_incident_evidence':0,'required_future_validation_copy':0,
            'note':'Value 1 is a pre-existing preservation incident, not a mutation during baseline capture.'},
        'limitation':'Not proof of pre-incident full-disk integrity. External ISO references recorded, not part of protected tree hashes.',
        'verification':{'full_hash_passes':2,'all_hashes_match':True,'sizes_and_LastWriteTimeUtc_unchanged':True},
        'monitor_evidence':'run2/monitor-ready.json; run2/monitor-heartbeat.json; run2/monitor-final.json (required before acceptance)',
        'serialization':'UTF-8, sorted object keys, sorted relative-path inventories, indent 2, trailing LF; timestamps fixed for this capture'}
    monitor();mh=write('baseline-manifest.json',manifest)
    if hashlib.sha256((OUT/'baseline-manifest.json').read_bytes()).hexdigest()!=mh:raise RuntimeError('Manifest reread mismatch')
    write('manifest-sha256.json',{'file':'baseline-manifest.json','SHA256':mh})
    print('CAPTURE_VERIFIED '+mh,flush=True)
    (MON/'collector-finished.json').write_text(json.dumps({'status':'HASHES_VERIFIED','utc':utc()}))
except BaseException as exc:
    write('capture-failure.json',{'status':'BLOCKED','error':str(exc),'utc':utc()})
    (MON/'collector-finished.json').write_text(json.dumps({'status':'BLOCKED','utc':utc()}))
    raise
