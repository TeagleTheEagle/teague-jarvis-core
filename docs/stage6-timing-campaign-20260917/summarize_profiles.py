from pathlib import Path
import json,pstats,hashlib
D=Path(__file__).resolve().parent
rows=[]
for evidence in list(D.glob('reproduction-*.json'))+list(D.glob('full-profile-*.json'))+list(D.glob('negative-profile-*.json')):
    data=json.loads(evidence.read_text())
    for control in data['control_processes']:
        if not control.get('profile'):continue
        path=Path(control['profile'])
        result={'evidence':evidence.name,'identity':control['identity'],'elapsed':control.get('elapsed'),'phase':control['phase'],'profile_available':path.exists(),'profile_path':str(path)}
        if path.exists():
            stats=pstats.Stats(str(path));result['profile_sha256']=hashlib.sha256(path.read_bytes()).hexdigest();result['profile_seconds']=stats.total_tt
            selectors={'package_verification':('contract.py','verify_package'),'hashing':('contract.py','digest'),'security_path_checks':('contract.py','safe_path'),'bounded_read_verification':('update_io.py','verification'),'staging':('update_io.py','stage_copy'),'owner_authentication':('enrollment.py','authorize'),'file_enumeration':('pathlib.py','rglob'),'lock_acquisition':('harness.py','__init__'),'durable_intent':('contract.py','write_protected'),'native_verification':('native.py','verify_native'),'bootstrap':('bootstrap.py','main'),'updater':('upgrade.py','operate')}
            result['measurements']={}
            for label,(file,fn) in selectors.items():
                matching=[v for k,v in stats.stats.items() if k[0].endswith(file) and k[2]==fn]
                result['measurements'][label]={'calls':sum(v[1] for v in matching),'inclusive_seconds':sum(v[3] for v in matching),'self_seconds':sum(v[2] for v in matching)}
            result['fsync']=[{'calls':v[1],'seconds':v[3]} for k,v in stats.stats.items() if 'fsync' in k[2]]
            result['process_and_profiler_overhead_seconds']=max(0,control.get('elapsed',0)-stats.total_tt)
        rows.append(result)
(D/'timing-summary.json').write_text(json.dumps({'note':'Nested inclusive timings overlap. cProfile overhead is included. Missing profiles on intentional os._exit interruption are not zero-time operations. Historical timeout not profiled; these values cannot reconstruct it. The packaged update uses a new release directory plus durable activation record, not in-place replacement.','rows':rows},indent=2))
print(json.dumps({'profiles':sum(x['profile_available'] for x in rows),'profiled_actions':len(rows),'completed_stage_seconds':[x['elapsed'] for x in rows if x['profile_available']]}))
