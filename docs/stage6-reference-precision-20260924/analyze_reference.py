import json,statistics,math
from context_config import R,LIVE,load,put
def interval(values,critical):
 mean=statistics.mean(values);sd=statistics.stdev(values);half=critical*sd/math.sqrt(len(values))
 return dict(mean=mean,sd=sd,standardError=sd/math.sqrt(len(values)),halfwidth=half,lower=mean-half,upper=mean+half,n=len(values))
def uncertainty(values):
 assert len(values)==640
 batch=[statistics.mean(values[i:i+40]) for i in range(0,640,40)]
 groups=[statistics.mean(values[i:i+5]) for i in range(0,640,5)]
 a=interval(batch,2.131449545559);b=interval(groups,1.978819534681)
 assert abs(a['mean']-b['mean'])<1e-8
 half=max(a['halfwidth'],b['halfwidth']);mean=statistics.mean(values)
 return dict(mean=mean,halfwidth=half,lower=mean-half,upper=mean+half,batchInterval=a,fivePairGroupInterval=b,batchMeans=batch)
if __name__=='__main__':
 execution=load(R/'execution.json');assert execution['status']=='COMPLETE' and execution['pairs']==640
 pairs=[];identities=[];order=[]
 for batch in range(16):
  folder=LIVE/f'batch-{batch:02}'
  rows=[json.loads(s) for s in (folder/'reference.jsonl').read_text().splitlines()];assert len(rows)==80
  ident=load(folder/'reference-exit.json');assert ident['exitCode']==0 and ident['waitResult']==0 and not ident['closeErrors']
  assert ident['initialProcess']['createdFILETIME']==ident['finalProcess']['createdFILETIME']
  assert ident['initialThread']['createdFILETIME']==ident['finalThread']['createdFILETIME']
  identities.append(ident)
  for i in range(40):
   two=rows[i*2:i*2+2];assert [t['variant'] for t in two]==([0,1] if i%2==0 else [1,0])
   assert all(t['callbacks']==1000000 and t['dispatcherCpu100ns']>0 and t['block']==i for t in two)
   a=next(t for t in two if t['variant']==0);b=next(t for t in two if t['variant']==1)
   p=dict(batch=batch,pair=i,order='AB' if two[0]['variant']==0 else 'BA',baseline=a,full=b,cpuPercent=100*(b['dispatcherCpu100ns']/a['dispatcherCpu100ns']-1),absoluteCpuDifference100ns=b['dispatcherCpu100ns']-a['dispatcherCpu100ns'],baselineNs=a['dispatcherCpu100ns']*100/a['callbacks'],fullNs=b['dispatcherCpu100ns']*100/b['callbacks'],deltaNs=(b['dispatcherCpu100ns']-a['dispatcherCpu100ns'])*100/a['callbacks'],throughputPercent=100*(a['wallSeconds']/b['wallSeconds']-1),processCpuPercent=100*(b['processCpu100ns']/a['processCpu100ns']-1),wallPercent=100*(b['wallSeconds']/a['wallSeconds']-1))
   pairs.append(p);order.append(dict(batch=batch,pair=i,order=p['order']))
 primary=uncertainty([p['cpuPercent'] for p in pairs]);target=.25
 precise=primary['halfwidth']<=target;prior=[1.191266939782601,1.6088796722099354]
 overlap=primary['upper']>=prior[0] and primary['lower']<=prior[1]
 status='REFERENCE_PRECISION_NOT_ESTABLISHED' if not precise else ('REFERENCE_PRECISION_ESTABLISHED' if overlap else 'BENCHMARK_REPRODUCIBILITY_DEFECT')
 batch=primary['batchMeans'];mean=statistics.mean(batch);den=sum((x-mean)**2 for x in batch)
 lag1=sum((batch[i]-mean)*(batch[i-1]-mean) for i in range(1,len(batch)))/den if den else None
 result=dict(status=status,primary=primary,targetHalfwidth=target,precisionMet=precise,priorInterval=prior,intervalOverlap=overlap,compatibility=('COMPATIBLE' if overlap else 'REPRODUCIBILITY_DEFECT') if precise else 'NOT_CLASSIFIED_UNTIL_PRECISION_SUFFICIENT',pairs=640,measuredTrials=1280,measuredCallbacks=1280000000,warmupCallbacks=25600000,batches=16,orderCounts={x:sum(p['order']==x for p in pairs) for x in ['AB','BA']},baselineMeanNs=statistics.mean(p['baselineNs'] for p in pairs),fullMeanNs=statistics.mean(p['fullNs'] for p in pairs),nsDifference=uncertainty([p['deltaNs'] for p in pairs]),throughputPercent=uncertainty([p['throughputPercent'] for p in pairs]),processCpuPercent=uncertainty([p['processCpuPercent'] for p in pairs]),wallPercent=uncertainty([p['wallPercent'] for p in pairs]),pairSD=statistics.stdev(p['cpuPercent'] for p in pairs),batchLag1Correlation=lag1,firstEightBatchMean=statistics.mean(batch[:8]),lastEightBatchMean=statistics.mean(batch[8:]),exclusions=[],harnessErrors=[],retries=0,componentVariantsExecuted=False,scope='Reference reproducibility/precision only, not overhead acceptance; no optional sample extension')
 put(R/'pairs.json',pairs);put(R/'order.json',order);put(R/'identities.json',identities);put(R/'result.json',result)
 print(json.dumps({k:result[k] for k in ['status','primary','compatibility','pairs','batchLag1Correlation']},indent=2))
