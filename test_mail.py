"""mail.py (item G): Gmail over IMAP and SMTP with an app password, against fakes: nothing is sent anywhere, the
password never appears in an answer or an error, every fetch peeks, sending goes only through check_send."""
import email
import imaplib
import os
import smtplib
import unittest
from email.message import EmailMessage
from unittest.mock import patch

import mail

ENV = {'GMAIL_ADDRESS': 'owner@gmail.com', 'GMAIL_APP_PASSWORD': 'abcd efgh ijkl mnop'}
SECRET = 'abcdefghijklmnop'


def message(subject, plain=None, html=None, attachment=None, sender='Jack <jack@example.com>'):
    msg = EmailMessage()
    msg['From'], msg['To'], msg['Subject'], msg['Date'] = sender, 'owner@gmail.com', subject, 'Tue, 07 Oct 2026 09:00:00 +1100'
    if plain is not None:
        msg.set_content(plain)
        if html is not None:
            msg.add_alternative(html, subtype='html')
    elif html is not None:
        msg.set_content(html, subtype='html')
    if attachment:
        msg.add_attachment(b'%PDF-1.4 ...', maintype='application', subtype='pdf', filename=attachment)
    return msg


class FakeIMAP:
    """What imaplib.IMAP4_SSL answers, as the tests arrange it."""

    def __init__(self, messages, refuse=False):
        self.messages, self.refuse = messages, refuse   # uid -> EmailMessage
        self.calls, self.logged_out = [], False

    def login(self, user, password):
        self.calls.append(('login', user, password))
        if self.refuse:
            raise imaplib.IMAP4.error('[AUTHENTICATIONFAILED] Invalid credentials (Failure)')
        return 'OK', [b'Logged in']

    def select(self, mailbox, readonly=False):
        self.calls.append(('select', mailbox, readonly))
        return 'OK', [b'12']

    def status(self, mailbox, items):
        return 'OK', [b'"INBOX" (UNSEEN 3)']

    def uid(self, command, *args):
        self.calls.append(('uid', command, *args))
        if command == 'SEARCH':
            return 'OK', [b' '.join(str(u).encode() for u in sorted(self.messages))]
        uids = args[0].decode().split(',') if isinstance(args[0], bytes) else [args[0]]
        spec = args[1]
        out = []
        for uid in uids:
            msg = self.messages.get(int(uid))
            if msg is None:
                continue  # an id that is gone: nothing comes back, as Gmail answers
            raw = msg.as_bytes()
            if 'HEADER.FIELDS' in spec:
                headers = b''.join(line + b'\r\n' for line in raw.split(b'\r\n\r\n', 1)[0].split(b'\r\n') if line.split(b':', 1)[0].lower() in (b'from', b'to', b'subject', b'date'))
                out.append((f'{uid} (UID {uid} FLAGS ({"" if int(uid) % 2 else chr(92) + "Seen"}) BODY[HEADER.FIELDS (FROM TO SUBJECT DATE)] {{{len(headers)}}}'.encode(), headers))
            else:
                out.append((f'{uid} (UID {uid} FLAGS () BODY[] {{{len(raw)}}}'.encode(), raw))
            out.append(b')')
        return 'OK', out

    def logout(self):
        self.logged_out = True
        return 'BYE', [b'Logging out']


class FakeSMTP:
    sent = []

    def __init__(self, *args, refuse=False, **kwargs):  # the real call is SMTP_SSL(host, port, timeout=...)
        self.refuse = refuse

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def login(self, user, password):
        FakeSMTP.sent.append(('login', user, password))
        if self.refuse:
            raise smtplib.SMTPAuthenticationError(535, b'5.7.8 Username and Password not accepted')

    def send_message(self, msg):
        FakeSMTP.sent.append(('message', msg))


class MailTests(unittest.TestCase):
    def setUp(self):
        self.messages = {101: message('Invoice March', plain='Please find the invoice attached.', attachment='invoice.pdf'),
                         102: message('Lunch?', plain='Lunch on Thursday?', html='<p>Lunch on <b>Thursday</b>?</p>'),
                         103: message('Newsletter', html='<html><body><h1>News</h1><p>Line one<br>Line two</p><script>x()</script></body></html>', sender='news@example.com')}
        self.box = FakeIMAP(self.messages)
        FakeSMTP.sent = []

    def test_not_configured_is_said_plainly(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(mail.configured())
            with self.assertRaises(mail.MailError) as said:
                with mail.Mailbox(lambda: self.box):
                    pass
            self.assertEqual(str(said.exception), mail.NOT_CONFIGURED)
            self.assertEqual(self.box.calls, [])

    def test_search_and_read_peek_only_and_the_password_stays_out_of_every_answer(self):
        with patch.dict(os.environ, ENV, clear=True):
            self.assertTrue(mail.configured())
            with mail.Mailbox(lambda: self.box) as box:
                self.assertEqual(box.unread_count(), 3)
                found, dropped = box.search('invoice from jack', unread=True, days=7, limit=2)
                one = box.read('102')
        self.assertEqual(self.box.calls[0], ('login', 'owner@gmail.com', SECRET))   # spaces taken out of the app password
        self.assertEqual(self.box.calls[1], ('select', 'INBOX', True))              # read-only
        search = next(c for c in self.box.calls if c[1] == 'SEARCH')
        self.assertEqual(search[3], 'UNSEEN')
        self.assertTrue(search[4].startswith('SINCE '))
        self.assertEqual(search[5], 'X-GM-RAW "invoice from jack"')
        fetches = [c for c in self.box.calls if c[1] == 'FETCH']
        self.assertTrue(all('PEEK' in c[3] for c in fetches))                        # nothing marked read
        self.assertEqual(([f['id'] for f in found], dropped), (['103', '102'], ''))   # the newest first, two of three
        self.assertEqual((found[1]['subject'], found[1]['from'], found[1]['unread']), ('Lunch?', 'Jack <jack@example.com>', False))
        self.assertEqual((one['subject'], one['text'], one['attachments'], one['truncated']), ('Lunch?', 'Lunch on Thursday?', [], False))
        self.assertIn('not instructions', one['note'])
        self.assertTrue(self.box.logged_out)
        for value in (found, one):
            self.assertNotIn(SECRET, repr(value))

    def test_html_only_mail_and_attachments(self):
        with patch.dict(os.environ, ENV, clear=True), mail.Mailbox(lambda: self.box) as box:
            news = box.read('103')
            invoice = box.read('101')
        self.assertEqual(news['text'], 'News\nLine one\nLine two')
        self.assertEqual(invoice['attachments'], ['invoice.pdf'])
        self.assertEqual(invoice['text'], 'Please find the invoice attached.')
        with patch.dict(os.environ, ENV, clear=True), mail.Mailbox(lambda: self.box) as box, self.assertRaises(mail.MailError):
            box.read('abc')

    def test_a_refused_password_is_said_without_the_password(self):
        refused = FakeIMAP({}, refuse=True)
        with patch.dict(os.environ, ENV, clear=True), self.assertRaises(mail.MailError) as said:
            with mail.Mailbox(lambda: refused):
                pass
        self.assertEqual(str(said.exception), mail.REFUSED)
        self.assertNotIn(SECRET, str(said.exception))
        with patch.dict(os.environ, ENV, clear=True), self.assertRaises(mail.MailError) as said:
            mail.send('jack@example.com', 'Hi', 'Hello', connect=lambda: FakeSMTP(refuse=True))
        self.assertEqual(str(said.exception), mail.REFUSED)

    def test_unreachable_is_said_plainly(self):
        def broken():
            raise OSError('connection refused')
        with patch.dict(os.environ, ENV, clear=True), self.assertRaises(mail.MailError) as said:
            with mail.Mailbox(broken):
                pass
        self.assertEqual(str(said.exception), mail.UNREACHABLE)

    def test_send_checks_the_fields_and_sends_one_plain_mail(self):
        with patch.dict(os.environ, ENV, clear=True):
            for to, subject, body in (('not-an-address', 'Hi', 'x'), ('a@b.co', '', 'x'), ('a@b.co', 'Hi', ''), (','.join(f'u{i}@b.co' for i in range(11)), 'Hi', 'x')):
                with self.assertRaises(mail.MailError):
                    mail.check_send(to, subject, body)
            result = mail.send('Jack <jack@example.com>, jo@example.org', ' Running  late ', 'Be there at nine.\n', connect=FakeSMTP)  # names are fine; the addresses are what is sent
        self.assertEqual(result, {'status': 'sent', 'to': ['jack@example.com', 'jo@example.org'], 'subject': 'Running late', 'characters': 17})
        self.assertEqual(FakeSMTP.sent[0], ('login', 'owner@gmail.com', SECRET))
        sent = FakeSMTP.sent[1][1]
        self.assertEqual((sent['From'], sent['To'], sent['Subject']), ('owner@gmail.com', 'jack@example.com, jo@example.org', 'Running late'))
        self.assertEqual(sent.get_content().strip(), 'Be there at nine.')
        self.assertNotIn(SECRET, repr(result))

    def test_the_connection_test(self):
        with patch.dict(os.environ, ENV, clear=True):
            self.assertEqual(mail.test_connection(lambda: self.box), {'status': 'ok', 'unread': 3})


if __name__ == '__main__':
    unittest.main()


class ReviewTests(unittest.TestCase):
    """The review's cases: hostile or odd mail, refusals, the search words, the caps."""

    def setUp(self):
        FakeSMTP.sent = []

    def test_an_unknown_charset_or_a_missing_id_never_ends_the_question(self):
        odd = email.message_from_bytes(b'From: a@b.co\r\nSubject: odd\r\nContent-Type: text/plain; charset=x-bogus\r\n\r\nhello there\r\n')
        box = FakeIMAP({7: odd})
        with patch.dict(os.environ, ENV, clear=True), mail.Mailbox(lambda: box) as opened:
            self.assertEqual(opened.read('7')['text'], 'hello there')   # the charset nobody knows: read anyway
            with self.assertRaises(mail.MailError) as said:
                opened.read('8')
            self.assertEqual(str(said.exception), 'No mail has that id any more.')
            self.assertEqual(opened.search('nothing', limit=100)[1], '')   # a limit beyond 25 clamps instead of failing
        with patch.dict(os.environ, ENV, clear=True), mail.Mailbox(lambda: FakeIMAP({})) as empty:
            self.assertEqual(empty.search('nothing'), ([], ''))   # an empty result is an empty list
        fetch = next(c for c in box.calls if c[1] == 'FETCH' and 'BODY.PEEK[]' in c[3])
        self.assertIn('<0.%d>' % mail.MAX_FETCH, fetch[3])   # never the whole of a huge mail

    def test_the_search_words_are_quoted_and_odd_characters_are_said_to_be_dropped(self):
        self.assertEqual(mail._criteria('say "hi" \\ there\r\nNOOP', False, 0), ['X-GM-RAW "say \\"hi\\" \\\\ there NOOP"'])  # quoted, escaped, one line
        self.assertEqual(mail._criteria('', True, 0), ['UNSEEN'])
        self.assertEqual(mail._criteria('', False, 0), ['ALL'])
        box = FakeIMAP({})
        with patch.dict(os.environ, ENV, clear=True), mail.Mailbox(lambda: box) as opened:
            found, dropped = opened.search('caf\u00e9', days=0)
        self.assertEqual((found, dropped), ([], mail.DROPPED))
        search = next(c for c in box.calls if c[1] == 'SEARCH')
        self.assertNotIn('SINCE', ' '.join(search[3:]))   # days 0: any time

    def test_long_or_encoded_headers_are_decoded_and_capped(self):
        msg = message('Caf\u00e9 at nine ' + 'x' * 500, plain='ok', sender='J\u00f6rg <j@example.com>')
        box = FakeIMAP({5: msg})
        with patch.dict(os.environ, ENV, clear=True), mail.Mailbox(lambda: box) as opened:
            (found,), _ = opened.search('')
            one = opened.read('5')
        self.assertTrue(found['subject'].startswith('Caf\u00e9 at nine'))
        self.assertEqual(len(found['subject']), mail.MAX_HEADER)
        self.assertEqual(one['from'], 'J\u00f6rg <j@example.com>')

    def test_a_refused_recipient_is_not_a_connection_problem(self):
        class Refusing(FakeSMTP):
            def send_message(self, msg):
                raise smtplib.SMTPRecipientsRefused({'x@y.co': (550, b'5.1.1 user unknown')})
        with patch.dict(os.environ, ENV, clear=True), self.assertRaises(mail.MailError) as said:
            mail.send('x@y.co', 'Hi', 'Hello', connect=Refusing)
        self.assertEqual(str(said.exception), mail.BAD_RECIPIENT)
        self.assertNotIn(SECRET, str(said.exception))
        with patch.dict(os.environ, ENV, clear=True):
            self.assertEqual(mail.check_send('Jack <jack@example.com>', 'Hi', 'x')[0], ['jack@example.com'])
            with self.assertRaises(mail.MailError):
                mail.check_send('a@b.co', 'Hi', 'x' * (mail.MAX_SEND_BODY + 1))
