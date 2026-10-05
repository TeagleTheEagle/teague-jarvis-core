# Command dashboard (release 1.0.15): first layout

**Superseded on 2026-10-05 by the second layout and the new look for the whole interface: see `NEW-LOOK.md`.**
This file is kept as the record of the first layout (commits 39901c5, 5d0c96d, f7776df) and of its review.

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

## As built (2026-10-05)

- `static/command-dashboard.css` and `static/command-dashboard.js` (new, loaded after `teague.css` / `teague.js`;
  registered in the server's static allowlist). They add `.cd-on` to `#commandView` and build the header band, side
  panels, centre overlay and tiles around the existing `.core-panel` / `canvas#core`, which stay where `app.js`
  expects them (one canvas, moved to the companion area on other views and back). No element `app.js` or `teague.js`
  looks up was removed.
- Data: `/api/state` (now also `devices` from the device registry), `/api/metrics`, `/api/workspaces`, `state.mode`,
  the microphone (an `AnalyserNode` on the capture source while listening, otherwise the level the voice front end
  already reports). A simulated device (the wearables test device) is shown as "Simulated only" and never counted.
- The old Command background image (`command-background.png`, never shipped, a 404) is no longer requested.
- Window sizes: full panels from 1500 px wide, compact panels down to 1181 px, core and tiles only below that; the
  header band hides below 960 px high. The side columns scroll if a short window cannot hold every panel.
- Checked in a sandbox Core (synthetic data, no keys, port 8799) at 1920x1080, 1280x900 and 760x560: no page
  errors, no horizontal overflow, the core canvas centred within 1 px, navigation to Communications and back keeps
  one canvas. Screenshots: `command-dashboard-preview-1920x1080.png`, `command-dashboard-preview-1280x900.png`.
  369 Python tests and the 17 interface scripts pass.
- After the owner's "get rid of this" (f7776df): the centre "JARVIS / CORE ONLINE" title is gone; the live mode
  shows under the activity bar.

## Independent review of 39901c5 and 5d0c96d: ten findings, all applied in 5f2ed59 (see `NEW-LOOK.md` for where)

Recorded 2026-10-05 from the session handover summary (the reviewer's own text was not carried over, so these are
the summarised findings). The owner chose "both" (fixes and the new look) the same day.

1. Stale data shows as ready when the Core is unreachable: show unknown, and "CONNECTING" before the first state.
2. "READY" overstates: the Voice row is always green, the ring can only read 5/6 or 6/6, and the note is hidden at
   960 px high or less. Check the voice profile against capabilities; say "CONFIGURED" or keep the note visible.
3. The expired simulated wearable shows "Offline": check simulated first.
4. The waveform compares `performance.now()` with `frameAt`, which is set from `Date.now()`, so it keeps drawing
   when the microphone is off.
5. "Last reply" includes failed runs: record the outcome in timings and use completed runs only.
6. `inspection_runtime` STATIC lacks the dashboard files and metrics: add them, plus a test that keeps STATIC in
   step with the tags in `index.html`.
7. `pro.css` limits the navigation height to 45 px at 1150 px wide or less, clipping the tiles: set `.cd-tiles`
   `height:auto`.
8. The live region re-announces every 1.5 s: put `aria-live` on the mode only and update it only on change.
9. Conversations are capped at 100: show "100+". Deleted linked tasks are counted: count only tasks that exist.
10. Push-to-talk still shows wake-word text; `teague.css` `padding:0!important` overrides the dashboard padding.

## New look shown by the owner (2026-10-05): built, see `NEW-LOOK.md`

The owner showed four images ("I want it to have this look"; "just look and tell me youve seen it"). The images
were sent again and are saved beside this file (`new-look-20261005-*.webp`). As described in the handover: a dashboard version 2 (Earth horizon, greeting, ask bar,
suggestion chips, recent activity, performance rings, world map, missions, schedule, quick tools); a Teague
Industries brand scene with the chrome T; a JARVIS logo (chrome T in a ring, "AI / Assistant", "Observe |
Understand | Assist | Innovate"); a "One core, many capabilities" globe. The real-data rule above still applies:
weather, the world map and emails need real sources or are left out.
