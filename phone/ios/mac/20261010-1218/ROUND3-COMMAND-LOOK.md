# Round 3: the command look (owner: "build the command look", 2026-10-07)

The owner showed a desktop command-centre picture (Teague Industries header, JARVIS core orb, system status with a
ring, device ecosystem, global network, voice input, live diagnostics tiles with sparklines, active projects,
upcoming, a bottom navigation) and a glowing core orb, and asked for the phone app to have that look. This record
says what is built, from which real data, and what is left out and why. CLAUDE.md's rules apply: real data only
(nothing on screen the Core does not send), the colour system of the design brief, captions never under 9 pt,
touch targets 44 pt, the emergency stop on every screen.

## 1. What changes

| Where | Change |
|---|---|
| Third tab | `StatusView` becomes `OverviewView` (tab label "Overview", same place, same gauge icon). Everything the old Status screen showed is still shown, inside the new panels. |
| Ask screen | The rings (`CoreRing`) are replaced by the new `CoreOrb`; the six readouts around it stay. The reply being written on the PC (Core 1.0.17, `assistant.draft`) shows as a dashed JARVIS bubble marked "Writing…" until the finished line replaces it. |
| Header word | "Offline" instead of "Not reached" (one shared `HeaderState` on Ask and Overview): the round 2 run showed the long word cutting the title to "JA…". |
| New file `CoreOrb.swift` | The glowing core: a bright nucleus, three tilted "petal" rings turning slowly, thin rings with tick marks, four bright arcs on the outer ring, a faint crosshair with bright nodes. Colour and speed follow JARVIS's state as the old rings did (cyan standing by, green listening and pulsing with the microphone level, amber thinking or working, red stopped, grey and still when the Core is not reached). Still when the system's Reduce Motion is on. |
| New file `Hud.swift` | The panel chrome of the picture: `HudPanel` (title row with a right-hand status word, cut corners, cyan rule), `HudStrip` (brand line and the real date and time), `Sparkline`, `ProgressRing`, `DiagnosticTile`, `WaveformBars`. |
| `SessionModel` | Keeps the last 60 health samples (CPU, memory, storage, link ms) while a screen polls, for the sparklines; keeps the microphone level trace of the current hold for the waveform, cleared when the hold ends; keeps the Core's draft of a reply (`writing`) while it is written, never spoken. The health polling has one owner, `MainTabs` (on for Ask and Overview, off on Chats, the lock and the pairing screen). Nothing new is sent to the Core. |
| `AudioRecorder` | Reports the sound level of each buffer (RMS of the PCM it already converts) beside the seconds it already reports. |
| `SettingsSheet` | The About line reads the app's version from the bundle instead of a fixed "1.1". |
| Project | MARKETING_VERSION 1.2 (round 3). |
| UI tests | The tab name "Status" becomes "Overview"; the header check also measures the title's width (a cut title keeps its full label) and skips the state word on Chats, which has none; the header and question checks fail plainly when the Core is not reached instead of passing on the question line alone. |
| Core request 1.0.17 | `assistant.draft` handled in `SessionModel.follow`: the whole text so far replaces the last draft, an empty text removes it, the finished reply replaces it, and a failure, a cancel, a new question, an interruption or the end of the pairing clears it. |

## 2. The Overview screen, top to bottom (393 pt wide, scrolling)

1. **Header** as on every screen: badge, JARVIS, subtitle "Command overview", the state dot and word, STOP ALL, the
   settings button.
2. **Strip**: "TEAGUE INDUSTRIES" and "Intelligence amplifies humanity" (brand words, not data) on the left; the real
   date and time on the right (the phone's clock, updated every minute).
3. **Core panel**: title "JARVIS CORE", right word = the state ("CORE ONLINE", "NOT REACHED", "EMERGENCY STOP",
   "THINKING", ...). The orb at 220 pt; the microphone widens its glow only while listening, and a change of state
   changes the pace of its motion, never its angle. Under it one line: the Core's version and uptime. (No motto
   under the orb: "Thinking. Learning. Supporting." beside a state word read as a claim about the Core; the brand
   lines live in the strip and the footer.)
4. **System status**: title "SYSTEM STATUS", right word "ALL SYSTEMS NOMINAL" (green) when six of six are ready,
   "N OF 6 READY" (amber) otherwise, "CORE NOT REACHED" (red) when the link is down. Left: six rows, each a dot, a
   name and a state word. Right: a ring with "N/6" and "READY".

   | Row | Ready when | Source |
   |---|---|---|
   | CORE LINK | the last request was answered | `reached` (hello/status/metrics round trip) |
   | CORE AI | the Core has a provider key | `metrics.ai_ready` |
   | SPEECH RECOGNITION | the owner allows this phone's microphone | `hello`/`status` allowed list contains `microphone` |
   | VOICE | the owner allows this phone's speakers | allowed list contains `speakers` |
   | EMERGENCY STOP | not stopped | `stopped` |
   | THIS PHONE | paired, with its name | `paired`, `deviceName` |
5. **Live diagnostics**: title "LIVE DIAGNOSTICS", right word the time of the Core's last sample. Four tiles, two by
   two: CPU %, MEMORY %, STORAGE %, LINK ms, each with its value and a sparkline of the last samples (while this
   screen or Ask is open; the trace starts empty and draws nothing until two samples exist). Under the tiles the
   Core's "Last reply N s" when it reports one, then: "CPU, memory and storage are read by the Core on the PC; link
   is this phone's round trip. Graphics, temperature, power and network traffic are not measured." Not shown: GPU,
   TEMP, POWER, NETWORK, AI LOAD from the picture (the Core measures none of them).
6. **Voice input**, fixed under the scrolling panels (not inside the scroll view: a hold on the microphone must
   never be handed to a scroll, which would leave the microphone open): title "VOICE INPUT", right word "LISTENING"
   while the hold is on, else "STANDING BY" (or the state). Left: the same hold-to-speak button as Ask. Right: the
   waveform, live bars from the microphone level during a hold and a flat baseline otherwise, with a hint under it
   ("Hold to speak.", the seconds of the hold, "RESUME on the PC." when stopped, "Microphone not allowed on the PC."
   when the owner has not allowed it). Under both the last line of the conversation, or the reply being written,
   one line cut, so a question asked here is seen to be answered; the full exchange is on Ask.
7. **Active projects**: title "ACTIVE PROJECTS", right word "N ACTIVE · M OPEN TASKS" (the Core's count of all open
   tasks, as the old Status screen showed it). A row per project from `overview.projects`:
   folder mark, name, a bar proportional to its open tasks against the largest, the count. Empty: "No projects on
   the PC."
8. **Upcoming**: title "UPCOMING", right word "N IN 24 H". A row per reminder from `overview.reminders`: time,
   title, "Done" when fired. Empty: "Nothing in the next 24 hours."
9. **This phone**: title "THIS PHONE", right word "PAIRED". Rows: connection and round trip, the Core's address,
   paired as, may save, the device id's first and last four characters (the old Status rows).
10. **Footer**: "TEAGUE INDUSTRIES OS · JARVIS FOR IPHONE <bundle version> · CORE <core version>".

## 3. Left out, said plainly

- **Device ecosystem** (suit, workstation, mobile, lab, vehicles, home, satellites, facility): the Core gives a
  phone no list of other devices. A fair request to the PC session (a `devices` read for paired devices).
- **Global network** (facilities, cities, continents, uptime %): no such data exists.
- **GPU, temperature, power, network speed, AI load**: the Core does not measure them, on the PC either.
- **The side word columns** (ANALYZE ... PROTECTION): decorative capabilities the app does not have (vision is
  version 2); left out rather than claimed.
- **Bottom navigation of seven items**: the phone keeps its three tabs; the picture's Browser, Technology, Security
  and Automation have no phone counterpart.

## 4. Checks for this round

Independent review of 2026-10-07 (one reviewer agent, read-only, against the contract and CLAUDE.md): 2 high,
3 medium, 12 low, all applied. High: the two screens' own start/stop of the one polling loop raced at a tab switch
(now one owner, `MainTabs`); the hold-to-speak button inside the Overview's scroll view could hand a hold to the
scroll and leave the microphone open (the voice panel is now fixed under the scroll). Medium: the microphone level
outlived the hold (cleared when a hold ends; the orb lifts only while listening); the motto under the orb read as a
state (removed); the Core's open-task count was decoded and not shown (in the projects' status word). Low: shrink
factors under 9 pt removed; `Theme.text` instead of white in the orb; the User-Agent reads the bundle version; one
shared header rule; the orb's phase carried across state changes; stale comments and the `Screen.status` case;
Core data cleared alike on forget and on a refused key; the title-width assertion in the UI test; the tiles' note
names the link as the phone's own; an empty sparkline draws nothing; this record amended; the unused sample time
dropped.

Built here, one independent reviewer on the files against the contract and these rules, findings applied; then
the signed build installed on the phone and the UI test's header check extended to the Overview; screenshots of
Ask and Overview in `records/round3-<date>/`; RESULTS.md gets a round 3 table; STATUS.md updated; a copy back to
the PC at the end of the round.
