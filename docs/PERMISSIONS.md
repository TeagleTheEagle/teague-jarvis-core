# Permissions in one place (release 1.0.15, scope item 3)

Built 2026-10-05 in the repo only. Master document sections 6 and 18: every action capability-scoped, attributable,
revocable and auditable; reading and changing told apart; sensitive changes ask first; a kill switch.

**Status (2026-10-05, late evening): built, tested and committed. The independent review found no high finding;
its 2 medium and 14 low findings are listed in section 9 and are NOT applied yet (the owner asked for a stop). Until
they are, a few sentences below say more than the code does; section 9 names each one.**

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

Still decided where they were: the owner's-own-words checks of four tools (in `App.tool`), the argument checks
(`actions.validate`), the limits of one question (6 model rounds, 8 tool calls, 120 seconds).

## 3. The emergency stop that holds

- **Stop:** `POST /api/emergency-stop`. Cancels every running question and inspection, drops every waiting approval
  (nothing that was waiting may go ahead later without being asked again), and stays on. Saved in the database
  (table `control`), so it holds across a restart of the Core. Everything that stops things happens before the
  writing down; if the disk fails, the stop still holds in memory and the screen says it was not saved.
- **While it holds:** no question is accepted from any device, no tool runs, no approval is carried out, no
  inspection or repair experiment starts. The owner can still open the sections, read the activity log and the
  history of JARVIS's own changes, and use the interface's own editing buttons (notes, tasks, settings).
  Timers that come due still show their alert: they are the owner's own alarms.
- **Resume:** `POST /api/resume`, reachable only from the signed-in interface on the PC: the RESUME button in the
  banner or in Settings > Permissions, or Resume JARVIS in the tray menu. No tool, no wearable route and no spoken
  or typed phrase resumes. A resume that cannot be written down leaves JARVIS stopped.
- **Ways to stop:** STOP ALL under the header of every section and in Settings > Permissions; the tray menu
  (Emergency stop), the emergency shortcut and STOP ALL on the floating JARVIS (desktop app); or the words
  "emergency stop", "stop everything", "stop all" or "kill switch" as a whole message, typed or spoken, on any
  device, also while JARVIS is busy (`permissions.STOP_PHRASE`; the window uses the same words, a test holds the two
  equal). The Core answers those words itself: no AI model, no tool.
- **On screen:** a red banner across the bottom of every section with the time, the device and RESUME JARVIS; the
  dashboard says "Emergency stop is on. STOPPED" instead of "At your service. STANDING BY" (`dashboard-model.js`).
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
  edited by hand to look approved is refused.
- **Proposals are kept with the data** (`<data>/development/`), not in the program folder.
- Undoing a personality change back to the shipped wording removes the private copy, so a later release's wording
  applies again. An empty style sheet removes the file.
- What the model is told (`development.guidance`) and the tool descriptions say the same. The shipped
  `personality.txt` no longer says that style and personality changes apply without approval.

## 5. Activity rows

`audit` has two new columns, `run_id` and `device`. Every row written through `App.audit` names the device, and the
question when there is one; the activity log shows "this PC · question 8dc0a0". Older rows keep empty values. An
older JARVIS (after a rollback) can still write to the same database.

## 6. One contradiction for the owner

Earlier records authorise style and personality changes **without** a prompt: the shipped `personality.txt` said so
("as authorized by Mr. Teague ... without repeated permission prompts"), `DESKTOP-ARCHITECTURE.md` records it, and
`test_automatic_actions.py` tested it. The master document (section 6) asks for approval of sensitive changes, the
capability plan lists this as decision D1 with "ask first" recommended, and the 1.0.15 scope list says "self-edits
ask first". Built: ask first for both. The capability plan is not approved yet, so **D1 still needs the owner's
word**; if style changes should apply at once again, that is one small change, and the personality can keep asking.

## 7. Not in this item

- Rules per device and pairing: scope item 4 (the table has the column a device rule will read).
- Usage limits per tool beyond the limits of one question; expiry of a permission.
- Stopping from a wearable by a dedicated route (the stop words already work from a wearable).
- The existing "SAVE button floats over a row" in Settings: still on the 1.0.15 list; the Permissions category
  hides the Save bar because its switches save themselves.

## 8. Checked

`test_permissions.py` (32 tests: the table, the decision, the stop words, an older database, the stop through the
Core and the routes, ask first, Off, the memory commands, the wearable), `test_development_workflow.py` (source
folder and installed layout), `test_permissions_view.cjs`, `test_dashboard_model.cjs`, the desktop app's
`backend.test.cjs` (stop holds in the shared Core for every joined app until resumed). Sandbox preview Core
(synthetic data, no keys): stop, banner, refusal of a question and of a tool, history still readable, resume, an
ask-first timer with its approval card, the stop by typed words, the activity log. Pictures:
`docs/design/permissions-preview-*.png`.

Not checked: the tray menu, the shortcut and the floating JARVIS in the running desktop app itself (their code path
is covered by `backend.test.cjs`, not their buttons); a spoken "emergency stop" through the microphone.

## 9. Independent review (one reviewer, 2026-10-05): no high finding; NOT applied yet

The reviewer read the change against this document, ran tests and small experiments in temporary folders, and
was stopped early on the owner's word. "Run" = reproduced by the reviewer; "read" = from reading the code.

**Medium**

1. **The stop words do not always work while JARVIS is busy** (read). The dashboard's "Ask JARVIS anything" box
   drops every message while JARVIS is busy, with no exception for the stop words (the Chat box has one). Spoken:
   while JARVIS works on an answer the microphone is not listened to, so a spoken "emergency stop" is not heard then;
   it is heard while JARVIS speaks in an open conversation, or when idle. Section 3 says "also while JARVIS is busy":
   true for the Chat box and for the Core, not for the dashboard box or for speech during thinking. Fix: the same
   exception in the dashboard box; for speech, keep listening for the wake word while thinking, or say when it is heard.
2. **Commands the window answers itself are outside Off and Ask first** (read): "inspect the settings page" (starts
   an inspection that can send masked screenshots to the AI provider), the microphone and hologram words, "open
   settings", timer status. Section 2 says every call passes `App.tool`: these never reach the Core as tool calls.
   Fix: when the matching tool is not Allowed, let the text go to the Core.

**Low**

3. While stopped, some of the interface's own buttons still reach the internet (web search, a Maps route, the
   connection test, speech, transcription), and a wearable can still have text spoken. "Does nothing" in the banner
   is wider than the code. Fix: refuse those routes while stopped, or narrower wording.
4. An approval stored at the moment the stop arrives survives the stop (run: a self-change without a question, such
   as UNDO CHANGE, being prepared as the stop lands; with a question attached it is refused). Fix: check the stop
   under the same lock that stores an approval, in all three places.
5. A running repair experiment is not cancelled by the stop, and cannot be cancelled while stopped (run and read).
6. The stop words from a wearable are easy to miss (run): the conversation id is checked first; the bridge's busy
   lock and 20-a-minute limit apply; the refusal text is the general one. "Emergency stop?", "Emergency, stop." and
   "Hey, Jarvis, emergency stop." do not match and go to the AI model. Fix: check the words first; ignore
   punctuation in both patterns (`permissions.py`, `static/permissions.js`).
7. STOP ALL in the window leaves screen sharing on; the tray and the shortcut end it (read).
8. The desktop app's stop and resume fail silently when the Core does not answer (read). Fix: a dialog.
9. A wearable's refused tool call writes no activity row: an older check fires before the gate (run).
10. An approved owner style sheet could hide or relabel the stop and approval controls (read). Not verified: an
    escaped `url(` passing the filter. Fix: refuse backslashes and rules for those controls in `owner-style.css`.
11. A failed attempt to add the two activity columns is swallowed like "already there" (read). Fix: look first.
12. "Installed" with the config folder equal to the program folder still writes the program folder (run:
    `JARVIS_DATA_DIR` set without `JARVIS_CONFIG_DIR`). A real installation and the sandbox preview set both.
13. `phone_bridge.py` (which nothing starts) ignores the stop, and its activity row names no device (read).
14. Wording that says more than the code:
    - the installer seeds a private `personality.txt` in the config folder at first install, so an existing
      installation keeps the old sentences about applying style and personality changes without approval; only the
      guidance the Core adds contradicts them (the tools enforce the approval either way);
    - undoing a personality change removes the private copy only when the result equals today's shipped text; after
      an update, undoing an older change keeps the older wording;
    - `inspection_findings` is listed as a read but writes status events;
    - the activity row "memory command / completed" is written even when the command changed nothing, and does not
      say which command;
    - `open_app` still tells the model "immediately; the user has authorized" when the owner chose Ask first;
    - the Intelligence page shows ONLINE with no banner while stopped.
15. Line endings: four existing lines of `store.py` (59 to 62) went from CRLF to LF; `development.py` is wholly LF
    (rewritten on purpose). No other file changed style.
16. For the release, not defects: after a rollback to 1.0.14 the stop and the switches are not enforced (the older
    Core does not know the two tables), which the update plan must say.

**Checked by the reviewer and found correct:** every model and command tool call passes `App.tool`; Off refuses even
with an approval; an approval is single use and carries out only what the Core kept; a draft of an ask-first tool is
asked about once; nothing but `POST /api/resume` resumes; the stop survives a restart, an unreadable record means
stopped, a failing disk still stops; the four derived lists equal the old ones; the repair prototypes still work
with a bare folder; an installed layout never writes program files, even with a hand-edited record; an older
database gains the columns; settings, export and import cannot reach the new tables; the new screen code writes
text, never HTML; the window's and the Core's stop words are identical; the generated request files match the code.

**Not reached:** the desktop app's own buttons and a spoken stop through a microphone; a packaged regression run;
`tests/lifecycle_stage4` and `desktop/test/backend.test.cjs` (the author ran the latter: 52 pass); a full pass over
`static/app.js`; thread stress beyond two forced orderings; the edits made to `recovery.py` and `switch_over.py`
during the review (the owner's style sheet in backups).
