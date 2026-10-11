import subprocess,sys,json
from pathlib import Path
p=Path(__file__).resolve().parent
with (p/'focused-tests.log').open('x',encoding='utf-8') as f:
 result=subprocess.run([sys.executable,'-B',str(p/'test_resolver_v2.py')],cwd=p,stdout=f,stderr=subprocess.STDOUT)
(p/'focused-result.json').write_text(json.dumps({'command':[sys.executable,'-B','test_resolver_v2.py'],'exit_code':result.returncode},indent=2))
print((p/'focused-tests.log').read_text())
raise SystemExit(result.returncode)
