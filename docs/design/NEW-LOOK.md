# New look for the whole interface (release 1.0.15)

Owner request, 2026-10-05, with four pictures: "both and use this as a guide I want the whole interface to have
this new design and be more organised" ("both" = apply the ten review findings and build the new look). Earlier
the same day: "I want it to have this look". The owner's rule from the first dashboard still applies: **"Same
look, real data only."**

The four pictures (saved here, the guide for this work):

| File | What it shows |
|---|---|
| `new-look-20261005-4-dashboard-v2.webp` | The dashboard: header with one row of sections, greeting card, recent activity, performance rings, the core over an Earth horizon, suggestion chips, ask bar, map, missions, schedule, quick tools |
| `new-look-20261005-1-teague-brand-scene.webp` | Teague Industries brand scene: chrome T above the Earth's horizon |
| `new-look-20261005-2-jarvis-logo.webp` | JARVIS logo: chrome T in a ring with blue arcs |
| `new-look-20261005-3-one-core-globe.webp` | "One core · many capabilities" globe |

## What was built

Three layers, all presentation; no control or handler was removed.

1. **Shell, every section** (`static/horizon.js`, `static/horizon.css`, loaded last):
   - Logo: `static/assets/branding/teague/jarvis-mark.svg` (the T in a ring, drawn after picture 2).
   - Header in one row: JARVIS / AI COMMAND CENTER, the sections, command search (opens the existing Ctrl K palette),
     connection, clock.
   - **Organised navigation:** eight everyday sections (Dashboard, Chat, Tasks, Projects, Memory, Files, Web, Maps),
     the rest under **More** (System status, Activity log, Diagrams, Release history, Applications), Settings last.
     These are the existing buttons, moved and relabelled; voice navigation ("open projects") is unchanged. In a
     narrow window sections that do not fit move under More and come back when there is room.
   - Strip under the header: "ONE CORE // MANY CAPABILITIES // LOCAL AND PRIVATE" and the running version
     (installed release, or the development revision) from `/api/state`.
   - Background for every section: stars and the Earth's horizon with city lights, drawn on a canvas once per window
     size. It is a drawing, not data, and does not move.
   - One colour system (deep navy, blue glow, teal for "ready", amber for "check"), rounded panels, the same
     buttons and inputs in every section.
2. **Dashboard** (`static/command-dashboard.js`, `.css`, second layout). Every panel and its source:

| Picture | Dashboard | Source |
|---|---|---|
| Greeting, date, time, weather, quote | Greeting, date, time, the owner's location label if one is set, the quote. **No weather** (no source) | PC clock; location label from the clock setting |
| Recent activity (scan, sync, mail, news) | The five newest entries of the activity log | this session's events and the Core's audit trail (`/api/state` logs) |
| System performance: CPU, memory, storage, network | CPU, memory, storage rings; fourth ring = systems configured (n of 6). **No network ring** (not measured). Below: Core uptime, last reply, AI model | `/api/metrics`, `/api/state` |
| Core with Online / Listening / Processing / Analysing | The existing core canvas; Online, Listening, Thinking, Speaking light up from the real assistant state | assistant state |
| "Systems nominal" list | Core, AI, Memory, Voice, Search, Devices: green only when set up, amber when it needs a look; heading says "ALL CONFIGURED" or "n TO CHECK", never "nominal" | `/api/state` capabilities, settings, devices |
| "Good morning. I'm JARVIS. At your service." + waveform | Same greeting (with the preferred name); the waveform is the live microphone and is flat when the microphone is off | assistant state, microphone |
| Suggestion chips | Four requests that are sent to JARVIS as typed, plus "Analyse my screen" (opens the existing screen check) | existing `send()` and screen vision |
| Ask bar | Sends the question through the existing `send()` and opens Chat so the reply is seen; the left button turns the microphone on or off (same as F4) | existing controls |
| Global situation (world map, regions, missions, alerts) | **Left out** (no source). In its place: Core overview = devices (this PC, phone, glasses) and counts of memories, documents, notes, conversations | device registry, `/api/state` |
| Mission overview | Projects with progress counted from linked tasks that exist | `/api/workspaces`, tasks |
| Today's schedule | Reminders and tasks due today | `/api/state` |
| Quick tools | New note, Analyse, Timer, Search, Settings: each presses the existing control | existing controls |
| Footer: Teague Industries, Secure / Private / Trusted | Teague Industries · A brighter tomorrow; Local / Private / Always with you; a dot that is green only while the Core is connected | fixed text, connection |

3. **Other sections** keep their content and controls and take the shell and the colour system.

## The ten review findings (of 39901c5 and 5d0c96d) and where each was fixed

1. Stale data as ready when the Core is unreachable: the dashboard has three states (connecting, connected, lost);
   when lost, every Core value reads "unknown" or "-", and the first paint says CONNECTING.
2. "READY" overstated: the Voice row checks the chosen voice against what is configured (amber "NOT SET UP"
   otherwise), the ring is labelled CONFIGURED, the heading says ALL CONFIGURED or n TO CHECK.
3. Simulated wearable shown as "Offline": simulated is checked first ("Simulated only").
4. Waveform compared two different clocks: it now compares `Date.now()` with the `Date.now()` stamp, and is flat
   whenever the microphone is off.
5. "Last reply" counted failed runs: the Core records `completed` with each timing (`server.py`), and
   `system_metrics.snapshot` uses completed runs only (test extended).
6. Inspection renderer lacked the dashboard files and metrics: `inspection_runtime.STATIC` now holds every file the
   page loads, `/api/metrics` answers "omitted", and `test_inspection_browser.py` keeps the list in step with
   `index.html`.
7. `pro.css` clipped the tiles at 1150 px or less: the second layout has no tile bar; the header sets its own height.
8. Live region re-announced every 1.5 s: only the mode line is a live region and it is rewritten only on change.
9. Conversations capped at 100: shown as "100+". Deleted linked tasks no longer count towards project progress.
10. Push-to-talk showed wake-word text: the voice line distinguishes hold-to-talk, listening, waiting for the wake
    word and microphone off. The dashboard padding now carries `!important` (teague.css sets `padding:0!important`).

## Not done / owner may change

- Weather, world map, mail and news counts: no real source, so not shown. A weather source or a calendar would be a
  new connection (owner decision).
- Navigation grouping and the new section names (Chat, Tasks, Activity log, Release history) are Claude's choice.
- The earlier `command-background.png` scene and the first dashboard layout are replaced by this one.
