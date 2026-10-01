"""Offline acceptance tests; temporary data and mocked news, no live API calls.

Run from the JARVIS directory: .venv/Scripts/python.exe -m unittest discover -s review -p briefing_regressions.py -v
"""
import tempfile
import unittest
from unittest.mock import patch
from server import App
import workspaces


class BriefingRegressions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.app = App(self.temp.name)

    def brief(self, news=None):
        with patch('actions.news_search', return_value=news or {'results': [], 'retrieved_at': '2026-09-09T00:00:00+00:00'}):
            return self.app.tool('daily_briefing', {})

    def test_empty_success_is_empty(self):
        result = self.brief()
        for key in ('news', 'tasks', 'projects', 'reminders'):
            self.assertEqual(result[key], [])

    def test_each_request_checks_news_again(self):
        with patch('actions.news_search', return_value={'results': []}) as check:
            self.app.tool('daily_briefing', {})
            self.app.tool('daily_briefing', {})
            self.assertEqual(check.call_count, 2)

    def test_news_failure_preserves_local_tasks(self):
        self.app.store.put('task', 'Review design')
        with patch('actions.news_search', side_effect=TimeoutError('synthetic outage')):
            result = self.app.tool('daily_briefing', {})
        self.assertEqual(result['tasks'][0]['body'], 'Review design')
        self.assertEqual(result['checks']['news']['status'], 'unavailable')

    def test_projects_match_project_workspace(self):
        created = workspaces.change(self.app.store, {'action': 'create', 'name': 'Acceptance project'})
        self.assertIn(created['id'], [item['id'] for item in self.brief()['projects']])

    def test_retrieval_timestamp_is_preserved_even_when_old(self):
        timestamp = '2000-01-01T00:00:00+00:00'
        result = self.brief({'results': [], 'retrieved_at': timestamp})
        self.assertEqual(result['checks']['news']['retrieved_at'], timestamp)

    def test_briefing_does_not_duplicate_tasks_or_timers(self):
        self.app.store.put('task', 'One task')
        self.app.store.reminder('One timer', 60)
        self.brief()
        self.brief()
        self.assertEqual(len(self.app.store.tasks()), 1)
        self.assertEqual(len(self.app.store.reminders()), 1)

    def test_local_failure_does_not_hide_other_sections_or_leak_error(self):
        with patch.object(self.app.store, 'tasks', side_effect=RuntimeError('sensitive-test-detail')):
            result = self.brief()
        self.assertEqual(result['checks']['tasks']['status'], 'unavailable')
        self.assertEqual(result['checks']['reminders']['status'], 'empty')
        self.assertNotIn('sensitive-test-detail', str(result))

    def test_truncation_and_measured_duration_are_explicit(self):
        for i in range(10):
            self.app.store.put('task', 'Task ' + str(i))
        result = self.brief()
        self.assertEqual(len(result['tasks']), 8)
        self.assertEqual(result['checks']['tasks']['total'], 10)
        self.assertTrue(result['checks']['tasks']['truncated'])
        self.assertGreaterEqual(result['checks']['tasks']['duration_ms'], 0)
