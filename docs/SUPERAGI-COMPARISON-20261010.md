# SuperAGI's abilities for the one JARVIS (2026-10-10)

**Owner's request:** "just read the zip and tell me how we can give jarvis these abilities instead of making multiple
agents", with `C:\Users\jonny\OneDrive\Desktop\SuperAGI-main (1).zip`.

**What was read:**
- The zip: 3,636,547 bytes, sha256 `4027818550f5748ec4ba267a7312a9bf5913f21d59b22e1aec9f342446b29723`, 771 files,
  no unsafe names. It was unpacked into the session's scratch folder only.
- What was read: the README, the licence, and the agent, jobs, models and tools packages by their file names. Nothing
  from it was run, installed or copied.

**What it is:** SuperAGI by TransformerOptimus (MIT licence). It is a framework to "provision, spawn and deploy
autonomous agents" with toolkits from a marketplace, a web GUI, an action console for permissions and input,
schedules, budgets, vector knowledge, templates and workflows. It runs on Docker with Postgres, Redis and Celery. Its
newest database change is dated 2023-10-04, so it is about three years old.

**The architecture rule stands:** one Core, one JARVIS, one identity and one memory. SuperAGI's many agents become
many **missions of the one JARVIS**: the same memory, the same permissions table, the same emergency stop, and each
mission with its own chat. The Workshop in 1.0.18 already has the mission itself: a plan, steps, self-correction, a
time limit and 60 tool calls.

## SuperAGI's abilities, as JARVIS would have them

| SuperAGI | For the one JARVIS | Already approved? |
|---|---|---|
| Several agents running at once | **Missions side by side**: several goals at once, each in its own chat, listed in Settings > Workshop and on the phone, each one stoppable. All are JARVIS, so a fact one mission learns, all know | New |
| Agent schedules (`agent_schedule`, `jobs/scheduling_executor.py`) | **Scheduled and repeating missions**: "every Monday at 8, check ... and tell me" | Part of the OpenJarvis item 2 (morning briefing and monitors) |
| Action console: permissions and input while an agent runs (`agent_execution_permission`) | **A mission that pauses to ask you**, on the PC or the phone, and goes on with your answer. Approvals of "ask first" tools exist already | New: the question part |
| Budgets and token control (`budget`, the iteration limits) | **A cost cap per mission** and its spend so far shown on the mission | New |
| Agent templates (`agent_template`) | **Mission templates**: "research a topic", "write and test a script", "weekly review" | With the OpenJarvis item 3 (skills) |
| Knowledge and vector databases, resources (`knowledges`, `vector_dbs`, `resource`) | **Files you give JARVIS to learn from**, found by meaning | The OpenJarvis item 5 (search by meaning) |
| Agent memory | JARVIS's one memory, with suggestions for your OK | The OpenJarvis item 4 |
| Performance telemetry | Each mission's time, tool calls and cost | New, with the cost cap |
| Workflows (ReAct predefined steps) | Routines and templates as above | With skills |
| Toolkits: web scraper, email, GitHub, Jira, Slack, Twitter, Instagram, image generation, Google Calendar, search, code, files, knowledge | JARVIS has search, news, calendar, mail (read), files and code (the Workshop). Worth adding, each on the owner's word: **reading a web page's text** (through the guard), **sending email** (ask first), **GitHub**, **image generation** | New, each on the owner's word |

## What not to take

- The many-agents design itself: separate identities, memories and permission sets break JARVIS's binding rule.
- The heavy stack: Docker, Postgres, Redis, Celery and a separate GUI. JARVIS's Core and window already do this job
  on one PC.
- The toolkit marketplace that downloads third-party code: every addition is built, reviewed and switched like
  JARVIS's own tools.

## The owner's decision (2026-10-10)

**"add the 4 new ones"**. They go on the 1.0.19 list after the eight OpenJarvis items:
- 9: missions side by side;
- 10: missions that pause to ask;
- 11: a cost cap and spend per mission;
- 12: reading a web page's text, after the guard.

Then, quoting "Sending email": **"and this"**. **Correction (the same afternoon): sending email is already built**, in
1.0.17, with no build needed:
- `mail_send` always waits for the owner's approval on screen;
- `mail_search` and `mail_read` read Gmail;
- they work over IMAP and SMTP with an app password (`mail.py`; the owner's steps in `docs/GOOGLE-STEPS.md` section 1).

This record wrongly listed it as worth adding; the table row's "sending email" is withdrawn. GitHub and image generation
stay on the owner's word.

## Recommendation

Add four new items to the 1.0.19 list, after the eight OpenJarvis items they build on:
- missions side by side;
- missions that pause to ask;
- a cost cap and spend per mission;
- reading a web page's text, after the guard.

The rest is already in the eight. Sending email, GitHub and image generation come each on the owner's word.
