"""Replies that appear while they are written (release 1.0.15, scope item 8; master document section 3).

The AI provider sends an answer in pieces. JARVIS has two checks that guard what it claims (verified_status.guard:
"the tests passed", "the service works"; answer_evidence.action_guard: "I saved it", "the timer is set"). Until
1.0.15 they ran once, on the finished answer, and only then was anything shown.

Here they work on a growing answer, and the rule is simple: nothing is shown that the checks have not passed.
The pieces are collected. Each time a sentence is complete, the checks run on everything written so far. While
they leave the text as it is, it is shown as a draft. From the moment they would change something, nothing more is
shown; the finished answer then goes through the checks exactly as before, and what they return replaces the
draft. So a draft can only ever be a beginning of text the checks accepted, never an unchecked claim.

This module knows nothing about providers, runs or the screen: it is given the check and the way to show.
"""
import re
import time

# Where a sentence ends: its closing mark (with any closing quote or bracket) followed by a blank, or a line break.
_SENTENCE_END = re.compile(r'[.!?:;]["\')\]]*(?=\s)|\n')
# A list number alone on the last line ("2.") begins the next item; it does not end a sentence.
_LIST_NUMBER = re.compile(r'(?:^|\n)[ \t]*\d+\.$')


def complete_sentences(text):
    """The beginning of `text` that consists of complete sentences ('' when the first is still being written)."""
    end = 0
    for match in _SENTENCE_END.finditer(text):
        end = match.end()
    ready = text[:end].rstrip()
    number = _LIST_NUMBER.search(ready)
    return ready[:number.start()].rstrip() if number else ready


class Drafts:
    """One answer being written.

    check(text) -> text    the claim checks, exactly as the finished answer will meet them
    show(text)             put this draft on screen (the whole draft so far, not a piece)
    every                  at most one draft in this many seconds, so that a fast provider does not flood the screen
    """

    def __init__(self, check, show, every=0.2, clock=time.monotonic):
        self.check, self.show, self.every, self.clock = check, show, every, clock
        self.text, self.shown, self.held, self.last = '', '', False, None

    def add(self, piece):
        """A piece of the answer arrived."""
        if self.held or not isinstance(piece, str) or not piece:
            return
        self.text += piece
        ready = complete_sentences(self.text)
        if len(ready) <= len(self.shown):
            return
        now = self.clock()
        if self.last is not None and now - self.last < self.every:
            return  # the next piece or the finished answer brings it
        try:
            passed = self.check(ready) == ready
        except Exception:
            passed = False  # a check that cannot run shows nothing early; the finished answer decides
        if not passed:
            self.hold()
            return
        self.shown, self.last = ready, now
        self.show(ready)

    def hold(self):
        """Show nothing more of this answer early. What is on screen stays until the finished answer replaces it."""
        self.held = True

    def clear(self):
        """This attempt at the answer is thrown away (the connection broke, or the model asked for a tool instead
        of answering): take the draft off the screen and start again with nothing."""
        had = bool(self.shown)
        self.text, self.shown, self.held, self.last = '', '', False, None
        if had:
            self.show('')
