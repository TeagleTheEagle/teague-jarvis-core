# Core release 1.0.16, "the phone release" (docs/PHONE-PLAN.md section 5)

Built 2026-10-06 in the repo only, on the owner's approval of the phone plan ("I approve the phone plan",
`../governance/PHONE-PLAN-APPROVAL-RECORD.json`). Nothing here has reached the owner's installed JARVIS; the release
is not built yet (section 7). Independent review: section 8.

**Why a Core release comes before the phone** (read-only survey of 1.0.15, 2026-10-06): the Core listens on
`127.0.0.1` only, the address is fixed in the program, and every request must name exactly `127.0.0.1:<port>`; the
desktop app starts the Core on a random port at every start; a paired device cannot list or read its conversations,
read the PC's health or the Core version, or save a memory (its memory commands are skipped); the answer route hands
over everything it has at once, so a client has to ask again and again; the pairing limits were written for a Core
reachable from this PC only. Each of these would have stopped the phone.

## 1. The private-network door: `remote_devices.py` (plan item 1, decision D1 option A)

Settings > Devices > **Private network**: a switch, "Reach JARVIS from paired devices over the private network
(Tailscale)", and a port. **Off by default; turning it on is the owner's act** (`CLAUDE.md`: networking is
owner-only). The state lives in the `control` table beside the emergency stop and the automatic backups: not a
setting, so neither the settings page, the JSON export nor a restored JSON backup can reach it
(`Store.remote_devices_state`, `set_remote_devices_state`). Owner routes: `GET/POST /api/remote-devices`
({enabled, port}); the state also comes with `GET /api/devices` as `remote`.

**What the switch does.** The Core's own door is unchanged: `127.0.0.1` only, as before. When the switch is on and
this PC has a Tailscale address (one in `100.64.0.0/10`, asked of Tailscale's own command `tailscale ip -4` and of
nothing else: an address in that range on another adapter, say a carrier link, is not Tailscale and never gets the
door), a **second server object** (`remote_devices.Door`) is bound to **that address and the chosen port** (default
8790) and nowhere else, with Windows' exclusive-use flag so that no other process can share the address. Through
it only `POST /api/device/<op>` is served (`device_gateway.handle`, the same code as on the PC door); every other
path or method is answered 404 "Not available here" as one plain JSON line (GET, HEAD, PUT, DELETE, OPTIONS, PATCH,
a malformed request), including `/api/resume`, `/api/emergency-stop`, `/api/state`, the pages, the settings and the
same-PC test client's route; no answer names Python (the `Server` header says JARVIS, on both doors). A request
through that door must name the door: Host = the address, the PC's full Tailscale name or its short name (the
first label, as MagicDNS also resolves it), each with the port, compared in lower case; the name comes from
`tailscale status --json`, kept for a minute. A browser origin is never accepted there. A peer that connects and
says nothing is dropped after 30 seconds. The owner's session cookie and the desktop token open nothing at the
door, and a device's key opens nothing on the PC door (as before).

**When it cannot open.** No Tailscale address: the panel says which it is (Tailscale not installed, its command not
found; or installed but not running or signed out) and nothing is open. **A watcher** (`watch()`, a daemon thread
started by `server.main()`) looks for the address again every 15 seconds while the switch is on, so the door opens
by itself when Tailscale comes up and closes when the address goes away, whether or not the Settings panel is open.
The port held by something else: said plainly ("port 8790 at 100.x.y.z could not be opened (...)"), nothing is taken
over. The switch off: the door closes at once; paired devices stay paired and still come in through the PC door.
The door binds without the reverse DNS lookup Python's HTTP server normally makes of the bound address, which can
hang for seconds on a private address.

**At start.** `server.main()` calls `ensure()` once after the App is made and then starts the watcher, so the owner's
saved choice holds across a restart of the Core; an `App` made by a test or an isolated instance opens nothing by
itself. The watcher is stopped and the door closed when the Core stops. Activity rows: "private network door switch"
(on/off), "private network door" (open at, closed, could not open port).

**What this is not.** Not HTTPS (decision D1: Tailscale encrypts between the owner's devices; option B, Tailscale
Serve with a certificate, stays available later). Not reachable from the public internet: only a device signed into
the owner's Tailscale account has a route to the address. Not a change to the 2026-10-01 decision that the Core
lives on this PC: it still does.

## 2. Pairing limits for a reachable Core (plan item 2): `device_gateway.py`

Every caller is counted by its address (`handler.client_address`), and for keys also by the device id the request
claims:

| Rule | Was (1.0.15) | Now |
|---|---|---|
| Pairing calls | 10 a minute, one counter for everyone | 10 a minute **per caller**, and 60 a minute in all |
| Wrong codes | the fifth ended the pairing for everyone | **5 from one caller lock that caller out of pairing for 15 minutes**, with the pairing left waiting for the right device; the pairing ends after 25 wrong codes in all (`devices.PAIRING_ATTEMPTS`, 25 tries in a hundred million) |
| Wrong keys | no limit | **20 in a minute from one caller for one device id lock that caller out of that device id for 15 minutes** |

**A valid key is never a guess, so a request with a valid key is never turned away by a lockout:** the key is
checked first, and only a wrong one is counted. So the stop of a paired device always goes through, and a
same-PC program in a retry loop with a dead key (every local caller is `127.0.0.1`) locks out only its own device
id, not the owner's other devices. A locked-out caller is answered 429 "Too many attempts from this device. Wait
fifteen minutes." for the pairing route, or for further wrong keys of that device id. The lockout is written to the
activity log once, outside the gateway's lock ("device door: a caller is locked out", with the reason and the
caller's address). `devices.WrongCode` (a `DeviceError`) is how the device book tells a wrong code from every other
refusal. On the PC door, the Host header is compared exactly as in 1.0.15; only the private-network door compares
names in lower case.

## 3. What a device may read (plan item 3): `wearables/service.py`

Four device routes, for paired devices only (the same-PC glasses test client keeps its old surface), limited to
120 calls a minute per device on top of the 20 a minute for questions, speech and recordings:

| Op | Body | Answer |
|---|---|---|
| `conversations` | `{}` | this device's own conversations (ids starting with `device-<id>-`), newest first, at most 50: id, created, updated, message count, the first question (80 characters), the last line (160) |
| `history` | `{conversation, limit?}` (1 to 100, default 60) | the messages of one of its own conversations: id, role, content, created. Another device's, or the PC's: refused |
| `metrics` | `{}` | the dashboard's reading (`system_metrics.snapshot`: CPU, memory, disk of the data drive, uptime, last reply) plus `core_version` (the installed release id; "development <revision>" in development), `ai_ready` (a key for the chosen provider is present) and `stopped`. Nothing new is measured: no graphics, no temperature |
| `overview` | `{}` | open tasks (count), the reminders due within 24 hours, the projects with their open-task counts, and the number of its own conversations |

The answer route `events` takes an optional cursor, `{run_id, after}`: it then **waits up to ten seconds for new
events** (as the PC window's `/api/runs/<id>/events` does) and returns only those after the cursor. The wait holds
no lock of the device's session, so a `cancel` or a `stop` is never held up by it. Without `after` the route
answers at once with everything, as before (the glasses client).

Also: a device's recording is **no longer turned into text while the emergency stop holds** (`transcribe` is refused
with the stop message; in 1.0.15 only the question that followed was refused).

## 4. "May save memories and tasks" (plan item 4, decision D2): `devices.py`, `permissions.py`, `server.py`

A tick per device in Settings > Devices, **off for every new device**, kept as a column `writes` of the device
book (an older database gets the column; an older JARVIS after a rollback ignores it). Owner action
`POST /api/devices {action: "writes", id, allowed}`; `hello` and `status` tell the device (`writes`, and `scope`
says "Questions, reading, and saving memories, notes, tasks and timers." or, without the tick, as before). Revoking
takes the tick away.

With the tick, a question from that device:

- runs the owner's **exact memory commands** on the PC as the PC's own questions do ("remember that I prefer ...",
  "forget memory: ...", "my name is ..."), under the same switches in Settings > Permissions;
- may call the four **saving tools** marked `device_writes` in the permissions table: `save_item` (a note, a task or,
  on the owner's own words, a fact), `set_timer`, `manage_timer`, `manage_saved_memory`. The model is told so in its
  instructions. A tool the owner set to "Ask first" asks on the PC: the device is told "waiting for approval", and
  the approval names the device;
- can still do nothing else that changes something: desktop control, the interface, settings, projects, files,
  resume and JARVIS's own program stay refused ("This operation is unavailable from the wearable client.").

Without the tick, a device that tries is told what would allow it: "... this device may not save memories or tasks.
The owner allows that in Settings > Devices on the PC." `permissions.decide` takes `writes`; `App.start_run` and
`Run` carry it; `App.work` (memory commands, the tools offered) and `App.instructions` read it at the start of the
question, and `App.tool` reads the tick **again from the device book at every tool call** (`App.device_writes`), so
a tick taken back while a question runs stops that question's next saving at once.

## 5. On screen (`static/devices.js`, `devices.css`)

Settings > Devices gained the **Private network** box (switch, port, the Core's own sentence about the door in
green when open, amber when on with nothing open, grey when off; a note on what the door is) and, in every paired
device's row, the tick **May save memories and tasks**. The words come from the Core's answer; the panel never
shows the door as open or a device as allowed unless the Core says so (`JarvisDevices.doorText`, `doorClass`,
`writesText`, tested in `test_devices_view.cjs`). The box is not redrawn while the owner's cursor is in it.

## 6. What the phone will do with this (for `phone/ios`, plan section 6)

Pair through the door with the code; keep `credential` in the Keychain; `hello` at start (declaring microphone and
speakers); `start` then `events {run_id, after}` in a loop until `done`; `speech {text}` for the reply's sound;
`transcribe {data}` for hold-to-speak (16 kHz mono PCM, base64, at most 30 s); `conversations` and `history` for
the Chats screen; `metrics` and `overview` for Status (the link time is the phone's own round trip of `status`);
`stop` for STOP. Protocol field: 2. Since 1.0.17 the events of a device's question also carry `assistant.draft`
(the whole reply so far, as far as the claim checks have passed it, at most every half second) when the PC's
"Show replies while they are written" setting is on; the finished reply still comes as `assistant.delta` and
`assistant.completed`, and a draft is never a claim the checks would change (docs/PHONE-CORE-FIXES-20261007.md).

## 7. Checked

- `test_remote_devices.py` (6 tests): off by default and nothing listens; the switch is not a setting and no
  device key reaches it; on: bound to the private address only (127.0.0.2 stands in for the Tailscale address in
  the tests), device routes through the door by address, by full name and by short name, pairing and the stop
  through the door, the PC door still refuses the private address, nothing else served through the door (eight
  owner routes and pages, the test client's route; GET, HEAD, PUT, DELETE, OPTIONS, PATCH and a malformed request
  all get the one JSON line, and no answer names Python), no browser origin and no wrong Host, off again closes at
  once and the device still comes in on the PC; Tailscale not installed, or no address, or a taken port: nothing
  opens and the panel says which; the owner's input checked; the saved switch holds across a restart of the Core;
  the watcher opens the door when the address appears and closes it when it goes, with no status call made, and
  stops with the Core; finding the address and the name (only from Tailscale's own answers).
- `test_phone_core.py` (13 tests): wrong codes lock the caller out of pairing and leave the pairing waiting; pairing
  calls limited per caller without ending anything; wrong keys lock the caller out of that device id and never a
  valid key (the device's own stop goes through while locked); without the tick a device only reads (tool refused,
  memory command not a command); with the tick memories and timers are saved from the device, the activity rows
  name it, everything else stays refused, and taking the tick back works; a tick taken back during a question stops
  that question's next saving; "Ask first" asks on the PC; revoking takes the tick away; a device lists and reads
  only its own conversations; the PC's health and the overview; the answer route waits for news and holds nothing
  up; a recording is refused while stopped; the permission table opens only the four saving tools to the tick.
- `test_devices.py`: the tick in the device book and the column added to an older database; the pairing's
  wrong-code count is now `WrongCode`. `test_devices_view.cjs`: the words of the door and the tick.
- The earlier suites that touch these modules (`test_device_gateway.py`, `test_permissions.py`,
  `test_permissions_review.py`, `test_wearable_real.py`, `test_reply_stream.py`, `test_answer_mode.py`) pass unchanged.
- Whole development tree after the change and the review fixes: 654 Python tests, 52 desktop tests, 18 Intelligence
  tests and 23 interface scripts pass (the first full run found one of the earlier gateway tests handing the session
  helper a device id where the new code expected the device's row; the helper now takes either).

Not checked: a real Tailscale address (none on this PC; the owner installs Tailscale at step 6 of the plan), a real
phone, the desktop app itself; the panel was looked at in a sandbox Core only (section 7a).

## 7a. In a window

Sandbox preview Core (synthetic data in `D:\JARVIS-release-work\dashboard-preview`, both provider keys blank, port
8799; the private-network switch was NOT turned on), Edge through Playwright at 1280 x 900, pictures and the words
read from the page in `docs/release-rehearsal-20261006-1016/devices-panel/`: Settings > Devices shows the Private
network box with the switch off, port 8790 and the grey sentence "Off. JARVIS listens only on this PC."; a pretend
device paired with the code read from the page (through the PC door) and appeared with its Microphone and Speakers
ticks and the tick "May save memories and tasks", off; ticking it made the device's own `hello` say "Questions,
reading, and saving memories, notes, tasks and timers."; REVOKE (two deliberate clicks) and REMOVE FROM LIST took it
off again. The row read "Not connected" in the picture because the panel had not reloaded in the two seconds after
the device's first `hello`: the next load shows it online (the same as in 1.0.15).

## 8. Independent review (one reviewer, 2026-10-06): no high finding; 3 medium and 11 low, all applied

The reviewer read the record and the plan, every changed file in full, ran the device, permission and wearable test
modules and its own experiments with an isolated Core (door on 127.0.0.2, callers from two loopback addresses;
nothing of the installed JARVIS touched). The fixes below were not reviewed again; the tests named in section 7
cover them.

**Medium**

1. On the PC door every caller is 127.0.0.1, so the key lockout was collective: twenty wrong keys from any local
   program answered every other local device 429 for fifteen minutes, the stop included (run). **Fixed:** the key
   is checked first and only a wrong one is counted, so a valid key, and so a device's stop, is never turned away by
   a lockout; wrong keys are counted per caller and per claimed device id.
2. The door did not open or close by itself: `ensure()` ran only when the panel or `main()` asked, so with the
   switch on and Tailscale starting later the door stayed closed until Settings > Devices was opened (run).
   **Fixed:** the watcher thread (section 1), started by `main()`.
3. The lockout's activity row was written while holding the gateway's lock that every device request takes, so a
   busy database at that moment held every device request, other devices' stops included (run: 1.9 s). **Fixed:**
   the row is written outside the lock, and a request with a valid key no longer takes that lock at all.

**Low**

4. The tick was a snapshot per question: unticking during a question changed nothing for it (run). **Fixed:**
   `App.tool` re-reads the tick from the device book at every tool call.
5. Other methods at the door got Python's HTML 501 page, and every answer carried `Server: BaseHTTP/0.6
   Python/3.12` (run). **Fixed:** one JSON line for every method and malformed request; `Server: JARVIS` on both doors.
6. Only the address and the full Tailscale name were accepted as Host; the short MagicDNS name was refused (run).
   **Fixed:** the short name is accepted too; the record says what the phone may use.
7. When Tailscale's command was missing or failed, any address of this PC in 100.64.0.0/10 was taken for
   Tailscale, a carrier link included (read). **Fixed:** the address comes from Tailscale's own command only.
8. No request timeout on the door (read). **Fixed:** 30 seconds.
9. `allow_reuse_address = False` does not stop a same-user process from sharing the address on Windows (read).
   **Fixed:** the exclusive-use flag at bind.
10. The new files were untracked, and the release build takes the committed tree (read). **Done:** added to the
    commit, by name.
11. Records that said more or other than the code: `docs/PERMISSIONS.md` (no `device_writes`), `docs/DEVICES.md`
    sections 2 and 3, a comment in `devices.py`, this record (sections 1, 2, 3). **Fixed** in each.
12. The lockout row named no caller. **Fixed:** the address is in the row.
13. In the panel a port change and a switch click could race each other with two saves in flight (read).
    **Fixed:** one save at a time.
14. The PC door's Host check had become tolerant of case and whitespace (run). **Fixed:** exact, as in 1.0.15;
    only the private-network door compares names in lower case.

Found while fixing: Python's HTTP server looks up the bound address in reverse DNS when it binds, which hung for
seconds on 127.0.0.2 while the door's lock was held (the door tests took 80 s). **Fixed:** the door binds without
that lookup (the tests take 23 s).

**Checked by the reviewer and found correct:** through the door only `POST /api/device/<op>` reaches code; nine
owner routes, the page, the switch route and the test client's route are refused; the owner's cookie opens
nothing there; the door is bound to the found address only; a held port is refused and said plainly; the switch
off closes within half a second while an in-flight ten-second wait still gets its answer; `history` and
`conversations` are confined to the device's own prefix with a strict id pattern and LIKE escaping; `metrics`
carries no path and no key; `events_after` is free of lost wake-ups, holds no service lock, lets a cancel pass and
wakes when the run finishes; the tick is off for new devices, revoked means off, only the four saving tools open,
memory commands gated by the same tick, approvals name the device; the switch state is in the control table and
unreachable from settings, export and a device key; no key, code, secret or path in any device-facing message;
the glasses test client is unchanged except the recording refused while stopped.

**Not reached by the review:** a real Tailscale address or `tailscale status --json`; a real phone; the desktop app
itself; the whole test tree (run by the author, section 7); IPv6 (Tailscale also gives one; the door is IPv4 only,
so a phone that tries IPv6 first falls back after a failed attempt: said for the app's design); the fixes above.
