# VERONICA joins JARVIS, and OpenRouter becomes the one AI connection: the plan

**Status: APPROVED by the owner on 2026-10-12, 16:04 local** ("i approve veronica merge plan": D1-D11 as recommended;
record `../governance/VERONICA-MERGE-PLAN-APPROVAL-RECORD.json`). Written 2026-10-12 by Claude Code, on the owner's "go".
Phase 0 done the same day (see `docs/CURRENT-STATUS.md`).

**Owner amendment of 2026-10-13: Qwen only.** "can we make it only use qwen models for all the functions?", then
"and veronica as well", then "DONT CHANGE ANY SAFTEY RULES FOR VERONICA OR JARVIS / keep fish audio api for both of
them". The owner is restricting the OpenRouter key to `qwen/*` with an OpenRouter guardrail. So, in place of D2, D3, D7
and D8 where they name other makers:
- coding and research jobs use **Qwen 3.8 Max** (`qwen/qwen3.8-max-0902`), not Claude Opus;
- OpenRouter's backup model is **Qwen 3.8 Flash** (`qwen/qwen3.8-flash`), not Claude Sonnet;
- the cloud option for hearing is **off** by default (OpenRouter's speech-to-text models are not Qwen); JARVIS hears on
  the PC, as before. An `OPENROUTER_STT_MODEL` line turns it back on;
- both voices stay on **Fish Audio**; no safety rule changes, for JARVIS or VERONICA.
Each model can still be changed in the key file. Done in `providers.py` on `claude/veronica-merge`, 2026-10-13.

**Owner amendment of 2026-10-13 evening: one model per job, by performance for the money, locked (replaces the
morning's Qwen only).** After a read of OpenRouter's whole model list with that day's prices (459 chat models, 33
search-by-meaning models, 25 speech-to-text models), the owner first chose the "best overall" column ("start this"), then
amended it: "allocate the best performance : cheapest ratio to each aspect for jarvis and lock in so that's the only
model it can use". So the models are fixed in `providers.py` (`OPENROUTER_MODELS`); a key-file line that would change one
(`OPENROUTER_MODEL`, `_VISION_MODEL`, `_FAST_MODEL`, `_CODING_MODEL`, `_FALLBACK_MODEL`, `_MAKERS`) is refused plainly
before any request, naming the line to remove. The allowed makers are **Anthropic, Qwen and Google** (`OPENROUTER_MAKERS`
in code; the owner widens the guardrail on the key to match). The fixed models:

| Job | Model | Price per million tokens (in / out) | Why this one |
|---|---|---|---|
| Everyday chat, tools, pictures | `anthropic/claude-haiku-5.5` | US$0.10 / 0.50 | Sees pictures, 1M context; 20× cheaper than Qwen 3.8 Max and judged at least its equal on everyday work |
| Economy, and the web search's small request | `anthropic/claude-haiku-5.5` | US$0.10 / 0.50 | The same model with thinking off |
| Coding and research jobs (missions) | `anthropic/claude-sonnet-5.5` | US$2 / 10 | Opus 5.5 is twice the price for a little more |
| Backup when the first model fails | `qwen/qwen3.7-plus` | US$0.32 / 1.28 | Another maker on purpose, so one outage does not take both |
| Hearing | this PC (Whisper), as before | free | `OPENROUTER_STT_MODEL=qwen/qwen3-asr-1.7b` (or `google/gemini-3.5-transcribe`) offers the cloud choice in Settings |
| Voice | Fish Audio, unchanged | | OpenRouter's two speaking models do no voice cloning |
| Search by meaning (memory, roadmap phase 3; not built) | `qwen/qwen3-embedding-8b` when it comes | US$0.01 | Among the best open embedding models, and the cheapest |

Roughly: 100 plain questions cost about US$0.25 (about US$4.40 before, on Qwen 3.8 Max); a question that uses tools runs
several rounds, so count two to three times that. The quality rankings are Hermes's judgement from general knowledge;
the yardstick (ASI roadmap phase 0) is what would measure them on the owner's own questions. Fish Audio and every safety
rule unchanged. Built on `claude/best-models` (a worktree beside `claude/veronica-merge`), 2026-10-13.

## 1. What the owner asked for (2026-10-12)

- "can you make veronica and jarvis one. add veroinca to jarvis's core and make one folder that has all the files of
  everything", then chose **"Veronica joins JARVIS"**: one app, one Core, one memory; her skills, voice, name and orb
  move into JARVIS's Core; her separate app is retired once it all works.
- "openrouter will be our main", then **"OPENROUTER WILL DO EVERYTHING EXCEPT KEEP FISH AUDIO ... LEAVE THE FISH AUDIO
  API KEY / MODEL FOR BOTH JARVIS AND VEROICA"**.
- VERONICA stays autonomous: "keep it as it is" (she sends email without asking).
- The OpenRouter key was created and tested by the owner ("openrouter works"; the function test passed tools on Qwen and
  Claude, web search and search by meaning; reading a picture and speech-to-text wait for a re-run after the owner adds
  credit; see section 8).

## 2. The result, in plain words

One JARVIS app on the PC and the phone, one Core, one memory. Say **"Hey JARVIS"** and JARVIS answers in his voice; say
**"Veronica"** and VERONICA answers in hers. Both are the same assistant underneath: the same memory, the same tools,
the same permission switches, the same emergency stop. Whatever you tell one, the other knows.

All the thinking goes through **one OpenRouter key**: Qwen for everyday chat, Claude for coding and research jobs.
Both voices stay on **Fish Audio**. Gmail, Calendar and Maps keep their own settings, as they are not AI services.

## 3. What stays exactly as it is

- The binding rules in `CLAUDE.md`, apart from the one amendment in decision D1.
- Everything JARVIS does today: his 51 tools (56 with the Workshop of 1.0.19), the permissions page, the emergency
  stop, the phone app and Tailscale door, backups, music, routine, notices, the You page.
- The release path: build and checks on this PC, the owner's Stage 7 check in the test computer, then the owner's
  everyday update. The installed JARVIS is never changed by Claude.
- Release 1.0.18 (the time fix) goes ahead on its own, unchanged by this plan.
- VERONICA's code tools never edit JARVIS's own code, the installed JARVIS, or the release and test folders. That
  boundary is kept in code, as it is in her `safety.py` today. (Connecting FRIDAY to JARVIS was stopped by Anthropic's
  safety system on 2026-10-10 and is not part of this plan.)

## 4. Decisions for the owner

Each has Claude's recommendation; the approval sentence accepts the recommendations unless the owner says otherwise.

- **D1. One Core, two names (amends "ONE IDENTITY").** JARVIS and VERONICA become two personas of the one Core: two
  names, two voices, two personalities, one memory, one set of tools and permissions. *Recommended* (this is what
  "Veronica joins JARVIS" means). `CLAUDE.md` gets one line recording the amendment (`AGENTS.md` stays unchanged, as
  `CLAUDE.md` requires).
- **D2. Which brain does what (all through OpenRouter).** Everyday chat, tools, pictures and web search:
  **Qwen 3.8 Max** (`qwen/qwen3.8-max-0902`, about US$2 in / US$6 out per million tokens). Coding and research jobs:
  **Claude Opus 5.5** (`anthropic/claude-opus-5.5`, about US$4 / US$20), what VERONICA uses today. *Recommended.*
  Cheaper alternative for coding: Claude Sonnet 5.5 (US$2 / US$10).
- **D3. Who answers.** The wake word decides the voice and personality ("Hey JARVIS" or "Veronica"); a typed message
  goes to whoever was last spoken to, with a switch in the window. Coding and research jobs use Claude whoever started
  them. *Recommended.*
- **D4. Sending email.** There is one permissions table, so one setting covers both names. The owner's decision for
  VERONICA was "keep it as it is" (sends without asking), which means `mail_send` set to **Allowed**: JARVIS would
  also send without asking. The alternative is **Ask first** (JARVIS today: a card to approve, also from the phone).
  *Claude carries the owner's decision (Allowed) and points out that it now covers JARVIS too.*
- **D5. VERONICA's calendar "add" and "edit".** They only pretend today. They are **not** carried over; real calendar
  writes stay on JARVIS's list (items 14-17, which need a Google sign-in). *Recommended.*
- **D6. Web search.** OpenRouter's web search (about US$0.007 a search) replaces Brave. *Recommended.*
- **D7. Hearing.** JARVIS keeps hearing you on the PC itself (free, nothing leaves the PC). OpenRouter's speech-to-text
  becomes the cloud option in place of Alibaba's. *Recommended.*
- **D8. No offline answers.** With OpenRouter for everything and Ollama uninstalled, JARVIS cannot answer when the
  internet is down; he says so. The OpenAI backup provider is replaced by OpenRouter's own fallback to a second model.
  *Recommended* (OpenRouter itself becomes the one dependency the owner chose).
- **D9. Old keys.** On switch-over day, after one trouble-free week on OpenRouter, the owner deletes the old Alibaba
  (DashScope), OpenAI, Anthropic and Brave keys on their websites (including the Anthropic key found in a Desktop file
  on 2026-10-12). Alibaba also takes the Qwen cloned voice with it; Fish Audio is the voice for both. *Recommended.*
- **D10. One folder.** VERONICA moves from `D:\VERONICA` into `C:\Users\jonny\JARVIS-claude-workspace\veronica` (beside
  `repo\` and `friday\`, where she was first built), with her git history; her Desktop shortcut follows. She keeps
  working there unchanged until phase 4 retires her. *Recommended.*
- **D11. Retiring the separate VERONICA app.** After the merged release is the everyday JARVIS and the owner says so,
  her folder is archived (moved, not deleted) and her shortcut removed. *Recommended.*

## 5. The work, in order

### Phase 0: one folder (one short session; no money needed)
1. Move VERONICA into the workspace (D10); point her shortcut, notes and Qwen's guard file at the new place; run her
   tests from a throwaway copy.
2. Bring her two memories (and nothing secret) into a list for phase 2.

### Phase 1: OpenRouter in the Core (about 2 sessions; tested with stand-ins, then once live after credit)
1. `providers.py`: a third provider `openrouter` (an OpenAI-style connection at `https://openrouter.ai/api/v1`, key
   `OPENROUTER_API_KEY`), with the model of D2 per kind of job; streaming, tools and pictures as today.
2. The answer-speed setting (Deep / Auto / Economy) drives OpenRouter's "thinking" control, so quick questions stay fast
   and cheap; reply limits leave room for Qwen's thinking (the function test showed it thinks before every answer).
3. Fallback: when the chosen model fails, OpenRouter tries a second model (D8) and the Core says so, as the backup
   provider does now.
4. Web search (`actions.py`): OpenRouter's search with its sources shown, replacing Brave (D6).
5. Settings > Connections, the connection tests and the health check show OpenRouter and Fish only; the old providers
   are removed from the code with their tests, as Groq and Gemini were in 1.0.15.
6. The function test re-run with credit (pictures and speech-to-text) before anything ships.

### Phase 2: VERONICA as JARVIS's second persona (about 2 sessions)
1. Her personality: her prompt carried over (without the "full authority" wording, which the permission switches now
   decide), as a second persona of the one Core (D1).
2. Her voice: a second Fish Audio voice (her `FISH_VOICE_ID`) beside JARVIS's.
3. Her name as a wake word: JARVIS's listener also answers "Veronica" (her own name-spotting from heard words; a trained
   "hey Veronica" detector like JARVIS's can come later).
4. Her look: her orb as a mode of the JARVIS window that follows whoever is speaking.
5. Her two memories into JARVIS's memory, marked as hers and dated.
6. The phone: the Core's routes carry the persona; the Mac session gets a short request for "Ask Veronica" in Siri.

### Phase 3: her skills as Core tools (about 3 to 4 sessions)
1. **Project helper:** the Workshop gains "projects": a folder the owner names (never JARVIS's folders), where she
   reads, edits and writes files, runs that project's tests, and every change can be undone until the end of the turn.
   Her `safety.py` rules come with it. These jobs use Claude (D2). Each tool keeps its switch on the permissions page.
2. **Checked research:** background research tasks with a spending cap per task (VERONICA's was US$3), web search
   through OpenRouter, and a report saved only when every quote matches a page that was really fetched (her citation
   check). Built on the Workshop's missions, not on Deep Agents, so there is one engine.
3. **Email, calendar, memory:** JARVIS's own tools already do these (`mail_search`, `mail_read`, `mail_send`,
   `calendar_events`, memory); her versions are not copied. `mail_send` follows D4.
4. Not carried over: her sub-agent tool (it did not work), her "secret scrubbing" (it scrubbed nothing), her
   conversation checkpoint files (nothing read them), the pretend calendar tools (D5).
5. Every item gets one independent review and its findings applied, as usual.

### Phase 4: release and switch-over (1 to 2 sessions, plus the owner's test-computer time)
1. One release with phases 1 to 3 (it follows 1.0.19), every check on this PC, the owner's Stage 7 check, and the
   owner's everyday update; the owner places `OPENROUTER_API_KEY` and her Fish voice in JARVIS's key file (Claude gives
   the exact steps; keys are owner-only).
2. One trouble-free week; then the owner deletes the old keys (D9) and says when to retire the separate VERONICA app
   (D11).

About **8 to 10 sessions** in all. Phases 0 to 3 need no OpenRouter credit except two short live tests.

## 6. Costs (rough)

- Everyday chat on Qwen through OpenRouter costs about what Qwen costs directly, plus OpenRouter's fee on credit
  (reported at about 5.5%); the 2026-10-05 estimate for Qwen was about US$11, 28 or 84 a month for light, normal or
  heavy use.
- Coding and research on Claude Opus cost more per job; research keeps a cap per task. A monthly spending limit can be
  set on the OpenRouter key itself.
- Fish Audio stays as it is. Brave, Alibaba, OpenAI and Anthropic bills stop after D9.

## 7. Owner-only steps in this plan

- The approval sentence below; decisions D1-D11 (or changes to them).
- Adding OpenRouter credit (at least US$0.50 for audio; US$10-20 suggested to start) and re-running
  `owner-steps\Test-OpenRouter-Functions.cmd`.
- Placing `OPENROUTER_API_KEY` and VERONICA's Fish voice id in JARVIS's key file at switch-over (Claude never handles
  keys).
- The Stage 7 check and the everyday update of the merged release.
- Deleting the old keys on their websites (D9); saying when to retire the separate VERONICA app (D11).

## 8. Evidence so far

- OpenRouter's model list (2026-10-12): `qwen/qwen3.8-max-0902` (text, image, video in; tools), `anthropic/claude-opus-5.5`
  (text, image, file in; tools), `qwen/qwen3-embedding-8b`, `openai/whisper-1` and 24 other speech-to-text models;
  no Fish Audio voices for speaking (Fish's transcription only).
- Owner's key test: "openrouter works" (key, credit, both models answered).
- Owner's function test: tools PASS on both models (`set_timer` with 5 minutes); web search PASS (3 sources); search by
  meaning PASS (0.96 vs 0.46); picture FAIL as a test fault (Qwen's thinking used the small reply limit; limit raised);
  speech-to-text not run (OpenRouter needs a balance of at least US$0.50 for audio).
- Owner's re-run after adding US$50 of credit (2026-10-13, phase 1 item 6): **6 of 6 PASS**: tools on Qwen 3.8 Max and
  Claude Opus 5.5 (`set_timer` with 5 minutes), picture ("TEAGUE 4271" read), web search (3 sources), speech-to-text
  (`openai/whisper-1` heard the sentence word for word), search by meaning (0.95 vs 0.45). The same day the owner chose
  Qwen only (amendment at the top), so the test now checks Qwen models only.

---

**To approve:** type **"I approve the Veronica merge plan"** (this accepts D1-D11 as recommended; add any changes,
for example "D2 Sonnet" or "D4 ask first").
