"""Offline TEST diagnostics only. Never produces an acceptance seal or substitutes for checker."""
import hashlib,json,math
from pathlib import Path
def percentile_bounds(distribution, percentile):
    bins=distribution['bins'];count=sum(bins)
    if not count:return None
    rank=math.ceil(count*percentile);total=0
    for i,n in enumerate(bins):
        total+=n
        if total>=rank:return [0 if i==0 else 1<<(i-1),0 if i==0 else (1<<i)-1]
    raise ValueError('HISTOGRAM')
def verify(value, *, run, session, channel, frequency):
    if (value.get('schema'),value.get('run'),value.get('session'),value.get('channel'),value.get('frequency')) != ('stage6-loss-diagnostic-v2',run,session,channel,frequency):raise ValueError('BINDING')
    if not value.get('diagnosticOnly') or value.get('acceptanceSealed') is not False:raise ValueError('NOT_ACCEPTANCE')
    if value.get('errors')!=0 or value.get('overflow')!=0:raise ValueError('TELEMETRY_FAILURE')
    if frequency<=0 or value.get('originQpc',0)<=0:raise ValueError('CLOCK')
    if value.get('intervalMs')!=100 or value.get('slowThresholdMs')!=5:raise ValueError('DIAGNOSTIC_CONFIGURATION')
    samples=value['samples']
    if not 0<len(samples)<=value['sampleCapacity'] or len(value['slowSpans'])>value['slowCapacity']:raise ValueError('BOUND')
    previous_end=0;last_callbacks=0;lost=0;transitions=[];buffer_loss=False
    for i,s in enumerate(samples,1):
        if s['sequence']!=i or s['beginQpc']<previous_end or s['endQpc']<s['beginQpc']:raise ValueError('SAMPLE_ORDER')
        previous_end=s['endQpc']
        if s['status']:
            if s['eventsLost'] is not None:raise ValueError('FALSE_ZERO')
            # Post-stop races are reported, never construed as healthy live samples.
            if not value['stopBeginQpc'] or s['beginQpc']<value['stopBeginQpc']:raise ValueError('LIVE_QUERY_FAILED')
            continue
        if s['callbackDelta']!=s['callbacks']-last_callbacks or s['callbackDelta']!=s['duration']['count']:raise ValueError('CALLBACK_COUNT')
        last_callbacks=s['callbacks']
        for name in ('duration','deliveryLag'):
            h=s[name]
            if len(h['bins'])!=64 or any(n<0 for n in h['bins']) or sum(h['bins'])!=h['count']:raise ValueError('HISTOGRAM')
        if s['eventsLost']<lost:raise ValueError('COUNTER_REGRESSION')
        buffer_loss |= bool(s['realtimeBuffersLost'] or s['logBuffersLost'])
        if s['eventsLost']!=lost:transitions.append({'beginQpc':s['beginQpc'],'endQpc':s['endQpc'],'previous':lost,'current':s['eventsLost']})
        lost=s['eventsLost']
    for s in value['slowSpans']:
        if s['endQpc']-s['beginQpc']<frequency/200 or not 0<=s['beforeSample']<=s['latestSample']<=len(samples):raise ValueError('SLOW_SPAN')
    # A valid telemetry file containing real loss still cannot qualify a live run.
    return {'diagnosticOnly':True,'acceptanceSealed':False,'telemetryValid':True,'lossTransitions':transitions,'observedLoss':lost,'liveEligibility':False if lost or buffer_loss else 'REQUIRES_UNCHANGED_CHECKER_AND_ALL_EXTERNAL_EVIDENCE'}
def bind_external(value,cleanup_path,phase_path):
    """Reopens existing final artifacts; never modifies those artifacts."""
    cleanup=json.loads(Path(cleanup_path).read_text());phase=json.loads(Path(phase_path).read_text())
    def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    binding=phase['binding']
    # Exact versioned binding structure is checked by the unchanged run checker.
    if binding.get('run')!=value['run'] or binding.get('frequency')!=value['frequency'] or cleanup.get('frequency')!=value['frequency']:raise ValueError('EXTERNAL_BINDING')
    if value['channel']=='authority' and binding.get('kernelSession')!=value['session']:raise ValueError('EXTERNAL_SESSION')
    if value['channel']=='detail':
        ready_path=Path(phase_path).parent/'detail'/'etw-ready.json'
        ready=json.loads(ready_path.read_text())
        if ready.get('session')!=value['session'] or ready.get('frequency')!=value['frequency']:raise ValueError('EXTERNAL_DETAIL_SESSION')
    if phase.get('cleanupEntryQpc')!=cleanup.get('cleanupEntryQpc') or phase.get('deadlineQpc')!=cleanup.get('deadlineQpc'):raise ValueError('PHASE_CLOCK')
    if cleanup['cleanupEntryQpc']<=0 or cleanup['deadlineQpc']-cleanup['cleanupEntryQpc']!=20*value['frequency']:raise ValueError('DEADLINE')
    return {'run':value['run'],'session':value['session'],'cleanupEntryQpc':cleanup['cleanupEntryQpc'],'frequency':value['frequency'],'cleanupSHA256':digest(cleanup_path),'phaseASHA256':digest(phase_path),'acceptanceSealed':False}
