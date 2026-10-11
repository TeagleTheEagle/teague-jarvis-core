# Open-source sources for the five "game-changing" capabilities, and what they can give JARVIS (2026-10-07)

Status: **a research record and a proposal for the owner, nothing applied.** Owner's words (2026-10-07, 18:00 local),
with a screenshot of five headings from another AI chat: "go on github / python and find the most power codes to
apply these game changing skills to jarvis". The five headings: 1. Open-Ended, Radical Task Generalisation (Zero-Shot
Mastery); 2. Unprompted, Multi-Week Autonomy (Goal-Setting); 3. Continuous, Closed-Loop Self-Modification; 4.
Genuinely Novel Knowledge Creation; 5. Multi-Instance Strategic Cohesion (The Digital Swarm). A sixth item from the
same hour: an own JARVIS voice from an audio file (section 7).

## 0. Said first, plainly

- Code from GitHub gives JARVIS **mechanisms**: loops that plan, act, check and retry; libraries of skills that grow;
  evolutionary search that keeps what scores better; several agents that hand work to each other. It does not make
  the model behind JARVIS (Qwen 3.8 Max today) smarter than it is. The five headings describe what a research lab
  would call AGI properties; what can be built in JARVIS is the bounded version of each, on top of what 1.0.17 and
  the Workshop (release 1.0.18) already have. Where the bounded version is already there, this record says so.
- Everything below stays inside the rules: ONE CORE on the owner's PC; every tool call through `App.tool` with the
  owner's switches and the emergency stop; JARVIS's own program changed only through approved proposals; nothing
  installed into the shipped Python (packages go into the workshop's own environment); nothing runs on a schedule or
  for weeks without the owner having said so once, with a stop that holds.
- Licences matter for a shipped product: research code is often MIT or Apache (usable) while trained weights can be
  non-commercial (CC-BY-NC); each item names what was found.

## 1. Open-ended task generalisation ("zero-shot mastery")

**What it means in practice:** given a job it has never seen, JARVIS works out how, from its tools and from what it
did before, rather than needing a feature written for it.

**Strongest open sources**
- **Voyager (NVIDIA/Caltech, 2023; MIT; 7,000+ stars)**: the pattern that matters is the **skill library**: every
  job that succeeded is stored as executable code with a natural-language description, indexed by embedding; a new
  job retrieves the five most relevant skills into the prompt; an automatic curriculum proposes the next job.
  Minecraft itself is irrelevant; the library and the iterative "run, read the error, fix" loop are the point.
- **Hermes Agent (Nous Research, 2026)**: a persistent agent with cross-session memory and a self-improving skills
  system, the closest shipping example of a skill library for a personal agent.
- **OpenClaw (2026, TypeScript, ~390,000 stars)** and its Python rewrite **nanobot (~4,000 lines)**: the current
  reference shape of a personal autonomous agent (tools, memory, scheduled tasks, channels). Useful as a design
  reference, not as code to vendor (another stack).

**What JARVIS has:** 56 tools, the question loop (6 rounds, 8 tool calls), the Workshop missions (plan, act, check,
correct), lessons by words.

**What to build (proposal 1, "skills"):** a skill library in the Workshop: when a mission finishes with outcome
done, the model is asked to save the reusable part as a **skill** (a script or a command recipe with a description
and the words it answers to), kept in `<workshop>\skills\` with a row in the database; a new goal retrieves the
matching skills into the mission's context (as lessons are today); a skill that fails is marked and not retrieved
until fixed. This is Voyager's mechanism on JARVIS's existing loop. Small: the lessons table, the mission guidance
and the retrieval already exist; the new parts are the skill rows, the retrieval of code, and a Settings list.

## 2. Unprompted, multi-week autonomy (goal-setting)

**What it means in practice:** JARVIS keeps a standing goal, works on it in sessions over days or weeks, picks the
next step himself, and reports; the owner sets the goal once.

**Strongest open sources**
- **lythelab/autonomous-agent (2026)**: a self-hosted agent that runs for hours or days, plans with an LLM, runs
  code in a sandbox, keeps persistent memory, resumable sessions, an API, results-only output: the closest shape to
  a "standing goal" runner.
- **nac** (an orchestrator with episodes for long-running tasks) and **Kapso** (long-running optimisation of
  systems, learning from every run): patterns for staying aligned with intent over many episodes.
- **BabyAGI (2023)** is the ancestor: a task list the agent itself extends; its successors above add the memory and
  the resumption it lacked.

**What JARVIS has:** missions (one at a time, a time limit, the stop that holds), the routine (`nudges.py`: blocks,
notices, the clock that runs every minute), tasks and reminders, the always-present brief
(`docs/ALWAYS-PRESENT-JARVIS-BRIEF.md`).

**What to build (proposal 2, "standing goals"):** a goal the owner sets once ("learn my calendar's shape and warn me
of clashes", "keep the workshop's tests green"), kept in a table with its state, its next step and its log; the
routine's clock starts a bounded mission on it at the times the owner allows (never at night, never while the
owner is asking), each session ending with a report and the next step written down; the owner sees the goals in
Settings, pauses or ends any, and the emergency stop holds across restarts. "Unprompted" is bounded by the owner's
times and the mission limits; "multi-week" is the goal row surviving restarts. This needs no outside code: the
mission runner, the routine clock and the notices exist.

## 3. Continuous, closed-loop self-modification

**What it means in practice:** JARVIS changes his own program or prompts, tests the change, keeps what is better and
reverts what is worse, on his own.

**Strongest open sources**
- **Darwin Gödel Machine (Sakana AI and UBC, 2025; github.com/jennyzzt/dgm)**: a coding agent that rewrites its own
  code, keeps a growing archive of variants, evaluates each on benchmarks (SWE-bench 20% to 50%), and branches from
  the archive; the loop and the archive are the reusable ideas; it costs many model runs.
- **GEPA (gepa-ai/gepa; in DSPy as `dspy.GEPA`)**: reflective prompt evolution: execution traces are read by the
  model, which proposes prompt changes, kept on a Pareto frontier; 10 to 20 points better than other optimisers with
  35 times fewer runs. **DSPy** itself: programs whose prompts are compiled against examples.
- **Agentic Context Engineering (ACE, 2025)**: evolving the context (the playbook the agent carries) instead of the
  weights; the paper's method is what JARVIS's lessons and skills amount to when they are curated.
- **FRIDAY** (the owner's separate project of 2026-10-07): Try-Verify-Rollback over pytest and git, the same loop in
  miniature, already written and dry-run.

**What JARVIS has:** `development.py` (proposals to his own personality, style and program, always the owner's
approval first, undo in Release history), the Workshop missions with the same-mistake guard, the test suites.

**What to build (proposal 3, "self-improvement runs"):** inside the Workshop, a mission kind "improve" that works on
a **copy** of JARVIS's program (never the installed one): it may change the copy, run the copy's own tests, keep the
change only when the tests pass and a measured score improves (answer time, a benchmark of saved questions, a test
count), and files the result as a **development proposal** for the owner's approval (the existing door). The
Darwin Gödel loop with the owner at the gate. A prompt-evolution run (GEPA's idea) can be the first "improve" kind:
the personality text and the tool guidance scored against a set of the owner's own past questions. Closed-loop
in the workshop; the owner closes the loop on the real JARVIS. The owner decided on 2026-10-05 (D1) that personality
and style changes ask first; this keeps that.

## 4. Genuinely novel knowledge creation

**What it means in practice:** JARVIS finds something true that was not in his training or his notes: a better
algorithm, a measurement, a pattern in the owner's data.

**Strongest open sources**
- **OpenEvolve (algorithmicsuperintelligence/openevolve; on PyPI; the open AlphaEvolve)**: you give it a starting
  program and an evaluator that scores it; it asks the model for variants, keeps the better ones in an island-based,
  quality-diversity archive, and has found real speed-ups and state-of-the-art solutions (circle packing, GPU
  kernels). Python, language-agnostic in what it evolves.
- **The AI Scientist (Sakana, 2024 to 2025)**: ideas, experiments, write-ups end to end; expensive and research-grade.
- **FunSearch (DeepMind, 2023)**: the ancestor of OpenEvolve; the ideas are in OpenEvolve.

**What JARVIS has:** the Workshop (write a program, run it, read the result), web search, the owner's data (chats,
tasks, memory, the home-network list, the calendar, mail).

**What to build (proposal 4, "discoveries"):** OpenEvolve as a workshop skill: a mission kind "evolve" that takes a
problem the owner states with a measurable score (a function to make faster, a schedule to make better, a model of
the owner's own data to make more accurate), installs OpenEvolve into the workshop's own environment, runs it for
the mission's time, and reports the best program with its score and how it was measured. Honest words for the
owner: this creates **new programs that score better on a stated measure**; "genuinely novel knowledge" in the
scientific sense needs a measure, data and time, and the result is only as true as the evaluator.

## 5. Multi-instance strategic cohesion ("the digital swarm")

**What it means in practice:** several JARVIS workers on one goal, dividing it, handing work to each other, with
one memory and one owner.

**Strongest open sources**
- **OpenAI Agents SDK (2026, the successor of Swarm; Python)**: agents, handoffs, guardrails, sessions; the smallest
  clean set of primitives for one agent handing a conversation to another.
- **AutoGen / Microsoft Agent Framework (61,000 stars)**: group chat, sequential, concurrent and handoff workflows
  with checkpointing; **CrewAI (59,000)**: role-based crews; **MetaGPT**: software roles (architect, engineer, QA)
  over a shared message pool; **CAMEL**: role-playing pairs; **LangGraph (42,000)**: graphs of steps with state.
- **SwarmClaw** (2026): a self-hosted multi-agent runtime with sub-agent spawning, memory and schedules, the
  personal-assistant shape of the above.

**What JARVIS has:** one Core and one memory by rule; missions run one at a time; the Core already serves several
clients (the PC window, the phone, the glasses test client).

**What to build (proposal 5, "crews"):** inside one mission, **sub-workers**: the mission's model may split the
goal into parts and start up to N bounded sub-missions (each its own thread, tool calls, time share and log, each
through `App.tool`), then gathers their reports; the cohesion is the shared mission record, the shared lessons and
skills, and one owner's switches. The rule ONE CORE, ONE MEMORY holds: sub-workers are threads of the one Core
with the one database, never a second JARVIS. The OpenAI Agents SDK's handoff shape is the model to copy, not its
code (it binds to OpenAI's API; JARVIS speaks to Qwen through its own `providers.chat`).

## 6. Recommended order, and what each needs from the owner

| Order | Proposal | Size | Needs from the owner |
|---|---|---|---|
| 1 | Skills (section 1) | small, on the Workshop | nothing |
| 2 | Standing goals (section 2) | medium: a table, the routine's clock, a Settings list | the times a goal may run; "ask first" or Allowed for commands |
| 3 | Sub-workers (section 5) | medium: inside `workshop.Mission` | a limit on how many at once (proposed 3) |
| 4 | Self-improvement runs (section 3) | medium to large: a copy of the program, a score, the proposal door | the measure to score against; approval of every change, as today |
| 5 | Discoveries with OpenEvolve (section 4) | medium: a package in the workshop's environment, a mission kind | a problem with a measurable score; the model cost of long runs |

Each goes into a release after 1.0.18 through the same chain (build, checks, the VM, the everyday update), with one
independent review per item, as every item so far. None is started until the owner says which first.

## 7. An own JARVIS voice from an audio file (owner, 18:07: "is it possible to program our own jarvis voice instead of using external sources and use the audio file i sent")

**Yes, on this PC, with open-source voice cloning.** The file sent (`Downloads\v09044g40000c5772e3c77uamtl3pdu0.mp3`,
747 KB, 320 kbps, about 18.7 s) is long enough: zero-shot cloning models need 5 to 30 s of clean speech. Today
JARVIS speaks through Fish Audio or Qwen's cloud voice (`voice_engine.py`, profiles auto, fish, openai, qwen); a
**local** profile would speak from this PC with no provider, no key and no cost per sentence.

**Which engine:** this PC has an NVIDIA GeForce GTX 1660 Ti with 4 GB of memory. Of the current open models that
clone from a reference clip, **Chatterbox (Resemble AI, MIT, about 0.5 billion parameters, 2 to 3 GB of GPU
memory)** and **F5-TTS (MIT code; the weights CC-BY-NC, so not for a sold product; about 2 GB)** fit; **XTTS v2**
(Coqui, 4 to 6 GB) is at the edge of this card and showed out-of-memory on a 6 GB card in one test; **Kokoro**
(Apache, tiny, fast) does not clone. First recommendation: **Chatterbox** (MIT for the code and the weights, the
best blind-test scores among open models in 2026, built for conversational use), with F5-TTS as the fall-back.
Both need PyTorch with CUDA in the workshop's own Python environment (not the shipped one), about 3 GB on disk.
Speed: on a card of this class a sentence takes well under its own length to make (real-time factors 0.1 to 0.3 on
newer cards; to be measured here); the first sentence after a start has a model-load delay of some seconds, so the
engine stays loaded while JARVIS runs.

**What to build (proposal 6, "local voice"):** a voice profile **local** in `voice_engine.py`: the reference clip
kept in the config folder (`config\voice\reference.wav`, converted once from the MP3), the engine loaded once in a
helper process in the workshop's environment, sentences spoken through the same path as the cloud voices (the
window's playback, the phone's spoken replies unchanged), a Settings > Voice choice with a preview, the existing
`check_voice_offline.py` extended to prove it without the network. One independent review, then a release.

**Said plainly about the clip:** it is a download of someone else's recording. Cloning a voice for the owner's own
private assistant on the owner's own PC is the owner's choice; the clone must not be published, sold or used to
pass as that person, and the voice itself is not JARVIS's to ship to anyone else. A recording of the owner's own
voice, or a voice with a licence, has no such limit.

## Sources

- The best open source frameworks for building AI agents in 2026: https://www.firecrawl.dev/blog/best-open-source-agent-frameworks
- Top 20 GitHub repositories for AI agents in 2026 (stars): https://fungies.io/top-github-repositories-ai-agent-frameworks-2026/
- OpenClaw (Wikipedia): https://en.wikipedia.org/wiki/OpenClaw ; awesome-openclaw: https://github.com/rohitg00/awesome-openclaw
- The Darwin Gödel Machine (Sakana AI): https://sakana.ai/dgm/ ; the paper: https://arxiv.org/html/2505.22954v3 ; code github.com/jennyzzt/dgm
- OpenEvolve: https://github.com/algorithmicsuperintelligence/openevolve ; PyPI: https://pypi.org/project/openevolve/
- Voyager: https://arxiv.org/abs/2305.16291 ; the skill-library guide: https://aiunderstanding.org/learn/voyager-and-skill-library-agents
- lythelab/autonomous-agent: https://github.com/lythelab/autonomous-agent ; awesome AI agents 2026: https://github.com/caramaschiHG/awesome-ai-agents-2026
- GEPA: https://github.com/gepa-ai/gepa ; Agentic Context Engineering: https://arxiv.org/pdf/2510.04618
- Multi-agent frameworks compared: https://langfuse.com/blog/2025-03-19-ai-agent-comparison ; https://arize.com/guides/ai-agent-handbook/agent-frameworks/ ; https://resources.rework.com/tools/ai-agents/best-multi-agent-frameworks-2026
- Open-source TTS and voice cloning in 2026: https://localaimaster.com/blog/best-local-tts-models ; https://rarebuildsoftware.com/blog/best-open-source-voice-cloning-2026 ; https://gigagpu.com/xtts-v2-vram-requirements/ ; https://gigagpu.com/tts-latency-benchmarks/ ; https://www.resemble.ai/resources/best-open-source-ai-voice-cloning-tools ; https://localaimaster.com/blog/kokoro-tts-local-setup
