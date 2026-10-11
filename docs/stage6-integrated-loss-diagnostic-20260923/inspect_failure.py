import pathlib,json,sys
R=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
C=pathlib.Path(read(R/'candidate.json')['code']);run=pathlib.Path(read(R/'normal-run.json')['root']);sys.path.insert(0,str(C))
import small_check
original=small_check.coverage;capture={}
def inspect(*args):
 value=original(*args);capture['coverage']=value;capture['expected']=args[0];capture['handles']=args[2];capture['native']=args[3];return value
small_check.coverage=inspect
try:small_check.check(run)
except ValueError as e:capture['checkerFailure']=str(e)
with (R/'coverage-failure-detail.json').open('x') as f:json.dump(capture,f,indent=2)
k=read(run/'etw-result.json');freq=read(run/'etw-ready.json')['frequency'];failed=[]
for r in capture['coverage']['identities']:
 if r['verified']:continue
 x=next(x for x in k['rows'] if x['pid']==r['pid'] and x['created']==r['created'])
 failed.append(dict(coverage=r,kernel=x,lifetimeSeconds=(int(x['exitFiletime'])-int(x['created']))/10000000,eventToCallbackSeconds=(x['startCallbackQpc']-x['startQpc'])/freq,imageQueryAfterStopSeconds=(x['imageBeginQpc']-x['stopQpc'])/freq))
with (R/'failed-identities.json').open('x') as f:json.dump(failed,f,indent=2)
print(json.dumps([dict(pid=x['kernel']['pid'],role=x['coverage']['role'],image=x['kernel']['image'],imageError=x['kernel']['imageError'],handleRetained=x['kernel']['handleRetained'],lifetimeSeconds=x['lifetimeSeconds'],callbackDelay=x['eventToCallbackSeconds'],queryAfterStop=x['imageQueryAfterStopSeconds']) for x in failed],indent=2))
