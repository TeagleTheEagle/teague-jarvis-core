import json
from pathlib import Path
R=Path(__file__).parent;P=R.parent/'stage6-creator-image-20260922'
b=json.loads((P/'analysis/coverage-live-inputs.json').read_text());first=b['handles'][0]
assert first['qualifiedPostExit'] and not first['retained']
s=(R/'test_combined.py').read_text();old="lambda b:b['coverage']['handles'][0].update(exitCode=999)";new="lambda b:next(h for h in b['coverage']['handles'] if h['retained']).update(exitCode=999)"
assert s.count(old)==1;s=s.replace(old,new).replace("R/'combined-tests.json'","R/'combined-tests-v2.json'")
with (R/'test_combined_v2.py').open('x') as f:f.write(s)
with (R/'fixture-correction.json').open('x') as f:json.dump(dict(kind='test selection defect',originalTarget=first,reason='first sorted record is a qualified post-exit helper with no retained handle; choose retained=True to actually inject a retained-handle contradiction',runtimeChanged=False,combinedRunStarted=False,originalPreserved=True),f,indent=2)
