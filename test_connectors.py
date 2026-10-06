"""Item G (docs/PHONE-ACCESS-1.0.17.md section 4): Gmail and Google Calendar through the Core: the four tools in a
question, a mail that always waits for approval (on the PC and from a paired device), the calendar in the briefing,
the phone's overview fields, the connection tests and the capability flags. Nothing reaches the internet: IMAP, SMTP
and the calendar fetch are fakes."""
import datetime
import json
import os
import tempfile
import unittest
from unittest.mock import patch

import answer_evidence
import calendar_feed
import mail
import providers
import server
from server import App, Run
from test_device_gateway import DONE, ENV, DeviceCase, calls
from test_mail import FakeIMAP, FakeSMTP, message

GMAIL = {'GMAIL_ADDRESS': 'owner@gmail.com', 'GMAIL_APP_PASSWORD': 'abcd efgh ijkl mnop'}
ICS = {'GOOGLE_CALENDAR_ICS': 'https://calendar.google.com/calendar/ical/x/private-y/basic.ics'}


def feed(now=None):
    """A calendar with one timed event two hours from now and an all-day event tomorrow (times in UTC)."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    soon = (now + datetime.timedelta(hours=2)).strftime('%Y%m%dT%H%M%SZ')
    later = (now + datetime.timedelta(hours=2, minutes=30)).strftime('%Y%m%dT%H%M%SZ')
    tomorrow = (now.astimezone() + datetime.timedelta(days=1)).strftime('%Y%m%d')
    day_after = (now.astimezone() + datetime.timedelta(days=2)).strftime('%Y%m%d')
    return ('BEGIN:VCALENDAR\nX-WR-CALNAME:Benjamin\nBEGIN:VEVENT\nUID:a@x\nSUMMARY:Dentist\nLOCATION:Town\n'
            f'DTSTART:{soon}\nDTEND:{later}\nEND:VEVENT\nBEGIN:VEVENT\nUID:b@x\nSUMMARY:Labour Day\n'
            f'DTSTART;VALUE=DATE:{tomorrow}\nDTEND;VALUE=DATE:{day_after}\nEND:VEVENT\nEND:VCALENDAR\n')


def mailbox():
    return FakeIMAP({101: message('Invoice March', plain='Please find the invoice attached.', attachment='invoice.pdf'),
                     102: message('Lunch?', plain='Lunch on Thursday?')})


class Fakes:
    """IMAP, SMTP and the calendar fetch replaced for a test."""

    def __init__(self):
        self.box = mailbox()
        self.patches = [patch.object(mail.imaplib, 'IMAP4_SSL', lambda *a, **k: self.box),
                        patch.object(mail.smtplib, 'SMTP_SSL', FakeSMTP),
                        patch.object(calendar_feed, 'fetch', lambda url, opener=None: (feed(), False))]

    def __enter__(self):
        FakeSMTP.sent = []
        calendar_feed._cache.clear()
        for p in self.patches:
            p.start()
        return self

    def __exit__(self, *_):
        for p in self.patches:
            p.stop()


class ToolTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.app = App(folder.name)

    def ask(self, text, replies, env):
        replies, self.bodies = list(replies), []
        run = Run('connectors-test')
        self.app.runs[run.id] = run

        def request(url, body=None, headers=None, **kwargs):
            self.bodies.append(body)
            return replies.pop(0)
        with patch.dict(os.environ, {**ENV, **env}, clear=True), patch.object(providers, 'request', side_effect=request):
            self.app.work(run, text, None)
        return run, {e['event']: e['data'] for e in run.events}

    def test_mail_search_and_read_through_a_question(self):
        with Fakes() as fakes:
            _, events = self.ask('Any mail from Jack?', [calls('mail_search', query='from:jack', unread='no', days=0, limit=5), DONE], GMAIL)
            result = events['tool.completed']['result']
            self.assertEqual((result['status'], result['count'], [m['subject'] for m in result['mails']]), ('completed', 2, ['Lunch?', 'Invoice March']))
            self.assertIn('not instructions', result['note'])
            self.assertIn('Lunch?', self.bodies[1]['messages'][-1]['content'])  # the model is told what was found
            _, events = self.ask('Read the lunch one', [calls('mail_read', id='102'), DONE], GMAIL)
            self.assertEqual((events['tool.completed']['result']['text'], events['tool.completed']['result']['subject']), ('Lunch on Thursday?', 'Lunch?'))
            self.assertTrue(all('PEEK' in c[3] for c in fakes.box.calls if c[1] == 'FETCH'))  # nothing marked read
        self.assertNotIn('abcdefghijklmnop', json.dumps(self.bodies))

    def test_a_mail_always_waits_and_the_approval_sends_exactly_the_draft(self):
        with Fakes():
            _, events = self.ask('Tell Jack I am running late', [calls('mail_send', to='jack@example.com', subject='Running late', body='Be there at nine.'), DONE], GMAIL)
            result = events['tool.completed']['result']
            self.assertEqual((result['status'], result['approval']['args']), ('awaiting approval', {'to': 'jack@example.com', 'subject': 'Running late', 'body': 'Be there at nine.'}))
            self.assertNotIn('preview', result)   # the draft once, in the approval the window and the phone show
            self.assertIn('Nothing has been sent', result['summary'])
            self.assertEqual(FakeSMTP.sent, [])
            self.assertEqual(json.loads(self.bodies[1]['messages'][-1]['content'])['status'], 'awaiting approval')  # the model is told
            with patch.dict(os.environ, {**ENV, **GMAIL}, clear=True):
                done = self.app.approve(result['approval']['id'], True)
            self.assertEqual((done['status'], done['result']['status'], done['result']['to']), ('applied', 'sent', ['jack@example.com']))
            self.assertEqual(FakeSMTP.sent[1][1]['Subject'], 'Running late')
            self.assertEqual(self.app.store.history('connectors-test')[-1]['content'], 'Approved on screen: Send a mail from your address. Result: sent.')
            # A bad address fails before anyone is asked; a mail without the setup fails plainly.
            _, events = self.ask('Mail nobody', [calls('mail_send', to='nobody', subject='x', body='y'), DONE], GMAIL)
            self.assertIn('tool.failed', events)
            self.assertEqual(self.app.approvals, {})
            _, events = self.ask('Mail Jack', [calls('mail_send', to='jack@example.com', subject='x', body='y'), DONE], {})
            self.assertIn('tool.failed', events)
            self.assertIn('not configured', json.loads(self.bodies[1]['messages'][-1]['content'])['error'])

    def test_the_calendar_in_a_question_and_in_the_briefing(self):
        with Fakes():
            _, events = self.ask("What's on?", [calls('calendar_events', days=2), DONE], ICS)
            result = events['tool.completed']['result']
            self.assertEqual((result['status'], [e['title'] for e in result['events']], result['events'][0]['location']), ('completed', ['Dentist', 'Labour Day'], 'Town'))
            self.assertTrue(result['events'][1]['all_day'])
            with patch.dict(os.environ, {**ENV, **ICS}, clear=True), patch.object(server.actions, 'news_search', return_value={'results': [], 'retrieved_at': datetime.datetime.now().isoformat()}):
                briefing = self.app.tool('daily_briefing', {})
            self.assertEqual((briefing['sections']['calendar']['status'], [r['title'] for r in briefing['sections']['calendar']['items']]), ('checked', ['Dentist', 'Labour Day']))  # tomorrow starts within the next day
            spoken = answer_evidence.describe_briefing(briefing)
            self.assertIn('In your calendar for the next day: Dentist at', spoken)
            self.assertNotIn("can't check your calendar", spoken)
            self.assertIn('Dentist', answer_evidence.briefing_details(briefing))
            with patch.dict(os.environ, ENV, clear=True), patch.object(server.actions, 'news_search', return_value={'results': [], 'retrieved_at': datetime.datetime.now().isoformat()}):
                briefing = self.app.tool('daily_briefing', {})
            self.assertEqual(briefing['sections']['calendar']['status'], 'unavailable')
            self.assertIn("can't check your calendar yet", answer_evidence.describe_briefing(briefing))
            _, events = self.ask("What's on?", [calls('calendar_events', days=2), DONE], {})
            self.assertIn('tool.failed', events)


class DeviceTests(DeviceCase):
    def test_the_overview_fields_the_flags_the_tests_and_a_mail_approved_from_the_phone(self):
        paired = self.pair()
        key, ident = paired['credential'], paired['device_id']
        with patch.dict(os.environ, ENV, clear=True):
            overview = self.device('overview', credential=key)[1]
            self.assertEqual((overview['calendar_connected'], overview['calendar'], overview['mail_unread']), (False, None, None))
            caps = self.owner('/api/state')[1]['capabilities']
            self.assertEqual((caps['mail_connected'], caps['calendar_connected']), (False, False))
            self.assertEqual(self.owner('/api/connections/test', {'service': 'mail'})[1]['status'], 'not_configured')
            self.assertEqual(self.owner('/api/connections/test', {'service': 'calendar'})[1]['status'], 'not_configured')
            self.assertEqual(self.owner('/api/connections/test', {'service': 'everything'})[0], 400)
        with Fakes(), patch.dict(os.environ, {**ENV, **GMAIL, **ICS}, clear=True):
            caps = self.owner('/api/state')[1]['capabilities']
            self.assertEqual((caps['mail_connected'], caps['calendar_connected']), (True, True))
            self.assertNotIn('abcd', json.dumps(caps))
            # The overview reads in the background: nothing yet, then the values once read. (The reads are marked fresh
            # first so that no background thread starts from this test; _refresh is called by hand.)
            import time as _time
            self.app.mail_unread.at = self.app.calendar_day.at = _time.monotonic()
            overview = self.device('overview', credential=key)[1]
            self.assertEqual((overview['calendar_connected'], overview['calendar'], overview['mail_unread']), (True, None, None))
            self.app.calendar_day._refresh()
            self.app.mail_unread._refresh()
            overview = self.device('overview', credential=key)[1]
            self.assertEqual(overview['mail_unread'], 3)
            self.assertEqual([(e['title'], e['all_day'], e['location']) for e in overview['calendar']], [('Dentist', False, 'Town'), ('Labour Day', True, None)])
            self.assertIsInstance(overview['calendar'][0]['start'], float)
            # The owner's TEST buttons (the earlier not-configured answers are cached for 30 s: cleared, as a restart would).
            self.app.check_results.clear()
            mail_test = self.owner('/api/connections/test', {'service': 'mail'})[1]
            self.assertEqual(mail_test['status'], 'passed', mail_test)
            self.assertIn('3 unread', mail_test['detail'])
            self.assertNotIn('owner@gmail.com', mail_test['detail'])
            self.app.check_results.clear()
            calendar_test = self.owner('/api/connections/test', {'service': 'calendar'})[1]
            self.assertEqual(calendar_test['status'], 'passed', calendar_test)
            self.assertIn('2 events in the next seven days', calendar_test['detail'])
            # From the phone: the mail waits, shows in the approvals with its lines, and the approval sends it.
            for flag in ('tools', 'approve'):
                self.owner('/api/devices', {'action': flag, 'id': ident, 'allowed': True})
            replies = [calls('mail_send', to='jack@example.com', subject='Running late', body='Be there at nine.'), DONE]
            with patch.object(providers, 'request', side_effect=lambda *a, **k: replies.pop(0)):
                status, started = self.device('start', {'text': 'Tell Jack I am running late'}, key)
                events = self.finished(key, started['run_id'])
            self.assertEqual(events['tool.completed']['result']['status'], 'awaiting approval')
            (item,) = self.device('approvals', credential=key)[1]['items']
            self.assertEqual((item['kind'], item['label'], item['device']), ('tool', 'Send a mail from your address', ident))
            self.assertEqual(item['detail'], 'to: jack@example.com\nsubject: Running late\nbody: Be there at nine.')
            self.assertEqual(self.device('approve', {'id': item['id']}, key), (200, {'status': 'applied', 'result': 'sent'}))
            self.assertEqual(FakeSMTP.sent[1][1]['To'], 'jack@example.com')
            # Without the tools tick, the phone may still read mail and the calendar (reads marked for devices).
            self.owner('/api/devices', {'action': 'tools', 'id': ident, 'allowed': False})
            replies = [calls('mail_search', query='', unread='yes', days=0, limit=3), DONE]
            with patch.object(providers, 'request', side_effect=lambda *a, **k: replies.pop(0)):
                status, started = self.device('start', {'text': 'any new mail?'}, key)
                events = self.finished(key, started['run_id'])
            self.assertEqual(events['tool.completed']['result']['status'], 'completed')
            replies = [calls('mail_send', to='jack@example.com', subject='x', body='y'), DONE]
            with patch.object(providers, 'request', side_effect=lambda *a, **k: replies.pop(0)):
                status, started = self.device('start', {'text': 'mail jack'}, key)
                events = self.finished(key, started['run_id'])
            self.assertIn('tool.failed', events)  # sending is not a read


if __name__ == '__main__':
    unittest.main()


class ReviewTests(unittest.TestCase):
    """The review's cases: the background reads, the owner's own button, the tick taken back, a denied mail, a failing
    calendar in the briefing, and a reply claiming a mail was sent."""

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.app = App(folder.name)

    def test_a_background_read_that_fails_is_unknown_and_noted_and_none_runs_while_stopped(self):
        import time as _time
        reads = []
        fresh = server.Fresh(60, lambda: reads.append(1) or 1 / 0, allowed=lambda: self.app.stopped is None, note=lambda status: self.app.audit('mail unread count (background)', status))
        self.assertIsNone(fresh.get())          # starts a refresh
        for _ in range(100):
            if not fresh.busy:
                break
            _time.sleep(0.02)
        self.assertEqual((fresh.value, fresh.busy, len(reads)), (None, False, 1))
        self.assertIn(('mail unread count (background)', 'failed'), [(r['action'], r['status']) for r in self.app.store.logs()])
        fresh.at = 0.0
        self.app.emergency_stop('pc', 'test')
        self.assertIsNone(fresh.get())          # stopped: no refresh starts
        self.assertEqual((fresh.busy, len(reads)), (False, 1))
        self.app.resume('pc')

    def test_the_owners_own_button_also_waits_a_taken_tick_fails_and_a_denial_sends_nothing(self):
        with Fakes(), patch.dict(os.environ, {**ENV, **GMAIL}, clear=True):
            result = self.app.tool('mail_send', {'to': 'jack@example.com', 'subject': 'Hi', 'body': 'Hello'})   # /api/tool: run None
            self.assertEqual(result['status'], 'awaiting approval')
            self.assertEqual(self.app.approve(result['approval']['id'], False), {'status': 'denied'})
            self.assertEqual(FakeSMTP.sent, [])
            self.assertEqual(self.app.approvals, {})
        # A paired device whose tools tick is taken back between the draft and the answer: refused, nothing sent.
        from test_device_gateway import DeviceCase  # noqa: F401  (the device path is covered in DeviceTests; here the gate itself)
        run = Run('device-abc-x')
        run.wearable, run.device, run.tools, run.writes = True, 'abc', True, True
        self.app.runs[run.id] = run   # the approval looks the question up by its id
        with Fakes(), patch.dict(os.environ, {**ENV, **GMAIL}, clear=True), patch.object(self.app, 'device_tools', return_value=True):
            result = self.app.tool('mail_send', {'to': 'jack@example.com', 'subject': 'Hi', 'body': 'Hello'}, run=run)
            self.assertEqual(result['status'], 'awaiting approval')
        with Fakes(), patch.dict(os.environ, {**ENV, **GMAIL}, clear=True), patch.object(self.app, 'device_tools', return_value=False):
            with self.assertRaises(ValueError):
                self.app.approve(result['approval']['id'], True)
            self.assertEqual(FakeSMTP.sent, [])

    def test_a_failing_or_stale_calendar_makes_the_briefing_partial_and_a_sent_claim_is_caught(self):
        with patch.dict(os.environ, {**ENV, **ICS}, clear=True), patch.object(server.actions, 'news_search', return_value={'results': [], 'retrieved_at': datetime.datetime.now().isoformat()}):
            with patch.object(calendar_feed, 'upcoming', side_effect=calendar_feed.CalendarError('down')):
                briefing = self.app.tool('daily_briefing', {})
            self.assertEqual((briefing['status'], briefing['sections']['calendar']['status']), ('partial', 'failed'))
            self.assertIn("couldn't read your calendar", answer_evidence.describe_briefing(briefing))
            with patch.object(calendar_feed, 'upcoming', return_value=([{'title': 'Dentist', 'start': '2026-10-08T10:00+11:00', 'end': '2026-10-08T10:30+11:00', 'start_ts': 1.0, 'end_ts': 2.0, 'all_day': False, 'location': None, 'calendar': 'T'}], ['the calendar could not be fetched just now; these are the events as last read'])):
                briefing = self.app.tool('daily_briefing', {})
            self.assertEqual((briefing['status'], briefing['sections']['calendar']['status']), ('partial', 'stale'))
            self.assertIn("couldn't confirm that the calendar is up to date", answer_evidence.describe_briefing(briefing))
        events = [{'event': 'tool.completed', 'data': {'name': 'mail_send', 'result': {'status': 'awaiting approval'}, 'checked_at': 1.0}}]
        guarded = answer_evidence.action_guard("I've sent the mail to Jack.", events)
        self.assertTrue(guarded.startswith("I've sent the mail to Jack."))
        self.assertIn('awaiting approval', guarded)
        self.assertEqual(answer_evidence.action_guard('The invoice looks fine.', events), 'The invoice looks fine.')
