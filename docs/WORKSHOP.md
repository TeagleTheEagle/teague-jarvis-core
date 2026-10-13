# The Workshop: JARVIS doing things himself on this PC (release 1.0.18)

Status: **BUILT in the repo on 2026-10-07 (Claude Code), on the owner's words "IMPLEMENT THESE ARE MANDATORY"** with
the pasted list: file system operations; terminal access; goal decomposition and planning; self-correction and
context loops; memory management (a short-term execution log, long-term lessons). Built while release 1.0.17's build 2
was under its checks, so it goes into the next release, **1.0.18** (1.0.17 is the tested build under acceptance and is
not changed by this). Independent review: the section at the end. Not in any release yet.

## In plain words

JARVIS now has a workshop: his own folder on this PC where he can read, write and delete files, run commands and
read their answers, keep his own Python environment for the packages a job needs, remember lessons from one job to
the next, and carry out a **mission** on his own: "Jarvis, start a mission: write a script that lists the ten largest
files in the workshop and make it run." He writes a plan, does the steps one by one, reads every result, fixes what
fails and runs it again until it works, within a time limit, and tells you when he is done. You can also type a
goal in Settings > Workshop and press START MISSION, watch the plan and the log there, stop it, and read or delete
the lessons he kept. Every tool a mission uses obeys its own switch in Settings > Permissions, and the emergency
stop ends a mission and its running command at once.

## The owner's five items and what was built for each

| The owner's item | Built as | Where |
|---|---|---|
| 1. File system operations: read, write, create, delete files autonomously | The tool `workshop_files`: list, read, write, append, delete, mkdir, move, inside the workshop folder and the folders you add. A replaced or deleted file goes to the workshop's recycle folder first (`.recycle`), so nothing JARVIS does to a file is lost. | `workshop.Folders`, `workshop.Files` |
| 2. Terminal/CLI access: run commands, run scripts it wrote, install packages with pip | The tool `workshop_run`: one command line at a time through cmd.exe, in a workshop folder, with a time limit (default 120 s, at most 600); the exit code, the output and the errors come back as data. `%JARVIS_PYTHON%` runs a script with JARVIS's own Python (the shipped packages). The tool `workshop_python` makes the workshop's own Python environment once (from the PC's own Python); after that `python` and `pip install` in a command use it, and never JARVIS's own. | `workshop.Runner`, `workshop.Interpreters` |
| 3. Goal decomposition and planning: a hidden "thought" step that breaks the goal into sub-tasks, then one sub-task at a time, inspecting each result | The tool `workshop_mission` (start): the mission first asks the model for a plan (JSON steps; the "thought"), records it, then runs the loop: model request, tool call, the whole result back to the model, next step. The plan and every step are written to the mission's own chat. | `workshop.Mission` |
| 4. Self-correction and context loops: a SyntaxError or ModuleNotFoundError is fed back, the agent changes its approach and retries until exit code 0 | Every `workshop_run` result carries the exit code, the errors and the note "Not done: read the errors, change the file or the command, and run again"; it goes back into the model's conversation at once, and the mission guidance says what to do with it. The same command line failing five times running is refused, so the loop cannot spin on one mistake. | `workshop.Runner.run`, `MISSION_GUIDANCE` |
| 5. Memory: a short-term execution log and long-term lessons learned | Short term: the mission's log (every tool call with its outcome, every step reported, kept in the mission record and its chat) and the model's own conversation during the mission. Long term: the tool `workshop_lessons` (save, search, list, delete) in JARVIS's database; the lessons a new goal's words match are given to the mission, and to an ordinary question in its context; a mission that did not complete leaves a lesson by itself. | `workshop.Lessons`, `workshop.Missions`, `Desk.context` |

## What is built

- **The folder** (`workshop.Folders`): `<install home>\workshop` for an installed JARVIS (beside `data` and `config`,
  so every update keeps it and the automatic backups do not carry it: it may hold a Python environment of thousands
  of files), `<repo>\workshop` in development (git-ignored), `<data>\workshop` for an isolated instance (the tests).
  Settings > Workshop lets the owner add other folders (the setting `workshop_folders`: full paths separated by
  semicolons; a folder that does not exist is ignored). Every path a tool names goes through `Folders.resolve`:
  relative to the workshop, or absolute inside an allowed folder, resolved with `os.path.realpath` (junctions and
  links lead where they really lead) and refused outside. A deleted or replaced file is moved to `.recycle` with a
  time stamp; the recycle folder is listed but never entered, written or deleted by JARVIS.
- **Files** (`workshop_files`): list (400 entries at most, depth 1 to 3; `.venv`, `__pycache__`, `node_modules`,
  `.git` and `.recycle` are listed as folders and not entered), read (UTF-8 text up to 2 MB, 200 lines a call with
  `next_line`, keys redacted as in `computer_read_file`), write (replaces; the old copy kept), append, delete,
  mkdir, move. File contents are returned as data with a note that they are not instructions.
- **Commands** (`workshop_run`): `cmd.exe /d /s /c "<line>"` started in a workshop folder, `CREATE_NO_WINDOW`, inside
  a **Windows Job Object** with KILL_ON_JOB_CLOSE (review finding 1): every process the command starts, detached or
  not, belongs to the job and ends with it, when the time limit or the stop ends the command and when the Core
  itself ends, so nothing a mission started outlives JARVIS; a program started in the background (`start /b`) is
  ended when its command ends and the result says so (a server to test is started, tested and stopped inside one
  command). The environment is this process's without any variable whose name holds KEY, TOKEN, SECRET, PASSW or
  CREDENTIAL, without `PYTHONPATH`/`PYTHONHOME`, with `JARVIS_PYTHON` (this Core's interpreter), `JARVIS_WORKSHOP`
  and UTF-8 output; when the workshop's `.venv` exists its `Scripts` folder is first on `PATH`. Output and errors are
  read as they come and only the tail is kept (nothing fills the Core's memory), redacted, the last 16,000 and 8,000
  characters. One command line at a time (several go in a script). An exit code other than 0 is `failed` with the
  note; the same command line failing five times running is refused until a file in the workshop changes through
  the file tool or a new mission starts (and failures are forgotten after fifteen minutes). Inside a question (not a
  mission) a command gets at most 90 s.
  **Said plainly (review finding 2):** the command line itself is not confined. It starts in a workshop folder and
  can reach everything on this PC the owner's account can, and the internet (`pip` does). What the Workshop does
  about it: a command line that names JARVIS's own config, data or program folders, the install home, `config.env`
  or `.env` (after `%LOCALAPPDATA%`-style variables are expanded, with either slash, case ignored) is refused as data,
  a net against the model's own mistakes, not a wall; the keys are out of the command's environment; and **the tool
  ships as "ask first"** (the owner's decision of 2026-10-07, "do both"): every command waits for the owner's
  approval on the PC before it runs, until the owner sets the switch to Allowed in Settings > Permissions (which a
  mission needs to run commands unattended). `permissions.Rule.shipped` holds that position; `permissions.effective`
  gives every tool's position as it stands (the owner's saved choice, else the shipped one), and the Core reads its
  switches through it. The panel, the permission row and the release note say the same.
- **Interpreters** (`workshop_python`): `status` names JARVIS's own Python, the workshop's environment when it exists
  and the PC's Python if one is installed (`py -3`, `python`, `python3`, never JARVIS's own and never the workshop's
  environment; the Store alias that is not installed answers with an error and is skipped). `make_venv` creates
  `<workshop>\.venv` with the PC's Python once; without a PC Python it says plainly that installing Python is the
  owner's step. Nothing is ever installed into JARVIS's own Python (the installer verifies every program file).
- **Lessons** (`workshop_lessons`, table `lessons`): save (8 to 600 characters, tags, deduplicated, never a key),
  search by the words of a query (scored by matching words), list, delete; `used` counts how often a lesson was
  given to a mission. Saved under the release that learned it.
- **Missions** (`workshop_mission`, table `missions`, class `Mission`): `start` (a goal of a few sentences) refuses a
  second mission while one runs, needs an AI provider key, is refused while the emergency stop holds. The mission
  runs on its own thread outside the question's limits, with its own `Run` (every tool call passes
  `server.App.tool`, so the owner's switches, the stop and the activity rows apply) that is not in `App.runs`, so the
  owner keeps asking questions meanwhile. Its chat `mission-<id>` holds the goal, the plan, every reported step and
  the result; it appears in Chats like any other. Bounds: the time limit (`workshop_minutes`, 1 to 180, default 15),
  60 tool calls, 80 model rounds; the oldest tool exchanges are dropped from the model's conversation past 160,000
  characters. The mission is offered the five workshop tools plus `web_search`, `time_now`, `calculate` and
  `computer_system_info`, each only if the owner has not switched it off. It ends on `finish` (outcome done or
  failed), on a reply without a tool call, on a limit, on an error, or on the stop; the end is a notice
  (`announce`, so the PC and a paired phone show and speak it like a nudge), an activity row (`mission started`,
  `mission finished|failed|stopped`) and the last line of its chat. A mission that did not complete leaves a lesson
  ("A mission did not complete: ...") so the next attempt knows.
- **The context of an ordinary question** gets `workshop.lessons` (up to four lessons whose words match the
  question) and `workshop.latest_mission` (while one runs or ended within a day), so "how is the mission going" is
  answered from the context and the tool. `conversation_context.TOOL_GUIDANCE` tells the model when to use the
  tools directly (one or two quick steps) and when to start a mission (several steps, corrections, waiting).
- **Settings > Workshop** (`static/workshop.js`, `workshop.css`; routes `GET /api/workshop`, `POST /api/workshop`
  with `start {goal}`, `stop`, `delete_lesson {id}`; the two settings through `/api/settings`): the folder and the
  recycle folder, which Python can run a script, the other folders, the time limit, the missions (a goal box and
  START MISSION, STOP THE MISSION while one runs, each mission's state, plan, last log lines, result and chat
  name), and the lessons with DELETE. The category "Workshop" sits between Music and Routine.
- **Permissions** (`permissions.py`): five rows, changes on this PC (`workshop_lessons` on JARVIS's own data); the
  reads (`list`, `read`, `status`, `search`, `list`, the mission's `status`, `list`, `progress`, `finish`) are read
  actions; `workshop_files`, `workshop_run` and `workshop_mission` are receipts for the claim check. Each can be set to
  "ask first" (a command then waits for the owner's approval on screen) or "off" (not offered to the model).
- **The emergency stop** ends the mission (its thread sees the cancel at its next step) and kills its running
  command; RESUME does not restart it. The Core's `/api/shutdown` does the same, so no command line outlives the
  Core.

## Limits, said plainly

- A mission is unattended, so a tool the owner set to "ask first" returns "awaiting approval" to the mission once;
  a second call of the same tool in that mission is answered "already waiting" without a new approval; the
  guidance tells the model to finish with outcome "failed" and say what waits. When the mission ends, the approvals
  it raised and their notices go with it (an approval given later would have run with no mission and no stop
  behind it: review finding 6). Commands ship as "ask first", so a mission's first command waits and the mission
  reports what waits; for unattended missions the owner sets "Run commands on this PC in the workshop" to Allowed
  in Settings > Permissions. Both positions are the owner's choice.
- `workshop_run` has no undo: a command that deletes or changes files inside the workshop is done when it is done
  (`workshop_files` keeps copies; a command does not). The folders the owner adds are open to commands too; JARVIS's
  own config, data and program folders, the install home and the folders holding them cannot be added (the panel
  says which were refused and why).
- The model decides what to run; the Workshop bounds where it starts, how long, with what environment and inside
  which job, keeps the owner's keys out of the environment and refuses JARVIS's own folders by name. It does not
  judge a command's purpose, and it cannot stop a command from reaching the rest of this PC or the internet.
- A mission that was running when the Core ended (a shutdown, a crash) is marked "stopped" at the next start, with
  the line "JARVIS was closed while it ran." in its chat and an activity row; nothing of it runs on (the Job
  Objects took its commands with the Core).
- Packages need a Python installed on the PC besides JARVIS's own (the shipped interpreter has no pip and takes no
  packages). On this PC one is installed; on a fresh PC the status says what to do.
- A mission's model conversation is trimmed from the oldest tool exchanges past 160,000 characters; a very long
  mission may lose early context (the plan and the goal always stay).
- Not built: a mission continuing after an approval; missions on a schedule; a mission started from the phone
  (the phone's "may use this PC's tools" tick lets it call the tool, as any PC tool).

The lessons and the mission records live in JARVIS's database (`jarvis.sqlite3`), so the automatic backups carry
them; only the workshop folder itself (the files, the environment, the recycle folder) is outside the backups.

## Goals JARVIS suggests (`goals.py`; owner's decision of 2026-10-13)

The owner asked that JARVIS and VERONICA "work and adopt goals on their own, just they have to ask". Built as:

- **`goal_propose` (goal, why)**: the model may suggest a goal it thinks worth doing (a job that keeps coming up, a
  problem it saw, an improvement to a project in the workshop). The Core keeps the suggestion as `proposed` and
  raises an **approval card**, the same card as every other approval: on the PC (Reliability > waiting approvals, and
  in the chat), and on a paired device the owner lets approve. The card and the suggestion wait a day
  (`goals.ANSWER_SECONDS`). Nothing starts before the owner answers; the tool's result tells the model so.
- **Yes** (`server.App.adopt_goal`): the goal is marked `adopted` and becomes a workshop mission, under everything a
  mission runs under: its time limit, its tool-call limit, the owner's switch for every tool it uses, the content
  guard and the emergency stop. A mission that cannot start (another runs, the stop holds) leaves the goal `failed`
  with the reason; JARVIS may suggest it again.
- **No**: the goal is kept as `declined`; the same goal is not accepted again for a week.
- **Caps, counted from the record** (not from the model's word): at most 3 suggestions wait at a time, at most 5 goals
  are adopted a day, never the same goal twice while it waits or within a week of a no.
- **No recursion**: a mission's tool set has no `goal_propose`, and a call from a mission is refused (work cannot
  propose more work). **Taint**: a question in which outside text tried to instruct the AI cannot suggest a goal at
  all. **Off**: the owner can switch "Suggest a goal of his own" off in Settings > Permissions.
- **At a Core start every waiting suggestion lapses** (the cards live in the Core's memory and did not survive it).
- The record (who suggested it, why, the owner's answer, the mission it became) is shown in Settings > Workshop under
  the missions. Tests: `test_goals.py`.

## Changes JARVIS proposes to his own program (`development.py`, widened the same day)

The owner also asked that they "have the ability to edit, improve, fix the core and themselves; they'll propose a
change but need my approval". The `development_read/propose/edit` tools, which asked first for every change already,
now reach **any Python module of the Core, any file of the window under `static/` and the companion's files**
(`development.allowed`). Protected, and refused by name: the action gateway and the approvals (`server.py`,
`actions.py`), the permission table, the guard (`content_guard.py`), `development.py` itself, the lock, the paths,
the database (`store.py`), `goals.py`, the tests, the launchers and the updater (`desktop/*.cjs`), and the tools.
An installed JARVIS applies none of them: a program-file change is saved as a **proposal only**, for the engineer and
the next release, which the owner approves as every release (ONE CORE, ONE JARVIS). Running from the source folder a
change applies after approval, with the difference shown, as before.

## Tests (`test_workshop.py`, 32; `test_workshop_view.cjs`)

The files (the recycle folder, nothing outside, an added folder, a binary file, the tool arguments); the runner (a
command and its exit code, a script with `%JARVIS_PYTHON%`, errors as data and the same-mistake guard, the time limit
and the stop, keys out of the command and its output, what is refused); the interpreters (status, the environment on
`PATH`, the probe skipping JARVIS's own and the workshop's); the lessons; the mission loop with a fake model (the plan,
the self-correction with a real SyntaxError fed back and fixed, the log, the chat, the notice, the activity rows, the
context; a plan in numbered lines; the time limit and the lesson a failure leaves; the tool-call limit; the stop
ending a running `ping`; a finish with outcome failed; a broken model); and the whole path through a real local
Core (the route, the settings, an added folder, a question using the tools under the switches "off" and "ask first",
a mission started from the panel through the real provider path with a fake Qwen answer, the emergency stop ending a
mission and its command, RESUME not restarting it). The panel's words in the view test. Real cmd.exe commands and
the test Python run; nothing else on the PC is touched.

## Independent review (one reviewer agent, 2026-10-07): 2 high, 9 medium, 10 low, all applied

The reviewer read the five new files and every changed hunk, ran one probe against the runner, and found:

**High.** (1) A program a command started in the background held the pipes after cmd.exe ended; the runner waited
for it without a time limit, the mission thread hung, and the stop could not reach the orphan. Fixed: every command
runs inside a Windows Job Object with KILL_ON_JOB_CLOSE; the stop ends the job; a detached program is ended with its
command and the result says so; the last wait has a limit and the pipes are closed from this side if Windows gave no
job (said in the result). (2) `workshop_run` was described as confined to the workshop while only its starting folder
was; the key file was one `type` away and the redaction is cosmetic against a transform. Fixed by honesty and a net:
the row, the panel and this record say what a command reaches; a command line naming JARVIS's own config, data or
program folders, the install home, `config.env` or `.env` is refused (variables expanded, either slash, any case);
the shipped default of the tool stays "allowed" (the owner's mandate of independence) with "ask first" one click
away, put to the owner.

**Medium.** (3) The trim could leave a tool reply without its request, which the providers refuse: whole exchanges
go now. (4) The same-mistake guard was keyed for the Core's lifetime: it resets when a file changes through the file
tool, when a mission starts, and after fifteen minutes. (5) A mission cut off by the Core's end stayed "running":
marked stopped at the next start, with its chat line and activity row. (6) An "ask first" approval raised by a
mission outlived its stop and would have run with no cancel: a mission's approvals and notices are dropped when it
ends, and a tool that answered "awaiting approval" once is answered "already waiting" after. (7) The PC's Python
under `Program Files` was never found (the probe split on spaces): fixed. (8) With OpenAI the reply budget of 1,024
tokens cut a file in two and killed the mission: a mission asks for 8,192 and a provider error is fed back to the
model once, three in a row end the mission. (9) A mission starting in the instant of the emergency stop ran the model
loop while the stop held: the stop is checked under the lock at the start and at every round. (10) `list` walked
junctions out of the workshop: a link whose real path is outside is not even named; one that stays inside is listed
as a folder and not entered. (11) Any folder could be added, the install home included: a folder that is, holds or
lies inside JARVIS's own config, data, program or install folders is refused, and the panel says why.

**Low.** (12) A question's command could hold the question for ten minutes: 90 s inside a question. (13) The mission's
stop killed a question's command too: the runner knows each command's owner. (14) The folders object was re-made in
place on every call: a new one is swapped in when the setting's text changes. (15) Every non-completion left a
"lesson" and every lesson reached every question: only the model's own diagnosis is kept, and a question's context
gets the lessons saved on purpose. (16) A command could run past the mission's time limit: its seconds are capped at
what remains, and a round with under five seconds left ends the mission. (17) A command's output was held unbounded:
read as it comes, the tail kept. (18) `.gitignore` had been normalised to LF: its bytes restored, the two lines added
with the file's own ending. (19) A no-op line and a test pinning finding 4 in the tests: fixed; the guard test now
shows the reset. (20) The panel: the goal box empties on an accepted start and gets its words back on a refusal; the
refused folders are shown. (21) The schemas against `actions.validate`: consistent, nothing to change.

The reviewer's verdict on the five mandatory items: all met in mechanism; the gaps named were 1, 2, 4, 7, 8, 10, 11
and 15, each closed above. Nine tests were added for the findings (`ReviewFixTests`, `ApprovalTests`); 32 pass.
