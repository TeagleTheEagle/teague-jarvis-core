from concurrent.futures import ThreadPoolExecutor
import tempfile
import unittest
from unittest.mock import patch
from store import Store
import workspaces as w
import project_budgets as b


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.s=Store(self.temp.name); w.setup(self.s)
        self.p=w.change(self.s,dict(action='create',name='Shared project'))['id']
        self.tasks=[self.s.task_put(name)['id'] for name in ('First','Second')]
        for task in self.tasks: w.change(self.s,dict(action='link',project=self.p,kind='task',ref=task))

    def configure(self,n=1):
        return w.change(self.s,dict(action='budget_configure',project=self.p,limits=dict(core_requests=n,container_checks=n*2)))

    def reserve(self,op,task=None):
        return w.change(self.s,dict(action='budget_reserve',project=self.p,operation=op,task=task or self.tasks[0],
                                   resources=dict(core_requests=1,container_checks=2)))

    def test_tasks_share_limit_and_restart_does_not_refund(self):
        memory=self.s.put('memory','Favourite colour blue')
        self.configure(); self.reserve('one')
        with self.assertRaises(ValueError): self.reserve('two',self.tasks[1])
        self.s=Store(self.temp.name); w.setup(self.s)
        with self.assertRaises(ValueError): self.reserve('three')
        replay=self.reserve('one')
        self.assertFalse(replay['new_reservation']); self.assertTrue(replay['replay'])
        self.assertFalse(replay['execution_authorized'])
        self.assertEqual(self.s.items('memory')[0]['id'],memory['id'])
        self.assertEqual(len(self.s.tasks()),2)

    def test_atomic_competing_reservations(self):
        self.configure()
        def attempt(i):
            try: return self.reserve(str(i))['new_reservation']
            except ValueError: return False
        with ThreadPoolExecutor(max_workers=8) as pool:
            self.assertEqual(sum(pool.map(attempt,range(8))),1)

    def test_replay_cannot_change_task_or_reset_usage(self):
        self.configure(); self.reserve('same')
        with self.assertRaises(ValueError): self.reserve('same',self.tasks[1])
        with self.assertRaises(ValueError): self.configure(0)
        self.configure(2)
        self.assertEqual(self.reserve('new')['remaining']['core_requests'],0)

    def test_no_implicit_budget_or_unlinked_task(self):
        with self.assertRaises(ValueError): self.reserve('before')
        self.configure()
        with self.assertRaises(ValueError): self.reserve('bad','absent')

    def test_invalid_counts_fail_closed(self):
        for value in (-1,True,1.5,10001,float('nan')):
            with self.assertRaises(ValueError):
                w.change(self.s,dict(action='budget_configure',project=self.p,
                                    limits=dict(core_requests=value,container_checks=2)))
        self.assertFalse(w.listing(self.s)[0]['budget']['configured'])

    def step(self,action,revision=0,**kwargs):
        return b.lifecycle(self.s,self.p,'one',action,revision,**kwargs)

    def test_expiry_does_not_refund_or_allow_start_and_unstarted_recovery(self):
        self.configure()
        with patch.object(b.time,'time',return_value=100): self.reserve('one')
        with patch.object(b.time,'time',return_value=401):
            self.assertEqual(w.listing(self.s)[0]['budget']['recovery_required'],['one'])
            with self.assertRaises(ValueError): self.step('start')
            self.assertEqual(self.step('expire')['state'],'recovery_required')
            with self.assertRaises(ValueError): self.reserve('two')
            self.step('release',1)
        self.assertTrue(self.reserve('two')['new_reservation'])
        self.assertTrue(self.step('release',1)['replay'])

    def test_partial_consumption_failure_settlement_releases_only_unused(self):
        self.configure(); self.reserve('one'); self.step('start')
        usage=dict(core_requests=1,container_checks=1)
        self.step('consume',1,usage=usage)
        budget=w.listing(self.s)[0]['budget']
        self.assertEqual(budget['held'],dict(core_requests=0,container_checks=1))
        self.assertEqual(budget['remaining']['container_checks'],0)
        self.step('settle',2,usage=usage,outcome='failed',evidence='verified-test-result')
        budget=w.listing(self.s)[0]['budget']
        self.assertEqual(budget['remaining'],dict(core_requests=0,container_checks=1))
        self.assertTrue(self.step('settle',2,usage=usage,outcome='failed',evidence='verified-test-result')['replay'])
        with self.assertRaises(ValueError): self.step('settle',3,usage=dict(core_requests=0,container_checks=0),outcome='failed',evidence='different')

    def test_started_expiry_keeps_charge_until_verified_settlement(self):
        self.configure()
        with patch.object(b.time,'time',return_value=100):
            self.reserve('one'); self.step('start')
        self.s=Store(self.temp.name); w.setup(self.s)
        with patch.object(b.time,'time',return_value=500): self.step('expire',1)
        with self.assertRaises(ValueError): self.step('release',2)
        with self.assertRaises(ValueError): self.reserve('two')
        self.step('settle',2,usage=dict(core_requests=0,container_checks=0),outcome='failed',evidence='verified-no-work-began')
        self.assertTrue(self.reserve('two')['new_reservation'])

    def test_stale_and_overconsumption_cannot_change_ledger(self):
        self.configure(); self.reserve('one'); self.step('start')
        with self.assertRaises(ValueError): self.step('start')
        with self.assertRaises(ValueError): self.step('consume',1,usage=dict(core_requests=2,container_checks=0))
        self.step('consume',1,usage=dict(core_requests=1,container_checks=0))
        with self.assertRaises(ValueError): self.step('consume',2,usage=dict(core_requests=0,container_checks=0))
        with self.assertRaises(ValueError): self.step('settle',2,usage=dict(core_requests=1,container_checks=0),outcome='failed')

    def test_corrupted_reservation_blocks_new_capacity(self):
        self.configure(2); self.reserve('one')
        with self.s.connect() as db:
            db.execute('UPDATE project_budget_reservations SET core_requests=-10')
        with self.assertRaises(ValueError): self.reserve('two')
        with self.assertRaises(ValueError): w.listing(self.s)

    def test_duplicate_concurrent_requests_one_grant(self):
        self.configure()
        with ThreadPoolExecutor(max_workers=8) as pool:
            results=list(pool.map(lambda _:self.reserve('one'),range(8)))
        self.assertEqual(sum(x['new_reservation'] for x in results),1)
        self.assertEqual(sum(x['replay'] for x in results),7)

    def test_start_release_race_one_transition_wins(self):
        self.configure(); self.reserve('one')
        def attempt(action):
            try: return self.step(action)
            except ValueError: return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(attempt,['start','release']))
        self.assertEqual(sum(x is not None for x in results),1)
