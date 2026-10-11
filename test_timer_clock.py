"""Release 1.0.18 (docs/CORE-FIXES-20261010.md, the owner's word on the Mac's item 4): a timer's result carries the
alert's time on this PC's clock beside the bare timestamp, and the reply names it, so JARVIS never has to turn the
number into a time himself (from the number alone he said "07:19" for an alert due at 10:29). The expected texts are
written out in full, in fixed time zones where the zone matters (review finding 6)."""
import datetime
import os
import tempfile
import time
import unittest
from unittest.mock import patch

import answer_evidence
from server import App

PLUS_10 = datetime.timezone(datetime.timedelta(hours=10))
PLUS_11 = datetime.timezone(datetime.timedelta(hours=11))


def moment(tz, *parts):
    return datetime.datetime(*parts, tzinfo=tz).timestamp()


def at(*parts):
    """A moment given on this PC's own clock."""
    return datetime.datetime(*parts).astimezone().timestamp()


class ClockTests(unittest.TestCase):
    def test_today_is_the_time_alone_in_the_zone_it_is_read_in(self):
        due, now = moment(PLUS_11, 2026, 10, 10, 10, 29), moment(PLUS_11, 2026, 10, 10, 10, 27)
        self.assertEqual(answer_evidence.clock(due, now, PLUS_11), '10:29')
        self.assertEqual(answer_evidence.clock(due, now, PLUS_10), '09:29')   # the same moment, an hour earlier there
        self.assertEqual(answer_evidence.stamp(due, PLUS_11), '2026-10-10T10:29:00+11:00')
        self.assertEqual(answer_evidence.stamp(due, PLUS_10), '2026-10-10T09:29:00+10:00')

    def test_past_midnight_names_the_day(self):
        now = moment(PLUS_11, 2026, 10, 10, 23, 59)
        self.assertEqual(answer_evidence.clock(now + 120, now, PLUS_11), '00:01 on Sunday 11 October')

    def test_another_year_says_the_year(self):
        self.assertEqual(answer_evidence.clock(moment(PLUS_11, 2027, 1, 5, 9, 30), moment(PLUS_11, 2026, 10, 10, 10, 27), PLUS_11),
                         '09:30 on Tuesday 5 January 2027')

    def test_without_a_zone_the_pcs_own_clock_is_used(self):
        self.assertEqual(answer_evidence.clock(at(2026, 10, 10, 10, 29), at(2026, 10, 10, 10, 27)), '10:29')


class DurationTests(unittest.TestCase):
    def test_lengths_in_words(self):
        for seconds, words in ((1, '1 second'), (2, '2 seconds'), (59.6, '1 minute'), (90, '1 minute 30 seconds'), (120, '2 minutes'),
                               (3600, '1 hour'), (3725, '1 hour 2 minutes'), (3630, '1 hour 30 seconds'), (300 * 3600, '12 days 12 hours'),
                               (31536000, '365 days'), (0.4, '0 seconds')):
            self.assertEqual(answer_evidence.duration(seconds), words, seconds)


class ReceiptTests(unittest.TestCase):
    def test_a_timers_receipt_says_when_it_goes_off(self):
        """Review finding 2: a timer approved later, on the PC or from the phone, says its time in the receipt."""
        with patch('answer_evidence.time.time', return_value=at(2026, 10, 10, 10, 27)):
            self.assertEqual(answer_evidence.receipt('set_timer', {'status': 'scheduled', 'due': at(2026, 10, 10, 10, 29)}), 'scheduled; goes off at 10:29')
            self.assertEqual(answer_evidence.receipt('manage_timer', {'status': 'adjusted', 'due': at(2026, 10, 10, 11, 0)}), 'adjusted; goes off at 11:00')
        self.assertEqual(answer_evidence.receipt('set_timer', {'status': 'scheduled', 'title': 'Tea'}), 'scheduled')    # no time, no clause
        self.assertEqual(answer_evidence.receipt('manage_timer', {'id': 'x', 'status': 'cancelled'}), 'cancelled')
        self.assertEqual(answer_evidence.receipt('save_item', {'status': 'saved', 'due': 1.0}), 'saved')                # other tools as before


class TimerResultTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        environment = patch.dict(os.environ, {}, clear=True)
        environment.start()
        self.addCleanup(environment.stop)
        self.app = App(folder.name)

    def test_set_timer_gives_the_local_clock_time_beside_the_timestamp(self):
        result = self.app.tool('set_timer', {'title': 'Tea', 'seconds': 120})
        self.assertIsInstance(result['due'], float)   # the timestamp stays, for everything that reads it
        shown = datetime.datetime.fromisoformat(result['due_local'])
        self.assertAlmostEqual(shown.timestamp(), result['due'], delta=1)
        self.assertEqual(shown.utcoffset(), datetime.datetime.fromtimestamp(result['due']).astimezone().utcoffset())   # this PC's zone

    def test_the_reply_names_the_length_and_the_time(self):
        result = {'id': 'x', 'title': 'Tea', 'due': at(2026, 10, 10, 10, 29), 'fired': 0, 'status': 'scheduled', 'seconds': 120}
        with patch('answer_evidence.time.time', return_value=at(2026, 10, 10, 10, 27)):
            self.assertEqual(App.describe('set_timer', result), 'Timer started for 2 minutes. It goes off at 10:29. Keep JARVIS running for the alert.')
            self.assertEqual(App.describe('set_timer', {**result, 'seconds': 1}),
                             'Timer started for 1 second. It goes off at 10:29. Keep JARVIS running for the alert.')

    def test_a_listing_says_the_time_now_and_what_is_left(self):
        """Review finding 1: "how long is left?" is read from the listing, not worked out."""
        made = self.app.tool('set_timer', {'title': 'Tea', 'seconds': 300})
        before = time.time()
        listed = self.app.tool('manage_timer', {'action': 'list'})
        self.assertAlmostEqual(datetime.datetime.fromisoformat(listed['now']).timestamp(), before, delta=2)
        [timer] = listed['timers']
        self.assertEqual(timer['id'], made['id'])
        self.assertAlmostEqual(datetime.datetime.fromisoformat(timer['due_local']).timestamp(), made['due'], delta=1)
        self.assertTrue(295 <= timer['seconds_left'] <= 300, timer['seconds_left'])

    def test_adjusting_gives_the_new_time_and_cancelling_none(self):
        made = self.app.tool('set_timer', {'title': 'Tea', 'seconds': 300})
        adjusted = self.app.tool('manage_timer', {'action': 'adjust', 'timer_id': made['id'], 'seconds': 600})
        self.assertAlmostEqual(datetime.datetime.fromisoformat(adjusted['due_local']).timestamp(), adjusted['due'], delta=1)
        cancelled = self.app.tool('manage_timer', {'action': 'cancel', 'timer_id': made['id']})
        self.assertEqual(cancelled, {'id': made['id'], 'status': 'cancelled'})


if __name__ == '__main__':
    unittest.main()
