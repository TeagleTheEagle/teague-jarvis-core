# Two Core fixes from the phone's checks (2026-10-10, for release 1.0.18)

**Owner's approval, word for word (2026-10-10):** "I approve both Core fixes from MAC-ANSWERS-20261010.md: item 4 (a
timer's reply gives the local clock time) and item 5 ("remember that" saves my own last line)."

Both defects were seen from the iPhone app against the everyday JARVIS 1.0.17. They were reported in the Mac's
STATUS.md ("Requests for the PC", items 4 and 5) and diagnosed in `docs/MAC-ANSWERS-20261010.md`. Both are Core-only
changes: the iPhone app needs nothing (it shows the Core's receipt words as they come). They go into the next build of
1.0.18. The everyday JARVIS gets them only through that release's checks and the owner's update approval.

## 1. A timer's reply gives the local clock time (item 4)

**Seen:** at 10:27 local the phone asked for a two-minute timer. JARVIS answered that it "should fire around 07:19".
Asked where 07:19 came from, he said he had not checked the clock.

**Cause:** `set_timer`'s result, which the model reads, was `store.reminder`'s record. Its `due` is a bare Unix
timestamp in seconds, and no clock time came with it. The model turned the number into a time itself and got it
wrong; the right answer was about 10:29. A question's request carries no current time either, unless the model calls
the time tool or reads the calendar.

**Change:**
- `answer_evidence.clock(value, now=None, tz=None)`, a new helper. It gives the time as the owner reads it on this
  PC's clock:
  - "10:29" for today;
  - "07:00 on Monday 12 October" for another day;
  - the year as well when it is not this year.
- `answer_evidence.duration(seconds)`, a new helper: a length in words ("2 minutes", "1 hour 30 minutes", "1 second").
- `answer_evidence.stamp(value, tz=None)`: the new `tz` is for tests only.
- `server.App.tool`:
  - `set_timer`'s result gains `due_local`, which is `stamp(due)`: ISO 8601 on this PC's clock with its UTC offset, as
    the Core's other receipts are stamped.
  - `manage_timer` gives `due_local` for every listed timer and for an adjusted one. A listing also gives `now` and,
    for each timer, `seconds_left`, so "how long is left?" is read, not worked out.
  - `due` stays as it was for everything that reads it, for example the desktop window's reminder list.
- `server.App.describe('set_timer')` is the reply used when no model is asked, for example for the local command
  "set a timer for 2 minutes". It now reads "Timer started for 2 minutes. It goes off at 10:29. Keep JARVIS running for
  the alert." It used to read "120 seconds", and very long timers read "1.08e+06 seconds".
- `answer_evidence.receipt`: a timer's receipt reads "scheduled; goes off at 10:29", or "adjusted; goes off at ...".
  An approved timer starts when it is approved, up to 15 minutes after the question, and the approval line now says
  when it goes off. That line is "Approved on screen: Set a timer. Result: ..." on the PC, and the `result` of a
  device's `approve` on the phone.
- Not changed: the request sent with every question still carries no clock. The fix stays within what the owner
  approved, and a clock that changes every minute would also keep Qwen's cache of the request's start from working.

**Tests:** `test_timer_clock.py` (new, 10 tests). The expected texts are written out in full, in fixed +10:00 and
+11:00 zones where the zone matters:
- today, past midnight, another year;
- the lengths in words;
- the receipts;
- `due_local` in this PC's zone;
- a listing's `now` and `seconds_left`;
- adjusting and cancelling.

`test_permissions.py` and `test_phone_access.py` now expect the new receipt words.

## 2. "Remember that" saves the owner's own last line (item 5)

**Seen:** after a line the owner typed and JARVIS's answer to it, "Remember that" saved JARVIS's answer ("Remembered:
JARVIS said: Already logged, Mr. Teague ...") instead of the owner's line.

**Cause:** as built in 1.0.17 (`docs/PHONE-CORE-FIXES-20261007.md` section 2), the pointer saved the line just
before it, whoever said it. After an answer, that line is the answer. "Remember what I said" did the same.

**Change:** `memory.py`:
- `pointer_role(text)` gives whose line a pointer means. It reads the same match as `is_pointer`, so the two never
  disagree:
  - "remember what you said" and "remember what you just said" mean JARVIS's last answer;
  - every other form means the owner's own last line: "remember that", "remember this", "remember it", "remember what
    I said", a bare "remember".
- The pointer also accepts "please" and "for me" any number of times, and "?" or "…" at the end. "Remember that?"
  used to save the word "that?".
- `previous_line` returns the last line of that speaker among the last 20 lines (8 before).
- Unchanged:
  - the skipped lines: other memory commands, and JARVIS's answers to them;
  - the 500-character cut;
  - the "JARVIS said:" prefix for JARVIS's words;
  - the Ask-first approval carrying the line it found when the command was said;
  - the credential refusal, and the "may save" tick for devices.
- The Core's own lines are never taken as JARVIS's words: approvals from a device, "There is nothing before this to
  remember", the credential refusal, and "I couldn't identify one ...".
- When only JARVIS's lines come before the command, nothing is saved and the answer is the existing "There is nothing
  before this to remember. ..." sentence.

**Tests:** `test_phone_core_fixes.py`:
- the phone's case for every owner form;
- "remember what you said" saves JARVIS's words, and reaches back past the owner's "Thanks.";
- whose line each form means;
- only JARVIS's lines before it saves nothing;
- the Core's own lines are skipped;
- the owner's line is found past ten approval receipts;
- the Ask-first approval carries the owner's line after an answer;
- the phone's case end to end through `App.work` on a device with the tick, with no model asked.

The 1.0.17 test that saved JARVIS's answer for "remember this" is replaced by these.

## 3. Review

One independent reviewer per item, one at a time. Neither edited anything.

**Timer (item 4):** no high, 1 medium, 5 low. Both files stay CRLF-only.
- Medium 1, a listing gave no time now and nothing left: **applied** (`now`, `seconds_left`).
- Low 2, an approved timer's receipt gave no time: **applied**.
- Low 5, the length as "1.08e+06 seconds" and "1 seconds": **applied** (`duration`).
- Low 6, tests built their expectations with the functions under test: **applied** (fixed zones, full texts,
  midnight). Not testable on this PC: a timer crossing a daylight-saving change, since Windows here has no time-zone
  database. `clock` and `stamp` take each moment's own offset, which the reviewer checked by hand: 01:58 + 5 minutes on
  4 October reads 03:03 (+11:00).
- **Not built, outside the approved scope:**
  - Low 3: a phone used in another time zone reads the PC's clock time. The phone sends no offset, so this needs a
    Core and app change.
  - Low 4: an old `set_timer` record still says "scheduled" after the timer is cancelled or changed, because
    `manage_timer` is not an evidence tool.
- **Outside this change, found on the way:** the window's own reminder route (`/api/reminder`) sets a timer while
  the emergency stop holds. This predates 1.0.18 and waits for the owner's word.

**"Remember that" (item 5):** 2 high, 1 medium, 6 low.
- **High 1 and High 2 wait for the owner's decision** (2026-10-10). Saving "the owner's own last line" goes wrong
  when that line is not a statement:
  - after "analyse my screen" on the PC, the owner's line is the window's built-in screen prompt (about 500
    characters of instructions);
  - after a question ("When is the meeting?"), it is the question;
  - after a command ("set a timer ..."), it is the command.
  - The choice put to the owner: A, save JARVIS's answer after a question or request and nothing after a command; or
    B, save nothing and tell the owner to say "remember what you said".
- Medium 3, the Core's own lines saved as JARVIS's words: **applied**.
- Low 4, "remember what you saidplease" got the wrong speaker: **applied**, since the speaker is read from the
  pointer's own match.
- Low 5, "Remember that?", "remember what you said?" and "for me, please" fell to the "remember <words>" rule and
  saved junk: **applied**.
- Low 6, the 8-line window: **applied**, now 20 lines.
- Low 8, stale wording: **applied** in `memory.py`, `server.py` and the status. The Mac's test comment is the Mac's.
- Low 9, a test that passes on the old code: **applied**, with "Thanks." between the answer and the command.
- **Not built:**
  - Low 7: a file left attached on the PC sends "remember that" to the model, and the model's instructions say
    nothing about the pointer. This predates 1.0.18.
- **Outside this change, found on the way:** "Call me when the build finishes." is taken as the name command and
  saves "when the build finishes" as the owner's preferred name (`memory._NAME`). This predates 1.0.18 and waits for
  the owner's word.
