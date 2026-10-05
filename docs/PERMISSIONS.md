# Permissions in one place (release 1.0.15, scope item 3)

Built 2026-10-05 in the repo only. Master document sections 6 and 18: every action capability-scoped, attributable,
revocable and auditable; reading and changing told apart; sensitive changes ask first; a kill switch.

**Status (2026-10-05, night): built, tested and independently reviewed. The review found no high finding; its
2 medium and 14 low findings are applied (section 9 says where each one was fixed), and the sentences below were
corrected where they said more than the code did.**

**Before:** the rules were spread over five hard-coded lists (what a wearable may call, which results are receipts,
which results are kept for the next question, what can be drafted for approval, which of JARVIS's own files apply
with no approval). The emergency stop only cancelled what was running at that moment. An activity row named the
action and nothing else. JARVIS could change its own personality and style with no approval, and its change tools
wrote into the folder the program runs from, which in the installed JARVIS is the release folder.

## 1. The table: `permissions.py`

One row for each of the 45 tools (`permissions.TABLE`). `test_permissions.py` holds the table equal to
`actions.TOOLS`; a tool without a row is refused.

| Column | Meaning |
|---|---|
| `label` | The tool in plain words, as Settings shows it. |
| `effect` | `reads` or `changes`. A few changing tools only read for some actions (listing timers, a Spotify or microphone status): `read_actions`. |
| `reach` | JARVIS on this PC, the JARVIS window, this PC, the internet, or JARVIS itself. |
| `undo` | Whether and how it can be undone. Required for every tool that changes something. |
| `asks` | `no`; `your own words` (the Core checks the owner's own words in the question); `always` (approval on screen first). |
| `repeat_adds` | Done twice, it happens twice (a second note, timer, file, window). Within one question an identical call is never run twice (unchanged rule in `server.App.work`). |
| `wearable` | A wearable client may call it. Only reads are marked. |
| `evidence`, `receipt`, `preview` | Kept for the next question; counts as a receipt for the claim check; can be drafted with `preview_action`. |

The four lists other modules kept are now read from the table (`WEARABLE_TOOLS`, `ACTION_TOOLS`, `EVIDENCE_TOOLS`,
`PREVIEW_TOOLS`); a test holds them equal to what they were. `development.IMMEDIATE` is gone (section 4).

## 2. The one decision: `permissions.decide`, called in `server.App.tool`

Every tool call passes `App.tool`: the AI model's, a typed or spoken command's, the interface's own buttons
(`POST /api/tool`, no question attached) and an approval being carried out. Before anything runs:

1. **Emergency stop** (section 3): refused. Only the owner's own interface may still read JARVIS's own records.
2. **Device:** a wearable's question may call only the tools marked for it (as before).
3. **The owner's switch for the tool** (Settings > Permissions, table `tool_modes` in the database):
   - **Allowed** (default): as the table says.
   - **Ask first:** JARVIS keeps the exact call and asks on screen; it runs once on approval (5 minutes, single use).
     Offered for changes that today happen at once; not for a read, not for a tool that already asks or already
     needs the owner's exact words, not for what happens inside the window that asked.
   - **Off:** refused when JARVIS is answering, with a plain message, and the tool is not offered to the AI model.
   The switch can only make a tool stricter. It governs what JARVIS does when answering; the owner's own buttons in
   the interface are their own approval and still work. It is out of reach of the settings page, the JSON export and
   a restored JSON backup.
4. A refusal writes an activity row `refused`.

The owner's exact memory commands (`memory.py`: "remember that I prefer ...", "my name is ...", "forget memory: ...")
are answered without a tool call. `App.memory_command` asks the same table first (the switch of `save_item` or
`manage_saved_memory`), so Off refuses them, Ask first makes them wait, and each one now writes an activity row.

**Commands the window answers by itself.** A few exact commands never reach the Core as a tool call, because the
window answers them at once: opening a section ("open settings"), the microphone and floating-JARVIS words, a
timer's status, starting screen sharing, "inspect the settings page". They obey the same switches: the Core's state
tells the window which switches differ from Allowed (`permissions.changed`, `state.permissions`), and when the
matching tool is Off or Ask first, or the emergency stop holds, the window does not act and sends the words to the
Core, which refuses, asks first or answers (`JarvisPermissions.windowMay`). Words that only switch something off
(mute, stop speaking, hide the floating JARVIS, stop sharing) always work in the window.

A tool set to Ask first is offered to the AI model with one more sentence ("the owner has chosen to be asked on
screen ... say that it is waiting"), so the model does not announce it as done (`permissions.offered`).

Still decided where they were: the owner's-own-words checks of four tools (in `App.tool`), the argument checks
(`actions.validate`), the limits of one question (6 model rounds, 8 tool calls, 120 seconds).

## 3. The emergency stop that holds

- **Stop:** `POST /api/emergency-stop`. Cancels every running question and inspection, drops every waiting approval
  (nothing that was waiting may go ahead later without being asked again), and stays on. Saved in the database
  (table `control`), so it holds across a restart of the Core. Everything that stops things happens before the
  writing down; if the disk fails, the stop still holds in memory and the screen says it was not saved.
- **While it holds:** no question is accepted from any device, no tool runs, no approval is carried out or stored
  (the stop is looked at under the same lock that stores one), no inspection or repair experiment starts and a
  running one is cancelled (it can still be looked at and cancelled). The interface's own buttons that reach the
  internet are refused too (web search and its pictures, a route, the connection tests, speech, cloud
  transcription), nothing is spoken for a wearable, the window says nothing aloud, and the commands the window
  answers by itself wait as well. A question cannot slip in at the moment a stop arrives: the stop is looked at
  under the lock the stop itself takes. The
  optional phone bridge (`phone_bridge.py`, which nothing starts) reads the same record and refuses. The owner can
  still open the sections, read the activity log and the history of JARVIS's own changes, and use the interface's
  own editing buttons (notes, tasks, settings). Timers that come due still show their alert: they are the owner's
  own alarms.
- **Resume:** `POST /api/resume`, reachable only from the signed-in interface on the PC: the RESUME button in the
  banner or in Settings > Permissions, or Resume JARVIS in the tray menu. No tool, no wearable route and no spoken
  or typed phrase resumes. A resume that cannot be written down leaves JARVIS stopped.
- **Ways to stop:** STOP ALL under the header of every section and in Settings > Permissions; the tray menu
  (Emergency stop), the emergency shortcut and STOP ALL on the floating JARVIS (desktop app); or the words
  "emergency stop", "stop everything", "stop all" or "kill switch" as a whole message, typed or spoken, on any
  device (`permissions.STOP_PHRASE`; capitals and punctuation do not matter, but anything else in the message, a
  digit, an emoji or a word in another script, means it is not the stop: "stop all 3" is about three things; the
  window uses the same words, tests hold the two equal). The Core looks at those words before anything else about
  a question and answers them itself: no AI model, no tool; a wearable's stop words are never turned away as busy
  or over its limit (once JARVIS is stopped, repeating them is an ordinary request again and writes nothing more).
  - *Typed:* at any time, also while JARVIS is busy, in the Chat box and in the dashboard's ask box.
  - *Spoken, with the wake word on:* when JARVIS is idle; while it speaks in an open conversation (hands-free
    interruption); and while it works on an answer: the wake word stays alive then, so "Hey JARVIS" interrupts the
    answer and listens (`static/voice.js`, `thinking`), also when the conversation was already open. **Not
    heard:** while JARVIS speaks a reply outside an open conversation or with hands-free interruption switched off;
    during the seconds in which a spoken reply is being fetched; while the words just spoken are still being
    turned into text; and in push-to-talk mode unless the button is pressed. There the buttons, the tray and the
    shortcut are the way to stop.
  - STOP ALL in the window also ends screen sharing, as the tray and the shortcut do. The tray's Emergency stop
    and Resume JARVIS say so in a dialog when the Core did not answer.
- **On screen:** a red banner across the bottom of every section with the time, the device and RESUME JARVIS; the
  dashboard says "Emergency stop is on. STOPPED" instead of "At your service. STANDING BY" (`dashboard-model.js`);
  the Intelligence page says STOPPED instead of ONLINE. The window sets the visibility of the stop button, the
  banner and RESUME on the elements themselves, so the usual ways of hiding them in a style sheet do not work.
  That is a help, not a guarantee (section 4): the tray, the shortcut and the stop words do not depend on any style.
- `POST /api/cancel-all` still exists and still only cancels what runs now: the desktop app uses it when its window
  reloads or its interface is gone. The Stop button and Escape for one answer are unchanged.

## 4. JARVIS changing itself (`development.py`)

- **Every change asks first**, the personality and the style included, with the difference shown; undo asks too.
- **Two kinds of file.** The owner's files, `personality.txt` and `owner-style.css`, live in the config folder
  beside the key file: an update, a rollback or a reinstall keeps them. `owner-style.css` is the owner's own style
  sheet, served at `/owner-style.css` and loaded after every other style; it is empty until a change is approved.
  The program's files (`static/pro.css`, the interface and voice scripts, four Python files) can be changed after
  approval only when JARVIS runs from the source folder.
- **An installed JARVIS never changes its program files.** A change to one is saved as a proposal only (status
  `proposal only`), is never applied, and cannot be approved; the model is told to say so. Even a proposal record
  edited by hand to look approved is refused. The same holds for the owner's two files in the one odd layout where
  the config folder is the program folder itself (a data folder set without a config folder): nothing is written
  among the program files.
- **Proposals are kept with the data** (`<data>/development/`), not in the program folder.
- **A proposed style sheet sets only how things look.** In `owner-style.css` JARVIS may propose plain rules that
  set colours, fonts, text size (not below a readable size), spacing (no negative or very large values), borders
  and shadows. Refused when the change is proposed: everything else (display, visibility, opacity, position,
  transform, sizes, generated text, `::before` and the like, @-rules, anything loaded from outside, a backslash),
  and any rule that names the emergency stop, the approval cards or the Permissions switches. The AI model is told
  this. **This limits a style change; it is not a guarantee.** Text coloured like its background is still text
  nobody can read. What protects the owner is the difference shown before approval, Undo, and the ways to stop
  that no style sheet reaches: the tray, the shortcut, the spoken and the typed stop words.
- Undoing a personality change back to a text that a release shipped (the running one's or an earlier one's) keeps
  no private copy: the wording of the running release applies, now and after later updates. When that is not the
  text being restored (an undo made after an update), the approval card says so. An empty style sheet removes the
  file.
- **The copy the installer makes.** At the first install the installer copies the shipped personality into the
  config folder. A copy that is still word for word a text some release shipped was never changed by the owner, so
  the running release's wording applies instead of it (`runtime_paths.SHIPPED_PERSONALITIES`,
  `personality_file_for`); the file itself is left alone. So an everyday JARVIS installed before 1.0.15 gets the
  new wording ("changes to itself ask first") with the update, and a personality the owner really changed stays.
- What the model is told (`development.guidance`) and the tool descriptions say the same. The shipped
  `personality.txt` no longer says that style and personality changes apply without approval.

## 5. Activity rows

`audit` has two new columns, `run_id` and `device`. Every row written through `App.audit` names the device, and the
question when there is one; the activity log shows "this PC · question 8dc0a0". Older rows keep empty values. An
older JARVIS (after a rollback) can still write to the same database. A tool call refused for a wearable has its
row like every other refusal. The row of an exact memory command names the command ("memory command: Change or
delete a saved fact") and says "nothing changed" when it matched nothing. If the two columns cannot be added to an
older database, opening it fails loudly instead of losing rows silently (`store.py` looks first).

**After a rollback to 1.0.14 or older, the emergency stop and the switches are not enforced:** that program does
not know the two tables. The records stay in the database and apply again after the next update. The update plan
for the everyday JARVIS has to say this.

## 6. One contradiction, decided by the owner

Earlier records authorise style and personality changes **without** a prompt: the shipped `personality.txt` said so
("as authorized by Mr. Teague ... without repeated permission prompts"), `DESKTOP-ARCHITECTURE.md` records it, and
`test_automatic_actions.py` tested it. The master document (section 6) asks for approval of sensitive changes, the
capability plan lists this as decision D1 with "ask first" recommended, and the 1.0.15 scope list says "self-edits
ask first". Built: ask first for both.

**Decided: the owner's words "ask first" (2026-10-05, 23:40 local, 12:40Z), after asking "what do you recommend".**
Every change JARVIS makes to its own personality or style asks first, with the difference shown. That replaces the
earlier authorisation to apply such changes without a prompt; opening Calculator, Notepad or Paint without a prompt
is unchanged (the owner can set that tool to Ask first in Settings > Permissions). This settles D1 only; the rest
of the capability plan is still a proposal.

## 7. Not in this item

- Rules per device and pairing: scope item 4 (the table has the column a device rule will read).
- Usage limits per tool beyond the limits of one question; expiry of a permission.
- Stopping from a wearable by a dedicated route (the stop words already work from a wearable).
- Stopping a spoken reply by voice outside an open conversation (section 3 says when a spoken stop is heard).

## 8. Checked

`test_permissions.py` (32 tests: the table, the decision, the stop words, an older database, the stop through the
Core and the routes, ask first, Off, the memory commands, the wearable), `test_permissions_review.py` (24 tests: one
or more for each finding of the two reviews), `test_development_workflow.py` (source folder and installed layout),
`test_reliability.py` (the real-size connection test), `test_permissions_view.cjs` (the words on screen, the stop
words, which commands the window may answer), `test_voice_thinking_wake.cjs` (the wake word while JARVIS works),
`test_dashboard_model.cjs`, the desktop app's `backend.test.cjs` (stop holds in the shared Core for every joined app
until resumed). Sandbox preview Core (synthetic data, no keys): stop, banner, refusal of a question and of a tool,
history still readable, resume, an ask-first timer with its approval card, the stop by typed words, the activity
log; after the first review also: a section command sent to the Core when its switch is Off, the stop controls
staying visible under a style sheet written to hide them, the internet routes refused while stopped, "mute" still
working while stopped. Pictures: `docs/design/permissions-preview-*.png`.

Not checked: the tray menu, the shortcut, the floating JARVIS and the two new dialogs in the running desktop app
itself (their code path is covered by `backend.test.cjs`, not their buttons); anything through a real microphone,
so the wake word while JARVIS works is tested as logic only, not by voice.

## 9. Independent review (one reviewer, 2026-10-05): no high finding; 2 medium and 14 low, all applied

The reviewer read the change against this document, ran tests and small experiments in temporary folders, and
was stopped early on the owner's word. "Run" = reproduced by the reviewer; "read" = from reading the code. Each
finding is followed by what was done about it (the same night). Tests: `test_permissions_review.py`,
`test_voice_thinking_wake.cjs`, `test_permissions_view.cjs`.

**Medium**

1. **The stop words did not always work while JARVIS was busy** (read): the dashboard's ask box dropped every
   message while JARVIS was busy, and the microphone was not listened to while JARVIS worked on an answer.
   **Fixed:** the dashboard box lets the stop words through (`command-dashboard.js`). The wake word stays alive
   while JARVIS works on an answer and plays nothing: "Hey JARVIS" interrupts the answer and listens, so "Hey JARVIS,
   emergency stop" is heard (`voice.js`, callback `thinking` in `app.js`; never while a reply is fetched or spoken;
   wake requests that come back late or fail during that time are dropped instead of switching the microphone
   off). A spoken stop is no longer held back by a provider's rate-limit pause. Section 3 now says exactly when a
   spoken stop is heard and when not. **A side effect to know:** saying "Hey JARVIS" while JARVIS is thinking now
   interrupts that answer, as it already did while JARVIS was speaking in an open conversation.
2. **Commands the window answers itself were outside Off and Ask first** (read). **Fixed:** the window is told
   which switches differ from Allowed and sends the words to the Core when the matching tool is not Allowed or the
   stop holds (section 2; `permissions.js` `windowMay`, `app.js`, `inspection-client.js`).

**Low**

3. While stopped, some of the interface's own buttons still reached the internet, and a wearable could still
   have text spoken. **Fixed:** web search, route, connection test, speech and cloud transcription are refused
   while stopped; so is a wearable's speech request; the window does not speak (section 3).
4. An approval stored at the moment the stop arrived survived the stop (run). **Fixed:** one method stores every
   approval and looks at the stop under the same lock (`App.keep_approval`), in all three places.
5. A running repair experiment was not cancelled by the stop, and could not be cancelled while stopped (run and
   read). **Fixed:** the stop cancels it; its status and cancel requests are answered while stopped.
6. The stop words from a wearable were easy to miss (run). **Fixed:** the Core looks at the words before anything
   else about the request; the wearable bridge lets them past its busy lock and its 20-a-minute limit; capitals and
   punctuation no longer matter in either pattern ("Emergency stop?", "Emergency, stop.", "Hey, Jarvis, emergency
   stop." all stop); while stopped a wearable is told so plainly instead of the general refusal.
7. STOP ALL in the window left screen sharing on (read). **Fixed:** it ends screen sharing too.
8. The desktop app's stop and resume failed silently when the Core did not answer (read). **Fixed:** a dialog says
   that the stop did not reach JARVIS (or that only the running work was cancelled), or that JARVIS was not resumed.
9. A wearable's refused tool call wrote no activity row (run). **Fixed:** the older check is gone; the one gate
   refuses it and writes the row.
10. An approved owner style sheet could hide or relabel the stop and approval controls (read). **Fixed:** such
    rules and any backslash are refused when the change is proposed, and the window keeps the stop button, the
    banner and RESUME visible by itself (section 4). The second review showed that this first filter was easy to
    get around; what replaced it is in section 10.
11. A failed attempt to add the two activity columns was swallowed like "already there" (read). **Fixed:** the
    store looks first; only "already there" is let through.
12. "Installed" with the config folder equal to the program folder still wrote the program folder (run).
    **Fixed:** there the owner's two files are proposals only (section 4).
13. `phone_bridge.py` (which nothing starts) ignored the stop, and its activity row named no device (read).
    **Fixed:** it reads the same stop record and refuses; its row names the phone.
14. Wording that said more than the code:
    - an existing installation kept the old personality sentences in its private copy. **Fixed in the code:** an
      untouched copy of an earlier release's text gives way to the running release's wording (section 4);
    - undoing a personality change: **the sentence in section 4 now says what happens**;
    - `inspection_findings` is listed as a read but brings statuses up to date: **the row now says so**;
    - the activity row of a memory command: **now names the command and says "nothing changed"** (section 5);
    - `open_app` told the model "immediately; the user has authorized": **the description no longer says so, and
      a tool set to Ask first is offered with a sentence saying it waits** (section 2);
    - the Intelligence page showed ONLINE while stopped: **it says STOPPED**.
15. Line endings: four existing lines of `store.py` had gone from CRLF to LF. **Restored** (that block is CRLF
    again). `development.py` is wholly LF on purpose.
16. After a rollback to 1.0.14 the stop and the switches are not enforced. **Said in section 5; to be repeated in
    the release notes and in the update plan of 1.0.15.**

**Checked by the reviewer and found correct:** every model and command tool call passes `App.tool`; Off refuses even
with an approval; an approval is single use and carries out only what the Core kept; a draft of an ask-first tool is
asked about once; nothing but `POST /api/resume` resumes; the stop survives a restart, an unreadable record means
stopped, a failing disk still stops; the four derived lists equal the old ones; the repair prototypes still work
with a bare folder; an installed layout never writes program files, even with a hand-edited record; an older
database gains the columns; settings, export and import cannot reach the new tables; the new screen code writes
text, never HTML; the window's and the Core's stop words are identical; the generated request files match the code.

**Not reached by that review:** the desktop app's own buttons and a spoken stop through a microphone; a packaged
regression run; `tests/lifecycle_stage4` and `desktop/test/backend.test.cjs` (the author ran the latter); a full
pass over `static/app.js`; thread stress beyond two forced orderings; the edits made to `recovery.py` and
`switch_over.py` during the review (the owner's style sheet in backups).

## 10. Second independent review (one reviewer, 2026-10-05, of the fixes in section 9): no high finding; 2 medium and 7 low, all applied

The reviewer read the fixes against this document, ran the tests and its own experiments in temporary folders
(a made-up provider, no real one). What was done about each finding the same night; the fixes of this section were
not reviewed a third time.

**Medium**

1. The wake word was ignored while JARVIS worked whenever the listener was still armed from an open conversation
   (run). **Fixed** (`voice.js`: a detection during the pause re-arms), with a test for that state.
2. An owner style sheet could still hide, relabel or cover the stop and approval controls (14 examples accepted by
   the first filter), and two sentences here promised otherwise. **Fixed both ways:** `owner-style.css` now accepts
   only a list of properties and plain rules (section 4; the examples the reviewer listed and two dozen more, 36 in
   all, are refused in the tests), and the sentences say that this limits a style change and is not a guarantee.

**Low**

1. The looser stop words also stopped on "Stop all 3", "kill switch 2", "stop everything" with an emoji, or with a
   word in another script. **Fixed:** only punctuation and blanks are ignored (section 3).
2. Wake requests that piled up while JARVIS worked could switch the microphone off after an answer without speech
   (run). **Fixed:** the queue is emptied when listening resumes.
3. Undoing a personality change after an update: the card showed the old wording, the running release's wording
   applied. **Fixed:** no copy of an earlier release's text is kept, and the card says which wording will apply.
4. A question could slip in at the moment a stop arrived (run, forced ordering; older than these fixes), and the
   same for a repair experiment. **Fixed:** both are looked at under the lock the stop takes.
5. Repeating the stop words from a wearable piled up answers and chat rows without limit (run). **Fixed:** once
   stopped, a repeat is an ordinary request (the bridge's limits apply), writes no chat rows, and old answers are
   cleared.
6. Small gaps in the window. **Fixed:** a spoken "take a screenshot" obeys the stop; a changed switch reaches the
   window at once; a command the window may not answer, typed while JARVIS is busy, is said instead of dropped;
   the mode says "listening" when the microphone is armed after an interrupted answer.
7. Sentences that said more than the code: the "Not heard" list (two cases added), "nothing reaches the internet"
   (pictures for search results were still fetched: now refused, and the sentence lists what is refused), a test
   named in the wrong file. **Corrected.**

**Checked by this reviewer and found correct:** nothing is sent to the wake detector while a reply is fetched or
spoken; push to talk and hands-free interruption are unchanged; with default switches and no stop nothing changes
for the owner; the instructions and the tool list sent to the AI model are the same as before for an ordinary and
a wearable question (only an ask-first tool's description differs); approvals are stored in one place only; opening
an older database from six processes at once never failed; an owner's really changed personality is never ignored
or deleted; an installed layout writes no program file; no untouched line changed its line ending.

**Not reached by this review:** the running desktop app (the new dialogs, repeated shortcut presses); a real
microphone or a rendered page for the style examples; the full test set beyond six modules; whether the everyday
JARVIS's personality copy equals the listed baseline text (the live installation was not touched).
