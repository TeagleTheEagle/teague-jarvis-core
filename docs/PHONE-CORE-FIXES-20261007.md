# The three Core items from the phone checks (2026-10-07, for release 1.0.17)

Owner: "do the core items" (2026-10-07, about 00:20 local), after the order of value was agreed: replies streamed to
the phone, "remember that", the action guard's false positive. All three came from the phone's first evening
(`docs/PHONE-V1-RESULT.md` section 2, items 9 and 11, and section 4). They ship with release 1.0.17 (the own-app
plan); nothing reaches the everyday JARVIS before that release's Stage 7 check and update, on the owner's approvals.

Status: **BUILT, TESTED AND INDEPENDENTLY REVIEWED ON THIS PC** (the review is section 5). The phone app shows the
drafts once the Mac session adds `assistant.draft` to its events loop (a request carried by the owner; the Core
sends the finished reply as before, so the app works unchanged until then).

## 1. Replies streamed to the phone

**Before:** `server.py` decided streaming with `not getattr(run, 'wearable', False)`: a device's question was asked
in one piece and its client got the finished reply only. The PC window got drafts (`assistant.draft` events,
`docs/REPLY-STREAM.md`) when Settings > AI > "Show replies while they are written" was on.

**Now:** the same decision without that clause. A device's question streams when the PC's setting is on and the
provider is Qwen; the drafts are the same `assistant.draft` events in the run's record, which the device's `events`
route already serves (`wearables/service.py`, `events {run_id, after}`), each carrying the whole draft so far and
only what the claim checks have passed (reply_drafts.py: a draft is never a claim the checks would change). A
device run refreshes its draft at most every half second (`App.DEVICE_DRAFT_SECONDS = 0.5`; the window's
`DRAFT_SECONDS` stays 0.2): a phone reads each draft as one whole event over its link, so fewer, larger steps. The
finished reply still comes as `assistant.delta` and `assistant.completed`; what is saved, spoken and given to the
phone as the reply is unchanged.

**The phone side (the Mac session):** in `SessionModel.follow`, on `assistant.draft` show `event.data["text"]` as
the reply being written (replace, not append: each draft is the whole text so far; an empty text takes the draft
away, as when a tool runs); on `assistant.completed` the finished text replaces it. Speak only the finished reply, as
the PC does. The PC's setting must be on; it is off on a new installation.

**Tests:** `test_reply_stream.py`: `test_another_devices_question_appears_as_it_is_written_too` (a device run gets
the two sentence drafts and the stream request; the finished answer unchanged); the harness sets
`DEVICE_DRAFT_SECONDS = 0` as it does `DRAFT_SECONDS`. The rest of that module (the promise that every draft is a
checked beginning of the answer, Stop, a broken stream, the backup provider) is unchanged and passes.

## 2. "Remember that."

**Before:** the exact memory commands (`memory.py`) knew "remember that I prefer ...", "my name is ...", "project
X: ...", "forget memory: ..."; a bare "Remember that." fell through to `actions.local_command`, whose "remember
<words>" rule saved the word "that." without asking the model (the phone's check 9: the saved memory "that.").

**Now:** `memory.py` has the pointer command: "remember that", "remember this", "remember it", "remember what I
just said", "remember what you said", "memorise that", or a bare "remember", also in the spoken forms "remember
that, please" and "remember it for me", with any spacing, punctuation and case (`is_pointer`). It saves the line
before it in the conversation (`previous_line`: the last user or assistant message other than the command itself,
which is already on record when the command runs; skipped are another memory command of the owner's, a repeated
pointer included, and JARVIS's answers to such commands, "Remembered:", "Saved:", "Saved that preference",
"Waiting for approval on screen" and the like; whitespace collapsed; cut at 500 characters). The owner's own line is
saved as it was; a line JARVIS said is saved as "JARVIS said: ...". The answer is "Remembered: <the line>", as the
local command's answer reads. With nothing before it, the answer says so, nothing is saved and nobody is asked.
Commands that carry their own words are not pointers: "remember that I prefer tea" stays the preference command,
"remember that the meeting moved" and "remember to buy milk" go to `actions.local_command` as before (it saves the
words after "remember"). `governed_by` returns `save_item` for the pointer, so the owner's switch for "Save a note, a
task or a fact" applies (Allowed, Ask first, Off) and the activity row is written as for every exact memory command.
**With "Ask first" the line is found when the command is said and carried inside the approval** (`memory_line`; the
approval card shows it as `line`), because by the time the owner approves, the last line of the conversation is the
waiting answer itself; `App.approve` saves that carried line. A line that holds a credential is refused by the store
and the refusal is the answer, with an activity row. On the phone the command reaches the Core only with the "may
save memories and tasks" tick (the D2 decision), as before; without it the words go the old way and a device may not
save.

**Tests:** `test_phone_core_fixes.py`: the owner's line saved; JARVIS's line saved as JARVIS's words; the forms that
point back (the spoken ones too) and the ones that do not; nothing before it; the confirmations of other commands
never the line; a line given with the command; a repeated pointer and its confirmation skipped; a long line collapsed
and cut; the other commands unchanged without a conversation; through `App.memory_command` with a conversation;
"Ask first" carrying the line and saving it on approval; nothing before it asks nobody; a credential refused as the
answer; a phone without the writes tick does not reach the command. `test_permissions.py` and
`test_permissions_review.py` (the switches and the activity rows of the exact memory commands) pass unchanged.

## 3. The action guard

**Before:** `answer_evidence.action_guard` replaced a whole reply whose wording claimed a finished action ("I've
saved", "the file has been updated", "I have completed ...") with one sentence when no action tool ran in the turn
("No matching action result was recorded for this request. Completion is not confirmed."), or with the receipts
block when one did. On 2026-10-06 the owner's question on the phone, "list improvements/additions needed in the next
build for the app", came back as that sentence (item 11): a list of suggestions that mentioned completed work tripped
it, and the answer was lost.

**Now:** the reply is kept and the truth is put under it, after a blank line: the receipts of this turn's action
tools (`receipts(events)`, the old block, with "failed" and "awaiting approval" where so) or, when none ran,
`NO_ACTION_NOTE`: "No action was carried out for this request: nothing was saved, created, scheduled or changed.
Completion is not confirmed." The wording the guard watches is unchanged (deliberately bounded). The drafts are
unchanged: a draft stops before a claim the checks would change (`check(text) != text`), so nothing of a claim is on
screen early; the finished reply then carries the note. The briefing path uses `receipts` directly. The note is
spoken with the reply on the PC and on the phone: an audible correction.

**The reading of the owner's instruction:** "append the caveat under the reply instead of replacing it" is applied to
every case, also to a false first-person claim with nothing run ("I've saved your note." followed by the note).
The claim and its correction stand together; replacing the claim hid the rest of the answer and left the owner with a
sentence about a request that often had not been an action at all. The watched wording was deliberately NOT narrowed
to first-person claims (the reviewer's suggestion, finding 2): "Your reminder has been created" from the model with no
tool run is the dangerous case, and dropping the note there would let a false claim stand; the cost of the wider
net is one extra sentence under prose that merely mentions a saved file or an applied update, now that the prose
itself stays. If that proves too noisy in use, narrowing is a one-line change in `answer_evidence.py`.

**Tests:** `test_phone_core_fixes.py` (a list that mentions updates is kept with the note; receipts follow a kept
claim; a failed action is said under the claim; "has been set" is not watched; no claim, no change);
`test_answer_evidence.py` (three tests re-pointed from the replaced reply to the kept reply with the truth under it);
`test_reply_stream.py` (`test_a_claim_the_checks_would_change_is_never_on_screen`: the drafts stop before the claim,
the finished reply is the claim with the note).

## 4. Records changed

`docs/PHONE-CORE-1.0.16.md` section 6 and `docs/DEVICES.md` (the `events` row): `assistant.draft` for devices;
`docs/REPLY-STREAM.md`: other devices get the drafts too, the guard's new ending; `docs/OFFLINE-ANSWERS.md` and
`docs/PERMISSIONS.md`: the guard's note and the pointer command. The release notes entry for 1.0.17 names the three
at the build.

## 5. Independent review (one reviewer, 2026-10-07): 1 high, 2 medium, 5 low; applied except where said

The reviewer read the diff against the Core, ran edge cases with the venv's Python and the changed test modules, and
confirmed for item 1 that nothing else assumed a device run has no drafts (speech is client-side from the completed
text; only the finished answer is saved; the repair and Stage 4 paths filter on the events they need; cancel and
stop clear the draft with an empty text, which the phone's future handler must treat as "take it away"; the
12,000-event cap is far off; the local glasses client's cursorless `events` now returns every draft on every poll,
tolerable). Line endings clean (counted with Python).

- **High, applied:** with "Ask first", an approved "remember that" saved nothing: `App.approve` ran the command
  later without the conversation, and carrying the conversation alone would have resolved the "Waiting for approval
  on screen" line. Now the line is found at command time, shown on the approval card and carried in the approval
  (section 2); a test covers the path. With nothing before it, nobody is asked.
- **Medium, not applied (reasoned in section 3):** narrow the guard to first-person claims when no tool ran.
- **Medium, applied:** `docs/REPLY-STREAM.md` claimed the phone already shows the drafts; corrected.
- **Low, applied:** the spoken forms of the pointer ("remember that, please", "remember it for me", double spaces),
  which otherwise fell to the local "remember <words>" rule and saved "that, please"; the confirmations of other
  commands (and the owner's other memory commands) are never the line; a credential in the line is refused as the
  answer with an activity row instead of a failed run; the record's account of where "Remembered: that." came from
  (the local command, not the model) and the test comment corrected; this record committed with the change.
- **Noted:** no other test pinned the old guard wording (one did, in `test_offline_core.py`, found by the full suite
  and re-pointed); the device's writes-tick gate and the ask-first path now have tests.

Tests after the review: the affected modules (`test_phone_core_fixes`, `test_memory_voice`, `test_permissions`,
`test_permissions_review`, `test_answer_evidence`, `test_reply_stream`, `test_offline_core`: 126 tests) pass; the full
Python suite result is in `docs/CURRENT-STATUS.md`.
