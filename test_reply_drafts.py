"""Replies that appear while they are written (release 1.0.15, scope item 8): what may be shown early.
Nothing is shown that the claim checks have not passed (reply_drafts.py); the checks here are the real ones.
"""
import unittest

import answer_evidence
import verified_status
from reply_drafts import Drafts, complete_sentences


def real_checks(events=()):
    """The two checks as the Core applies them to a finished answer without tool results."""
    def check(text):
        return answer_evidence.action_guard(verified_status.guard(text, {'health': None, 'connections': {}, 'tests': []}), list(events))
    return check


class Written:
    """Feeds an answer piece by piece and keeps what was shown."""

    def __init__(self, check=None, every=0):
        self.shown, self.now = [], 0.0
        self.drafts = Drafts(check or real_checks(), self.shown.append, every=every, clock=lambda: self.now)

    def write(self, text, size=7, seconds=0.0):
        for at in range(0, len(text), size):
            self.now += seconds
            self.drafts.add(text[at:at + size])
        return self


class SentenceTests(unittest.TestCase):
    def test_only_complete_sentences_count(self):
        self.assertEqual(complete_sentences(''), '')
        self.assertEqual(complete_sentences('A transistor is'), '')
        self.assertEqual(complete_sentences('A transistor is a switch.'), '')  # no blank after it yet: it may go on ("3.14")
        self.assertEqual(complete_sentences('A transistor is a switch. It'), 'A transistor is a switch.')
        self.assertEqual(complete_sentences('He said "stop." Then'), 'He said "stop."')
        self.assertEqual(complete_sentences('First line\nsecond'), 'First line')
        self.assertEqual(complete_sentences('Pi is 3.14 and'), '')
        self.assertEqual(complete_sentences('Really? Yes! Then: one; two, thr'), 'Really? Yes! Then: one;')
        self.assertEqual(complete_sentences('1. First\n2. Sec'), '1. First')  # a list number alone does not end anything
        self.assertEqual(complete_sentences('1. Fir'), '')
        self.assertEqual(complete_sentences('In short:\n\n1. It switches.\n2. It'), 'In short:\n\n1. It switches.')


class DraftTests(unittest.TestCase):
    ANSWER = 'A transistor is a semiconductor switch. It amplifies or switches signals. Billions sit in one chip.'

    def test_an_ordinary_answer_appears_sentence_by_sentence(self):
        shown = Written().write(self.ANSWER).shown
        self.assertEqual(shown, ['A transistor is a semiconductor switch.', 'A transistor is a semiconductor switch. It amplifies or switches signals.'])
        for draft in shown:  # every draft is a beginning of the answer, made of complete sentences
            self.assertTrue(self.ANSWER.startswith(draft))
        self.assertEqual(real_checks()(self.ANSWER), self.ANSWER)  # and the finished answer passes unchanged

    def test_a_claim_the_checks_would_change_is_never_shown(self):
        for claim in ('I have saved the note for you.', 'All the tests passed successfully.', 'The timer has been scheduled for five minutes.'):
            answer = 'Certainly, sir. ' + claim + ' Anything else?'
            self.assertNotEqual(real_checks()(answer), answer, claim)  # the finished answer will be replaced by the checks
            written = Written().write(answer)
            self.assertEqual(written.shown, ['Certainly, sir.'], claim)  # the sentence before it; never the claim
            self.assertTrue(written.drafts.held)
            written.write(' More text. And more. ')
            self.assertEqual(written.shown, ['Certainly, sir.'], 'nothing more is shown once the checks would change the answer')

    def test_a_claim_with_its_receipt_is_still_held_because_the_checks_rewrite_it(self):
        events = [{'event': 'tool.completed', 'data': {'name': 'set_timer', 'result': {'status': 'scheduled', 'title': 'Tea'}, 'checked_at': 1.0}}]
        answer = 'Done. I have scheduled the timer. Enjoy your tea.'
        self.assertNotEqual(real_checks(events)(answer), answer)  # the checks answer with the receipt instead
        self.assertEqual(Written(real_checks(events)).write(answer).shown, ['Done.'])

    def test_not_more_often_than_the_interval_and_nothing_twice(self):
        fast = Written(every=0.2).write(self.ANSWER, size=5, seconds=0.01)   # a fast provider: one draft, then quiet
        self.assertEqual(fast.shown, ['A transistor is a semiconductor switch.'])
        slow = Written(every=0.2).write(self.ANSWER, size=5, seconds=0.1)    # a slow one: each sentence as it completes
        self.assertEqual(len(slow.shown), 2)
        self.assertEqual(len(set(slow.shown)), len(slow.shown))

    def test_a_check_that_fails_shows_nothing(self):
        def broken(text):
            raise RuntimeError('the check could not run')
        written = Written(broken).write(self.ANSWER)
        self.assertEqual(written.shown, [])
        self.assertTrue(written.drafts.held)

    def test_a_thrown_away_attempt_is_taken_off_the_screen(self):
        written = Written().write('Let me look that up. One moment')
        self.assertEqual(written.shown, ['Let me look that up.'])
        written.drafts.clear()                       # the model asked for a tool, or the connection broke
        self.assertEqual(written.shown[-1], '')
        written.write(self.ANSWER)                   # the next attempt starts from nothing
        self.assertEqual(written.shown[-1], 'A transistor is a semiconductor switch. It amplifies or switches signals.')
        clean = Written()
        clean.drafts.clear()                         # nothing was shown: nothing to take away
        self.assertEqual(clean.shown, [])

    def test_odd_pieces_are_ignored(self):
        written = Written()
        for piece in (None, '', 5, b'bytes', ['list']):
            written.drafts.add(piece)
        self.assertEqual((written.shown, written.drafts.text), ([], ''))


if __name__ == '__main__':
    unittest.main()
