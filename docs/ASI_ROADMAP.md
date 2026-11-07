# JARVIS: the blueprint for an autonomous, self-improving assistant (proposal for the owner's approval)

**Date:** 2026-10-12. **Written by:** Claude Code (Opus 5.5), on the owner's request: "Inspect the entire JARVIS
codebase ... Evaluate our tools, memory architecture (Serena), and sub-agents. Produce a detailed step-by-step
architectural blueprint and actionable plan in ASI_ROADMAP.md explaining how to transform JARVIS into a fully
autonomous, self-improving, ASI-level personal AI assistant."

**Status: PROPOSAL, nothing approved, nothing built.** Nothing here changes the binding rules in `CLAUDE.md`.
It is one ordered plan that brings together three earlier documents:
- the approved `docs/VERONICA-MERGE-PLAN.md` (2026-10-12), which goes first and is unchanged;
- the unapproved `docs/CAPABILITY-PLAN.md` (2026-10-05, seven stages), whose stages this plan updates and replaces
  if the owner approves it;
- the unapproved `docs/MEMORY-ROADMAP.md` (2026-10-10), which this plan keeps as the detailed design of its memory
  phase, reconciled with the merge plan.

It was written from three read-only surveys of the workspace made today (the Core's architecture, the memory
systems, and the agents and their governance). The evidence is cited by file.

---

## 1. In plain words: what "ASI-level" can and cannot mean here

**Where JARVIS's intelligence comes from.** It comes from the AI model he calls. After the merge that is
OpenRouter: Qwen 3.8 Max for conversation and Claude Opus 5.5 for coding and research
(`VERONICA-MERGE-PLAN.md` D2). No code in this repository makes that model smarter than it is. "ASI" (a
superintelligence) is not something an application can be engineered into. Saying otherwise would be a promise
nobody can keep, and `docs/CAPABILITY-PLAN.md` section 1 already said the same on 2026-10-05.

**What the code controls is everything around the model**, and that is where the gains are:
1. **What he knows when he answers:** memory and recall.
2. **What he can do:** tools.
3. **How long he can carry a job:** durable jobs, a scheduler, roles that work in parallel.
4. **How much he may do without asking:** autonomy within limits the owner sets.
5. **Whether he gets better, and whether that is proven:** an evaluation set and a self-improvement loop measured
   against it.

Put together well, these make a very capable assistant. He would remember years of the owner's life accurately,
run research and projects for hours or days, watch for the things the owner cares about, and get measurably better
release after release, each step proven by scores.

**"Fully autonomous" in this plan means as autonomous as the owner chooses, area by area, inside limits.** These
stay in place:
- the emergency stop;
- approval for anything consequential: sending, spending, deleting outside JARVIS's own data, or changing JARVIS
  himself;
- the owner-only list in `CLAUDE.md`.

There are three reasons:
- **The binding rules require it:** `CLAUDE.md` OWNER-ONLY; `permissions.py`, where `development_*` always asks;
  "An installed JARVIS never changes its program files".
- **JARVIS reads text that strangers write**, in mail and on web pages. Text can carry instructions, so an agent that
  reads strangers' text and can also send mail or run commands unattended can be steered by them (section 7, risk 1).
- **Self-improvement without a fixed yardstick is drift, not improvement.** The yardstick (the evaluation set) and
  the owner's approval are what make the loop real.

**"Self-improving" in this plan means an engineering loop:**
1. JARVIS notices a weakness (a failed evaluation case, a "not helpful" rating, a tool error, a failed job).
2. He drafts a change.
3. The change is tried on a sandbox copy and scored.
4. The owner sees the before-and-after scores and approves.
5. The change ships in an ordinary release through the same checks as every release.

Wording, tool descriptions and memory rules can improve this way often. Program code improves the same way, built
by Claude Code into a release. JARVIS never edits his installed program, his permission table, his tests or his
evaluation set.

---

## 2. Where JARVIS stands today (evaluation, 2026-10-12)

### 2.1 Scorecard

| Area | Strong today | Holding him back |
|---|---|---|
| **Tools** (59; `actions.py`, `permissions.py`, `server.App.tool`) | One permission row per tool: reads or changes, reach, ask first, off. An emergency stop that holds. Outside text passes a guard (`content_guard.py`). Receipts for actions. A device boundary (`device_gateway.py`). | **Per-question limits:** 6 model rounds, 8 tool calls and 120 s per question (`server.py` ~1664-1783). **One question at a time** across the PC and every device (`server.py` ~945). **Error handling:** only `ValueError` and `ProviderError` come back to the model as usable errors; anything else ends the answer. **Structure:** the dispatch is a 53-branch `elif` chain in a 2,497-line `server.py`. |
| **Memory** (`store.py`, `memory.py`, `about_you.py`) | One SQLite store. Saving only on the owner's own words, checked in code (`server.py` ~1026). Release stamps on every fact. Backups with restore rehearsal (`recovery.py`, `auto_backup.py`). The You page. | **Recall:** keyword overlap only, always 20 facts, relevant or not (`memory.py` 48-52); no search by meaning; history is the last 40 messages (18,000 characters) with no summaries. **Corrections:** a fact with the same key is overwritten silently, deletes are hard, and nothing records what was replaced. **Privacy:** everything in context goes to the provider with every question, and secret detection is a pattern match. **Scale:** every question loads every memory. **Merge:** VERONICA's memory is a second, differently shaped store. |
| **Serena** | A good code-navigation tool for Claude Code sessions. It now works (fixed today, `.mcp.json`). | **Not JARVIS's memory.** It is a developer tool, nothing in the Core uses it, and its memory folder is empty. See 2.2. |
| **Agents and long jobs** | Workshop missions (`workshop.py`) have a plan step, a loop, time limits, the stop, and lessons kept from failures. VERONICA's research worker (`veronica/tasks.py`, `research.py`) has per-task cost caps, resume after a restart, schedules, and a citation check (`citations.py`). | **Missions:** one at a time, at most 180 minutes, 80 rounds and 60 calls; **no cost cap, no resume after a restart, no schedule**, cannot wait for an approval and continue, cannot save memory or send anything. **VERONICA's research worker:** the best long-running engine in the workspace, but on a separate stack (Deep Agents and LangGraph) that the merge plan does not carry over. **Sub-agent tool:** VERONICA's `task` tool does not work (`subagents.py`). **No planner across jobs** and no parallel workers. |
| **Self-improvement** | `development_propose/edit/rollback` ask first, every time; the installed copy changes only its personality and owner style. Lessons from failed missions. | **No yardstick:** no evaluation of answer quality at all; the unit tests use stand-in providers. **Write-only data:** "not helpful" ratings are stored and never read. **Repair prototypes** (`repair_*`, `improvement_experiment.py`) work on one toy fixture, and the sandbox is "blocked on host prerequisites". **Program changes** are proposals that nothing turns into a release. **Validation** of a change is a syntax check only. |
| **Evaluation and release** | 889 Python tests, 78 Node tests and 28 interface scripts. A release regression on the built release. Stage 7 in a clean virtual machine, approved by the owner every time. | **Nothing scores the answers themselves.** The 305 tests under `tests/` never run (that folder has no `__init__.py`). Stage 7 has no AI keys, so no conversation is tested. |
| **Governance** | Owner-only list, standing authority, approval records (`governance/`), one writer, the stop, the boundary keeping VERONICA's tools out of JARVIS's folders. | **Deny rules not in force:** `repo/.claude/settings.json` holds deny rules (no reading `.env`, no `git push`) that are not in force when a session starts at the workspace root, as sessions now do. **Tension in the workspace `CLAUDE.md`:** its "Autonomous Execution Guidelines" (added 2026-10-12 16:46, not in the status file) pull against the OWNER-ONLY "stop and ask". |

### 2.2 The four memories, told apart

| | What it is | Who uses it | Verdict |
|---|---|---|---|
| A. JARVIS's Core memory (`jarvis.sqlite3`) | Facts, chats, the You page, lessons, evidence | JARVIS, for the owner | **The one memory** (`CLAUDE.md`: ONE MEMORY). Phase 3 below rebuilds its recall. |
| B. VERONICA's memory (`veronica/data/veronica.db`) | Memories with free-text provenance; research checkpoints | VERONICA until she is retired | Her two memories move into A (merge plan, phase 2 item 5). Her checkpoint files are dropped. |
| C. Serena (`.serena/`) | A code index and notes for Claude Code sessions | Claude Code while developing | Keep it as a developer tool. Optionally record a code map in its memories. It never becomes part of JARVIS. |
| D. Claude Code's memory, the `CLAUDE.md` files and `docs/CURRENT-STATUS.md` | Instructions and hand-offs between development sessions | Claude Code | **Fragmented.** The workspace's memory folder is empty, the useful notes sit under old start folders, and `CURRENT-STATUS.md` is 275 KB. Phase 9 tidies this up. |

### 2.3 What the merge plan already fixes

The approved merge plan (phases 1 to 4) already does several of these things:
- moves all AI to one OpenRouter key, with a fallback model;
- adds a second persona;
- brings VERONICA's checked research and project helper into the Workshop;
- removes the old providers.

The phases below build on top of it and do not repeat it.

---

## 3. The target architecture

Everything stays inside **the one Core and the one Store** on the owner's PC (`CLAUDE.md`: one Core, one memory,
many devices). No second Core, no second store and no second AI stack. "Sub-agents" are **roles run by the Core's
own job engine**, not separate programs.

```
   PC window · phone · wearable · Siri          (devices are clients; two personas: JARVIS, VERONICA)
                    │
        ┌───────────▼────────────────────────────────────────────────────────────────┐
        │  THE ONE CORE (127.0.0.1)                                                    │
        │                                                                              │
        │  Conversation ──► Context builder ──► Model router (OpenRouter: Qwen / Claude,│
        │      │             (memory recall,        fallback model, thinking budget,    │
        │      │              You page, evidence,   per-job model choice by score/cost) │
        │      │              lessons; budgets)            │                            │
        │      │                                           ▼                            │
        │      │                                   Tool registry (59+ tools, one entry   │
        │      │                                   each: schema · permission row ·       │
        │      │                                   handler · verifier)                   │
        │      │                                           │                            │
        │      ▼                                           ▼                            │
        │  Job engine ◄── Scheduler          Policy engine (permission table + budgets +│
        │  (durable jobs, steps, waits,      autonomy levels + emergency stop + taint)  │
        │   resume, cost caps, approvals                  │                            │
        │   that park a job)                               │                            │
        │      │   roles: Researcher · Project helper · Monitor · Briefer · Reviewer     │
        │      ▼                                                                         │
        │  Memory service: episodes (chats + summaries) · facts with validity and        │
        │  source · procedures (lessons) · documents; full-text + meaning search          │
        │                                                                              │
        │  Evaluation harness (personal question set, scored by rule) ◄── Improvement loop│
        │  (signals → draft → sandbox copy → scores → owner approves → release)           │
        │                                                                              │
        │  Ledger: tokens, cost, timings, outcomes (kept across restarts)                 │
        └──────────────────────────────────────────────────────────────────────────────┘
                    │ one SQLite Store (+ encrypted off-PC backups, owner's choice)
```

Design rules for every phase:
1. **Every action goes through one gate**, `App.tool` and then `permissions.decide`, whether the model, a job, a
   role or a device asked for it. A role can never have more than the owner's switches allow.
2. **Text from tools is data, never instructions.** The existing guard and taint rule (`permissions.TAINTED_MESSAGE`)
   extend to jobs and roles.
3. **No step without a yardstick.** Each phase must raise its evaluation group, or at least not lower any group,
   before it ships.
4. **Each item gets one independent review** with its findings applied, and each release goes through the owner's
   Stage 7 check, as today.
5. **No silent fallback to mocks** (`CLAUDE.md`).

---

## 4. The plan, step by step

The rough session counts are Claude Code sessions. Each phase starts only on the owner's word. Each phase is one
release, or part of one.

### Phase A: finish what is in flight (approved; first)

1. **Release 1.0.19 from `claude/main`:** the Workshop, the You page, the guard, the devices route, and today's
   `system_diagnostics` tool. Before release:
   - apply the 15 review findings on the You page that are still open;
   - merge `claude/release-1.0.18` into `claude/main`;
   - rename the release-notes entry.
2. **The merge plan, phases 1 to 4.** Phase 1 (OpenRouter in the Core) has uncommitted work in
   `D:\JARVIS-release-work\src-merge` (branch `claude/veronica-merge`, last touched 16:45 today). The next session
   reviews it, finishes it and commits it.
3. **Hygiene the later phases depend on:**
   - Make the repo's deny rules hold for sessions that start at the workspace root: a workspace
     `.claude/settings.json` mirroring `repo/.claude/settings.json`. That needs the owner's word, since it is outside
     `repo\`.
   - Replace `repo\.env` (today VERONICA's keys file) with JARVIS's own development key file. That is an owner step:
     Claude never handles keys.

### Phase 0: measure first (2 to 3 sessions; nothing else is proven without it)

From CAPABILITY-PLAN stage 1 and MEMORY-ROADMAP section 6, merged and brought up to date:

1. **`evals/` in the repo: the personal evaluation set.** About 80 cases in groups:
   - memory: remember, correct, forget, recall a year-old fact, refuse a secret;
   - tools: the right tool with the right arguments; a failure reported plainly;
   - honesty: no "done" without a receipt;
   - injection: instructions hidden in a mail or web page are not obeyed;
   - planning: a 5-step job with a wait;
   - conversation;
   - speed and cost.

   Each case states what must be true afterwards and is **scored by rule**. A case that needs judgement is marked
   "read by a person" and is not counted. About 20% of the cases are **held out**: the improvement loop of Phase 6
   never sees them.
2. **`evals/run.py`:** it starts a sandbox Core with made-up data in a throwaway folder (as
   `tools/release_regression.py` already does), runs the set against the real model through OpenRouter, and writes
   a report card: the score per group, seconds, tokens and cost.
   - The test key is placed by the owner in a git-ignored file. Claude never reads or prints it.
   - A run with a stand-in provider joins the release regression, so the harness itself is tested at no cost.
3. **The ledger in the Core:**
   - tokens and cost per answer from OpenRouter's own figures, kept by day;
   - reply timings kept across restarts (today the last 20, lost on restart);
   - the "not helpful" ratings listed, so they become candidate cases.

**Done when:**
- the set has run twice and the spread between the runs is recorded;
- the report card is in the release notes;
- the baseline is written into this document.

### Phase 1: tools that can carry more (3 to 4 sessions)

1. **A tool registry in place of the `elif` chain.** Each tool is one entry: schema, permission row, handler,
   optional verifier.
   - `actions.TOOLS`, `permissions.TABLE`, `docs/PERMISSIONS.md` and the request templates are generated from it.
   - A test holds them equal (today nothing checks the templates).
   - `server.py` loses roughly 300 lines.
2. **Every tool failure goes back to the model as a plain error it can act on**, including unexpected exceptions,
   with the type recorded in the activity log. The model may retry once, or try another way.
3. **Verified actions.** Every acting tool confirms its result from the Store or the system, not from the model's
   words. This extends `answer_evidence.action_guard`.
4. **Limits that follow the answer-speed setting**, set by evaluation scores rather than by guesses. For example:
   - Economy: 4 rounds;
   - Auto: 6 rounds, 8 calls (today's limits);
   - Deep: 12 rounds, 16 calls, 300 s.
5. **Read-only tool calls in one round run in parallel**, for example a search and a calendar read together.
6. **Long work leaves the question lock.** Anything over the limits becomes a job (Phase 4), so a question asked
   while a job runs still gets an answer.

**Done when:** the tools and honesty groups are at or above the baseline, and no group is lower.

**Progress (begun on the owner's word of 2026-10-12, before Phase 0 exists, so proven by tests only):**
- **Item 2: built and reviewed 2026-10-12.** A tool failing unexpectedly no longer ends the answer.
  - The model reads `server.tool_error_text`: the error's kind, never its text. A read says "try another way"; a change
    says "it may or may not have taken effect: do not repeat it".
  - Missions get the same words.
  - The failure is still marked in the run, with "before start" when it came before the tool began. The activity log
    records "failed: <kind>".
  - The review found no high issue; 1 medium and 4 low were applied. Tests: `test_tool_errors.py` (10).
- **Items 1, 3 and 5:** next. Item 1 (the registry) is best done after the merge plan's uncommitted phase 1 work is
  committed, since both touch `server.py` and `actions.py`.
- **Item 4:** its values wait for Phase 0's scores.
- **Item 6:** waits for Phase 4.

### Phase 2: the merge's skills on the new tool layer (inside merge plan phase 3)

No new work beyond the merge plan. Its checked research and project helper are built on the registry (Phase 1) and
the job engine (Phase 4) as those land, rather than as one-offs. Where the order allows, Phase 1 comes before merge
plan phase 3.

### Phase 3: memory that lasts a lifetime (about 10 sessions; `MEMORY-ROADMAP.md` is the detailed design)

The roadmap's design stands, with three things settled by later decisions:

1. **Search by meaning.** The roadmap preferred local ONNX embeddings. The merge plan has since chosen OpenRouter
   for all AI (D8: no local models), and the owner's test showed OpenRouter's `qwen3-embedding-8b` works. That is
   decision E3 below.
   - Local keeps everything on the PC.
   - OpenRouter is simpler but sends each memory's text out once, to be embedded.
2. **A `source`/provenance column** in `items`, needed anyway for VERONICA's memories (merge plan phase 2 item 5),
   and kept for every fact from then on.
3. **The 20-fact rule becomes a relevance threshold with a character budget.**

The steps, in the roadmap's order:
1. FTS5 full-text indexes over messages, items, documents and lessons. This replaces the unindexed `LIKE` search
   and the 500-lesson cap.
2. Embeddings stored beside the rows: numpy at first, `sqlite-vec` past about 100,000 chunks.
3. **Facts with validity:**
   - a new fact supersedes an old one rather than overwriting it, and the old one is kept with its end date;
   - a deletion leaves a tombstone;
   - two facts that disagree are raised with the owner and never silently merged.
4. **Episodes:** a nightly summary of each day's conversations (scheduled by Phase 4), so continuity no longer
   depends on the last 40 messages.
5. **A `recall` tool** for deliberate search: by meaning, by date, by person.
6. **Privacy:**
   - a "never send" class (PINs, door codes, account numbers) detected more broadly than today's pattern match,
     stored only for the owner, never put in context;
   - context budgets per kind of memory;
   - saved facts pass the same guard as other outside text.
7. **Off-PC, encrypted backups**, if the owner chooses (decision E9). Today every backup sits on the same PC.

**Done when:**
- the memory group rises clearly above the baseline;
- a year-old fact is recalled;
- no "never send" fact appears in context for an unrelated question;
- VERONICA's memories are in, marked as hers and dated.

### Phase 4: durable jobs and a scheduler (4 to 5 sessions; the engine for everything after)

From CAPABILITY-PLAN stage 4 and the Workshop's own "not built" list (`docs/WORKSHOP.md`), with VERONICA's best
ideas carried over without her stack:

1. **A `jobs` table and a `job_steps` table in the one Store:** goal, plan, steps, state, waits, budget, spend,
   owner and role.
2. **A scheduler inside the Core** (no separate service):
   - recurring jobs;
   - the daily briefing fired from the Core rather than from an open window (`static/app.js` 490);
   - recurring tasks that actually recur;
   - the nightly memory consolidation.
3. **Resume after a restart.** A job continues from its last completed step and never repeats one. VERONICA's lease
   idea is carried over: `tasks.py` uses a 120 s lease renewed every 20 s.
4. **Approvals park a job.** "Awaiting approval" pauses the job, the approval card names it (on the PC, or on a
   device that may approve), and the job continues after approval. Today a mission can only fail and say what waits.
5. **Cost caps per job and per day**, from the ledger (Phase 0), carried over from VERONICA's `GuardMiddleware`. A job
   stops at its cap and says so.
6. **Several jobs at once.** Read-only work runs in parallel; acting work runs one at a time per area.
7. **A Jobs page:** goal, steps, what it waits for, spend so far, and a stop button per job. The emergency stop ends
   all jobs. RESUME never restarts them by itself, as today.

**Done when:**
- a 3-hour research job survives a restart and an approval in the middle, and stays under its cap;
- the briefing arrives with the window closed;
- the planning group rises.

### Phase 5: roles, the sub-agents done right (3 to 4 sessions)

A **role** is a fixed recipe the job engine runs: a model (Qwen or Claude, chosen by evaluation score and cost), a
prompt, a tool subset, a budget, and a permission ceiling that can never exceed the owner's switches.

| Role | Does | Never |
|---|---|---|
| Researcher | Background research with checked citations (VERONICA's `citations.py` rule: every quote matches a page really fetched) | Sends or saves outside its report |
| Project helper | Works in folders the owner names: reads, edits, runs that project's tests, undo until the end of the job; VERONICA's `safety.py` rules | Touches JARVIS's folders, the installed JARVIS, or release and test folders (`CLAUDE.md` D1 amendment) |
| Monitor | Watches conditions the owner sets (mail from a person, a calendar clash, `system_diagnostics` attention items, a price on a page) and raises a notice | Acts on what it sees; it only tells |
| Briefer | Morning and evening summaries from mail, calendar, tasks and memory | Sends anything |
| Reviewer | A second model checks a plan, a report or a code proposal before the owner sees it | Approves anything; only the owner approves |

**The planner**, used when the owner gives a goal rather than a task:
1. It breaks the goal into jobs for roles.
2. It shows the plan with its budget.
3. It runs the plan once the owner approves.
4. It replans when a step fails and says why.

VERONICA's `task` sub-agent tool is not carried over (merge plan phase 3). FRIDAY is not connected: that was stopped
by Anthropic's safety system on 2026-10-10 and is not to be built.

**Done when:**
- the planning group passes;
- two read-only roles run at once without interfering;
- the Reviewer catches the seeded faults in its evaluation cases.

### Phase 6: bounded autonomy (2 to 3 sessions; the owner sets every limit)

From CAPABILITY-PLAN stage 5, made concrete:

1. **Autonomy levels per area** (mail, calendar, files, research, projects, money), set on the permissions page.
   The shipped level for every area is 1.

   | Level | What happens |
   |---|---|
   | 0 | Ask for everything |
   | 1 | Act alone on things that can be undone inside JARVIS's own data |
   | 2 | Act alone inside a plan the owner approved, within its budget |
   | 3 | Standing permission for a routine the owner named, for example "file my receipts every Friday" |

2. **The consequential set always asks**, at every level:
   - anything sent to a person;
   - anything spent;
   - anything deleted outside JARVIS's own data;
   - any change to JARVIS himself;
   - anything on the owner-only list.

   The one exception is a routine the owner named at level 3, with the recipients or targets fixed in it.
3. **Taint stops autonomy.** A job that has read outside text (mail, web pages, documents) cannot take a
   consequential action in that job without the owner, whatever the level. This extends the existing rule that
   tainted questions change nothing.
4. **Daily caps** on actions and spend. Every step is in the activity log. JARVIS may *suggest* a goal and never
   *adopts* one by himself. **Built 2026-10-13** (`goals.py`, `goal_propose`, docs/WORKSHOP.md): a suggestion is an
   approval card; yes makes a workshop mission; caps of 3 waiting and 5 adopted a day; no recursion, no taint.
   The same day `development.py` was widened: JARVIS may propose a change to any Core module, window or companion
   file (never the gateway, the permission table, the guard, the tests or the launchers); installed, it is a
   proposal for the engineer and the next release.

**Done when:**
- the injection group passes 100%;
- a week of the owner's real routines runs unattended with no consequential action outside an approval or a named
  routine (checked from the activity log).

### Phase 7: self-improvement, the measured loop (4 to 5 sessions)

From CAPABILITY-PLAN stage 6, with the evaluation harness now real:

1. **Signals:**
   - failed evaluation cases;
   - "not helpful" ratings;
   - tool errors from the ledger;
   - failed jobs and their lessons;
   - answers the owner corrected.

   Each becomes an **improvement candidate**.
2. **Drafts.** JARVIS drafts a change of one of four kinds:

   | Kind | What changes | Where it ends up |
   |---|---|---|
   | (a) wording | His instructions, tool descriptions, memory rules | Saved in the config folder; undo exists |
   | (b) routing | Which model or answer-speed for which kind of job | Saved in the config folder; undo exists |
   | (c) a new evaluation case | A case drawn from the failure | **Reviewed by the owner** before it joins the set |
   | (d) a code proposal | The change, the reason and the evidence, in a folder | Built by Claude Code into an ordinary release, through Stage 7 |

3. **Trial on a sandbox copy.** The draft is tried on a copy of the Core with made-up data (as `release_regression`
   already isolates) against the unit tests and the evaluation set, held-out cases included. The report card shows
   before and after.
4. **The owner approves on screen.** Kinds (a) and (b) are applied to the config folder. Kind (d) goes to Claude Code.
5. **What JARVIS never does:**
   - edit his installed program, his tests, his evaluation set or the held-out cases;
   - edit his permission table or the stop;
   - run code he wrote outside the sandbox.

   The `repair_*` prototypes are reused here or archived. Their WSL and podman sandbox is "blocked on host
   prerequisites", and setting those up is an owner step (decision E7).

**Done when:**
- three approved improvements have each raised a score on held-out cases;
- one rejected draft is on record with the reason.

### Phase 8: resources stay manual (folded into Phases 0 and 4)

JARVIS reports what he uses, estimates a job's cost before it starts, and stops at caps. He never buys anything,
signs up for anything, enters payment details, handles a key or raises his own limits. A monthly spend limit on the
OpenRouter key itself is the owner's step (merge plan section 6).

### Phase 9: engineering hygiene (spread over the phases)

1. **Split `server.py`:** the registry (Phase 1), routes by area, and the job engine in its own module.
2. **Take the Stage 4 test harness off the shipped path.** Today `stage4_*` modules ship, and `server.py` has 43
   `stage4` branches.
3. **The 305 tests under `tests/`:** make them run (an `__init__.py` and a runner) or archive them.
4. **`docs/CURRENT-STATUS.md`:** keep the last two weeks, and move the rest to `docs/status-archive/` (moved, never
   deleted).
5. **Developer memory:**
   - one Claude Code memory folder for the workspace, filled from the old start folders' notes;
   - optionally a Serena code map (its onboarding), so new sessions start fast.

---

## 5. Order and size

| Release | Contents | Rough sessions |
|---|---|---|
| 1.0.19 | What is on `claude/main` today, including `system_diagnostics` | 1 to 2 |
| The merged release | Merge plan phases 1 to 4 (OpenRouter, VERONICA as a persona, her skills, switch-over) | 8 to 10 (the plan's own estimate) |
| R1 | Phase 0: measure | 2 to 3 |
| R2 | Phase 1: tools | 3 to 4 |
| R3 | Phase 3: memory | about 10 |
| R4 | Phase 4: jobs and the scheduler | 4 to 5 |
| R5 | Phase 5: roles | 3 to 4 |
| R6 | Phase 6: bounded autonomy | 2 to 3 |
| R7 | Phase 7: the self-improvement loop | 4 to 5 |

In all, about **40 to 50 sessions** after the merge. Phase 0 can start alongside the merge, since it needs only an
OpenRouter test key. Phase 3 can swap with Phase 4 if the owner wants long jobs before better recall.

---

## 6. What "done" looks like for the whole plan

- **Measured:** every release carries a report card. No group falls, and the overall score rises release over
  release.
- **Remembers:** a fact from a year ago is recalled when it matters and never when it doesn't. Corrections keep
  their history.
- **Carries work:** jobs of hours or days survive restarts and approvals and stay inside their budgets. Several run
  at once.
- **Acts alone where allowed:** the owner's routines run unattended for a week with nothing consequential outside an
  approval or a named routine.
- **Gets better:** each approved self-improvement raised a held-out score, and each rejected one is on record.
- **Still safe:** the stop ends everything. Injection cases pass 100%. The owner-only list is untouched.

---

## 7. Risks, said plainly

1. **Mail plus autonomy is the biggest risk.** The owner's merge decision D4 sets `mail_send` to Allowed, which is
   not built yet. Put that together with:
   - mail and web pages read as input;
   - jobs running unattended;

   and a stranger's mail could instruct JARVIS to send private information out. Phase 6 item 3 (taint stops
   autonomy) is the defence. Decision E4 asks whether unattended jobs may ever send mail without a card.
2. **Cost.** Claude Opus for long jobs costs about US$4 in and US$20 out per million tokens. Without caps, one runaway
   job can cost more than a month of chat. Caps come in Phase 0 (the ledger) and Phase 4 (per job). The OpenRouter
   key gets its own limit (owner).
3. **One provider.** After merge plan D8, OpenRouter is the only door, and nothing answers offline. Jobs must fail
   clearly and resume, which Phase 4 provides.
4. **One database.** Memory, chats, switches and the stop share one SQLite file. Off-PC encrypted backups are
   decision E9, and a restore is rehearsed every release.
5. **Gaming the yardstick.** A loop that sees its own test can learn the test rather than the skill. The held-out
   cases, the owner's review of new cases, and the rule that JARVIS never edits the set are the defence.
6. **Privacy toward the provider.** Everything in context leaves the PC with every question. Phase 3 adds context
   budgets and the "never send" class.

**Not in this plan, and not to be built:**
- removing approvals or the stop;
- JARVIS editing his installed program, permissions, tests or evaluation set;
- connecting FRIDAY or any outside agent to write JARVIS's code;
- JARVIS acquiring keys, accounts, money or computing power;
- copying himself anywhere;
- opening JARVIS to the network beyond the owner's existing Tailscale door.

---

## 8. Decisions for the owner

Each decision has Claude's recommendation. The approval sentence accepts the recommendations unless the owner says
otherwise.

| | Decision | Recommended |
|---|---|---|
| E1 | This plan replaces `CAPABILITY-PLAN.md` as the umbrella; `MEMORY-ROADMAP.md` stays as Phase 3's design | Yes |
| E2 | Evaluation runs with a test OpenRouter key the owner places once in a git-ignored file (Claude never reads it) | Yes, with a small monthly limit on that key |
| E3 | Search by meaning: OpenRouter `qwen3-embedding-8b` (simpler; the text goes out once to be embedded) or a local model (stays on the PC; one more download) | Local, for privacy, unless the evaluation shows it clearly worse |
| E4 | May unattended jobs send mail without a card? | **No**: only a level-3 routine with fixed recipients. Cards stay for everything else, even with D4's Allowed for questions the owner asks himself |
| E5 | The shipped autonomy level per area | 1 (act alone only on what can be undone in JARVIS's own data) |
| E6 | Default caps | US$2 per job and US$10 per day, raised by the owner on the Jobs page |
| E7 | The sandbox for trying drafts: today's isolated-copy method (works now) or WSL and podman (stronger; needs host setup, an owner step) | The isolated copy first; WSL and podman when the owner sets it up |
| E8 | Order | As in section 5; Phase 0 alongside the merge |
| E9 | Off-PC encrypted backups (a destination the owner picks) | Yes, before Phase 6 |
| E10 | A workspace `.claude/settings.json` mirroring the repo's deny rules | Yes, now |

---

**To approve:** type **"I approve the ASI roadmap"**. This accepts E1 to E10 as recommended; add any changes, for
example "E3 OpenRouter" or "E4 yes". Each phase still starts only when the owner says so, and the merge plan goes
first.
