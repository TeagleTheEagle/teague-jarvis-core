# What JARVIS already has for the capability plan (survey, 2026-10-05)

Why this exists: on 2026-10-05 the owner showed two answers from the everyday JARVIS (twelve improvements; what
"recursive self-improvement, setting goals, acting autonomously, acquiring resources" would need), asked "how can
we implement this?" and then said "plan". Before writing that plan, one read-only survey agent went through the
code to find what exists for each part. This file is its report, kept so the plan can be written without repeating
the survey. **Nothing was run; behaviour is from reading the code at HEAD 8963d7c.** Claude checked the items
marked (checked) against the code afterwards; the rest is the agent's reading. The plan itself is not written yet.

Tags: WIRED = called by the running Core and reachable from the AI model or the interface. API-ONLY = a Core route
exists but nothing in the interface or the model calls it. TEST/CLI-ONLY = a script or a fixture.

Request path: `POST /api/chat` -> `App.start_run` (`server.py:173`) -> thread `App.work` (`server.py:425`).
Deterministic routes run first (`memory.command`, `actions.local_command`, `answer_evidence.command`,
`verified_status.status_question`); otherwise the provider loop: at most 6 model rounds, 8 tool calls, 120 s, one
run at a time.

## Two findings for the owner before any plan (checked)

1. **JARVIS can already change two of its own files with no approval.** `development.py:17`:
   `IMMEDIATE = ('static/pro.css', 'personality.txt')`. `personality.txt` is the base instruction text for every
   request, so a change the AI model makes to it applies to all later requests without the owner seeing it first.
   Eleven more files (`static/app.js`, `voice.js`, `index.html`, `mic-worklet.js`, `desktop/companion.*`,
   `wake.py`, `local_stt.py`, `voice_engine.py`, `maps.py`) can be changed after one approval click.
2. **Those tools act on the folder the Core runs from** (`server.ROOT`). In the installed everyday JARVIS that is
   the release folder, which the release design calls read-only and hash-verified. An edit there would make the
   installed build differ from the tested build, would be flagged by the installer's verify, and would be lost at
   the next update. Whether this has ever happened on the installed 1.0.14 is not known (not exercised, and the
   live installation is not read). No automatic test, restart or rollback follows an applied change.
   Recommendation for the plan: owner customisations (style, personality) live in the config folder (the Core
   already prefers `config\personality.txt`, `runtime_paths.py:94`), and in an installed release the tools
   propose instead of applying, until the sandboxed route of the plan exists. Owner decision.

## 1. Measurement and evaluation

There is runtime instrumentation and there are runtime claim-guards. There is **no scoring of answer quality, no
fixed question set, and nothing kept over time**.

- Response timing, WIRED: `Run.measurements` (`server.py:86`), `response.timing` events, `App.timings` (last 20
  runs, in memory, lost on restart; now with `completed`), the model tool `response_timings`, `GET /api/metrics`.
- Browser and voice timing, WIRED, in page memory only: `static/latency.js` (20 records: endpoint wait, STT, first
  token, TTS, playback), `voiceDiagnostic()` (30 entries), `local_stt.py` latency fields, the voice lab page.
- Claim guards, WIRED (filters on single replies, not scores): `verified_status.py` (`GUIDANCE` in every system
  prompt, `guard` replaces "tests passed / service works" claims without recorded evidence); `answer_evidence.py`
  (`evidence` event per reply, `action_guard` rewrites completion claims without a matching tool result, briefing
  sections labelled checked / stale / unverified / failed).
- Live checks, WIRED: `providers.live_health()` (real OpenAI model lookup or an 8-token Qwen completion, Brave),
  `connection_checks.check()` behind `POST /api/connections/test` (one real chat, voice, search or route call with
  latency; results in memory only).
- User ratings, WIRED but write-only: HELPFUL / NOT HELPFUL on every reply -> table `feedback`. **No code reads it.**
- `computer_run_tests` runs the Python unit tests only; no live-model answers.
- Closest to a fixed set: the Ollama shadow comparison (section 7), `check_voice_offline.py` (one sentence, two
  keywords), `tools/host/Test-AiKeys.ps1` (owner-run, one full-size request per provider, pass/fail).
- **Provider usage accounting: none.** `providers.py` never reads `usage` or token counts; no cost, token or
  monthly figure exists in the Core (section 6).

## 2. Memory and documents

Selection is **keyword overlap and recency; no embeddings** (`VOICE-AND-MEMORY.md` says so).

- `memory.py`, WIRED, no model: commands ("remember ...", corrections, "forget memory: exact text", "find memory").
  `relevant()` counts shared words (3+ characters, an 8-entry synonym table), ties by recency, returns the top 20
  with **no threshold** (unrelated items fill the slots).
- `store.py`: a new memory with the same normalised key overwrites the old one, latest wins, **no conflict flag**.
  "I like blue" and "I like cyan" are not seen as conflicting. `source`, `confidence`, `category` are stored and
  never used. Notes and tasks are not de-duplicated. Credential-looking text is refused in four places.
- Each model request carries: settings, up to 20 saved facts, the last 3 research result sets, up to 8 compact tool
  results, project context if the chat is linked, the last 40 messages trimmed to 18,000 characters, attachment
  text (30,000 characters, marked untrusted). **Notes, tasks and documents are not injected**; they come through
  tools (`list_items`, `research_report`, `project_read`).
- Past chats: `conversation_search` (SQL LIKE on up to 8 words) and `conversation_read`.
- Documents: whole text kept (30,000 characters, no chunking); `search_documents` sums raw word counts over every
  document, top 5 with an excerpt. Reached from the Files search, `research_report`, `project_read`.
- No test found for `search_documents`, `index_document`, `/api/documents/search`, `manage_saved_memory`,
  `research_report`.

## 3. Tools

- 45 tools: `actions.TOOLS` (`actions.py:33-80`) plus the interface inspection tool; dispatch in `App.tool`
  (`server.py:210-391`); arguments validated by `actions.validate`.
- Categories: interface control and inspection (6); items and timers (7); chats, projects, documents (8); web and
  media (9); this PC (6: system info, files, read file, run tests, open page, open calculator/notepad/paint);
  self-status and self-modification (9).
- A request with an image gets no tools. The wearable client gets 9 read tools. `POST /api/tool` lets the signed-in
  interface call a tool without the model (used for Change History and Undo).
- **Approval-gated: only `preview_action` and `development_*` on executable files.** Everything else acts at once
  (save_item, set_timer, create_file, project_*, open_app, computer_open_page, spotify, youtube, and
  `development_*` on `static/pro.css` and `personality.txt`). Approvals are in memory, single-use.
- Gates tied to the user's own words: `manage_timer`, `manage_saved_memory`, `save_item` for memory,
  `assistant_control` (exact command plus an interface acknowledgement within 30 s).
- Recording: `Store.audit` (the activity log), tool events with `checked_at`, `record_evidence` for 7 tools,
  `answer_evidence.receipt`, `ACTION_TOOLS` (16 tools checked by `action_guard`).
- Errors: only `ValueError` / `ProviderError` from a tool go back to the model; any other exception ends the run
  with "The request failed internally". **No tool retries.**
- No root test found for `Archive`, `manage_timer`, `manage_memory` or the inspection tools.

## 4. Planning, persistent tasks, background work

- Tasks, WIRED: priority, due, `recurrence` (**stored and shown, never acted on**).
- Timers and reminders, WIRED: fired lazily when `/api/state` is polled; alerts in the page only (toast and chime),
  **no Windows notification**, nothing while the page is closed.
- Projects: workspaces with links; model tools `project_catalog`, `project_link_chat`, `project_read`,
  `project_save_document`.
- **Task plans exist, API-ONLY and read-only:** `plan_task` stores objective, success criteria, blocker and
  depends_on (cycle check); `task_plan()` returns READY / BLOCKED / COMPLETED / MISSING with
  `execution_authorized: False` always. **No executor, scheduler or queue exists.**
- Background machinery that exists: the single chat run thread; `inspection_jobs.py` (in memory, one job, 900 s);
  the Ollama shadow thread; a speech warm-up thread. **No scheduler and no persistent job table.**
- Proactive: setting `proactive` (default off); a page timer sends "Give me my daily briefing" at `briefing_time`
  while the page is open.

## 5. Self-improvement and development tools

- What the assistant can change, WIRED: see the two findings above. Flow: `development_read` ->
  `development_edit` / `development_propose` -> validation (Python `ast.parse`; JavaScript syntax check that needs
  the Electron in `desktop/node_modules`, absent from a release; CSS braces) -> approval for executable files ->
  `development.apply` (re-checks hashes and syntax, writes the file) -> `development_rollback` (restores the
  earlier text if the file is unchanged since). Change History panel with UNDO.
- `update_history.py` records per-file hashes and changed-file lists (not contents) when `/api/state` is polled.
- Sandboxed loop pieces, **all TEST/CLI-ONLY except one API route, all hard-wired to one toy function**
  (`delay(seconds)`), all reporting `deployed: False`: `improvement_experiment.py` (isolated child process, 10-30 s
  budget), `repair_trial.py` (candidate checked by a numeric AST interpreter, never executed), `repair_sandbox.py`
  (rootless Podman in WSL: no network, read-only, 128 MiB, 15 s; whether WSL/Podman works today is not known),
  `repair_workflow.py` (baseline, one Core request, validation, second check, diff), `budgeted_repair.py` behind
  `POST /api/repair-experiment` (needs a confirmation string, a project budget and a linked task; nothing calls it).
- Documents on this topic already in the repo: `DEVELOPMENT-WORKFLOW.md`, `docs/BOUNDED-IMPROVEMENT-STAGE-1.md`
  (a five-step "path to greater autonomy", marked planned, not activated), `docs/COMMAND-OVERLAY-AND-NEXT-STAGE.md`
  ("one governed improvement loop" with the same four capabilities the owner asked about: goal formation,
  autonomous execution, self-improvement, resource management), `docs/STAGE-3-FUTURE-COMPATIBILITY.md`,
  `docs/REPAIR-CONTROLLER-STAGE-1.md`, `docs/REAL-REPAIR-TRIAL.md`, `docs/REPAIR-WORKFLOW-AND-PROJECT-PLANS.md`.

## 6. Budgets and resources

- `project_budgets.py`, API-ONLY and test-used: counts only `core_requests` and `container_checks` per project,
  with reservations (held -> started -> settled or released, 300 s lease). `cost_usd` is always None. Its own
  document says "Not a financial billing ledger". Nothing in the interface shows it.
- **No provider usage or spend is recorded anywhere in the Core.** Output caps exist (1,024 or 8,192 tokens), a
  history budget of 18,000 characters, per-run limits, upload limits, a wearable rate limit.
- HTTP 429 handling is the only cost-related behaviour (billing versus rate limit, per provider).
- Spend control is manual: estimates in `docs/AI-PROVIDER-PLAN.md`, a suggested Alibaba budget alert (owner step).

## 7. Shadow and alternative model experiments

- `ollama_provider.py`: a loopback-only adapter to a local Ollama (`qwen3:4b`) that only classifies intent.
- `ollama_shadow.py`, **WIRED and on by default**: for a small closed set of deterministic commands a background
  thread asks the local model to classify the same text, compares, and appends a line without the request text to
  `<data>/provider-shadow.jsonl`. Nothing returns to execution. If Ollama is not running, each eligible command
  ends in a logged "offline". Phase 2 (letting it route) is not started.
- `shadow_report.py`: CLI summary of that log.
- Providers in production: `openai` and `qwen` only, no automatic fallback.

## 8. Planning documents that exist

- `docs/ROADMAP.md` (approved 2026-10-02): Phase 0 Stage 6 (done), Phase 1 cutover and Stage 7 (done), Phase 2
  codebase clean-up and two providers, Phase 3 automatic backups, Phase 4 device pairing and the phone, Phase 5
  glasses. **No phase covers evaluation, memory, tools, planning, autonomy, self-improvement or budgets.** Its
  "Qwen plus one local model" differs from the code (OpenAI and Qwen, no local chat model).
- `docs/POST-CUTOVER-FIXES.md` open items: non-administrator install untested; a known limit of the uninstall.
- `docs/owner/JARVIS-MASTER-ARCHITECTURE.md`: no section on autonomy or evaluation; related design goals in
  sections 3, 6, 16-19 (approvals by capability, reversibility, kill switch, capability expansion model).

## Looks unused or prototype-only

- `improvement_experiment.py`, `repair_trial.py`, `repair_workflow.py`, `repair_sandbox.py`,
  `verify_repair_sandbox.py` (they ship in the release `app\` folder).
- `budgeted_repair.py` and `POST /api/repair-experiment`; the budget actions and `plan_task` through
  `POST /api/workspaces`; `task_plan` readiness (no executor).
- `shadow_report.py`, `probe_ollama_shadow.py`, `probe_desktop_shadow.py`; `ollama_shadow.py` is wired but only
  writes a log.
- `stage4_*.py`, `tests/`, `deployment_test/`, `stage4_native/` (Stage 4 test harness).
- `phone_bridge.py`, the `intelligence/` shell, `desktop_launcher.py` and the manual helper scripts.
- Stored but never used: the `feedback` table; task `recurrence`; memory `source`, `confidence`, `category`.
- `review/` (203 tracked files of historical candidates; its tests are outside the regression).
- Not determined: whether the everyday install has Ollama running or a shadow log; whether WSL/Podman works;
  whether the installed release folder is write-protected.
