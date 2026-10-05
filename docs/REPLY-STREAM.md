# Replies that appear while they are written (release 1.0.15, scope item 8)

Built 2026-10-06 in the repo only. Master document section 3: a reply should not make the owner wait for its last
word before the first is shown.

**Before:** JARVIS asked the AI provider for a complete answer, ran its claim checks on it, and only then showed
anything. A long answer meant a long empty wait.

**Off by default.** Settings > AI > "Show replies while they are written (Qwen)". Until the owner ticks it, every
request is exactly the one sent before, and nothing in this record happens. It has **not been tried against the real
Qwen service** (section 6): the first real answer after ticking the box is the first real test.

## 1. What happens

With the box ticked and Qwen as the chosen provider, the Core asks for the answer in pieces (the same request with
`"stream": true`). As the pieces arrive:

1. They are collected. Nothing is shown piece by piece.
2. Each time a sentence is complete, the Core runs its claim checks on everything written so far: the same checks,
   through the same function (`App.claim_checks`), that every finished answer meets.
3. While the checks leave the text exactly as it is, it is shown as a **draft** (at most five times a second).
4. From the moment the checks would change anything, nothing more of that answer is shown early.
5. The finished answer goes through the checks as it always did, and what they return replaces the draft on screen.
   Only that finished, checked answer is saved in the conversation, spoken, and given to other devices.

So a draft is always the beginning of an answer, made of complete sentences, that the checks accepted as it stood.
A sentence such as "I have saved the note" with no receipt behind it is never on screen, not even for a moment: the
draft stops at the sentence before it, and the finished answer then says what the checks say ("No matching action
result was recorded…").

## 2. The rule, and what follows from it

**Nothing is shown that the claim checks have not passed.** The checks are `verified_status.guard` ("the tests
passed", "the service works": only with the result on record) and `answer_evidence.action_guard` ("I saved it", "the
timer is set": only with the receipt), and the removal of the lines only the Core may write (who answered).

- **Not even the beginning of a line only the Core may write is shown.** A draft stops before "[OpenAI answered…"
  or "[Answered offline…" (the finished answer removes the whole line; its first sentence would otherwise have been
  on screen until then).
- **A model's thinking is never shown.** A thinking model sends its thinking first, in a separate field; the Core
  ignores that field. In Deep mode the first sentence therefore appears when the thinking is over.
- **Words that come with a tool request are taken off the screen.** If the model writes "Let me look at the clock"
  and then asks for a tool, those words were never part of the reply (they never were before either). The draft is
  cleared and the next attempt starts empty.
- **A daily briefing is not shown early at all.** Its text is written by the Core from its own data, not by the model.
- **Stop takes the unfinished reply off the screen, at once**, also while the provider is silent (the connection is
  ended from outside the part that reads it). Nothing of an answer that was not finished is kept or shown; the
  window says "Stopped." as before.
- **Speech starts when the answer is complete**, as before. Speaking a draft would mean speaking words the finished
  answer may replace.
- **Other devices get the finished reply only.** A question from a paired device is asked in one piece.
- **OpenAI is unchanged** (one piece). The setting says "(Qwen)" for that reason.

## 3. When the pieces do not arrive properly

No partial answer is ever accepted.

- **Asked again the usual way, in one piece, once:** when the stream breaks, goes quiet for 60 seconds, sends
  something that is not a piece of an answer, ends without the mark that says it is finished, or when the provider
  turns the request for pieces down (HTTP 400 that is not a bill or a limit). The draft is taken off the screen
  first. The rest of that question (for example after a tool) stays in one piece too. If that also fails, the backup
  provider and the offline answer apply exactly as they do without this setting.
- **Not asked again:** an answer still arriving after 120 seconds. It ends as the one-piece request does after that
  time ("Connection timed out"), and the backup provider or the offline answer may take over as without this
  setting. Asking the same provider again could not succeed in the time that is left.
- **Not asked twice either:** a refusal that has nothing to do with pieces (a wrong key, an unpaid bill, a rate
  limit, a server error). Its message is shown as always.

## 4. Where it lives

| Part | What it does |
| --- | --- |
| `reply_drafts.py` | `complete_sentences(text)` and `Drafts`: collects pieces, runs the check it is given on the complete sentences, shows what passed, holds from the first change, clears a thrown-away attempt. Knows nothing about providers or the screen. |
| `providers.py` | `chat(..., stream=True)` for Qwen: `_compatible_stream` reads the server-sent events, hands each piece of text to the Core as `assistant.piece`, puts a tool request that arrives in parts together, and returns the same response the one-piece request returns. `_end_stream` and `cut_connection` end the connection from outside on Stop and when the time is up. Limits: `STREAM_QUIET_SECONDS`, `STREAM_TOTAL_SECONDS`, `STREAM_MOST_BYTES`. The key travels as in every other request (never forwarded on a redirect). `BACKUP_OPENING` (and `offline_answers.OFFLINE_OPENING`): the beginnings a draft stops before. |
| `server.py` | `App.claim_checks` (the one place the checks are applied: drafts, finished answers and the local model's answers), `App.drafts_for`, and in `work()` the decision to stream, the pieces going to the drafts instead of the screen, the second attempt, and the clearing on failure, tool request and stop. Setting `reply_stream` (`store.py`, default off). |
| `static/app.js` | Event `assistant.draft` `{text}`: the whole draft so far (empty text: take it away). It replaces what is shown; `assistant.delta` and `assistant.completed` then put the checked answer in its place. The tick box. |

`assistant.piece` never leaves the Core. `assistant.draft` events stay in the run's event list like every other
event; they contain only text the checks passed.

## 5. Checked

`test_reply_drafts.py` (8 tests, with the real checks: only complete sentences count, and a list number alone ends
nothing; an ordinary answer appears sentence by sentence; a claim the checks would change is never shown, with or
without a receipt; not more often than the interval; a check that cannot run shows nothing; a thrown-away attempt is
cleared; odd pieces ignored).

`test_reply_stream.py` (24 tests, the provider played back by a stand-in connection, nothing contacted). At the
provider: the request is the usual one plus `"stream": true`; pieces add up to the same answer; thinking is not part
of it; a tool request in parts is put together, and parts that cannot be put in order are a broken stream; seven
kinds of broken stream and an oversized one are errors with no partial answer; Stop works between pieces and while
the provider is silent; an answer still arriving when the time is up ends as "timed out"; a refusal or no connection
reads as it always did; OpenAI stays in one piece. Through the Core's real answer path: drafts first and the checked
answer last, only the finished answer saved; a claim never on screen in any event; **every draft of seven answers
made to break the rule, at three piece sizes, is a beginning of the answer that the checks leave unchanged**; not
even the beginning of a "who answered" line is shown; words with a tool request cleared; a broken stream and a
turned-down request asked again in one piece, a wrong key and an unpaid bill not; time that is up not followed by a
second attempt; a tool runs once when the stream breaks after it; a broken stream, then no connection, then the
backup provider; Stop clears the draft and keeps nothing; off by default with the old request; another device's
question in one piece.

**Over a real connection on this PC** (a small server on 127.0.0.1 inside the test program, no encryption): a
complete answer; Stop pressed while the provider was silent returned after 0.5 seconds; with the total time set to
2 seconds a silent provider and one sending bytes without ever ending a line both ended after 2 seconds as "timed
out"; 2 seconds of silence against a 2-second quiet limit ended as a broken stream. The first try of this showed
that on Windows a waiting reader is not woken by shutting the connection down, only by closing the socket itself
(Stop took 25 seconds); `cut_connection` does both, and the offline answer's Stop uses the same.

**Seen in the window** on 2026-10-06, before the review (a sandbox Core with empty data, a made-up key, the
provider replaced by a stand-in on this PC that writes an answer slowly, and every connection to anything but this
PC refused):

- The tick box is in Settings > AI, unticked on a new installation; ticked and saved, it is still ticked after a
  reload.
- An ordinary answer: the first sentence was on screen after about 1 second, then sentence after sentence, and the
  complete answer after about 4.3 seconds (the same answer in one piece: nothing for about 3 seconds, then all of it).
- An answer containing "I have saved the note for you": the two sentences before it appeared, the claim never did,
  and the reply ended as "No matching action result was recorded for this request. Completion is not confirmed."
- Words followed by a tool request: "Let me look at the clock first." appeared, was taken away when the tool ran,
  and the real answer then appeared sentence by sentence.
- A stream that broke halfway: the first sentence appeared, was taken away, the window said "Waiting for AI
  response…", and the complete answer arrived in one piece about 3 seconds later.
- Stop pressed after two sentences: both were taken away and the window said "Stopped."

And again after the review's fixes, from the repo: an ordinary answer sentence by sentence as before; an answer with
a forged "[OpenAI answered this question because Qwen could not. …]" line showed only the sentence before it and
ended without the line; a stand-in that went silent after two sentences, with Stop pressed 3.5 seconds in, said
"Stopped." within a tenth of a second, and the next question was answered normally.

## 6. Not checked

- **The real Qwen service.** The shape of its stream (`data:` lines, `delta.content`, `delta.reasoning_content`,
  `delta.tool_calls` with an `index`, `finish_reason`, `[DONE]`) is taken from Alibaba's published description of the
  OpenAI-compatible interface, not from a recording on the owner's account. If the real stream is malformed in the
  reader's eyes, or the request for pieces is turned down with HTTP 400, that question is asked again in one piece;
  what the owner would notice is a reply that appears all at once after a slightly longer wait. Any other refusal of
  the streamed request fails the question as it would without the setting.
- Stop and the time limit over an encrypted connection (the real service is reached with encryption; the same two
  calls are made on the encrypted socket, which was not tried).
- Whether the first sentence really arrives sooner on the owner's account, and by how much.
- Very long answers: each draft event carries the whole draft so far, which is simple and cannot get out of step,
  and costs memory in proportion to the square of the answer's length for the life of that run.

## 7. Independent review (2026-10-06, one reviewer): nothing serious, 5 lesser findings, all applied

The reviewer worked on a separate copy of the tree with the change applied, ran 20 answers made to break the rule
at 9 piece sizes through the real answer path (201 drafts: every one left unchanged by the checks and a beginning
of the answer), compared the refactored check function with the old logic on 416 answers (the same), and ran the
window's own handler lines.

| | Found | Done |
| --- | --- | --- |
| 1 | A draft could show the first sentence of a forged "who answered" line ("[OpenAI answered this question because Qwen could not.") until the finished answer removed the line. | A draft stops before the beginning of either line. |
| 2 | An unpaid bill (Alibaba answers it with HTTP 400) was asked twice, contrary to this record. | Only an HTTP 400 that is not a bill or a limit is asked again. |
| 3 | A healthy answer cut off at 120 seconds was asked again in one piece, which could not succeed either: about four minutes and two paid answers. | The time limit ends the question as it does without the setting; no second attempt once the time is used up. |
| 4 | Stop while the provider was silent waited for the quiet limit (up to a minute), and bytes without a line end were not bounded by the total time. | The connection is ended from outside the reader on Stop and when the time is up (and really ended on Windows, see section 5). |
| 5 | Tool-request parts with mixed kinds of index, or a deeply nested line, escaped the reader's own handling: "failed internally", the draft left on screen. | Both are a broken stream like any other. |

Also from the review: the test that claimed to compare drafts with finished answers did not look at drafts; it is
replaced by the one in bold in section 5. Five cases it found untested are tested. The fixes were not reviewed again.
