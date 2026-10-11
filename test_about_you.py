"""The You page (release 1.0.19, about_you.py, docs/ABOUT-YOU.md; the owner's "lets make jarvis and me more connected
personally", "He knows my life"): the entries and their checks, the dates that come round, the summary every question
carries, the about_you and remember_about_you tools through the Core (an offer waits for the owner's OK, and the OK
keeps exactly what the card showed), the owner's own clicks, the export and the permissions."""
import datetime
import json
import os
import tempfile
import time
import unittest
from unittest.mock import patch

import about_you
import content_guard
import permissions
from about_you import Profile, ProfileError
from server import App, Run
from store import Store


class ProfileCase(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.store = Store(folder.name)
        self.profile = Profile(self.store)


class EntryTests(ProfileCase):
    def test_entries_are_checked_kept_once_changed_and_removed(self):
        will = self.profile.add('person', '  Will ', 'brother', 3, 14, 1996)
        self.assertEqual((will['title'], will['detail'], will['month'], will['day'], will['year']), ('Will', 'brother', 3, 14, 1996))
        self.assertEqual(self.profile.add('person', 'will', 'brother', 3, 14, 1996)['id'], will['id'])   # the same entry twice is kept once
        self.profile.add('about', 'I work as an electrician in Sydney')
        self.profile.add('like', 'AC/DC')
        self.profile.add('date', 'Wedding anniversary', '', 6, 20, 2020)
        self.assertEqual([r['section'] for r in self.profile.entries()], ['about', 'person', 'date', 'like'])
        changed = self.profile.update(will['id'], detail='older brother')
        self.assertEqual((changed['detail'], changed['month']), ('older brother', 3))
        self.assertEqual(self.profile.remove(will['id'])['title'], 'Will')
        self.assertEqual(len(self.profile.entries()), 3)
        with self.assertRaises(ProfileError):
            self.profile.remove(will['id'])

    def test_what_is_refused_is_said_plainly(self):
        for args, words in ((('pet', 'Rex'), 'section is one of'), (('like', ''), 'Write the line'),
                            (('like', 'x' * 121), 'at most 120'), (('person', 'Will <b>'), '< or >'),
                            (('date', 'Anniversary'), 'needs its day and month'), (('like', 'AC/DC', '', 3, 14), 'Only a person'),
                            (('person', 'Will', '', 2, 30), 'does not exist'), (('person', 'Will', '', 2, 29, 2023), 'does not exist in that year'),
                            (('person', 'Will', '', 13, 1), 'does not exist'), (('person', 'Will', '', 3, 14, 1800), 'between 1900'),
                            (('about', 'My wifi password: OPENAI_API_KEY=sk-0123456789abcdef0123456789abcdef'), 'Passwords, keys and tokens')):
            with self.subTest(args=args), self.assertRaises(ProfileError) as refused:
                self.profile.add(*args)
            self.assertIn(words, str(refused.exception))
        self.assertEqual(self.profile.add('person', 'Leap', '', 2, 29)['day'], 29)   # 29 February without a year is fine

    def test_dates_parse_from_the_tool(self):
        self.assertEqual(about_you.parse_date('1996-03-14'), (3, 14, 1996))
        self.assertEqual(about_you.parse_date('10-14'), (10, 14, None))
        self.assertEqual(about_you.parse_date(' '), (None, None, None))
        with self.assertRaises(ProfileError):
            about_you.parse_date('14 March')


class UpcomingTests(ProfileCase):
    def test_birthdays_and_dates_come_round_soonest_first(self):
        today = datetime.date(2026, 10, 10)   # a Saturday
        self.profile.add('person', 'Will', 'brother', 10, 13, 1996)
        self.profile.add('person', 'Mum', 'mother', 10, 10)
        self.profile.add('date', 'Wedding anniversary', '', 10, 11, 2020)
        self.profile.add('person', 'Far', '', 12, 25)
        soon = self.profile.upcoming(today)
        self.assertEqual([(s['entry']['title'], s['days'], s['years']) for s in soon],
                         [('Mum', 0, None), ('Wedding anniversary', 1, 6), ('Will', 3, 30)])
        self.assertEqual([Profile.soon_words(s) for s in soon],
                         ['Mum’s birthday: today, Saturday 10 October', 'Wedding anniversary: tomorrow, Sunday 11 October, 6 years',
                          'Will’s birthday: in 3 days, Tuesday 13 October, turns 30'])

    def test_the_year_turns_and_29_february(self):
        self.profile.add('person', 'Jan', '', 1, 2, 2000)
        self.profile.add('person', 'Leap', '', 2, 29, 2000)
        soon = self.profile.upcoming(datetime.date(2026, 12, 20), days=40)
        self.assertEqual([(s['entry']['title'], s['date'], s['years']) for s in soon], [('Jan', datetime.date(2027, 1, 2), 27)])
        leap = self.profile.upcoming(datetime.date(2027, 2, 20))
        self.assertEqual([(s['entry']['title'], s['date']) for s in leap], [('Leap', datetime.date(2027, 2, 28))])   # kept on the 28th


class ContextTests(ProfileCase):
    def test_the_summary_comes_up_first_and_stays_bounded(self):
        self.assertIsNone(self.profile.context())
        today = datetime.date(2026, 10, 10)
        self.profile.add('about', 'I work as an electrician in Sydney')
        self.profile.add('person', 'Will', 'brother', 10, 13, 1996)
        self.profile.add('goal', 'Run 10 km by Christmas')
        summary = self.profile.context(today)
        self.assertEqual(summary['coming_up'], ['Will’s birthday: in 3 days, Tuesday 13 October, turns 30'])
        self.assertEqual((summary['about'], summary['people'], summary['goals']),
                         (['I work as an electrician in Sydney'], ['Will (brother), birthday 13 October 1996'], ['Run 10 km by Christmas']))
        self.assertNotIn('more', summary)
        for n in range(80):
            self.profile.add('like', f'Song number {n} by a band with a long name')
        summary = self.profile.context(today)
        self.assertLessEqual(len(json.dumps(summary, ensure_ascii=False)), about_you.CONTEXT_CHARS)
        self.assertIn('coming_up', summary)
        self.assertIn('read them with about_you', summary['more'])

    def test_search_finds_by_words_and_section(self):
        self.profile.add('person', 'Will', 'brother', 10, 13, 1996)
        self.profile.add('like', 'AC/DC')
        self.assertEqual([f['line'] for f in self.profile.search('brother')], ['Will (brother), birthday 13 October 1996'])
        self.assertEqual([f['line'] for f in self.profile.search('likes')], ['AC/DC'])
        self.assertEqual(len(self.profile.search('')), 2)


class PermissionTests(unittest.TestCase):
    def test_reading_runs_an_offer_keeps_its_own_approval_and_a_device_needs_the_tick(self):
        self.assertEqual(permissions.decide('about_you', {})[0], 'run')
        self.assertEqual(permissions.TABLE['remember_about_you'].asks, permissions.ALWAYS)
        self.assertEqual(permissions.decide('remember_about_you', {}, tainted=True)[0], 'run')   # its own card, also in a marked question
        self.assertEqual(permissions.decide('about_you', {}, wearable=True)[0], 'run')
        self.assertEqual(permissions.decide('remember_about_you', {}, wearable=True)[0], 'refuse')
        self.assertEqual(permissions.decide('remember_about_you', {}, wearable=True, writes=True)[0], 'run')
        self.assertTrue({'about_you', 'remember_about_you'} <= content_guard.OWN)   # JARVIS's own records: the guard leaves them


class CoreTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        environment = patch.dict(os.environ, {'OPENAI_API_KEY': 'test-only-not-a-key'}, clear=True)
        environment.start()
        self.addCleanup(environment.stop)
        blocked = patch('providers.request', side_effect=AssertionError('no network in these tests'))
        blocked.start()
        self.addCleanup(blocked.stop)
        self.app = App(folder.name)
        self.script, self.seen = [], []
        chat = patch('providers.chat', side_effect=self.fake_chat)
        chat.start()
        self.addCleanup(chat.stop)

    def fake_chat(self, messages, tools, emit, cancel, vision=False, **options):
        self.seen.append(json.loads(json.dumps(messages, default=str)))
        return self.script.pop(0) if self.script else {'role': 'assistant', 'content': 'Done.'}

    @staticmethod
    def call(name, **args):
        return {'role': 'assistant', 'content': None,
                'tool_calls': [{'id': 'c' + name, 'type': 'function', 'function': {'name': name, 'arguments': json.dumps(args)}}]}

    def ask(self, words, conversation='you'):
        started = self.app.start_run({'text': words, 'conversation': conversation})
        run = self.app.runs[started['run_id']]
        deadline = time.time() + 30
        while not run.done and time.time() < deadline:
            time.sleep(0.02)
        self.assertTrue(run.done, 'the question did not end')
        return run

    def test_every_question_carries_the_summary_and_the_guidance(self):
        self.app.profile_action({'action': 'add', 'section': 'person', 'title': 'Will', 'detail': 'brother', 'month': 3, 'day': 14, 'year': 1996})
        self.app.profile_action({'action': 'add', 'section': 'about', 'title': 'I work as an electrician'})
        self.script[:] = [{'role': 'assistant', 'content': 'Hello.'}]
        self.ask('Hi there')
        system, context = self.seen[0][0]['content'], self.seen[0][1]['content']
        self.assertIn(about_you.GUIDANCE, system)
        self.assertIn('Will (brother), birthday 14 March 1996', context)
        self.assertIn('I work as an electrician', context)

    def test_an_offer_waits_for_the_owner_and_the_ok_keeps_exactly_the_card(self):
        self.script[:] = [self.call('remember_about_you', section='person', title='Will', detail='brother', date='1996-03-14',
                                    reason='You said your brother Will turns 30.'),
                          {'role': 'assistant', 'content': 'I have offered to remember that.'}]
        run = self.ask('My brother Will turns 30 on the 14th of March')
        self.assertEqual(self.app.profile.entries(), [])                     # nothing kept yet
        offered = [e['data']['result'] for e in run.events if e['event'] == 'tool.completed' and e['data']['name'] == 'remember_about_you'][0]
        self.assertEqual(offered['status'], 'awaiting approval')
        card = offered['approval']['args']
        self.assertEqual((card['section'], card['title'], card['detail'], card['date']), ('person', 'Will', 'brother', '1996-03-14'))
        self.assertEqual(self.app.approvals[offered['approval']['id']]['args'], card)
        self.app.approve(offered['approval']['id'], True)
        kept = self.app.profile.entries()
        self.assertEqual([(r['title'], r['detail'], r['month'], r['day'], r['year']) for r in kept], [('Will', 'brother', 3, 14, 1996)])
        # A denied offer keeps nothing.
        self.script[:] = [self.call('remember_about_you', section='like', title='Long walks', detail='', date='', reason='You said so.'),
                          {'role': 'assistant', 'content': 'Offered.'}]
        run = self.ask('I love long walks')
        offered = [e['data']['result'] for e in run.events if e['event'] == 'tool.completed' and e['data']['name'] == 'remember_about_you'][0]
        self.app.approve(offered['approval']['id'], False)
        self.assertEqual(len(self.app.profile.entries()), 1)

    def test_an_offer_with_a_secret_is_refused_before_any_card(self):
        self.script[:] = [self.call('remember_about_you', section='about', title='My key is sk-0123456789abcdef0123456789abcdef', detail='', date='', reason='x'),
                          {'role': 'assistant', 'content': 'No.'}]
        run = self.ask('Here is something about me')   # not "remember ...": that is JARVIS's own memory command, answered without the model
        failed = [e['data'] for e in run.events if e['event'] == 'tool.failed' and e['data']['name'] == 'remember_about_you']
        self.assertTrue(failed)
        self.assertEqual(self.app.approvals_waiting(), 0)
        self.assertIn('Passwords, keys and tokens', self.seen[1][-1]['content'])

    def test_reading_the_page_and_the_owners_own_clicks(self):
        state = self.app.profile_action({'action': 'add', 'section': 'like', 'title': 'AC/DC'})
        self.assertEqual([e['line'] for e in state['entries']], ['AC/DC'])
        entry = state['entries'][0]['id']
        state = self.app.profile_action({'action': 'update', 'id': entry, 'title': 'AC/DC, Shoot to Thrill'})
        self.assertEqual(state['entries'][0]['line'], 'AC/DC, Shoot to Thrill')
        run = Run('you-read')
        run.wearable, run.writes, run.device, run.user_text = False, False, 'pc', 'what music do I like?'
        self.app.runs[run.id] = run
        read = self.app.tool('about_you', {'query': 'shoot'}, run)
        self.assertEqual([e['line'] for e in read['entries']], ['AC/DC, Shoot to Thrill'])
        self.assertEqual(self.app.profile_action({'action': 'remove', 'id': entry})['entries'], [])
        with self.assertRaises(ValueError):
            self.app.profile_action({'action': 'explode'})
        self.assertEqual([r['status'] for r in self.app.store.logs() if r['action'].startswith('you page')], ['Likes', 'Likes', 'Likes'])


if __name__ == '__main__':
    unittest.main()
