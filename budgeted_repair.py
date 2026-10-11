"""TEST ONLY integration owned by the existing App and its canonical Store."""
import asyncio
import threading

import permissions
import project_budgets as budgets
import repair_workflow
from repair_sandbox import check_candidate
from wearables.real_core import RealCore

CONFIRMATION = 'RUN TEST ONLY DELAY REPAIR'
ALLOCATION = {'core_requests': 1, 'container_checks': 2}


class ExistingServiceCore(RealCore):
    """Reuse the already initialized bridge in-process, never create a Service."""
    def __init__(self, service):
        self.service = service
        self.measurements = []
        self.last_failure = None

    def request(self, op, body):
        return self.service.dispatch(op, body)


async def run(store, core, project, task, operation, confirmation, cancel=None, checker=check_candidate,
              *, before_step=None, test_workflow=None):
    # Optional trusted TEST host hooks. Default workflow/accounting is unchanged.
    # Callbacks cannot be supplied through a renderer/model request.
    if test_workflow is not None and before_step is None:
        raise ValueError('Synthetic workflow requires a lifecycle admission hook.')
    stop = cancel if cancel is not None else threading.Event()
    receipt = budgets.change(store, dict(action='budget_reserve', project=project,
                                        task=task, operation=operation, resources=ALLOCATION))
    if not receipt['new_reservation']:
        return {'status':'REPLAY_NOT_EXECUTED','budget':receipt,'deployed':False}
    # Separate explicit local-user confirmation; budget availability is not consent.
    if confirmation != CONFIRMATION or stop.is_set():
        budgets.lifecycle(store,project,operation,'release',0)
        return {'status':'NOT_AUTHORIZED' if confirmation != CONFIRMATION else 'CANCELLED',
                'deployed':False,'budget_state':'released'}
    lease=budgets.lifecycle(store,project,operation,'start',0)
    revision=lease['revision']
    usage={'core_requests':0,'container_checks':0}
    uncertain=False
    lock=threading.Lock()

    def charge(resource):
        nonlocal revision
        if before_step is not None: before_step()
        if stop.is_set(): raise InterruptedError()
        with lock:
            next_usage={**usage,resource:usage[resource]+1}
            value=budgets.lifecycle(store,project,operation,'consume',revision,usage=next_usage)
            usage.update(next_usage); revision=value['revision']

    class MeteredCore:
        async def respond(self, *args, **kwargs):
            nonlocal uncertain
            charge('core_requests')  # Write-ahead attempt, not guessed token cost.
            try:
                return await core.respond(*args, **kwargs)
            except BaseException:
                uncertain=True
                raise

    def metered_check(source, cancellation):
        nonlocal uncertain
        charge('container_checks')
        try:
            value=checker(source,cancellation)
            if value.get('cleanup') is not True: uncertain=True
            return value
        except BaseException:
            uncertain=True
            raise

    try:
        report=await (test_workflow or repair_workflow.run)(MeteredCore(),stop,metered_check)
    except BaseException:
        # Abrupt/outer cancellation cannot claim verified completion or refund.
        stop.set()
        budgets.lifecycle(store,project,operation,'uncertain',revision)
        raise
    if uncertain:
        budgets.lifecycle(store,project,operation,'uncertain',revision)
        report['budget_state']='recovery_required'
    else:
        success=report['status']=='READY_FOR_REVIEW'
        budgets.lifecycle(store,project,operation,'settle',revision,usage=usage,
                          outcome='succeeded' if success else 'failed', evidence='repair-workflow:'+operation)
        report['budget_state']='settled'
    report['budget_usage']=usage
    report['operation']=operation
    report['execution_authorized_by']='explicit local-user fixture confirmation'
    return report


def dispatch(app, service, body, *, stage4_token=None):
    """Called only AFTER the existing desktop HTTP authentication checks."""
    if getattr(app,'stage4',None) is not None:
        # TEST requests cannot fall through to the actual sandbox/service path.
        return app.stage4.repair_dispatch(stage4_token,body)
    if type(body) is not dict: raise ValueError('Expected object.')
    action=body.get('action')
    operation=body.get('operation')
    if type(operation) is not str or not 1<=len(operation)<=100: raise ValueError('Invalid operation ID.')
    with app.lock:
        current=getattr(app,'repair_experiment',None)
        if action in ('status','cancel'):
            if set(body)!={'action','operation'} or not current or current['operation']!=operation:
                raise ValueError('Unknown experiment.')
            if action=='cancel': current['cancel'].set()
            return {'operation':operation,'status':current['status'],
                    'cancel_requested':current['cancel'].is_set(),'deployed':False}
        if action!='run' or set(body)!={'action','operation','project','task','confirmation'}:
            raise ValueError('Only the fixed approved fixture is supported.')
        if current and current['status']=='RUNNING': raise ValueError('A repair experiment is already running.')
        # Looked at under the lock the emergency stop takes, so no experiment starts as a stop arrives.
        if getattr(app,'stopped',None) is not None: raise ValueError(permissions.STOPPED_MESSAGE)
        stop=threading.Event()
        current={'operation':operation,'status':'RUNNING','cancel':stop}
        app.repair_experiment=current
    try:
        result=asyncio.run(run(app.store,ExistingServiceCore(service),body['project'],body['task'],
                              operation,body['confirmation'],stop))
        with app.lock: current['status']=result['status']
        return result
    finally:
        with app.lock:
            if current['status']=='RUNNING': current['status']='FAILED'
