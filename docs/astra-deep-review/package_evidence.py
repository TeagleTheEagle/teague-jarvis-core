"""Package only this milestone and the subsequent approved diagnostic evidence."""
from pathlib import Path
import json,hashlib,shutil,difflib
base=Path(__file__).resolve().parent;repo=base.parents[1];diag=repo/'docs/ollama-acceptance-diagnosis'
astra=['stage4_deep_review.py','stage4_runtime.py','stage4_response_history.py','tests/test_stage4_deep_review.py',
 'tests/astra_deep_review_integration.py','tests/astra_restart_probe.py','tests/build_astra_pipe_probe.py','tests/astra_pipe_probe.py']
diagnostic=['tests/ollama_thinking_diagnosis.py','tests/ollama_ui_diagnostic.cjs','tests/build_ollama_ui_diagnostic.py','tests/ollama_ui_probe.py']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
compiled=[]
for folder,names in ((base,astra),(diag,diagnostic)):
 diff=[]
 for name in names:
  source=repo/name;dest=folder/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
  if source.suffix=='.py':compile(source.read_text(),str(source),'exec');compiled.append(name)
  old=folder/'before'/name
  diff.extend(difflib.unified_diff(old.read_text().splitlines(True) if old.exists() else [],source.read_text().splitlines(True),fromfile='before/'+name,tofile='after/'+name))
 (folder/'source-changes.diff').write_text(''.join(diff))
before=json.loads((base/'production-source-before.json').read_text(encoding='utf-8-sig'))
protected=[]
for item in before:
 p=Path(item['Path']);unchanged=sha(p).upper()==item['Hash'];assert unchanged
 protected.append({'path':str(p),'sha256':sha(p),'unchanged':unchanged})
(base/'production-source-verification.json').write_text(json.dumps(protected,indent=2))
(base/'compilation.json').write_text(json.dumps({'passed':compiled,'method':'in-memory compile, no module execution'},indent=2))
unchanged=[]
for name in ('stage4_client.cjs','stage4_ollama_transport.py'):
 original=repo/'docs/real-ollama-test/source'/name
 assert sha(repo/name)==sha(original)
 unchanged.append({'file':name,'sha256':sha(repo/name),'unchanged_from_prior_evidence':True})
(diag/'no-correction-verification.json').write_text(json.dumps(unchanged,indent=2))
shutil.copyfile(repo/'docs/real-ollama-test/local-model-metadata.json',diag/'installed-model-metadata.json')
shutil.copyfile(repo/'docs/real-ollama-test/ollama-version.json',diag/'ollama-version.json')
ui=json.loads((diag/'ui-diagnostic-cc87bea3e13d4059a3bd84dfe379d645.json').read_text())
for shot,name in zip(ui['screenshots'],('screenshot-immediate.png','screenshot-delayed.png')):shutil.copyfile(shot['file'],diag/name)
for folder in (base,diag):
 manifest=[{'path':p.relative_to(folder).as_posix(),'sha256':sha(p)} for p in sorted(folder.rglob('*')) if p.is_file() and p.name!='SHA256.json']
 (folder/'SHA256.json').write_text(json.dumps(manifest,indent=2));print(folder.name,len(manifest),'files hashed')
