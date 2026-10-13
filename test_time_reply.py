"""Release 1.0.18 (docs/RELEASE-1.0.18.md): the Core's own answer to "what time is it" is a sentence, not the raw clock
reading. Before, the reply was "Local time: 2026-10-10T14:36:17.893246+11:00", which Siri read out as it was (the Mac's
request 8 of 2026-10-10). The sentence itself, the words that reach it, and a real local Core answering the question
itself with no AI, from this PC and from a paired phone.
"""
import contextlib
import datetime
import os
import unittest
from unittest.mock import patch

import actions
import providers
import server
from test_device_gateway import DeviceCase

DAYS = '(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)'
MONTHS = '(January|February|March|April|May|June|July|August|September|October|November|December)'
SENTENCE = r"^It's (1[0-2]|[1-9]):[0-5]\d (AM|PM) on " + DAYS + r' ([1-9]|[12]\d|3[01]) ' + MONTHS + r' \d{4}\.$'


@contextlib.contextmanager
def no_ai():
    """Only what the Core answers itself: the provider keys out and every way to the AI refused (review finding L4 of
    2026-10-10: the rest of the environment stays, and a call to the AI fails the test instead of passing unseen)."""
    refuse = AssertionError('No AI needed')
    with patch.dict(os.environ), patch.object(providers, 'chat', side_effect=refuse), \
            patch.object(providers, 'request', side_effect=refuse):
        for key in ('OPENAI_API_KEY', 'DASHSCOPE_API_KEY'):
            os.environ.pop(key, None)
        yield


class SpokenTimeTests(unittest.TestCase):
    def test_the_sentence(self):
        cases = {
            '2026-10-10T14:36:17.893246+11:00': "It's 2:36 PM on Saturday 10 October 2026.",   # the reading Siri read out
            '2026-10-10T00:05:00+11:00': "It's 12:05 AM on Saturday 10 October 2026.",          # just after midnight
            '2026-10-10T12:00:00+11:00': "It's 12:00 PM on Saturday 10 October 2026.",          # noon
            '2026-10-10T11:59:59+11:00': "It's 11:59 AM on Saturday 10 October 2026.",          # seconds are not said
            '2026-12-31T23:59:59+11:00': "It's 11:59 PM on Thursday 31 December 2026.",
            '2026-01-05T09:07:00+11:00': "It's 9:07 AM on Monday 5 January 2026.",               # one-digit hour and day
            '2026-02-28T11:59:00': "It's 11:59 AM on Saturday 28 February 2026.",               # a reading without an offset
            '2026-10-10T13:00:00Z': "It's 1:00 PM on Saturday 10 October 2026.",                # a reading in UTC
        }
        for stamp, said in cases.items():
            self.assertEqual(server.spoken_time(stamp), said, stamp)
            self.assertRegex(said, SENTENCE)

    def test_every_day_and_month_by_its_english_name(self):
        days = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
        monday = datetime.date(2026, 10, 5)
        self.assertEqual(monday.weekday(), 0)
        for offset, name in enumerate(days):  # Monday 5 to Sunday 11 October 2026
            day = monday + datetime.timedelta(days=offset)
            self.assertEqual(server.spoken_time(day.isoformat() + 'T08:00:00+11:00'),
                             f"It's 8:00 AM on {name} {day.day} October 2026.")
        months = ('January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
                  'November', 'December')
        for number, name in enumerate(months, start=1):
            self.assertIn(f' 1 {name} 2026.', server.spoken_time(f'2026-{number:02d}-01T20:00:00+11:00'))

    def test_an_unreadable_reading_is_said_as_it_is(self):
        self.assertEqual(server.spoken_time('garbage'), 'Local time: garbage')
        self.assertEqual(server.spoken_time(None), 'Local time: None')
        self.assertEqual(server.spoken_time(''), 'Local time: ')

    def test_the_reply_and_the_words_that_reach_it(self):
        self.assertEqual(server.App.describe('time_now', {'time': '2026-10-10T14:36:17.893246+11:00'}),
                         "It's 2:36 PM on Saturday 10 October 2026.")
        for said in ('what time is it', 'What time is it?', 'time', 'date', 'what is the date', 'What is the date.'):
            self.assertEqual(actions.local_command(said), ('time_now', {}), said)


class CoreTests(DeviceCase):
    """A real local Core (test_device_gateway.DeviceCase) answering "what time is it" by itself."""

    def setUp(self):
        super().setUp()
        self.app.ollama_shadow.enabled = False  # review finding L3: no request to a real local Ollama

    def answered(self, events, said):
        self.assertNotIn('run.failed', events, said)
        text = events['assistant.completed']['text']
        self.assertRegex(text, SENTENCE, said)
        self.assertNotIn('Local time', text)
        self.assertEqual(events['tool.completed']['name'], 'time_now')

    def test_from_this_pc(self):
        for said in ('what time is it', 'date'):
            with no_ai():
                status, started = self.owner('/api/chat', {'text': said, 'conversation': 'time-test'})
                self.assertEqual(status, 200, started)
                events = self.pc_events(started['run_id'])
            self.answered(events, said)

    def test_from_a_paired_phone(self):  # the route the iPhone app and Siri use (review finding L5)
        paired = self.pair()
        with no_ai():
            status, started = self.device('start', {'text': 'What time is it?',
                                                    'conversation': 'device-' + paired['device_id'] + '-chat'},
                                          paired['credential'])
            self.assertEqual(status, 200, started)
            events = self.finished(paired['credential'], started['run_id'])
        self.answered(events, 'What time is it?')

    def pc_events(self, run_id):
        seen, collected = -1, {}
        for _ in range(60):
            status, events = self.owner('/api/runs/' + run_id + '/events?after=' + str(seen))
            self.assertEqual(status, 200, events)
            for event in events['events']:
                collected[event['event']] = event['data']
                seen = max(seen, event['id'])
            if events['done']:
                return collected
        self.fail('The question did not finish.')


if __name__ == '__main__':
    unittest.main()
