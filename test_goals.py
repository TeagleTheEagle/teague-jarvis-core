"""Goals JARVIS suggests (goals.py; owner, 2026-10-13: "work and adopt goals on their own, just they have to ask"), and
the wider set of program files he may propose a change to (development.py): a suggestion is only ever a card for the
owner; yes makes a mission, no is kept; nothing starts by itself. Also what is protected: the gateway, the permission
table, the guard, the tests, the launchers.
"""
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import actions
import development
import goals
import permissions
from server import App, Run
from store import Store


class GoalsRecordTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.goals = goals.Goals(Store(self.temp.name))

    def test_a_suggestion_is_kept_and_answered_once(self):
        row = self.goals.propose('Tidy the downloads folder into dated subfolders', 'the owner asked three times this week')
        self.assertEqual((row['state'], row['by'], row['mission']), ('proposed', 'JARVIS', None))
        self.assertEqual(self.goals.list()[0]['id'], row['id'])
        done = self.goals.answer(row['id'], True)
        self.assertEqual(done['state'], 'adopted')
        self.goals.started(row['id'], 'mission-1')
        self.assertEqual(self.goals.get(row['id'])['mission'], 'mission-1')
        with self.assertRaises(goals.GoalError):
            self.goals.answer(row['id'], False)   # once

    def test_the_words_are_checked(self):
        with self.assertRaises(goals.GoalError): self.goals.propose('short', 'because')
        with self.assertRaises(goals.GoalError): self.goals.propose('a' * 601, 'because')
        with self.assertRaises(goals.GoalError): self.goals.propose('A fair goal in words', '')
        self.assertEqual(self.goals.propose('  Sort   the\nphotos  ', 'they pile up')['goal'], 'Sort the photos')

    def test_caps_the_same_goal_twice_and_the_day(self):
        for n in range(goals.PENDING_MAX):
            self.goals.propose(f'Goal number {n} of the morning', 'noticed it')
        with self.assertRaises(goals.GoalError) as caught:
            self.goals.propose('One suggestion too many', 'noticed it')
        self.assertIn('already wait', str(caught.exception))
        first = self.goals.list()[-1]
        self.goals.answer(first['id'], False)
        with self.assertRaises(goals.GoalError) as caught:
            self.goals.propose(first['goal'].upper(), 'again')   # declined this week, case apart
        self.assertIn('already suggested', str(caught.exception))
        # The daily cap counts adoptions, from the record.
        g = goals.Goals(Store(tempfile.mkdtemp(dir=self.temp.name)))
        for n in range(goals.DAILY_MAX):
            g.answer(g.propose(f'Adopted goal {n}', 'worth it')['id'], True)
        with self.assertRaises(goals.GoalError) as caught:
            g.propose('A sixth goal today', 'worth it')
        self.assertIn('today', str(caught.exception))

    def test_unanswered_suggestions_lapse_and_a_core_start_lapses_them_all(self):
        old = self.goals.propose('An old idea nobody answered', 'noticed', now=time.time() - goals.ANSWER_SECONDS - 5)
        self.goals.propose('A fresh idea', 'noticed')
        states = {r['goal']: r['state'] for r in self.goals.list()}
        self.assertEqual(states, {'An old idea nobody answered': 'expired', 'A fresh idea': 'proposed'})
        with self.assertRaises(goals.GoalError):
            self.goals.answer(old['id'], True)
        again = goals.Goals(self.goals.store)   # the Core starts again: the cards are gone, so the waiting suggestions lapse
        self.assertEqual({r['state'] for r in again.list()}, {'expired'})
        self.assertEqual(again.propose('A fresh idea', 'noticed')['state'], 'proposed', 'a lapsed goal may be suggested again')


class GoalsInTheCoreTests(unittest.TestCase):
    """Through App.tool and App.approve, as a question and the owner's click reach it."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.app = App(Path(self.temp.name))
        self.run = Run('goal-test')
        self.run.user_text = 'what should we do about the photos?'
        self.app.runs[self.run.id] = self.run

    def suggest(self, run=None, goal='Sort the photo folder by year and month', why='the owner asked about it twice'):
        return self.app.tool('goal_propose', {'goal': goal, 'why': why}, run if run is not None else self.run)

    def test_the_tool_and_its_rule(self):
        self.assertTrue(actions.validate('goal_propose', {'goal': 'x', 'why': 'y'}))
        rule = permissions.TABLE['goal_propose']
        self.assertEqual((rule.asks, rule.effect, rule.receipt), (permissions.ALWAYS, permissions.CHANGES, True))
        self.assertIn('goal_propose', [t['function']['name'] for t in self.app.offered_tools()])
        self.assertNotIn('goal_propose', [t['function']['name'] for t in self.app.workshop.mission_tools()], 'a mission cannot propose more work')
        self.assertIn('goal_propose', self.app.instructions())
        self.assertIn('nothing starts until they say yes', self.app.instructions())

    def test_a_suggestion_waits_as_a_card_and_starts_nothing(self):
        result = self.suggest()
        self.assertEqual(result['status'], 'awaiting approval')
        self.assertIn('Nothing has started', result['summary'])
        card = self.app.approvals[result['approval']['id']]
        self.assertEqual((card['tool'], card['generic'], card['label']), ('goal_propose', True, goals.LABEL))
        self.assertEqual(card['args']['goal'], 'Sort the photo folder by year and month')
        self.assertAlmostEqual(card['expires'] - card['created'], goals.ANSWER_SECONDS, delta=5, msg='the card waits as long as the suggestion')
        self.assertEqual(self.app.goals.list()[0]['state'], 'proposed')
        self.assertIsNone(self.app.workshop.running())
        self.assertEqual(self.app.workshop_listing()['goals'][0]['id'], card['args']['id'])
        rows = self.app.approval_rows()   # a paired device that may approve sees the goal and the reason
        self.assertEqual(rows[0]['label'], 'Suggest a goal of his own')
        self.assertIn('Sort the photo folder', rows[0]['detail'])
        self.assertIn('twice', rows[0]['detail'])

    def test_no_declines_it_and_keeps_it(self):
        result = self.suggest()
        self.assertEqual(self.app.approve(result['approval']['id'], False), {'status': 'denied'})
        row = self.app.goals.list()[0]
        self.assertEqual(row['state'], 'declined')
        self.assertIsNone(self.app.workshop.running())
        said = [m for m in self.app.store.history('goal-test') if m['role'] == 'assistant']
        self.assertTrue(said and said[-1]['content'].startswith('Declined on screen'), said)
        with self.assertRaises(ValueError):
            self.suggest()   # the same goal is not suggested again this week

    def test_yes_adopts_it_and_starts_a_mission(self):
        result = self.suggest()
        started = {}
        def start_mission(goal):
            started['goal'] = goal
            return {'status': 'started', 'id': 'm-1', 'chat': 'mission-chat', 'minutes': 15, 'note': 'runs'}
        with patch.object(self.app.workshop, 'start_mission', start_mission):
            done = self.app.approve(result['approval']['id'], True)
        self.assertEqual(done['status'], 'applied')
        self.assertEqual(done['result']['status'], 'started')
        self.assertEqual(started['goal'], 'Sort the photo folder by year and month')
        row = self.app.goals.list()[0]
        self.assertEqual((row['state'], row['mission']), ('adopted', 'm-1'))
        with self.assertRaises(ValueError):
            self.app.approve(result['approval']['id'], True)   # single use

    def test_a_mission_that_cannot_start_leaves_the_goal_failed(self):
        result = self.suggest()
        self.app.stopped = time.time()   # the emergency stop holds: approving is refused and the card stays
        with self.assertRaises(ValueError):
            self.app.approve(result['approval']['id'], True)
        self.app.stopped = None
        self.assertEqual(self.app.goals.list()[0]['state'], 'proposed')
        with patch.object(self.app.workshop, 'start_mission', side_effect=ValueError('A mission is running already')):
            with self.assertRaises(ValueError) as caught:
                self.app.approve(result['approval']['id'], True)
        self.assertIn('could not start', str(caught.exception))
        row = self.app.goals.list()[0]
        self.assertEqual(row['state'], 'failed')
        self.assertIn('running already', row['mission'])

    def test_refused_from_a_mission_and_after_outside_text(self):
        mission_run = Run('mission-chat')
        mission_run.mission = 'm-1'
        with self.assertRaises(ValueError) as caught:
            self.suggest(mission_run)
        self.assertIn('mission cannot suggest', str(caught.exception))
        self.run.tainted = True
        with self.assertRaises(ValueError) as caught:
            self.suggest()
        self.assertEqual(str(caught.exception), goals.TAINTED)
        self.assertEqual(self.app.goals.list(), [])
        self.assertEqual(self.app.approvals, {})

    def test_the_caps_hold_through_the_core(self):
        for n in range(goals.PENDING_MAX):
            self.suggest(goal=f'Goal number {n} for the owner')
        with self.assertRaises(ValueError):
            self.suggest(goal='One too many for today')
        self.assertEqual(len(self.app.approvals), goals.PENDING_MAX)

    def test_switched_off_means_no_suggestions(self):
        self.app.set_permission('goal_propose', permissions.OFF)
        with self.assertRaises(ValueError):
            self.suggest()
        self.assertNotIn('goal_propose', [t['function']['name'] for t in self.app.offered_tools()])


class ProgramFilesTests(unittest.TestCase):
    """What JARVIS may propose a change to (development.allowed): any module of the Core, the window, the companion;
    never what decides whether a change happens."""

    def test_allowed_and_protected(self):
        for path in ('nudges.py', 'workshop.py', 'music.py', 'static/workshop.js', 'static/style.css', 'static/index.html',
                     'desktop/companion.js', 'personality.txt', 'owner-style.css'):
            self.assertTrue(development.allowed(path), path)
        for path in ('server.py', 'actions.py', 'permissions.py', 'content_guard.py', 'development.py', 'core_lock.py',
                     'runtime_paths.py', 'store.py', 'goals.py', 'test_goals.py', 'test_jarvis.py', 'desktop/main.cjs',
                     'desktop/local-updates.cjs', '../wake.py', '.env', 'C:/x.py', 'static/../server.py', 'tools/build.py',
                     'docs/x.md', 'Server.py', None, 7):
            self.assertFalse(development.allowed(path), path)

    def test_reading_and_proposing_a_core_module(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name) / 'program'
        root.mkdir()
        (root / 'nudges.py').write_text('LIMIT = 3\n', encoding='utf-8')
        (root / 'personality.txt').write_text('You are JARVIS.\n', encoding='utf-8')
        where = development.layout(root)
        self.assertEqual(development.read(where, 'nudges.py'), 'LIMIT = 3\n')
        with self.assertRaises(ValueError) as caught:
            development.read(where, 'server.py')
        self.assertIn('excluded', str(caught.exception))
        with self.assertRaises(ValueError) as caught:
            development.read(where, 'music.py')   # allowed in kind, but no such file here
        self.assertIn('No such program file', str(caught.exception))
        p = development.edit(where, 'nudges.py', 'LIMIT = 3', 'LIMIT = 4', 'one more nudge')
        self.assertTrue(p['requires_approval'])
        self.assertIn('-LIMIT = 3', p['diff'])
        self.assertEqual((root / 'nudges.py').read_text(encoding='utf-8'), 'LIMIT = 3\n', 'nothing applied before approval')
        with patch('runtime_paths.installed', return_value=True):
            installed = development.layout(root, data=root / 'data', config=Path(temp.name) / 'config', installed=True)
            p = development.edit(installed, 'nudges.py', 'LIMIT = 3', 'LIMIT = 5', 'for the next release')
        self.assertEqual((p['status'], p['requires_approval']), (development.PROPOSAL_ONLY, False), 'an installed JARVIS keeps it for the engineer')
        self.assertIn('engineer', development.guidance(True))
        self.assertIn('any Python module of the Core', development.guidance(False))


if __name__ == '__main__':
    unittest.main()
