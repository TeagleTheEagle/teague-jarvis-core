"""Rerun the explicit accepted regression inventory, preserving unique logs."""
import datetime
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
stamp=uuid.uuid4().hex
records=[]
target=OUT/('regressions-'+stamp+'.json')
commands=json.loads((ROOT/'docs/lifecycle-stage5-evidence/regressions-081519.json').read_text(encoding='utf-8-sig'))
for old in commands:
    log=OUT/(old['name']+'-'+stamp+'.log')
    record=dict(name=old['name'],command=old['command'],cwd=old['cwd'],log=str(log),started=time.time())
    with log.open('x',encoding='utf8') as stream:
        process=subprocess.Popen(record['command'],cwd=record['cwd'],stdout=stream,stderr=subprocess.STDOUT,
                                 close_fds=True,creationflags=0x08000000)
        record['pid']=process.pid
        try:record['exit']=process.wait(timeout=900)
        except subprocess.TimeoutExpired:
            record['exit']=None;record['retained_for_review']=True
    record['elapsed']=time.time()-record['started'];records.append(record)
    target.write_text(json.dumps(records,indent=2),encoding='utf8')
    print(record['name'],record['exit'],flush=True)
    if record['exit']!=0:
        print('STOP: preserved failure',target,flush=True);sys.exit(1)
print('PASS',len(records),'commands;',target,flush=True)
