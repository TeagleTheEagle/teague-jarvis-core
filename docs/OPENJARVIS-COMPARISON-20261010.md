# OpenJarvis compared with our JARVIS (2026-10-10)

**Owner's request:** "what does this jarvis have that ours doesn't see this zip and use it to improve our jarvis",
with `C:\Users\jonny\Downloads\OpenJarvis-main.zip`.

**What was read:**
- The zip: 44,300,071 bytes, sha256 `2ad9782976fa88f4dada23533cadf1b6cb99b4594e37d60187242b39f63e56df`, 2,169 files,
  no unsafe names. It was unpacked into the session's scratch folder only.
- What was read: the README, the licence, the package list with each package's own description, and the files named
  below. Nothing from it was run or installed, and nothing was copied into JARVIS.

**What it is:** Stanford's OpenJarvis, "Personal AI, On Personal Devices" (paper arXiv 2605.17172, May 2026; Apache
2.0). It is a framework for local-first assistants: Python with a Rust extension and a web and desktop front end.
Agents, tools, skills, memory, speech, connectors, channels, a scheduler, security guards, evaluations and a learning
layer are building blocks that presets combine ("morning digest", "deep research", "code assistant", "scheduled
monitor").

**Licence:** Apache 2.0. Its code may be reused with its licence notice kept and changes stated. The plan is to write
JARVIS's own versions in JARVIS's style, with OpenJarvis as a reference, so that no new dependency comes in.

## What it has that our JARVIS does not

| # | OpenJarvis | Our JARVIS today | Worth it for us |
|---|---|---|---|
| 1 | **Guards on what the AI reads**: a prompt-injection scanner, an SSRF guard that blocks requests to private addresses, taint tracking, a credential stripper (`security/`) | Web, mail and file text is marked as data in the request ("not an instruction"); there is no scanner | **High.** JARVIS reads web pages and mail, and with 1.0.18 runs commands. A page saying "ignore your rules and ..." should be caught before the model sees it |
| 2 | **Scheduled and continuous agents** ("operators", `scheduler/`): a spoken morning digest at a set time (mail, calendar, news, health), monitors that watch something for days | A briefing on request, nudges tied to the routine, reminders | **High.** It fits the owner's always-present brief (`docs/ALWAYS-PRESENT-JARVIS-BRIEF.md`) and proposal 2, standing goals (`docs/CAPABILITY-SOURCES-20261007.md`) |
| 3 | **Skills** (`skills/`, the agentskills.io format): reusable how-tos the agent loads when needed, importable from public libraries (Hermes about 150, OpenClaw about 13,700), improved from its own traces | None | **Medium to high.** This is proposal 1 of the capability record. Imported skills are untrusted text and would go through item 1's guard and the owner's approval |
| 4 | **Memory that learns by itself** (`memory/extractor.py`): after each exchange a small local model picks out lasting facts | Explicit memory commands and saved facts only | **Medium.** For us, only with the owner's OK per fact, or a daily list to approve: nothing saved silently |
| 5 | **Search by meaning** over documents and notes: embeddings, hybrid search, chunking, retrieval with citations (`connectors/`) | Keyword matching (`store.search_documents`) | **Medium.** Better "what did I save about ..." and research over the owner's own files |
| 6 | **A local voice**: Kokoro text-to-speech, open source and offline (`speech/kokoro_tts.py`); also Cartesia, Deepgram, OpenAI | Fish Audio and the Qwen cloned voice, both online | **Medium.** It gives an offline voice. A cloned local voice stays proposal 6 (Chatterbox) |
| 7 | **Apple connectors**: Health, Notes, Calendar, Contacts, Music, iMessage; also Notion, Obsidian, Outlook, Oura, Strava, weather, RSS | Google Calendar, mail, Spotify, news, maps | **Later, with the Mac mini:** the Apple ones need macOS |
| 8 | **Channels**: Telegram, WhatsApp, Signal, iMessage, SMS, Discord, Slack and about 25 more (`channels/`) | The iPhone app, and the PC | **Later, on the owner's word.** It would let JARVIS message the owner away from the app. Each channel is an outside service and an account |
| 9 | **MCP tools** (`mcp/`, `tools/mcp_adapter.py`): plug in any Model Context Protocol server as tools | None | **Later.** A large toolbox, but every server is outside code and needs the permissions table |
| 10 | **A model router** (`learning/routing`): a cheap or a strong model chosen per question, learning from results | "Answer speed": Deep, Auto, Economy | **Low to medium.** It could lower the Qwen bill |
| 11 | A browser agent that clicks and reads pages (`tools/browser*.py`), PDF reading, a git tool, an OpenAI-compatible API, DAG workflows, agent-to-agent protocol, evaluations | Partly (web search, research workspace, the Workshop) | Low, case by case |

## What we should not take

- **Pearl mining** (`mining/`; design `docs/design/2026-05-05-vllm-pearl-mining-integration-design.md`): "Proof-of-Useful-Work" cryptocurrency mining that runs on the user's own hardware while it does AI work.
  It is an optional extra there, and **not for JARVIS**.
- **Anonymous usage analytics** sent to their servers (`analytics/`): against JARVIS's rule that nothing leaves the
  owner's machines unasked.
- The Docker sandbox (no Docker here; the Workshop uses a Windows Job Object), their installers and their own
  frontend: JARVIS has its own.

## The owner's decision (2026-10-10)

The owner quoted the eight items of the reply (items 1 to 8 of the table above, in the reply's words) and wrote
**"build all of these"**. The order, said to the owner:
1. the guard on what JARVIS reads;
2. the morning briefing and monitors;
3. skills;
4. memory suggestions, which wait for the owner's OK;
5. search by meaning;
6. the offline voice;
7. messaging apps;
8. Apple connectors.

They go into **1.0.19**, after 1.0.18, each with tests and one reviewer.

The owner's own steps, asked for when each item is reached:
- **Search by meaning and the offline voice:** permission to download a model, given its file, source and size
  first.
- **Telegram:** the owner makes a bot and puts its token in the key file.
- **WhatsApp:** no safe official route for personal use; the unofficial bridge risks the number being banned.
- **Signal:** needs a spare number.
- **Apple Health, Notes, Contacts and iMessage:** need a Mac, so the Mac mini, or the phone app for Health and
  Contacts.

## Recommendation

Proposed order, each as its own small plan for the owner's approval, then built, reviewed and checked through the
release chain after 1.0.18:

1. **The guard on what JARVIS reads** (item 1): small, and it protects everything else.
2. **A morning briefing on a schedule, and standing monitors** (item 2).
3. **Skills** (item 3), behind item 1's guard.
4. Memory that offers facts to keep, and search by meaning (items 4 and 5).
5. An offline voice (item 6).

Then, with the Mac mini, the Apple connectors (item 7). Channels and MCP come only on the owner's word.
