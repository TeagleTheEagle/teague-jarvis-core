import asyncio
from concurrent.futures import ThreadPoolExecutor
import tempfile
import threading
import unittest
from unittest.mock import patch
from store import Store
import workspaces as w
import budgeted_repair as r
from test_repair_workflow import CoreFixture,checker


class BudgetedRepairTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.s=Store(self.tmp.name); w.setup(self.s)
        self.p=w.change(self.s,dict(action='create',name='TEST ONLY'))['id']
        self.t=self.s.task_put('Fixture repair')['id']
        w.change(self.s,dict(action='link',project=self.p,kind='task',ref=self.t))
        w.change(self.s,dict(action='budget_configure',project=self.p,limits=r.ALLOCATION))
        self.core=CoreFixture()

    def run_case(self,operation='one',confirmation=r.CONFIRMATION,check=checker):
        return asyncio.run(r.run(self.s,self.core,self.p,self.t,operation,confirmation,checker=check))

    def test_success_single_core_settles_and_replay_does_not_execute(self):
        result=self.run_case()
        self.assertEqual(result['status'],'READY_FOR_REVIEW')
        self.assertEqual(result['budget_state'],'settled')
        self.assertEqual(result['budget_usage'],r.ALLOCATION)
        self.assertEqual(self.core.calls,1)
        self.assertEqual(self.run_case()['status'],'REPLAY_NOT_EXECUTED')
        self.assertEqual(self.core.calls,1)

    def test_budget_is_not_authorization(self):
        result=self.run_case(confirmation='')
        self.assertEqual(result['status'],'NOT_AUTHORIZED')
        self.assertEqual(self.core.calls,0)
        self.assertEqual(w.listing(self.s)[0]['budget']['remaining'],r.ALLOCATION)
        self.assertEqual(self.run_case()['status'],'REPLAY_NOT_EXECUTED')

    def test_failure_with_verified_no_future_work_releases_unused(self):
        result=self.run_case(check=lambda *_:dict(cleanup=True,status='FAILED',execution_status='EXITED',exit_code=1))
        self.assertEqual(result['status'],'FAILED')
        self.assertEqual(result['budget_state'],'settled')
        remaining=w.listing(self.s)[0]['budget']['remaining']
        self.assertEqual(remaining,dict(core_requests=1,container_checks=1))

    def test_uncertain_cleanup_holds_remaining_capacity_across_restart(self):
        def broken(*_): raise RuntimeError('cleanup uncertain')
        result=self.run_case(check=broken)
        self.assertEqual(result['budget_state'],'recovery_required')
        self.s=Store(self.tmp.name); w.setup(self.s)
        self.assertEqual(w.listing(self.s)[0]['budget']['remaining'],dict(core_requests=0,container_checks=0))
        with self.assertRaises(ValueError): self.run_case('two')

    def test_duplicate_concurrent_attempts_one_workflow(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda _:self.run_case(),range(2)))
        self.assertEqual(sorted(x['status'] for x in results),['READY_FOR_REVIEW','REPLAY_NOT_EXECUTED'])
        self.assertEqual(self.core.calls,1)

    def test_existing_bridge_is_reused(self):
        class Service:
            def dispatch(self,op,body): return {'op':op,'body':body}
        service=Service()
        client=r.ExistingServiceCore(service)
        self.assertIs(client.service,service)
        self.assertEqual(client.request('status',{})['op'],'status')

    def test_cancel_prevents_next_resource(self):
        stop=threading.Event()
        def cancelled(source,token):
            value=checker(source,token); stop.set(); return value
        result=asyncio.run(r.run(self.s,self.core,self.p,self.t,'one',r.CONFIRMATION,stop,cancelled))
        self.assertEqual(result['status'],'CANCELLED')
        self.assertEqual(self.core.calls,0)
        self.assertEqual(result['budget_usage'],dict(core_requests=0,container_checks=1))
