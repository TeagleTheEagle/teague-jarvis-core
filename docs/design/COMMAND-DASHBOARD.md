# Command dashboard (release 1.0.15)

Owner request, 2026-10-05: "can we apply this new and improved version of jarvis's interface into the application",
with the concept image `command-dashboard-concept-20261005.jpg` (from the owner's `Copy of Untitled presentation.pdf`,
one page, one picture). Owner decisions the same day: **"Same look, real data only"** and **"In 1.0.15"**.

## Rule

Same layout, glowing core, panels and style as the concept, but every value on screen comes from a real source and
says what it covers. Nothing is invented: a panel JARVIS has no source for is replaced by a real one or says "not
connected". Configured is not the same as tested (`verified_status.GUIDANCE`); the dashboard says "configured" or
"ready" for configuration and keeps live tests in Settings.

## Panel by panel

| Concept | Dashboard | Source |
|---|---|---|
| Header: Teague Industries, JARVIS, "Intelligence amplifies humanity", date and time | Same branding and taglines; the PC's clock | browser clock |
| "Secure / Private / Always on your side" | "Local core / 127.0.0.1 / Keys stay on this PC" (facts, not claims) | fixed text |
| System status (Core AI, processing cluster, memory, global network, security matrix, auxiliary) + "100% operational" | Core, AI provider, memory store, voice, web search, devices; ring = rows ready out of six, labelled "ready", not "operational" | `/api/state` capabilities, counts, device registry |
| Device ecosystem (suit, workstation, mobile, lab, vehicles, home, satellites, facility) | Devices JARVIS supports: this PC (workstation), phone, glasses; "not paired" until they are | device registry |
| Global network (map, facilities, cities, uptime) | Knowledge: saved memories, documents, notes, conversations | `/api/state` |
| Central core "JARVIS core online, thinking, learning, supporting" | Existing core visual restyled; status follows the real assistant state (idle, listening, thinking, speaking) and the connection to the Core | assistant state |
| Side labels (analyze ... protection) | Capabilities JARVIS has, dimmed when not configured (for example Vision without a vision model) | capabilities |
| "Human potential. Amplified." + progress bar | Tagline kept; the bar shows activity (moving while thinking), never a made-up percentage | assistant state |
| Bottom tiles (overview, browser, projects, technology, security, automation, settings) | Shortcuts to existing sections (Command, Communications, Web, Projects, Memory, Focus & tasks, Settings); top navigation stays | navigation |
| Voice input: listening, waveform, "Just say the word." | Microphone state and live level from the microphone while listening; "Say 'Hey Jarvis'" | voice front end |
| Live diagnostics: CPU, GPU, memory, temperature, network, power, storage, AI load | Processor, memory, disk (JARVIS data drive), Core uptime, last response time, AI model; small graphs from readings taken while the page is open. Graphics, temperature, network and power are not measured, so not shown | `/api/metrics` (`system_metrics.py`) |
| Active projects with percentages | Saved projects; a bar only where it can be computed from linked tasks | `/api/state` projects, tasks |
| Upcoming (meetings) | Reminders and timers due today; "Nothing scheduled" when empty | `/api/state` reminders |

Out of scope for 1.0.15: phone and glasses clients, network and graphics telemetry, calendar integration.
