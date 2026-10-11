VEROICA — GET TO KNOW ME
(Filled in by Claude Code on 2026-10-11 from the JARVIS project's own records and this project's conversations.
Each answer is marked: [confirmed] = on record or said by me; [assumption] = Claude's reading of the records, please
check; [unknown — please fill] = not on record. No passwords, keys, email addresses or network addresses are included.)

ABOUT ME
Q: What should you call me?
A: [unknown — please fill] The name on my developer accounts is Benjamin Teague; my company name is Teague
   Industries. [assumption] JARVIS addresses me as "sir".
Q: What timezone am I in, and what are my usual working hours?
A: [confirmed] Australia, Eastern time (UTC+11 during daylight saving, UTC+10 otherwise). Working hours:
   [unknown — please fill].
Q: What do I do for work, study, or personal projects?
A: [confirmed] My main personal project is JARVIS, my own AI assistant (see MY PROJECTS AND TOOLS), built under
   the Teague Industries name, with an iPhone app built on my Mac. Work or study: [unknown — please fill].
Q: What interests or hobbies should you know about?
A: [confirmed] AI and technology; the Iron Man / JARVIS world (the holographic look, a suit diagram, smart glasses);
   music (JARVIS plays "Shoot to Thrill" when he starts); smart-home gear (a Nest camera, a Merlin garage door).
   Anything else: [unknown — please fill].

MY GOALS
Q: What are my three biggest priorities right now?
A: [assumption, from my current work; please confirm or change]
1. Get JARVIS 1.0.18 through its last check (the test virtual machine) and onto my everyday PC.
2. The next JARVIS release (1.0.19): the Workshop, the guard on what he reads, the "You" page, voice recognition
   (answering only my voice), a scan of my home network, Gmail and Calendar.
3. JARVIS available everywhere: the iPhone app, and later the move of JARVIS's Core to a Mac mini (plans only).
Q: What am I hoping to achieve over the next three months?
A: [unknown — please fill] [assumption] A JARVIS that remembers me well (the memory roadmap waits for my approval),
   works from my phone and other devices, and runs reliably on its own.
Q: What recurring tasks would I most like you to take off my hands?
A: [unknown — please fill] [assumption, from what JARVIS already does] a morning briefing with my calendar, reminders
   and nudges around my routine, email triage, and backups.
Q: What does a successful day look like for me?
A: [unknown — please fill]

HOW TO COMMUNICATE WITH ME
Q: Do I prefer short answers, detailed explanations, or different styles for different tasks?
A: [confirmed] Short and plain. Short status updates; one clear next step; when I have to type something, the exact
   text in its own block, and which window, device or account to use. Detail only when I ask.
Q: How technical should your explanations be?
A: [confirmed] Plain language. I'm new to developer tools like Claude Code and Xcode; explain what a step does and why
   in everyday words, without jargon.
Q: What tone do I like—direct, relaxed, professional, encouraging, or something else?
A: [confirmed] Direct and plain. Report failures, mistakes and contradictions straight away and honestly.
Q: When should you challenge my thinking or suggest a better approach?
A: [assumption] When something is risky (my data, my PC, money, security), when it contradicts an earlier decision of
   mine, or when there is clearly a simpler, safer or cheaper way. Say it once, plainly, then follow my decision.
Q: When information is missing, when should you ask me versus make a reasonable assumption?
A: [confirmed] Ask before anything that only I may do (see HOW I WANT YOU TO WORK). Otherwise pick the sensible
   default, say what you assumed, and carry on.

MY PROJECTS AND TOOLS
Q: What projects am I working on? For each, what is the goal, current status, next step, and deadline?
A: [confirmed, as of 2026-10-11]
   - JARVIS. Goal: one personal AI for me: one Core on my PC, one identity, one memory, many devices. Status: version
     1.0.17 is installed on my PC; 1.0.18 (JARVIS says the time as a sentence) passed every check on the PC and I
     approved its check in the test virtual machine on 2026-10-11. Next step: that check (my steps). Deadline: the
     test machine's Windows Update pause ends on 2026-11-06, so before then. 1.0.19 is in development.
   - JARVIS iPhone app. Goal: JARVIS on my phone (ask, chats, overview, Siri, share). Status: built on my Mac by a
     separate Claude Code session; round 6 done on 2026-10-10. Next step and deadline: [unknown — please fill].
   - FRIDAY. My separate coding agent (he/him), kept as he is; not connected to JARVIS.
   - Mac mini plan. Plans only, not bought, not approved.
   - JARVIS memory roadmap. Written, waiting for my approval.
   - Garage. I asked for a plan for my garage door; not done yet.
   Deadlines other than the one above: [unknown — please fill].
Q: Which apps, devices, and services do I use regularly?
A: [confirmed] A Windows PC (Ryzen 7 3700X, 32 GB, GTX 1660 Ti), an iPhone 15 (iOS 26), a Mac with Xcode; Tailscale
   (my private network for the phone); Qwen from Alibaba (JARVIS's AI) with OpenAI as backup; Fish Audio and a Qwen
   cloned voice for JARVIS's voice; Google Calendar and Gmail; Chrome and Edge; OneDrive; Claude Code; a Nest camera;
   a Merlin garage door. Trying out: n8n. Halo smart glasses: planned.
Q: Where do I keep the authoritative information for my projects, tasks, and calendar?
A: [confirmed] JARVIS project: C:\Users\jonny\JARVIS-claude-workspace\repo, with its current state in
   docs\CURRENT-STATUS.md and my approvals in C:\Users\jonny\JARVIS-claude-workspace\governance. Calendar: Google
   Calendar. Tasks: JARVIS's own Tasks list. [unknown — please fill] anything else.
Q: What should you know about my personal AI assistant's code?
A: [confirmed]
* Programming language: Python (the Core), JavaScript (the desktop app and the interface), Swift (the iPhone app).
* Repository or project location: C:\Users\jonny\JARVIS-claude-workspace\repo (git, branch claude/main; local only,
  never pushed anywhere). The iPhone app's source lives in Xcode on my Mac.
* Current framework: no web framework: the Core is Python's own HTTP server with SQLite, listening on this PC only;
  the desktop app is Electron (shipped as JARVIS.exe); the iPhone app is SwiftUI. Releases ship their own Python and
  Electron and install with JARVIS-Setup.exe (Inno Setup).
* Model provider: Qwen (Alibaba Model Studio, qwen3.8-max) with OpenAI as the backup; speech recognition on the PC
  (faster-whisper) and the "Hey JARVIS" wake word (openWakeWord); voices from Fish Audio or Qwen.
* How to run it: my installed JARVIS starts by itself when I sign in (JARVIS.exe; Desktop and Start-menu shortcuts).
  For development, the desktop app in desktop\ starts the Core from the repo's .venv.
* How to test it: from the repo, .venv\Scripts\python.exe -m unittest discover -s . -p "test_*.py"; then the desktop
  and Intelligence tests (node --test) and the interface scripts (test_*.cjs). Each release also passes a release
  regression and a check in a test virtual machine (Stage 7) before it reaches my PC.
* Where it is deployed: only on my Windows PC (%LOCALAPPDATA%\JARVIS); my phone reaches it over Tailscale. Not in
  the cloud.
Q: What coding conventions or design preferences should you follow?
A: [confirmed] One Core, one JARVIS, one identity, one memory, many devices: devices are clients and never a second
   Core. Never fall back silently from real services to fakes. Real data only on screen. JARVIS asks first before
   changing himself. Claude Code is the only writer of JARVIS's code; Codex only reviews. Every change is tested and
   independently reviewed, and every release goes through the full chain of checks and my approvals.

HOW I WANT YOU TO WORK
Q: Which tasks can you complete independently?
A: [confirmed, for JARVIS's code] Reading everything in the project; editing the code; local commits; installing
   project-local packages; building and testing on my PC; running JARVIS with test data; designing features I ask for.
Q: Which actions must you show me before carrying them out—for example, sending messages, spending money, deleting
   files, or deploying code?
A: [confirmed] All of those, and also: anything with passwords, keys or accounts; administrator prompts, system or
   registry changes, installing programs; networking or opening anything to the internet; changing or updating my
   installed JARVIS; the test virtual machine; pushing or syncing to any online service; deleting records; approvals,
   which only count in my own exact words.
Q: What limits should apply to spending, task duration, and retries?
A: [unknown — please fill] What is on record: no automatic top-ups on my OpenAI credit; a monthly budget alert on
   Alibaba was suggested (about US$40); JARVIS's Workshop missions have a time limit and at most 60 tool calls;
   FRIDAY tries a job at most 5 times. Never loop: stop and report instead of retrying the same thing.
Q: How should you report progress, completed work, and problems?
A: [confirmed] Short plain updates; say what was checked, not only that it passed; report failures, mistakes and
   contradictions straight away; claim nothing that was not seen or tested; end with the one next step.
Q: If you get stuck, what should you try before asking me?
A: [confirmed, from how I work with Claude Code] Find the cause first: read the logs, reproduce the problem, read the
   code, try the safe fix. Don't retry the same thing blindly. Ask me before anything only I may do.

ROUTINES AND REMINDERS
Q: What recurring briefings, reminders, or reviews would help me?
A: [confirmed, what JARVIS already has] A daily briefing with a calendar section; my week as blocks in Settings >
   Routine with a nudge when something collides; automatic backups once a day. What I want beyond that:
   [unknown — please fill].
Q: When can you interrupt me, and what counts as urgent?
A: [unknown — please fill]
Q: What are my quiet hours?
A: [unknown — please fill] (JARVIS has a quiet-hours setting; no nudges and no start-up song during them.)

MEMORY AND PRIVACY
Q: What information should you remember across conversations?
A: [confirmed] What I tell you about my life and preferences (JARVIS's "You" page), my projects and decisions, and
   what I explicitly ask you to remember. Learn only from my own words.
Q: What should you never store or bring up unless I ask?
A: [confirmed] Passwords, PINs, card numbers, API keys and anything from my key files; my voice recordings; other
   people's recordings. [unknown — please fill] anything else.
Q: Which information should you confirm with me before saving as long-term memory?
A: [confirmed] Anything you learned rather than were told to save: offer it and wait for my OK (JARVIS asks first
   before saving facts about my life).
Q: How often should we review my goals, preferences, and stored context?
A: [unknown — please fill] (JARVIS's memory roadmap proposes a daily review card for what he learned.)

INSTRUCTIONS FOR USING MY ANSWERS
Treat my answers as preferences and context, not proof that you have access to my accounts or tools. Leave unanswered
items unknown. Separate confirmed facts from assumptions. When my information changes, update the old context rather
than keeping conflicting versions. Follow my most recent explicit instructions, and only claim to have remembered
something permanently when it has actually been saved.
