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

**The owner's choice, 2026-10-10** (asked after the review's two highs, answered "His answer (Recommended)"): for
"remember that", "remember this", "remember it" and a bare "remember", the owner's last line decides
(`memory.line_kind`, `pointer_role` 'auto'):
- **a statement**, where the owner told JARVIS something ("I did 30 push-ups this morning."): that line is saved;
- **a question or a request**, where the owner asked something: JARVIS's answer to it is saved, as "JARVIS said: ...".
  This covers:
  - a "?" at the end, or a question word first;
  - a request such as "write", "tell", "show", "analyse", "explain" or "find";
  - the PC window's screen question (`memory.SCREEN_PROMPT`, kept in step with `static/app.js` by a test);
- **a command**, where JARVIS was made to do something ("set a timer ...", "play ...", "open ...", the stop words,
  "resume", and local commands that change something): nothing is saved, and the answer is `memory.COMMAND_HINT`.
  It reads "Nothing saved: that was a command, not something to remember. Say what to remember, for example “remember
  that the gate code is 4421”, or “remember what you said” for my answer." With "Ask first" nobody is asked;
- looked past, with JARVIS's reply to them: a word of thanks or a yes ("Thanks.", "ok", "got it"), and a line that
  saved itself ("remember that the meeting moved", a note).

"Remember what I said" stays the owner's own line as it is, and "remember what you said" JARVIS's last answer. On an
approval card the line shown is the one that would be saved.

**Tests:** `test_phone_core_fixes.py`:
- the phone's case for every owner form;
- "remember what you said" saves JARVIS's words, and reaches back past the owner's "Thanks.";
- whose line each form means;
- only JARVIS's lines before it saves nothing;
- the Core's own lines are skipped;
- the owner's line is found past ten approval receipts;
- the Ask-first approval carries the owner's line after an answer;
- the phone's case end to end through `App.work` on a device with the tick, with no model asked.

The 1.0.17 test that saved JARVIS's answer for "remember this" is replaced by these. For the owner's choice:
- what kind of line each example is;
- a question or request keeps JARVIS's answer;
- after the window's real screen question, read from `static/app.js`, the analysis is kept;
- after a command nothing is saved and the hint is given, with nobody asked under "Ask first";
- thanks and self-saving lines are looked past;
- "remember what I said" keeps the owner's line as it is;
- with "Ask first" after a question, the approval carries JARVIS's answer.

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
- **Outside this change, found on the way:** the window's own reminder route (`/api/reminder`) set a timer while the
  emergency stop held. This predates 1.0.18. **Fixed on the owner's word ("Fix both"):** the route now calls
  `require_running` first, as `set_timer` through `App.tool` does. `test_permissions.py` checks it is refused with
  the stop sentence and that no reminder is made.

**"Remember that" (item 5):** 2 high, 1 medium, 6 low.
- **High 1 and High 2: resolved by the owner's choice** (section 2). Saving "the owner's own last line" went wrong
  when that line is not a statement:
  - after "analyse my screen" on the PC, the owner's line is the window's built-in screen prompt (about 500
    characters of instructions);
  - after a question ("When is the meeting?"), it is the question;
  - after a command ("set a timer ..."), it is the command.
  - The two choices put to the owner were A, save JARVIS's answer after a question or request and nothing after a
    command, or B, save nothing and tell the owner to say "remember what you said". **The owner chose A.**
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
- **Outside this change, found on the way:** "Call me when the build finishes." was taken as the name command and
  saved "when the build finishes" as the owner's preferred name (`memory._NAME`). This predates 1.0.18. **Fixed on the
  owner's word ("Fix both"):** a name may not begin with words such as "when", "if", "after", "at", "in", "back",
  "later", "tomorrow", "a" or "the" (`memory._NOT_A_NAME`). Such a line goes to the model as any other question.
  `NameCommandTests` checks those lines, and that "call me Alex", "Call me Mr. Teague." and "my name is Jordan" still
  work.

**The follow-up** (the owner's choice and the two older fixes) had one reviewer: 4 high, 4 medium, 5 low. It found no
import cycle and no line-ending change, and confirmed that a command asks nobody and that the stopped reminder route
shows the stop sentence. What was done about each finding:
- **High 1**, thanks saved as facts ("Thanks a lot!", "Yes please", "Sounds good"): **applied.** Thanks are now
  checked word by word (`_COURTESY`, greetings included) instead of with a pattern.
- **High 2**, the question test ran before the command test and read statements as questions ("May 12 is Mum's
  birthday.", "Don't use emojis.") and polite commands as requests ("Can you set a timer?"): **applied.**
  - "Jarvis," and "can you / could you / please" are taken off first, and commands are recognised before questions.
  - A question needs a "?", a question word with no comma after it, or "is/do/can/..." followed by a subject.
  - A line that starts with "don't" or "can't" is a statement.
- **High 3**, the name fix bypassed through a saved memory ("remember that my name is on the lease", or a remembered
  "Call me when ..."): **applied.** `memory.name_from` is the one rule for the name command, for `key()` and for the
  store's name setting. It accepts name-shaped values only: up to four words, no digits or commas, never a time, and
  several words only when each is capitalised. "Call me A.J." and "My name is An Nguyen" now work.
- **High 4**, "Remember that, Jarvis." saved "that, Jarvis." (older): **applied.** The pointer allows "Jarvis".
- **Medium 5**, "remember what you said" did not look past thanks: **applied.** The conversation is read as
  exchanges, each owner line with JARVIS's lines after it.
- **Medium 6**, music words ("louder", "volume 40"): **applied.** `music.command` is consulted.
- **Medium 7**, frames the live screen sharing sends by itself: **applied.** They are looked past (`LIVE_FRAME`; a
  test keeps it in step with `static/app.js`).
- **Medium 8**, more misreadings: **applied.**
  - "Lock code ... is 1234." and "Help desk number is ..." are statements, because of the "is".
  - "Remind me what ..." asks; "I need a / I'd like a ..." is a request.
- **Low 9**, a pathological thanks line could take seconds: **applied.** The pattern is gone, and a test times it.
- **Low 10**, the iPhone's curly apostrophe: **applied.**
- **Low 11**, the approval card showed the bare answer while "JARVIS said: ..." was saved: **applied**
  (`memory.saved_value`).
- **Low 12**, other window routes that act while the emergency stop holds (turning on the private-network door,
  the Spotify sign-in callback): **not built.** They are outside the owner's "Fix both" and are recorded for the
  owner. The owner's own edits of items while stopped are fine.
- **Low 13**, the tests: **applied.** Every finding has its case, and the `app.js` check fails cleanly.

Known limit: the kind of line is read from its wording, so an unusual sentence can still be misread. The answer
"Remembered: ..." always shows what was saved, and a wrong fact is deleted on the Memory page.

**Seen in the full Python suite at f9b3088** (836 tests, 1 error): `test_jarvis.LocalTests.test_local_run_emits_terminal_event`
could not clean its temporary folder ("The directory is not empty"). The module passes 3 of 3 alone. The test asks
"What time is it?", one of the Ollama side-check's questions (`ollama_shadow.py`), and that check writes its record in
the background after the test has ended. This is an older timing race of the test, not of these fixes.
