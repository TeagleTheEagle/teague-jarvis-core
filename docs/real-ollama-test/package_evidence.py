"""Snapshot only this TEST task's nonsecret source and evidence; no runtime action."""
from pathlib import Path
import json,hashlib,difflib,shutil
base=Path(__file__).resolve().parent;repo=base.parents[1]
files=['stage4_ollama_transport.py','stage4_runtime.py','stage4_provider_fallback.py','stage4_client.cjs',
       'tests/test_stage4_ollama_transport.py','tests/ollama_audit_boundary.py',
       'tests/real_ollama_validation.py','tests/build_real_ollama_probe.py']
compiled=[];diff=[]
for name in files:
 source=repo/name;dest=base/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
 if source.suffix=='.py':compile(source.read_text(),str(source),'exec');compiled.append(name)
 before=base/'before'/name
 old=before.read_text() if before.exists() else ''
 diff.extend(difflib.unified_diff(old.splitlines(True),source.read_text().splitlines(True),fromfile='before/'+name,tofile='after/'+name))
(base/'source-changes.diff').write_text(''.join(diff))
(base/'compilation.json').write_text(json.dumps({'passed':compiled,'method':'compile source in memory; no imports/execution or pycache'},indent=2))
trial=json.loads((base/'real-ollama-electron-fc4c82a589a7455c9a4b79f832ca07f3.json').read_text())
result=next(c['result'] for c in trial['cases'] if c['case']=='real response evidence')
answer=next(e['data']['text'] for e in result['status']['events'] if e['event']=='assistant.completed')
shutil.copyfile(trial['screenshots'][0]['file'],base/'electron-reviewed.png')
(base/'acceptance-review.json').write_text(json.dumps({'overall':'NOT_ACCEPTED','automatic_checks_passed':23,
 'final_answer_only':answer.strip()=='4','reasoning_marker_in_content':'</think>' in answer,
 'screenshot_visibly_contains_answer':False,'visual_review':'Captured image inspected; shows initial TEST attachment text, not returned Qwen response.',
 'active_inference_shutdown_measured':False,'physical_voice_verified':False,'production_activated':False},indent=2))
manifest=[]
for p in sorted(base.rglob('*')):
 if p.is_file() and p.name!='SHA256.json':manifest.append({'path':p.relative_to(base).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(base/'SHA256.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'files_hashed':len(manifest),'source_files':files}))
