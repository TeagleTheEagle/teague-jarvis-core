# JARVIS capability plan (proposed 2026-10-05, for the owner's approval)

Status: **PROPOSAL, not approved.** Asked for by the owner on 2026-10-05 ("how can we implement this?", then
"plan") after JARVIS described how it could improve itself, set goals, act on its own and acquire resources.
Written from the survey of what already exists (`docs/CAPABILITY-SURVEY-20261005.md`). Nothing here changes the
rules in `CLAUDE.md`, and `docs/ROADMAP.md` stays the record approved on 2026-10-02; section 6 says how the two
fit. Every stage starts only on the owner's word, and every stage reaches the everyday JARVIS the usual way: a
release, an independent review, the regression, the VM check, then the owner's approval of the update.

## 1. In short

Seven stages, each one tested before the next, in the order JARVIS itself suggested:

| Stage | What you get |
|---|---|
| 1. Measure first | A fixed set of real questions and tasks that every release is scored on, plus a true count of what JARVIS uses and costs. Without this nobody can show a later stage made JARVIS better. |
| 2. Better memory and documents | The right fact or file is found, JARVIS shows where it came from, and two facts that disagree are raised instead of one silently replacing the other. |
| 3. Dependable tools | Every action confirms that it really happened; a failure is said plainly and JARVIS tries another way; reminders reach you when the window is closed. |
| 4. Plans that last | Work with several steps survives a restart, shows its steps and what it waits for, and has a stop button. |
| 5. Bounded autonomy | JARVIS carries out a plan you approved, by itself, inside limits you set. Anything consequential still asks first. Everything is logged. |
| 6. Self-improvement in a sandbox | JARVIS proposes a change to itself; it is tried on a copy against the stage 1 scores; you approve; it ships as a normal release. |
| 7. Resources stay manual | JARVIS reports and stays inside budgets. Keys, accounts, payments and new services stay yours, by hand. |

Two limits, said plainly. The app cannot make the AI model itself smarter: how well JARVIS reasons is set by the
model it is given (today `qwen3.8-max` or `gpt-6-astra`). What this plan improves is what JARVIS knows at the moment
it answers, how reliably it acts, how long it can carry a job, and that each improvement is proven. The result is a
more capable and more reliable assistant, not a superintelligence. "Recursive self-improvement" here means an
engineering loop with your approval at every turn, not a system that rewrites itself unattended.

## 2. Two decisions first (found by the survey, checked in the code)

1. **JARVIS can already change two of its own files with no approval.** `development.py` line 17 lists
   `static/pro.css` (style) and `personality.txt` (the instruction text sent with every question) as applied at
   once. A change the AI model makes to `personality.txt` then shapes every later answer without you seeing it
   first. Eleven more files change after one approval click.
   **Decision D1.** (a) Every such change asks first and shows the difference (recommended), or (b) leave as it is.
   **Decided by the owner on 2026-10-05: "ask first"** (built in 1.0.15, `docs/PERMISSIONS.md` sections 4 and 6).
2. **Those tools write into the folder the program runs from.** In the installed everyday JARVIS that is the
   release folder, which is meant to stay exactly as tested: an edit there makes the installed build differ from
   the checked build, the installer's verify would flag it, and the next update would discard it. Whether this has
   ever happened on the installed 1.0.14 is not known (the live installation is not read).
   **Decision D2.** In an installed JARVIS, your style and personality changes are saved in the config folder
   (they survive updates; the Core already prefers `config\personality.txt`), and a change to a program file
   becomes a proposal only, until stage 6 exists (recommended). Fix it in 1.0.15, which is not built yet
   (recommended), or in a later release.

## 3. Before the stages: speed, and the right model for each job (asked 2026-10-05)

The owner, 2026-10-05: "is it possible that we could combine the openai api and qwen api and they work together
because jarvis took a bit to respond", and "the qwen api doesn't just offer the qwen 3.8 max it has others lets
use them". The owner's master document already says the same (section 3: `qwen3.8-max` "for more complex
reasoning/planning", `qwen3.8-flash` "for fast/routine requests once fully validated", multiple providers kept).

What is true today (code and Alibaba's pages, read 2026-10-05):

- JARVIS uses one AI provider at a time (`JARVIS_PROVIDER`), one model for everything, and no fallback.
- **Thinking is on for every Qwen request.** Alibaba's page lists `qwen3.8-max` and `qwen3.8-flash` as "thinking
  mode enabled by default"; JARVIS's Qwen adapter never sets `enable_thinking`, so the model thinks before every
  answer, including "what time is it". Thinking is billed as output.
- JARVIS waits for the complete answer before showing or speaking any of it (both adapters ask for one complete
  answer), and a question that uses a tool is two requests.
- Prices per million tokens, Singapore: `qwen3.8-max` 2.00 in / 6.00 out; `qwen3.8-flash` 0.15 in / 0.47 out
  (about a thirteenth), also with tools, pictures and a 1 million token window.
- **Measured by the owner on 2026-10-05** with `tools/host/Test-AiSpeed.ps1` (owner-run like Test-AiKeys, keys never
  shown; the same full JARVIS question to each choice; one sample each). A 150-word answer: `gpt-6-astra` 7.2 s;
  `qwen3.8-max` as JARVIS asks it today 11.9 s, of whose 485 output tokens 297 were thinking; `qwen3.8-max` with
  thinking off 5.8 s; `qwen3.8-flash` with thinking off 5.8 s. A question that needs a tool: 2.3, 3.1, 3.4 (a cold
  request) and 2.0 s. So the wait is mostly the default thinking, and `qwen3.8-flash` is cheaper but not faster.

  A second run the same evening gave 16.9 s against 6.2 s, and for a picture 7.1 s with thinking against 5.6 s
  without (so "thinking off" is accepted together with an image on this account).

Proposed (**Decision D3**). Built in the repo for 1.0.15 on 2026-10-05 as Settings > Answer speed. **The default
stays Deep, which is today's behaviour, until the owner says yes to Auto** ("auto default"); the wording is the
owner's to change:

| Job | Proposed |
|---|---|
| Everyday questions and commands | Qwen, fast: thinking off, and `qwen3.8-flash` if the numbers and the stage 1 scores show nothing is lost |
| Hard questions (planning, research, long documents, "think hard about ...") | `qwen3.8-max` with thinking on |
| Pictures and screen analysis | `qwen3.8-max` or `qwen3.8-flash`, whichever the measurement favours |
| Speaking | the Qwen cloned voice once a voice ID exists on the current Alibaba account (already built); Fish Audio until then |
| Listening | stays on this PC (offline Whisper); Qwen speech recognition as a cloud backup later |
| When Qwen refuses or is down (as on 2026-10-05) | OpenAI answers that question, and the screen says so |

How JARVIS chooses, as built: one visible setting, Answer speed: Auto / Deep / Economy. Auto keeps the main model
and answers without thinking first; "think hard about ..." (or "take your time", "think it through") gets a
thinking answer for that one question in every mode. Deep is exactly what 1.0.14 does. Economy uses
`qwen3.8-flash` for everything except pictures. Auto is recommended as the default on the strength of the
measurement above; whether it loses anything against Deep on everyday questions is what the stage 1 question set
will show ("let's not minimise or make jarvis less"), and each mode is one click away. Not proposed:
asking both companies at once (double cost, no better answer) or OpenAI for everyday questions (about ten times
Qwen's price). A later step for speed: showing a reply while it is being written; it needs the checks that guard
JARVIS's claims to work on partial text, so it is not part of 1.0.15.

## 4. The stages

### Stage 1: measure first (in detail)

- **A fixed question set**, about 50 cases in groups: memory (remember, correct, forget, recall), documents (find
  the right passage), tools (the right tool is asked for with the right details), honesty (no "done" without a
  tool result; a failed tool is reported; instructions hidden in a document or web page are not obeyed),
  conversation (follow-ups, formatting), speed (seconds per reply), voice (the offline speech check that exists).
- **Scored by rule, not by opinion.** Each case states what must be true afterwards (this tool was asked for, this
  fact is in the answer, this false claim is not, this row exists). A case that needs judgement is marked "read by
  a person" and is not counted in the score.
- **Run against a sandbox Core with made-up data**, never your data and never the live installation, with the real
  AI model, because real answers are what is measured. That needs a key. **Decision D4:** (a) you place a test key
  file in the workspace once, as `CLAUDE.md` already allows, and Claude runs the set when needed (recommended;
  Claude never reads or prints the file), or (b) you start every run yourself with a launcher.
- **Cost of one full run** (estimate from the prices above and in `docs/AI-PROVIDER-PLAN.md`): about 1 to 3 US
  dollars on `qwen3.8-max`, a few cents on `qwen3.8-flash`, 10 to 14 dollars on `gpt-6-astra`.
- **Kept over time:** a result file and a one-page report card per release (score per group, seconds, tokens,
  estimated cost), stored beside the release's other records, so releases can be compared.
- **In JARVIS itself:** tokens used are recorded per day from the provider's own figures (today nothing in the Core
  counts them) and shown in Settings and on the dashboard with a month estimate; reply timings are kept across
  restarts (today the last 20, lost on restart); the HELPFUL / NOT HELPFUL ratings, stored today and never read,
  get a list you can open, and the "not helpful" ones become candidates for the question set.
- **Done when:** the set runs end to end twice and the spread between the two runs is recorded; its own tests run
  in the release regression with a stand-in provider (no paid calls there); the release notes of every later
  release carry the scores.

### Stage 2: better memory and documents

A relevance threshold (today the 20 slots are filled even with unrelated facts); "I like blue" against "I like
cyan" is raised as a conflict and asked about; every recalled fact shows where it came from; long documents are
kept in passages and searched in full (today the first 30,000 characters, whole); relevant notes and tasks are
offered to the model (today only through tools); tests for document search (none today). Search by meaning
(embeddings) only if the stage 1 scores show word matching is not enough; local or Alibaba is decided then.

### Stage 3: dependable tools

Every tool failure goes back to the model as a plain error it can act on (today anything but two error types ends
the reply with "The request failed internally"); one retry for a network hiccup; every acting tool confirms the
result from the Store or the system, not from the model's words; reminders raise a Windows notification when the
window is closed; recurring tasks recur (today stored, never acted on); tools can be used together with a picture
(today a request with an image gets none). **For your decision at that stage:** one table of which tools act at
once and which ask first (today only previews and code changes ask).

### Stage 4: plans that last

A job table in the one Store and a scheduler inside the one Core (no second Core, no separate service). A plan
shows its goal, steps, state and what it is waiting for, in Tasks, with a stop button; after a restart it carries
on without repeating a step; the daily briefing fires from the Core, not from an open page. At this stage a plan
moves one step at a time on your word. Roadmap Phase 3 (automatic backups) uses the same scheduler.

### Stage 5: bounded autonomy

You approve a plan together with its limits: which tools, how many AI requests, until when. Inside those limits
JARVIS works unattended, but only with actions that can be undone inside its own data (notes, tasks, documents,
searches). Anything else pauses and asks: files elsewhere on the PC, opening programs, anything sent or spent. One
switch pauses everything; every step is in the activity log; a daily cap applies; JARVIS may suggest a goal and
never adopts one by itself; text inside web pages and documents is information, never an instruction.

### Stage 6: self-improvement in a sandbox

JARVIS notices a weakness (a failed case, a "not helpful" rating, an error), drafts a change, and the change is
tried on a sandbox copy against the stage 1 scores. Two kinds. Its own wording and style: you see before and
after with the scores, approve in the app, it is saved in the config folder, and undo exists. Program code: JARVIS
writes a proposal (the change, the reason, the evidence) into a folder; it becomes part of JARVIS only through a
normal release. JARVIS never runs code it wrote, and never edits the installed program, its tests, the question
set or its own permission rules. The prototypes that exist (`repair_*`, `improvement_experiment.py`) work on one
toy example; they are reused here or archived at the clean-up.

### Stage 7: resources stay manual

From stage 1 JARVIS knows what it uses. Here it warns at limits you set, estimates what a plan will cost before it
starts, and stops at a cap. It never buys, signs up, enters payment details, handles a key or raises its own
limits; those stay yours, by hand.

## 5. Order of releases (proposed)

1. **1.0.15** (in progress, not built): the new look, the provider clean-up, formatted replies, the remaining
   items in `docs/CURRENT-STATUS.md`; with your word also D1/D2 and the first speed step of section 3.
2. **The installer** (`JARVIS-Setup.exe`), asked for twice ("a download app not a short cut"): one file to
   double-click, per user, no administrator rights. Windows shows "unknown publisher" unless a code-signing
   certificate is bought (your purchase, your decision); putting the file online is your step; the VM check learns
   to install from it.
3. **Stages 1 to 7**, one release each, in this order.

## 6. How this fits the approved roadmap

The roadmap's remaining phases stay as approved: Phase 2 clean-up, Phase 3 automatic backups, Phase 4 device
pairing and the phone, Phase 5 glasses. Proposed placing (**Decision D5**): automatic backups no later than stage
4 and before stage 5 (drive E: holds no current backup of JARVIS's data today, see `docs/CHAT-REVIEW-20261005.md`);
the clean-up before stage 6; phone and glasses whenever you say, they do not depend on these stages.

One contradiction between records, reported and not chosen (**Decision D6**): roadmap Phase 2 says the release
ships "Qwen (primary) and one local model" with OpenAI retired; your decision of 2026-10-05 keeps OpenAI and Qwen
and the code has no local chat model. Confirm which one stands.

## 7. What needs your word

| Decision | Recommended |
|---|---|
| D1 changes to its own personality and style | ask first. **Decided 2026-10-05: "ask first".** |
| D2 installed JARVIS never edits its program files; customisations in the config folder | yes, in 1.0.15 |
| D3 models and speed | after the speed check, from the numbers |
| D4 key for the question set | a test key file in the workspace, placed by you once |
| D5 order against the roadmap | as in section 6 |
| D6 providers in the roadmap | OpenAI and Qwen |

Approve by replying "I approve the capability plan", with changes if any; the approval is then recorded here. Each
stage still starts only when you say so.
