"""Post-campaign paired analysis; never used to choose additional trials."""
import math,statistics,json,datetime
from preflight import R,LIVE,load,put,sha

def interval(values,critical):
    mean=statistics.mean(values);sd=statistics.stdev(values);half=critical*sd/math.sqrt(len(values))
    return dict(n=len(values),mean=mean,sd=sd,standardError=sd/math.sqrt(len(values)),halfwidth=half,lower=mean-half,upper=mean+half)
def grouped(values):return [statistics.mean(values[i:i+8]) for i in range(0,len(values),8)]
def percent(on,off):return 100*(on/off-1)
if __name__=='__main__':
    ex=load(R/'execution.json');assert ex['status']=='EXECUTION_COMPLETE' and ex['pairs']==256
    protocol=load(R/'protocol.json');assert sha(protocol['binary'])==protocol['binarySHA256']
    pairs=[];orders=[];identities=[]
    for batch in range(32):
        rows=[json.loads(s) for s in (LIVE/f'batch-{batch:02}.jsonl').read_text().splitlines()]
        identity=load(LIVE/f'batch-{batch:02}-exit.json')
        assert identity['exitCode']==0 and identity['waitResult']==0 and not identity['handleCloseErrors']
        assert identity['processInitial']['createdFILETIME']==identity['processFinal']['createdFILETIME']
        assert identity['threadInitial']['createdFILETIME']==identity['threadFinal']['createdFILETIME']
        identities.append(identity)
        trials=rows[1:];assert len(trials)==16
        for i in range(8):
            two=trials[2*i:2*i+2];off=next(t for t in two if not t['enabled']);on=next(t for t in two if t['enabled'])
            assert off['callbacks']==on['callbacks']
            p=dict(batch=batch,pair=i,order='BA' if two[0]['enabled'] else 'AB',callbacksPerState=off['callbacks'],baselineDispatcherCpu100ns=off['dispatcherCpu100ns'],enabledDispatcherCpu100ns=on['dispatcherCpu100ns'],absoluteDifference100ns=on['dispatcherCpu100ns']-off['dispatcherCpu100ns'],percentDifference=percent(on['dispatcherCpu100ns'],off['dispatcherCpu100ns']),off=off,on=on)
            pairs.append(p);orders.append(dict(batch=batch,pair=i,order=p['order']))
    values=[p['percentDifference'] for p in pairs];batches=grouped(values)
    primary=interval(batches,2.0395134463964077);supplementary=interval(values,1.9693105698491928)
    status='MEASUREMENT_OVERHEAD_SCREEN_PASSED' if primary['upper']<=1 else ('MEASUREMENT_OVERHEAD_CONFLICT' if primary['lower']>1 else 'OVERHEAD_THRESHOLD_NOT_ESTABLISHED')
    metrics={}
    funcs={
        'throughput':lambda t:t['callbacks']/t['wallSeconds'],
        'processCpuSeconds':lambda t:t['processCpu100ns']/1e7,
        'wallSeconds':lambda t:t['wallSeconds'],
        'sampledMedianLatencyUs':lambda t:t['sampledLatencyTicks']['p50']/t['frequency']*1e6,
        'sampledP95LatencyUs':lambda t:t['sampledLatencyTicks']['p95']/t['frequency']*1e6,
        'sampledP99LatencyUs':lambda t:t['sampledLatencyTicks']['p99']/t['frequency']*1e6,
        'sampledMaximumLatencyUs':lambda t:t['sampledLatencyTicks']['max']/t['frequency']*1e6,
        'cumulativePeakWorkingSetBytes':lambda t:t['peakWorkingSetBytes'],
        'cppAllocationCount':lambda t:t['allocations']}
    for name,func in funcs.items():
        a=[func(p['off']) for p in pairs];b=[func(p['on']) for p in pairs]
        differences=[percent(y,x) for x,y in zip(a,b)]
        ci=interval(grouped(differences),2.0395134463964077)
        metrics[name]=dict(disabledMean=statistics.mean(a),enabledMean=statistics.mean(b),disabledMaximum=max(a),enabledMaximum=max(b),pairedPercentBatch95=ci,intervalExcludesZero=ci['lower']>0 or ci['upper']<0)
    mean=statistics.mean(batches);den=sum((x-mean)**2 for x in batches)
    lag1=sum((batches[i]-mean)*(batches[i-1]-mean) for i in range(1,len(batches)))/den if den else None
    result=dict(status=status,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),primary=primary,supplementary=supplementary,batchMeansPercent=batches,batchLag1CorrelationDescriptive=lag1,pairCount=len(pairs),batchCount=len(identities),callbacks=sum(p['callbacksPerState']*2 for p in pairs),orderCounts={o:sum(p['order']==o for p in pairs) for o in ['AB','BA']},exclusions=[],harnessErrors=[],warmupsExcluded=True,benchmarkBinarySHA256=sha(protocol['binary']),primaryMethod=protocol['primaryInterval'],secondary=metrics,issue='none under this offline screen' if status=='MEASUREMENT_OVERHEAD_SCREEN_PASSED' else ('point estimate above budget and lower confidence bound above budget' if primary['lower']>1 else ('variance/precision insufficient with point estimate below or equal to budget' if primary['mean']<=1 else 'point estimate above budget; uncertainty also crosses budget')),limitations=['Offline unknown-parent START branch only; not integrated observer acceptance','Batch-level t interval assumes sufficiently independent, stable batch means; host systematic bias not bounded by this interval','No per-callback exhaustive latency maximum; existing sparse timing unchanged','Peak working set cumulative per process; not an isolated allocation measurement','No new materiality threshold applied to supplementary metrics','No ETW loss diagnosis inferred from this offline experiment'])
    put(R/'pairs.json',pairs);put(R/'trial-order.json',orders);put(R/'process-thread-identities.json',identities);put(R/'result.json',result)
    print(json.dumps({k:result[k] for k in ['status','primary','pairCount','callbacks','issue','batchLag1CorrelationDescriptive']}))
