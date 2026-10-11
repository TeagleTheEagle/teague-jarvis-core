import pathlib,json,sys,uuid,subprocess,threading,time
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'plan.json').read_text())['code']);sys.path.insert(0,str(C))
from workspace import new_run,activate_temp
from native_bridge import NativeBridge
from probe_timing import Probe
from journal import ticks,frequency
import bounded_sampler
root=new_run('native-smoke-'+uuid.uuid4().hex);activate_temp(root)
script=C/'python_marker_probe.py'
script.write_text("import time\nENTRY=time.perf_counter_ns()\nimport sys\nfrom workspace import run_dir\nfrom integration_marks import Marks\nm=Marks(run_dir(sys.argv[1]),'smoke',ENTRY)\nm.add('WORK_BEGIN')\nprint('preserved stdout')\nm.add('WORK_END')\nm.close('RETURNED')\n")
bridge=NativeBridge(root);bridge.install();p=None
try:
 probe=Probe(C/'J6Probe.exe');assert probe.wait_approved(lambda:None,lambda x:None,ticks()/frequency()+30)==0
 probe.finish_observation();assert not probe.row['independentObserverFailed'];probe.process._handle.Close()
 p=subprocess.Popen([sys._base_executable,'-B',str(script),root.name],stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=0x08000000,close_fds=True)
 out,err=p.communicate(timeout=5);assert p.returncode==0 and out.strip()==b'preserved stdout' and not err
 sample=bounded_sampler.query(root,'normal',0,threading.Event());assert sample['allExited'] and sample['handleClosed'] and sample['status']=='AVAILABLE',sample
finally:bridge.close()
native=[json.loads(x.read_text()) for x in root.glob('native-*.json') if x.name!='native-bridge-cleanup.json']
assert len(native)==3
for n in native:assert n['entryQpc']>0 and not n['fault'] and not n['deadlineExceeded'] and n['finalWait']==0
correlations=[]
for f in root.glob('integration-*.json'):
 rows=json.loads(f.read_text());marker=rows[0];n=next(x for x in native if x['pid']==marker['pid'] and x['created']==marker['created'])
 assert n['entryQpc']<=marker['pythonEntryNs']*n['frequency']/1e9<=marker['qpc']
 correlations.append(dict(pid=n['pid'],created=n['created'],nativeToPythonMs=(marker['pythonEntryNs']/1e9-n['entryQpc']/n['frequency'])*1000))
result=dict(root=str(root),nativeCount=len(native),correlations=correlations,sampler=sample,status='PASS')
(R/'native-smoke.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
