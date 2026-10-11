import json,statistics,math
from prepare import R,W,load,put
from run import ci
T=2.262157163
def clustered(values):return ci([statistics.mean(values[i:i+4]) for i in range(0,40,4)],T)
def ns(t):return t['dispatcherCpu100ns']*100/t['callbacks']
if __name__=='__main__':
 ref=load(R/'reference-result.json');assert ref['status']=='REFERENCE_COMPATIBLE'
 assert load(R/'attribution-execution.json')['status']=='COMPLETE'
 rows=[json.loads(s) for s in (W/'raw'/'attribution.jsonl').read_text().splitlines()]
 blocks=[]
 for b in range(40):
  five=rows[b*5:b*5+5];d={t['variant']:t for t in five};assert len(d)==5
  base=[0,1,4,2,3];row=b%10;expected=[(base[p if row<5 else 4-p]+row%5)%5 for p in range(5)]
  assert [t['variant'] for t in five]==expected
  assert all(t['callbacks']==1000000 and t['dispatcherCpu100ns']>0 for t in five)
  blocks.append(d)
 variants={}
 for v in range(5):
  changes=[100*(ns(d[v])/ns(d[0])-1) for d in blocks]
  delta=[ns(d[v])-ns(d[0]) for d in blocks]
  throughput=[100*((d[v]['callbacks']/d[v]['wallSeconds'])/(d[0]['callbacks']/d[0]['wallSeconds'])-1) for d in blocks]
  variants[str(v)]=dict(name=blocks[0][v]['name'],cpuPercent=clustered(changes),nsPerCallback=statistics.mean([ns(d[v]) for d in blocks]),nsDelta=clustered(delta),throughputPercent=clustered(throughput),callbacksPerSecond=statistics.mean([d[v]['callbacks']/d[v]['wallSeconds'] for d in blocks]))
 contrasts={}
 weights={'clockAlone_CminusA':{2:1,0:-1},'clockInStorageContext_BminusD':{1:1,3:-1},'storagePackage_DminusA':{3:1,0:-1},'recordStoresConditional_DminusE':{3:1,4:-1},'bookkeeping_EminusA':{4:1,0:-1},'interaction_BminusCminusDplusA':{1:1,2:-1,3:-1,0:1}}
 for name,weight in weights.items():
  values=[sum(n*ns(d[v]) for v,n in weight.items()) for d in blocks]
  contrasts[name]=dict(ns=clustered(values),baselinePercent=clustered([100*x/ns(d[0]) for x,d in zip(values,blocks)]),rawNs=values)
 full=variants['1']['cpuPercent'];old=ref['oldInterval']
 compatible=not(full['upper']<old[0] or full['lower']>old[1])
 if not compatible:status='BENCHMARK_REPRODUCIBILITY_DEFECT'
 elif full['halfwidth']>.75:status='MORE_PROFILING_REQUIRED'
 elif variants['3']['cpuPercent']['upper']<=1 and contrasts['clockInStorageContext_BminusD']['ns']['lower']>0:status='TIMESTAMP_REUSE_STRONGLY_SUPPORTED'
 elif variants['2']['cpuPercent']['upper']<=1 and contrasts['recordStoresConditional_DminusE']['ns']['lower']>0:status='RECORD_STORE_OPTIMIZATION_STRONGLY_SUPPORTED'
 else:status='OVERHEAD_COMPONENT_ATTRIBUTION_COMPLETE'
 result=dict(status=status,reference=ref,attributionReferenceCompatible=compatible,variants=variants,contrasts=contrasts,blocks=40,trials=200,callbacks=200000000,exclusions=[],retries=0,notes=['Partial variants are NOT acceptance instrumentation','D substitutes arrival for completion only to remove a clock call in an experiment; it does not validate real timestamp reuse','Clock-only has no record growth/reset; book/store contrasts include replay and compiler-layout interactions','Residual is an algebraic contrast, not proof of independent/additive physical costs','C++ compiler fuses enable checks in variants without the extra clock call','No historical trace-loss causation established'])
 put(R/'attribution-result.json',result)
 print(json.dumps(dict(status=status,variants=variants,contrasts={k:v['ns'] for k,v in contrasts.items()}),indent=2))
