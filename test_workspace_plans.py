import tempfile
import unittest
from store import Store
import workspaces as w


class ProjectPlanTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store=Store(self.tmp.name); w.setup(self.store)
        self.project=w.change(self.store,{'action':'create','name':'Test'})['id']
        self.a=self.task('Inspect'); self.b=self.task('Repair')

    def task(self,text):
        ref=self.store.task_put(text)['id']
        w.change(self.store,dict(action='link',project=self.project,kind='task',ref=ref))
        return ref

    def plan(self,ref,deps=None,blocker=''):
        return w.change(self.store,dict(action='plan_task',project=self.project,kind='task',ref=ref,
                         plan=dict(objective='Approved fixture',success_criteria='Tests pass',blocker=blocker,depends_on=deps or [])))

    def test_shared_records_readiness_and_restart(self):
        memory=self.store.put('memory','Preferred colour blue')
        self.plan(self.a); self.plan(self.b,[self.a])
        w.change(self.store,dict(action='link',project=self.project,kind='task',ref=self.b))
        self.assertEqual(len(w.listing(self.store)[0]['task_plan']),2)
        rows={x['task_id']:x for x in w.task_plan(self.store,self.project)}
        self.assertEqual(rows[self.b]['state'],'BLOCKED')
        self.store.complete_task(self.a)
        reopened=Store(self.tmp.name); w.setup(reopened)
        rows={x['task_id']:x for x in w.task_plan(reopened,self.project)}
        self.assertEqual(rows[self.b]['state'],'READY')
        self.assertFalse(rows[self.b]['execution_authorized'])
        self.assertEqual(len(reopened.tasks()),2)
        self.assertEqual(reopened.items('memory')[0]['id'],memory['id'])

    def test_cycles_unknown_and_duplicate_dependencies_rejected(self):
        self.plan(self.b,[self.a])
        for deps in ([self.b],[self.a],['missing'],[self.b,self.b]):
            with self.assertRaises(ValueError): self.plan(self.a,deps)
        self.assertEqual(len(w.task_plan(self.store,self.project)),1)

    def test_unlink_dependency_fails_closed_and_blocker(self):
        self.plan(self.b,[self.a])
        self.store.complete_task(self.a)
        w.change(self.store,dict(action='unlink',project=self.project,kind='task',ref=self.a))
        self.assertEqual(w.task_plan(self.store,self.project)[0]['state'],'BLOCKED')
        self.plan(self.b,blocker='Review required')
        self.assertEqual(w.task_plan(self.store,self.project)[0]['state'],'BLOCKED')
