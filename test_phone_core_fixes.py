"""Release 1.0.17, the three Core items from the phone checks (docs/PHONE-CORE-FIXES-20261007.md): "remember that"
saves the line before it; the action guard puts the truth under a reply instead of replacing it; a device's question
appears as it is written (that one is in test_reply_stream.py). Since 1.0.18 (the owner's word, docs/CORE-FIXES-20261010.md)
"remember that" saves the owner's own last line, and JARVIS's last answer only for "remember what you said"."""
import os
import tempfile
import unittest
from unittest.mock import patch

import answer_evidence
import memory
from server import App, Run
from store import Store


class RememberThatTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.store = Store(folder.name)

    def bodies(self):
        return [r['body'] for r in self.store.items('memory')]

    def test_remember_that_saves_the_line_before_it(self):
        self.store.message('c1', 'user', 'My car is a blue Tesla.')
        self.store.message('c1', 'user', 'Remember that.')
        self.assertEqual(memory.command(self.store, 'Remember that.', 'c1'), 'Remembered: My car is a blue Tesla.')
        self.assertEqual(self.bodies(), ['My car is a blue Tesla.'])

    def test_after_an_answer_the_owners_own_line_is_remembered(self):
        """1.0.18, the phone's check of 2026-10-10: after the owner's line and JARVIS's answer, "remember that" saved the
        answer; the owner means their own line."""
        self.store.message('c1', 'user', 'I did 30 push-ups this morning.')
        self.store.message('c1', 'assistant', 'Already logged, Mr. Teague. Nice work.')
        for text in ('Remember that', 'remember this', 'Remember it.', 'remember what I said', 'Remember what I just said!', 'remember'):
            with self.subTest(text=text):
                self.assertEqual(memory.command(self.store, text, 'c1'), 'Remembered: I did 30 push-ups this morning.')
        self.assertEqual(self.bodies(), ['I did 30 push-ups this morning.'])

    def test_remember_what_you_said_keeps_jarvis_words_as_his(self):
        self.store.message('c1', 'user', 'When is the meeting?')
        self.store.message('c1', 'assistant', 'Your meeting is at 3 pm on Friday.')
        self.store.message('c1', 'user', 'remember what you said')
        self.assertEqual(memory.command(self.store, 'remember what you said', 'c1'), 'Remembered: JARVIS said: Your meeting is at 3 pm on Friday.')
        self.assertEqual(memory.command(self.store, 'Remember what you just said.', 'c1'), 'Remembered: JARVIS said: Your meeting is at 3 pm on Friday.')
        self.assertEqual(self.bodies(), ['JARVIS said: Your meeting is at 3 pm on Friday.'])

    def test_whose_line_each_form_means(self):
        for text in ('remember that', 'Remember this.', 'remember it for me', 'Remember', 'please remember that', 'remember what I said', 'memorise that'):
            self.assertEqual(memory.pointer_role(text), 'user', text)
        for text in ('remember what you said', 'Remember what you just said!', 'remember  what  you  said, please'):
            self.assertTrue(memory.is_pointer(text), text)
            self.assertEqual(memory.pointer_role(text), 'assistant', text)

    def test_with_only_jarvis_lines_before_it_nothing_is_saved(self):
        self.store.message('c7', 'assistant', 'Good morning. Your first meeting is at 9.')
        self.store.message('c7', 'user', 'remember that')
        self.assertEqual(memory.command(self.store, 'remember that', 'c7'), memory.NOTHING_BEFORE)
        self.assertEqual(self.bodies(), [])

    def test_remember_what_you_said_reaches_back_past_the_owners_thanks(self):
        """Review 2026-10-10, finding 9: the answer is found past a later line of the owner's (the old rule saved "Thanks.")."""
        self.store.message('c8', 'user', 'What is the gate code?')
        self.store.message('c8', 'assistant', 'The gate code is 4421.')
        self.store.message('c8', 'user', 'Thanks.')
        self.store.message('c8', 'user', 'remember what you said')
        self.assertEqual(memory.command(self.store, 'remember what you said', 'c8'), 'Remembered: JARVIS said: The gate code is 4421.')

    def test_the_cores_own_lines_are_never_what_jarvis_said(self):
        """Review finding 3: a refusal, "nothing before this" and an approval from the phone are not answers to remember."""
        for line in (memory.NOTHING_BEFORE, 'Credentials cannot be saved as memory.', 'Approved from My phone. Remembered: The spare key is under the pot.',
                     'Approved from My phone: Set a timer. Result: scheduled; goes off at 10:29.', 'I’ll call you Ben. Your preferred name is saved.',
                     'I couldn’t identify one saved memory to replace. Use Edit in the Memory Bank.'):
            with self.subTest(line=line):
                self.store.message('c9', 'assistant', line)
                self.assertEqual(memory.previous_line(self.store, 'c9', 'remember what you said'), None)

    def test_whose_line_comes_from_the_same_match_as_the_pointer(self):
        """Review findings 4 and 5: no separator before "please", a question mark, "…", "for me, please"."""
        for text in ('remember what you saidplease', 'remember what you said?', 'Remember what you just said, for me, please.'):
            self.assertTrue(memory.is_pointer(text), text)
            self.assertEqual(memory.pointer_role(text), 'assistant', text)
        for text in ('Remember that?', 'Remember that…', 'Remember that for me, please', 'remember it, please, for me!'):
            self.assertTrue(memory.is_pointer(text), text)
            self.assertEqual(memory.governed_by(text), 'save_item', text)
            self.assertEqual(memory.pointer_role(text), 'user', text)

    def test_the_owners_line_is_found_past_approval_receipts(self):
        """Review finding 6: twenty lines are looked at, so a run of receipts does not hide the owner's line."""
        self.store.message('c10', 'user', 'The spare key is under the pot.')
        for n in range(10):
            self.store.message('c10', 'assistant', f'Approved on screen: Set a timer. Result: scheduled; goes off at 10:{n:02d}.')
        self.store.message('c10', 'user', 'remember that')
        self.assertEqual(memory.command(self.store, 'remember that', 'c10'), 'Remembered: The spare key is under the pot.')

    def test_the_forms_that_point_back_and_the_ones_that_do_not(self):
        for text in ('remember that', 'Remember that.', 'remember this', 'remember it', 'Remember what I just said!',
                     'remember what you said', 'memorise that', 'Memorize it.', 'Remember', 'please remember that'):
            self.assertEqual(memory.governed_by(text), 'save_item', text)
            self.assertIsNotNone(memory._POINTER.fullmatch(text), text)
        for text in ('remember that I prefer tea', 'remember my name is Jo', 'what do you remember', 'that', 'remember to buy milk',
                     'remember that the meeting moved'):
            self.assertIsNone(memory._POINTER.fullmatch(text), text)
        for text in ('Remember that, please', 'remember it for me', 'Remember  that', 'Remember that.\n'):
            self.assertTrue(memory.is_pointer(text), text)                               # the spoken forms (review finding 4)
        self.assertEqual(memory.governed_by('remember that I prefer tea'), 'save_item')   # as before: its own words
        self.assertIsNone(memory.governed_by('remember to buy milk'))                     # not a pointer: actions.local_command saves the words, as before

    def test_nothing_before_it_is_said_plainly_and_nothing_is_saved(self):
        self.store.message('c2', 'user', 'remember that')
        self.assertEqual(memory.command(self.store, 'remember that', 'c2'), memory.NOTHING_BEFORE)
        self.assertEqual(memory.command(self.store, 'remember that', None), memory.NOTHING_BEFORE)
        self.assertEqual(self.bodies(), [])

    def test_the_confirmations_of_other_commands_are_never_the_line(self):
        """Review finding 5: after "remember that I prefer tea" and its answer, the pointer must not save the answer."""
        self.store.message('c5', 'user', 'The gate code is 4421.')
        self.store.message('c5', 'user', 'remember that I prefer tea')
        self.store.message('c5', 'assistant', memory.command(self.store, 'remember that I prefer tea'))
        self.store.message('c5', 'user', 'remember that')
        self.assertEqual(memory.command(self.store, 'remember that', 'c5'), 'Remembered: The gate code is 4421.')

    def test_a_line_given_with_the_command_wins_over_the_conversation(self):
        self.store.message('c6', 'user', 'Later line.')
        self.assertEqual(memory.command(self.store, 'remember that', 'c6', line=['user', 'The earlier line.']), 'Remembered: The earlier line.')

    def test_a_repeated_pointer_and_its_confirmation_are_skipped(self):
        self.store.message('c3', 'user', 'The gate code is 4421.')
        self.store.message('c3', 'user', 'remember that')
        self.store.message('c3', 'assistant', 'Remembered: The gate code is 4421.')
        self.store.message('c3', 'user', 'remember that')
        self.assertEqual(memory.command(self.store, 'remember that', 'c3'), 'Remembered: The gate code is 4421.')
        self.assertEqual(self.bodies(), ['The gate code is 4421.'])   # the same fact once: the store merges equal keys

    def test_the_line_is_collapsed_and_cut_at_500_characters(self):
        self.store.message('c4', 'user', ' word \n' * 300)
        self.store.message('c4', 'user', 'remember that')
        answer = memory.command(self.store, 'remember that', 'c4')
        self.assertEqual(len(answer) - len('Remembered: '), 500)
        self.assertNotIn('\n', answer)

    def test_the_other_commands_still_work_without_a_conversation(self):
        self.assertEqual(memory.command(self.store, 'remember that I prefer tea'), 'Saved that preference. You can say “forget memory: Preference: I prefer tea” any time.')
        self.assertIsNone(memory.command(self.store, 'What is my name?'))


class RememberThatThroughTheCoreTests(unittest.TestCase):
    def test_the_core_passes_the_conversation_and_answers_without_the_model(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        with patch.dict(os.environ, {}, clear=True):
            app = App(folder.name)
            run = Run('phone-1')
            run.wearable, run.writes, run.device, run.user_text = False, False, 'pc', 'Remember that.'
            app.store.message('phone-1', 'user', 'The spare key is under the pot.')
            app.store.message('phone-1', 'user', 'Remember that.')
            self.assertEqual(app.memory_command(run, 'Remember that.'), 'Remembered: The spare key is under the pot.')
            self.assertEqual([r['body'] for r in app.store.items('memory')], ['The spare key is under the pot.'])

    def test_ask_first_carries_the_line_and_saves_it_on_approval(self):
        """Review finding 1: approved later, the command must save the line as it stood when it was said."""
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        with patch.dict(os.environ, {}, clear=True):
            app = App(folder.name)
            app.set_permission('save_item', 'ask')
            run = Run('phone-2')
            run.wearable, run.writes, run.device, run.user_text = False, False, 'pc', 'Remember that.'
            app.runs[run.id] = run
            app.store.message('phone-2', 'user', 'The spare key is under the pot.')
            app.store.message('phone-2', 'user', 'Remember that.')
            waiting = app.memory_command(run, 'Remember that.')
            self.assertIn('Waiting for approval on screen', waiting)
            app.store.message('phone-2', 'assistant', waiting)   # as App.work records the answer
            self.assertEqual(app.store.items('memory'), [])
            approval = next(iter(app.approvals.values()))
            self.assertEqual(approval['args'], {'command': 'Remember that.', 'line': 'The spare key is under the pot.'})
            done = app.approve(approval['id'], True)
            self.assertEqual(done['result']['summary'], 'Remembered: The spare key is under the pot.')
            self.assertEqual([r['body'] for r in app.store.items('memory')], ['The spare key is under the pot.'])

    def test_ask_first_carries_the_owners_line_after_an_answer(self):
        """1.0.18: with "Ask first" the line carried in the approval is the owner's own, not JARVIS's answer."""
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        with patch.dict(os.environ, {}, clear=True):
            app = App(folder.name)
            app.set_permission('save_item', 'ask')
            run = Run('phone-5')
            run.wearable, run.writes, run.device, run.user_text = False, False, 'pc', 'Remember that.'
            app.runs[run.id] = run
            app.store.message('phone-5', 'user', 'I did 30 push-ups this morning.')
            app.store.message('phone-5', 'assistant', 'Already logged, Mr. Teague. Nice work.')
            app.store.message('phone-5', 'user', 'Remember that.')
            app.store.message('phone-5', 'assistant', app.memory_command(run, 'Remember that.'))
            approval = next(iter(app.approvals.values()))
            self.assertEqual(approval['args'], {'command': 'Remember that.', 'line': 'I did 30 push-ups this morning.'})
            self.assertEqual(app.approve(approval['id'], True)['result']['summary'], 'Remembered: I did 30 push-ups this morning.')
            self.assertEqual([r['body'] for r in app.store.items('memory')], ['I did 30 push-ups this morning.'])

    def test_the_phones_case_end_to_end(self):
        """The phone's check of 2026-10-10 through App.work: a device with the tick, the owner's line, JARVIS's answer,
        then "Remember that." with no model asked."""
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test'}, clear=True), patch('providers.chat', side_effect=AssertionError('no model needed')):
            app = App(folder.name)
            run = Run('device-x-2')
            run.wearable, run.writes, run.device = True, True, 'device-x'
            app.runs[run.id] = run
            app.store.message('device-x-2', 'user', 'I did 30 push-ups this morning.')
            app.store.message('device-x-2', 'assistant', 'Already logged, Mr. Teague. Nice work.')
            app.work(run, 'Remember that.', None)
            self.assertEqual([r['body'] for r in app.store.items('memory')], ['I did 30 push-ups this morning.'])

    def test_nothing_before_it_asks_nobody(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        with patch.dict(os.environ, {}, clear=True):
            app = App(folder.name)
            app.set_permission('save_item', 'ask')
            run = Run('phone-3')
            run.wearable, run.writes, run.device, run.user_text = False, False, 'pc', 'remember that'
            app.store.message('phone-3', 'user', 'remember that')
            self.assertEqual(app.memory_command(run, 'remember that'), memory.NOTHING_BEFORE)
            self.assertEqual(app.approvals, {})

    def test_a_credential_in_the_line_is_refused_as_the_answer(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        with patch.dict(os.environ, {}, clear=True):
            app = App(folder.name)
            run = Run('phone-4')
            run.wearable, run.writes, run.device, run.user_text = False, False, 'pc', 'remember that'
            app.store.message('phone-4', 'user', 'My api key is sk-proj-abcdefghijklmnop')
            app.store.message('phone-4', 'user', 'remember that')
            self.assertEqual(app.memory_command(run, 'remember that'), 'Credentials cannot be saved as memory.')
            self.assertEqual(app.store.items('memory'), [])

    def test_a_phone_without_the_writes_tick_does_not_reach_the_command(self):
        """App.work asks memory_command only for the PC or a device with the owner's tick (decision D2)."""
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test'}, clear=True), patch('providers.chat', side_effect=AssertionError('no model needed')):
            app = App(folder.name)
            for writes, expected in ((True, ['The spare key is under the pot.']), (False, [])):
                run = Run('device-x-1')
                run.wearable, run.writes, run.device = True, writes, 'device-x'
                app.runs[run.id] = run
                app.store.message('device-x-1', 'user', 'The spare key is under the pot.')
                app.work(run, 'Remember that.', None)
                self.assertEqual([r['body'] for r in app.store.items('memory')], expected, writes)
                for row in app.store.items('memory'):
                    app.store.delete('memory', row['id'])


class ActionGuardTests(unittest.TestCase):
    EVENTS = [{'event': 'tool.completed', 'data': {'name': 'save_item', 'result': {'id': 7}, 'checked_at': 1}}]

    def test_a_reply_that_merely_mentions_updates_is_kept_with_the_note_under_it(self):
        reply = ('Improvements for the next build:\n1. The header has been updated in round 2 already.\n'
                 '2. I have completed nothing here; these are suggestions.')
        out = answer_evidence.action_guard(reply, [])
        self.assertTrue(out.startswith(reply))
        self.assertTrue(out.endswith('\n\n' + answer_evidence.NO_ACTION_NOTE))

    def test_with_receipts_the_reply_stays_and_the_receipts_follow(self):
        out = answer_evidence.action_guard("I've saved your note.", self.EVENTS)
        self.assertTrue(out.startswith("I've saved your note.\n\nAction evidence for this request:\nsave item: saved. Checked at "))
        self.assertTrue(out.endswith('These receipts cover only the listed actions.'))

    def test_a_failed_action_is_said_under_the_claim(self):
        failed = [{'event': 'tool.failed', 'data': {'name': 'set_timer', 'checked_at': 1}}]
        out = answer_evidence.action_guard('Your timer has been scheduled.', failed)
        self.assertTrue(out.startswith('Your timer has been scheduled.\n\nAction evidence'))
        self.assertIn('set timer: failed.', out)
        # "has been set" is not a wording the guard watches (deliberately bounded): such a reply is left alone.
        self.assertEqual(answer_evidence.action_guard('Your timer has been set.', failed), 'Your timer has been set.')

    def test_no_claim_means_no_change_and_no_receipts_is_empty(self):
        self.assertEqual(answer_evidence.action_guard('A transistor is a switch.', self.EVENTS), 'A transistor is a switch.')
        self.assertEqual(answer_evidence.receipts([]), '')
        self.assertIn('save item: saved.', answer_evidence.receipts(self.EVENTS))


if __name__ == '__main__':
    unittest.main()
