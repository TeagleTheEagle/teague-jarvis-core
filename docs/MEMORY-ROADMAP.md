# JARVIS long-term memory: technical roadmap (proposal for the owner's approval)

**Date:** 2026-10-10.
**Status:** PROPOSAL. Nothing in it is built, and nothing is approved.
**The owner's request:**

> "I want you to be able to save context and memories from our conversations so that you have an ever increasing
> understanding of who I am, what is important to me and how I work best. Can you create a technical roadmap of how I
> would build this. I want to keep the semantic layer under the UI and separate from the LLM, so that I could switch to
> a different LLM if needed. I do not want to build everything from scratch, so research open source products that I
> can leverage to do this."

**Research behind it (2026-10-10):** four research agents:
- the memory frameworks;
- the storage, search and embedding building blocks;
- the design patterns, safety and evaluation evidence;
- a read-only map of the JARVIS code.

The sources are listed at the end. Facts were checked against primary sources (repositories, PyPI, model cards, papers).
Vendors' own benchmark scores are marked as such, because several are publicly disputed.

---

## 1. In plain words

- JARVIS gets a **memory service** inside the Core, between the window or phone and the AI model:
  - it keeps every conversation;
  - it finds things **by meaning**, not only by matching words;
  - after each conversation, it **suggests** what it learned about you, and you approve or reject it;
  - over time it builds up three things: your profile (who you are), your priorities (what matters to you) and your
    working style (how you work best).
- **The AI model is only a worker the memory service calls.** All memories, their search index and their "meaning"
  numbers (embeddings) belong to JARVIS. They live in JARVIS's own database on your PC.
  - Switching from Qwen to OpenAI, or to anything else, changes nothing in the memory.
  - The meaning numbers are made on your PC by a small open-source model, not by Qwen or OpenAI.
- **Reused, not built from scratch:**
  - the search engine: SQLite full-text search and a vector search;
  - the meaning model and its runtime (ONNX Runtime, already inside every JARVIS release);
  - the design of how memories are pulled out of conversations, kept current and never silently overwritten, from Mem0,
    Graphiti/Zep and the research behind them;
  - the standard way for other AI apps to share the memory (the Model Context Protocol).

  JARVIS writes only the glue: when to learn, your approval cards, your Memory page, and the safety rules.
- **No complete memory "product" is adopted today.** Each one tested either needs a separate database server, keeps its
  own second memory store, owns the AI loop itself, sends usage data by default, or changes its interface often
  (section 4). The design keeps the door open: the memory service has one interface, and a product such as Mem0 can be
  put behind it later if it measurably does better on *your* conversations (section 8, Phase 4).
- **About ten long sessions in five phases**, each one tested and released through the normal chain. You approve the
  decisions in section 9 before Phase 1.

---

## 2. Where JARVIS is today (the code map, 2026-10-10)

- **One database file, `jarvis.sqlite3`.** It holds:
  - `messages`: every question and answer, kept;
  - `items`: saved facts, notes, tasks and projects;
  - `profile`: the You page, 1.0.19, under review;
  - `research`, `turn_evidence`, `documents`, `lessons`, `feedback`.
- **Everything is found by matching words; nothing is found by meaning.**
  - `memory.relevant()` scores facts by shared words and **always fills 20 slots, even when nothing matches**
    (`memory.py:48-52`).
  - Past chats are searched with SQL `LIKE`.
  - No embeddings exist anywhere in the code.
- **JARVIS learns only from explicit commands.** It saves on "remember …" commands. The new You page *offers* to keep
  something, and you approve each offer.
- **Signals nobody uses yet:**
  - the helpful / not-helpful ratings (`feedback`);
  - the `source` and `confidence` columns of saved facts.

  These are the raw material for "how you work best".
- **What every question carries:**
  - the personality and guidance;
  - 20 facts;
  - the You page summary;
  - the last 3 research results and 8 tool results;
  - up to 40 messages of history in an 18,000-character budget.

  The offline (local model) path gets less, and no You page.
- **The AI layer** (`providers.py`) is plain HTTP to OpenAI or Qwen's OpenAI-compatible endpoint. The context reaches
  the model as provider-neutral JSON, so the model is already swappable; the memory must stay that way.
- **What a release can carry.**
  - The release bundles its own Python 3.12 with no `pip`. Every package must be locked with hashes
    (`tools/build_release.py`), and every model file is pinned by SHA-256.
  - Already shipped: `onnxruntime 1.30.0`, `numpy`, `tokenizers`, `huggingface-hub`.
  - SQLite 3.49.1 has full-text search (FTS5) built in and can load extensions.
- **Owner rules that bind this design:**
  - **one memory**, inside the Core (`CLAUDE.md`);
  - **nothing saved silently** (1.0.19 item 4);
  - **a model download needs your permission**, with its file, source and size (1.0.19 list);
  - the **guard** (`docs/GUARD.md`): outside text never instructs the AI;
  - the permission switches and the emergency stop;
  - the backups (`recovery.py` copies the whole database and counts every table's rows).
- **Contradictions found, for you to settle (decision D1 covers them):**
  - The README says external embeddings are deliberately avoided.
  - `docs/CAPABILITY-PLAN.md`, never approved, allows embeddings only after measurements nobody has made.
  - The newer "build all of these" (2026-10-10) includes item 5, "search by meaning".
  - The same list says "no new dependency". This roadmap needs at least a model file, and perhaps one small package
    (section 5).

---

## 3. The design

```
  JARVIS window · phone · (later) other AI apps over MCP
                     │  Core routes and tools
  ┌──────────────────▼───────────────────────────────────────────────────┐
  │ MEMORY SERVICE (memory/ in the Core; one interface)                  │
  │  remember · propose · review · recall · profile · forget · export    │
  │                                                                      │
  │  write path: index every turn → after the conversation, extract      │
  │  candidates → dedupe / conflict check → YOUR REVIEW → keep           │
  │  read path:  profile + working style always · hybrid recall per      │
  │  question (words + meaning + recency + importance) · recall tool     │
  │                                                                      │
  │  Embedder (local ONNX model)  ←  fixed, owned by JARVIS              │
  │  Extractor (any AI model)     ←  only through extract(schema, text)  │
  └──────────┬────────────────────────────────┬──────────────────────────┘
             │ one SQLite file (backed up)    │ providers.py (Qwen / OpenAI / local)
  raw turns · memories with validity · profile · FTS5 index · vectors · tombstones
```

### 3.1 Three rules that keep the AI model replaceable

1. **The memory service never calls an AI provider directly.** It asks one narrow interface:
   `extract(schema, text) → validated JSON`. It is implemented on `providers.chat`, with the provider's strict JSON
   mode where it exists, and otherwise JSON mode plus validation and one repair attempt.
   - When a model cannot follow the schema, extraction **fails visibly** and nothing is saved ("never fall back
     silently", `CLAUDE.md`).
   - Prompts are versioned. Every memory records which model and prompt version extracted it.
2. **Embeddings are JARVIS's own**, made by a local open-source model that never changes with the chat model.
   - Each vector records the model, its revision, its dimensions and its runtime.
   - Changing the embedding model is a planned re-index job, never a silent mix of two models.
3. **What reaches the chat model is plain text or JSON** (the profile, the working style, the recalled items with
   their dates). Any model can read it.
   - The personal evaluation (section 6) is re-run whenever the model, the extraction prompt or the embedding model
     changes.

### 3.2 What is kept (four kinds of memory, from the research)

| Kind | What it is | Where it lives | How it is used |
|---|---|---|---|
| **Episodes** (what happened) | Every turn, verbatim, with time and conversation. Kept forever. Raw turns beat compressed summaries in the LongMemEval study | the existing `messages`, plus a `chunks` index table | Found by recall when relevant |
| **Facts** (who you are, what matters) | Short statements, each with a source, a confidence and a validity period (`valid_from`, `valid_to`). A newer fact *supersedes* an older one, and the older one is kept, never deleted (the Graphiti/Zep design) | a new `memories` table, in the same file | Found by recall; the important ones are promoted to the profile |
| **Profile** | The You page: people, dates, likes, goals | `profile` (1.0.19) | Always in context, capped |
| **Working style** (how you work best) | Short rules *you approved*, e.g. "prefers short answers, one step at a time" | `memories` with kind `style` | Always in context, capped (about 1–2k tokens with the profile) |

Every memory carries:
- **provenance**: the conversation, the turns, who said it, the extractor model and prompt version;
- a **status**: pending, approved, rejected, forgotten.

Forgetting leaves a **tombstone**, so the same thing is not learned again.

### 3.3 Write path: how JARVIS learns

1. **Every turn is indexed:**
   - full-text search at once;
   - the meaning vector by a background worker, which stops in the emergency stop like everything else.
2. **After a conversation goes quiet, and once a night, not while you wait:**
   - the extractor reads **only your own words** in that conversation;
   - it proposes candidates: a fact, a preference, a person, a date, a goal, a working-style rule, each with the
     evidence turns.
   - **Never from:**
     - web pages, mail, files or tool results;
     - any question the guard marked as tainted.

     Published attacks (SpAIware on ChatGPT, delayed memory injection on Gemini, MINJA, AgentPoison) planted
     instructions in assistants' memories through exactly that kind of content.
3. **Each candidate is checked against what is already kept**, by meaning plus words, and labelled: new, duplicate
   (dropped), update (supersedes an older one) or conflict.
4. **You review:**
   - a short daily card, "JARVIS learned 3 things about you today", on the PC and the phone: approve, edit or reject
     each one;
   - "remember …" still saves at once, as today.

   This answers the research finding that most memory errors start at extraction (HaluMem) and keeps the 1.0.19 rule
   "nothing saved silently".
5. **Never inferred:**
   - health, religion, politics, sexuality, ethnicity, union membership, genetic or biometric details (the GDPR
     Article 9 list);
   - JARVIS keeps such things only when you say so yourself.
6. **Nightly consolidation:**
   - merges duplicates;
   - writes a weekly "what happened" summary;
   - marks facts that look out of date;
   - proposes working-style rules from your corrections and your helpful / not-helpful ratings, e.g. "you shortened 3
     long answers this week: keep answers short?". Like every candidate, those wait for your OK.

### 3.4 Read path: how JARVIS remembers

1. **Always in context, small and capped:** the profile and the working-style rules you approved.
2. **Per question, a hybrid recall:**
   - full-text (BM25) and meaning (vector) results are joined by reciprocal rank fusion, then weighted by recency and
     importance;
   - superseded facts are left out unless the question is about the past;
   - questions with a time ("last month") are filtered by date;
   - **a relevance threshold applies**: nothing is added when nothing is relevant.

     Today's `relevant()` always adds 20 facts. The OP-Bench study found assistants over-use memories that are not
     needed.
3. **A `recall` tool** lets the AI model look deeper when the question needs it ("what did I say about the garage in
   August?").
4. **The guidance tells the model that memory describes you, not the answers you want to hear.** A CHI 2026 study
   found memory profiles made models agree with users far more (+45% for one model).

### 3.5 Your control

A Memory page (the existing Memory section, grown) holds:
- every memory with its source conversation;
- edit, forget and pause learning;
- "don't remember this conversation";
- export everything as JSON or Markdown;
- the review queue.

The phone gets the review card and the pause switch, as a request for the Mac session.

---

## 4. What to reuse: the frameworks, compared

| Project | Licence | Verdict for JARVIS | Why |
|---|---|---|---|
| **Mem0** (2.2.1, Sep 2026) | Apache-2.0 | **Design reference; candidate engine at Phase 4** | The most used memory library; in-process; LLM and embedder configurable. But it keeps its own vector store and history database (a second memory). Its current algorithm only *adds*, so contradictions pile up. Usage data is on by default (`MEM0_TELEMETRY`). Breaking changes are frequent. Its best scores come from its paid platform (*vendor*) |
| **Hindsight** (0.10.3, Oct 2026) | MIT | **Candidate engine at Phase 4** | Closest to "an understanding of who you are" (observations, mental models, reflect). Native Windows. But it runs an embedded Postgres process, it is young (0.x), and its benchmark is its own |
| **Graphiti / Zep** | Apache-2.0 | **Design reference** (facts with validity periods) | On Windows it needs a Neo4j server (Java). Small models break its JSON. Zep's free server is discontinued |
| **Cognee** (1.6.3) | Apache-2.0 | Not now | Fully embedded, with Windows wheels. But very heavy dependencies, usage data on by default, frequent breaking releases |
| **Letta** (MemGPT) | Apache-2.0 | No | Its Python server is retired. Its successor is an agent that owns the AI loop, so memory and model are not separable |
| MemOS, MIRIX, Memobase | Apache-2.0 | No | Need Docker, Postgres, Neo4j or Redis servers, or have pivoted to the cloud |
| LangMem | MIT | No | Releases stale (Oct 2025); tied to LangGraph |
| Supermemory | server not open source | No | Closed server with a document cap |
| Basic Memory | AGPL-3.0 | No | AGPL obligations if bundled; does no extraction of its own |
| MCP reference "memory" server | MIT | No | A toy store: plain text search, no meaning |

**The independent evidence is humbling.**
- In MemoryAgentBench, **plain BM25 keyword search (41.5) scored above Mem0 (21.1), Zep (24.0) and MemGPT (28.3)**.
- Letta reached 74% on LoCoMo with plain files plus search.
- Mem0, Zep and Letta publicly dispute each other's numbers.

So no product earns a place on its reputation. Your own evaluation decides (section 6).

## 5. What to reuse: the building blocks (recommended stack)

| Need | Choice | Licence | Why | Size |
|---|---|---|---|---|
| Store | **The existing SQLite file** | public domain | One memory, one backup, one transaction | none |
| Word search | **SQLite FTS5** (built in) | public domain | BM25 ranking; already in the release's SQLite 3.49.1 | none |
| Meaning search, phase 1 | **Vectors as ordinary BLOB columns, searched with numpy** (already shipped) | BSD | No extension, so backups, restores and the backup check stay as they are. At JARVIS's size (about 1,400 messages, 1.3 MB database) a full scan takes milliseconds | none |
| Meaning search, at scale | **sqlite-vec** 0.1.9 (pinned) | MIT / Apache-2.0 | 293 KB wheels for Windows and Mac arm64. Brute force is comfortable to about 200k chunks, and its index arrives in 0.1.10. Adopted only past about 100k chunks, because its virtual tables need the backup check to load the extension | 0.3 MB |
| Join words and meaning | **Reciprocal rank fusion in SQL/Python** (a documented sqlite-vec pattern) | – | Simple, well tested, no reranker needed at first | none |
| Meaning model runtime | **FastEmbed** 0.9.0 on **ONNX Runtime** (already shipped) | Apache-2.0 / MIT | No PyTorch; runs offline from files shipped in the release (`HF_HUB_OFFLINE`). A thin wrapper straight on `onnxruntime` + `tokenizers` is the fallback if FastEmbed's extra packages cause trouble | ~5 MB of packages |
| Meaning model | **Measured in Phase 1** between **granite-embedding-small-english-r2** (IBM, 47M parameters, 384 dims, fast) and **Qwen3-Embedding-0.6B** (best in its size class, 1024 dims, slower on this CPU) | Apache-2.0 both | You speak English, so the small model may be enough; your evaluation decides. Both are in FastEmbed. Not chosen: EmbeddingGemma (gated download, Gemma terms), Jina (non-commercial) | ~0.1 GB or ~0.6 GB |
| Reranker | **None at first.** Later, if needed, ms-marco-MiniLM-L-12 through FastEmbed | Apache-2.0 | A large reranker takes seconds per question on this CPU | – |
| Graph of people and things | **Not yet.** Entity and link tables in SQLite when needed; LadybugDB (the maintained Kuzu fork, Windows wheels) only for real multi-hop questions | MIT | Kuzu is archived; FalkorDBLite has no Windows wheels; Neo4j is a Java server | – |
| Structured extraction | **JSON Schema validation** (`jsonschema` or Pydantic, whichever the release already carries, else a small validator) | MIT | Provider-neutral; the repair-or-fail rule in 3.1 | small |
| Sharing with other AI apps | **The official MCP Python SDK**, local only (stdio) | MIT | Claude Desktop, Claude Code or any MCP client could read and propose memories through the same rules. Network exposure stays owner-only | small |

**Cloud embeddings** (OpenAI text-embedding-3-small, $0.02 per million tokens; Alibaba text-embedding-v4, $0.07) are
not recommended:
- they would send all your memories out once more;
- they would tie the memory to a vendor.

They stay possible only as your explicit choice, as a separate fully re-indexed space, and never as a silent stand-in.

**Footprint:** a few MB of packages, plus the model (0.1 or 0.6 GB on disk, 0.3–3 GB of RAM while loaded, unloaded when
idle). Vectors at 384 dims take 1.5 KB per chunk (15 MB for 10,000 chunks).

---

## 6. Measuring it: your personal evaluation (before anything else)

Public benchmarks do not predict how well memory works for *one* person, and the vendor claims conflict. So Phase 0
builds a small evaluation from your own JARVIS history: **60–100 questions with the expected answer and the turns
that prove it**. The question types follow LongMemEval:
- single facts;
- facts spread over several conversations;
- facts that changed (old value versus current);
- time questions;
- questions JARVIS should say it does not know;
- applying your working style;
- **over-personalisation probes**, where the memory is irrelevant;
- **poisoning probes**: a document or web page with a planted "remember …".

How it is run:
- with memory off, profile only, and profile plus recall, on each AI model;
- three runs each, with a fixed judging model;
- reported as the change against memory off.

Every phase must improve it, or at least not make it worse.

## 7. Safety and privacy, in one list

- One memory, on this PC, in the backed-up database. Exported only by you.
- Learned memories wait for your OK. Sensitive categories are never inferred.
- Learning reads only your own words, never outside content or a tainted question. Every memory keeps its source.
- Forgetting is real and remembered (tombstones). "Don't remember this conversation" and "pause learning" are switches.
- Everything the AI model reads still goes to its provider (Qwen on Alibaba today), as now. Extraction sends your own
  turns to that provider once more, unless you choose a local model for it (decision D3).
- No usage data leaves the PC. Every reused package is pinned, and its telemetry is switched off if it has any.
- The emergency stop halts indexing and learning. Backups and restores include everything; the restore check is
  extended to the new tables.

## 8. The phases

Each phase is built, tested, independently reviewed and recorded, then shipped in a release through the normal chain:
build, regression, the Stage 7 check in the VM (yours), and the everyday update (yours).

**Phase 0: foundations (about 1 session).**
- The personal evaluation set (needs D5).
- The `memory/` service boundary around today's facts and the You page.
- The new tables and their migration, with provenance columns.
- The backup and restore checks for them.
- This roadmap turned into an approved plan.

**Phase 1: search by meaning (about 2 sessions; delivers 1.0.19 item 5).**
- The local embedder (the model you approve, D2) and the `chunks` index over messages, facts, the You page and
  documents.
- FTS5 and vectors with fusion, recency and a relevance threshold.
- It replaces `memory.relevant()`, which always adds 20 facts, and the word-only chat search. It also gives the offline
  path the You page.
- The `recall` tool, the re-index job, and the first evaluation run; the embedding model is chosen here by your
  evaluation.

**Phase 2: learning from conversations, with your OK (about 3 sessions).**
- The provider-neutral extractor, run when JARVIS is idle and nightly, on your own words only, never tainted questions.
- Duplicate and conflict checks; facts with validity periods and tombstones.
- The daily review card (PC; phone through the Mac session); the sensitive-category rule.
- The evaluation, including the poisoning probes.

**Phase 3: understanding how you work (about 2 sessions).**
- Working-style rules proposed from your corrections and ratings.
- Weekly "what happened" summaries.
- Stale-fact detection; the profile and working style always in context, capped.
- The sycophancy guidance and its probes.

**Phase 4: portability and control (about 2 sessions).**
- The Memory page: sources, edit, forget, export, pause, don't-remember.
- The local MCP server (D6).
- **The framework checkpoint:** Mem0 and Hindsight run behind the same interface, on your evaluation. One is adopted
  only if it clearly beats JARVIS's own pipeline, and only with telemetry off and no second store.

**Later, only when needed:**
- sqlite-vec past about 100k chunks;
- a reranker;
- a people-and-things graph;
- the Mac mini move, if approved (the Mac arm64 wheels exist; the Mac's bundled Python must allow SQLite extensions).

**In total about 10 long sessions**, plus the release checks. Phases 0 and 1 can join the 1.0.19 work already under
way.

## 9. Decisions for you

| # | Decision | Recommended |
|---|---|---|
| D1 | The architecture: a memory service in the Core, one SQLite file, open-source components rather than a whole product, with the Phase 4 checkpoint. This also settles the README / capability-plan / "no new dependency" contradictions (section 2) | Yes |
| D2 | The meaning-model download: granite-embedding-small-english-r2 (~0.1 GB) and/or Qwen3-Embedding-0.6B (~0.6 GB), from Hugging Face, shipped inside the release | Both, for the Phase 1 measurement; one ships |
| D3 | Which AI model extracts memories: the chat provider (best quality; your words go to it once more), or the local Ollama model (private, less reliable) | The chat provider, with local as a switch |
| D4 | Review: every learned memory waits for your OK, or low-risk kinds are saved by themselves later | Every one waits, at first |
| D5 | The personal evaluation is built from your real conversations, read from a backup copy, never from the installed JARVIS | Yes |
| D6 | A local-only MCP server so other AI apps can use the same memory | Later, in Phase 4 |
| D7 | Keep raw conversations forever, or delete them after some months | Forever (they are the source of truth) |
| D8 | Where this goes in the queue: the You page review, voice recognition, the network scan, Gmail | After the You page and voice recognition; Phases 0–1 could go first if you prefer |

Approval wording, if you accept all the recommended answers:

```
I approve the memory roadmap, accept all recommendations
```

Or name changes, for example "D3 local" or "D8 memory first".

---

## Sources (selected; the full lists are in the research reports of 2026-10-10)

- **Frameworks:**
  - Mem0 https://github.com/mem0ai/mem0 · https://docs.mem0.ai/migration/oss-v2-to-v3.md · paper https://arxiv.org/abs/2504.19413
  - Hindsight https://github.com/vectorize-io/hindsight
  - Graphiti https://github.com/getzep/graphiti
  - Zep paper https://arxiv.org/abs/2501.13956
  - Cognee https://github.com/topoteretes/cognee
  - Letta https://github.com/letta-ai/letta
- **Building blocks:**
  - sqlite-vec https://github.com/asg017/sqlite-vec · hybrid search https://alexgarcia.xyz/blog/2024/sqlite-vec-hybrid-search/index.html
  - FastEmbed https://pypi.org/project/fastembed/
  - Qwen3-Embedding https://huggingface.co/Qwen/Qwen3-Embedding-0.6B
  - granite-embedding-small-english-r2 https://huggingface.co/ibm-granite/granite-embedding-small-english-r2
  - Kuzu (archived) https://github.com/kuzudb/kuzu · LadybugDB https://github.com/LadybugDB/ladybug
  - embedding model migration https://qdrant.tech/documentation/tutorials-operations/embedding-model-migration/
- **Patterns and evidence:**
  - CoALA https://arxiv.org/abs/2309.02427
  - LongMemEval https://arxiv.org/abs/2410.10813
  - MemoryAgentBench https://arxiv.org/abs/2507.05257
  - HaluMem https://arxiv.org/abs/2511.03506
  - Generative Agents https://arxiv.org/abs/2304.03442
  - Letta benchmark https://www.letta.com/blog/benchmarking-ai-agent-memory
  - Zep and Mem0 dispute https://github.com/getzep/zep-papers/issues/5
  - context engineering https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
  - MCP https://modelcontextprotocol.io/specification/2025-06-18
- **Safety:**
  - SpAIware https://embracethered.com/blog/posts/2024/chatgpt-macos-app-persistent-data-exfiltration/
  - Gemini memory injection https://embracethered.com/blog/posts/2025/gemini-memory-persistence-prompt-injection/
  - MINJA https://arxiv.org/abs/2503.03704
  - AgentPoison https://arxiv.org/abs/2407.12784
  - sycophancy with memory https://arxiv.org/abs/2509.12517
  - over-personalisation https://arxiv.org/abs/2601.13722
  - GDPR Article 9 https://gdpr-info.eu/art-9-gdpr/
