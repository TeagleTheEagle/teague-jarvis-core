# Devices the right way round (release 1.0.15, scope item 4)

Built 2026-10-06 in the repo only, independently reviewed (no high finding; 5 medium and 7 low, all applied:
section 8). Master document sections 5 and 19: ONE CORE, MANY DEVICES. A device is
introduced, pairs with the Core, says what it can do, and the Core decides. Being seen, registered or paired is not
permission to do everything; each capability is allowed by the owner, per device, and can be taken back at any time.

**Before:** the list of devices lived in memory only and was empty after every restart. A device was an id with
free-text capabilities; it had no name, no kind and no key. Every same-PC client shared one token. There was no
pairing, no revoking and no panel, and a client could declare itself "not simulated", so the dashboard would have
counted it as a real online device.

**What this does not do:** it opens no port. The Core still listens on `127.0.0.1` only (owner decision of
2026-10-01). So today only a program on this PC can pair. A phone or the glasses can pair once the owner has decided
how JARVIS is reached from other devices (section B of `docs/RELEASE-1.0.15-SCOPE.md`); the pairing, the keys and
the device-facing routes they will use are what this item builds.

**Release 1.0.16 (`docs/PHONE-CORE-1.0.16.md`, on the approved `docs/PHONE-PLAN.md`) builds on this record:** a switch in
Settings > Devices, off by default, opens a second door for the device routes only at the PC's Tailscale address
(`remote_devices.py`); wrong codes and wrong keys are counted per caller; a device may read its own conversations,
the PC's health and an overview; the answer route waits for news; and a per-device tick "may save memories and
tasks" lets the owner's own phone save things. Where that record and this one differ, the 1.0.16 record is current.

## 1. Who the devices are: `devices.py` (the device book)

Kept in the Core's database (table `devices`), so pairing survives a restart. A device has:

| | |
|---|---|
| name | given by the owner when pairing; can be renamed |
| kind | phone, glasses, computer or other |
| its own key | made at pairing, shown to the device once. Only a keyed hash is stored. |
| declared | what the device says it has: microphone, camera, speakers, display |
| allowed | what the owner lets it use, never more than it declares |
| last seen, revoked | times |

**The key is bound to this installation.** The hash is made with a secret kept in the config folder beside the key
file (`.env.device-secret`). The secret is made when the owner first starts a pairing, and a file that is there but
cannot be read is never written over (pairing is refused and says why): every paired device depends on it. A
backup carries the database but never that secret, so data restored into another installation brings no working
device keys: those devices show "its key belongs to another installation" and pair again.

**Revoking is remembered twice:** in the database, and in a small list beside the secret (`.env.device-revoked`).
So an older copy of the database put back into the same installation does not bring a revoked or removed device
back to life: its key stays refused, and its row says revoked. (The older `phone_bridge.py` keeps plain token hashes
in the database; it is unchanged and nothing starts it.)

## 2. Pairing: a code the owner reads from the PC

1. Owner, Settings > Devices: a name, a kind, PAIR A DEVICE. The Core shows an eight-digit code once. One pairing at
   a time; the code is good for five minutes and for one use. (1.0.15: five wrong codes ended the pairing. Since
   1.0.16 five wrong codes from one caller lock that caller out for fifteen minutes while the pairing keeps waiting,
   and the pairing ends after 25 wrong codes in all: `docs/PHONE-CORE-1.0.16.md` section 2.)
2. The device sends the code and what it declares (`POST /api/device/pair`). It gets its id and its key, once.
3. What it declared at that moment is allowed (the owner just paired it, on the PC); each item has a tick box in the
   panel. Anything it declares later is not allowed until the owner ticks it.

No pairing starts while the emergency stop holds. At most 20 devices; ten pairing attempts a minute (since 1.0.16 per
caller, and 60 a minute in all). The code is for whoever hands it over first: the owner reads it to their own device
and to nobody else.

**Known limit of 1.0.15, changed in 1.0.16 before the Core became reachable from elsewhere:** anyone who could reach
the pairing route could end a pairing with five wrong codes, or use up the ten attempts a minute so that the right
code had to wait. Since 1.0.16 the counts are per caller (`docs/PHONE-CORE-1.0.16.md` section 2). Guessing the code
itself is not practical (25 tries in a hundred million).

## 3. What a paired device can do: `device_gateway.py`

Routes `POST /api/device/<op>`, header `X-Jarvis-Device: <id>.<key>`. The same loopback and same-origin checks as
every route. The proof is the device's own key: these routes ask neither for the owner's session nor for the
desktop app's token, and a device's key opens none of the owner's routes. Decided on every request:

| Op | Needs | |
|---|---|---|
| `hello`, `status` | | who it is, what is allowed, whether JARVIS is stopped; `hello` may re-declare capabilities |
| `start` | camera allowed, if a picture is sent | a question. It may call only the tools marked for other devices in `permissions.py` (reads); memory commands and every changing tool stay on the PC |
| `events`, `cancel` | | only for its own questions. Its conversations are its own too: each starts with the device's id, and no device can write into or continue another's. Since 1.0.17 `events` also carries `assistant.draft` while the reply is written, when the PC's streaming setting is on |
| `transcribe` | microphone allowed | local speech recognition |
| `speech` | speakers allowed | speaks a text the device sends (up to 12,000 characters) with the voice JARVIS uses; meant for the reply |
| `stop` | | the emergency stop (docs/PERMISSIONS.md). Any paired device may stop; **none can resume**. A stop is handled before anything else about the request, also as the stop words in a question: it is not turned away because a picture came with it, a capability is not allowed, or the database is busy. (1.0.16: a stop with a valid key is never turned away by the per-caller lockout either; only a wrong key is counted) |
| `bye` | | marks it disconnected |

Each device has its own session (`wearables.service.Service`): its own questions, its own limit of 20 requests a
minute. A question's activity rows carry the device's id, and the activity log shows its name. A device is told
only a few fixed sentences when something is refused; nothing of the program's own error text, no path and nothing
from a provider crosses to it. "Pair this device again" is said only when its key is refused.

**Revoke:** from that moment the key is refused, what the device was running is cancelled, nothing stays allowed.
A revoke that lands while a request of that device is on its way in is looked for again during the request: the
request is refused and a question it just started is cancelled. The row stays (the activity log keeps the name)
until the owner removes it from the list.

## 4. The same-PC test client can no longer call itself real

`/api/wearable/` (one shared token, used to try the glasses pipeline) still works and still only reads. Whatever it
says about itself, it is listed as a simulated test client and is never counted as a device. Only a paired device
can be a real one (`App.device_rows`).

## 5. On screen

- **Settings > Devices** (`static/devices.js`): this PC, the test client if one is connected, every paired device
  with its state, last seen, a tick box per declared capability, RENAME (with SAVE NAME and CANCEL), REVOKE (two
  deliberate clicks: a double click does not count), REMOVE FROM LIST for a revoked one; and the pairing box with
  the code and its remaining time. The code stays on screen until it is used, cancelled or runs out.
- **Dashboard:** the three places (this PC, phone, glasses) are filled from what a device is (its kind), a real
  connected device first; a revoked one is not shown.
- **Emergency stop banner and activity log:** name the device ("from My phone").
- "Meta glasses" is "Halo glasses" in the Lab card.

## 6. Not in this item

- Reaching the Core from another machine (the owner's networking decision), the iPhone app, the Halo glasses,
  seeing devices on the Wi-Fi network: section B of the scope list.
- Rules per device and per tool beyond "other devices only read"; a device changing saved things.
- Moving `phone_bridge.py` onto the device book.

## 7. Checked

`test_devices.py` (7 tests: the device book by itself), `test_device_gateway.py` (16 tests through the Core's own
routes with a real local server, seven of them for the review's findings; the first nine: pairing needs the owner's session and the code works once; no device joins while
the emergency stop holds; a device survives a restart of the Core; only its own key opens the door and it opens
none of the owner's routes; a question from a device only reads and its activity rows name the device; another
device cannot look at its question; what it may use is the owner's choice; any paired device can stop everything
and none can resume; revoked means refused from the next request on, with what it ran cancelled; the test client
cannot declare itself real; the review's: a device's stop is never turned away; an older copy of the database
does not bring a revoked device back; a backup leaves the key files out; each device has its own conversations; a
revoke that lands during a request lets nothing through; only a refused key says "pair again"; the secret is made
on the owner's click and never written over), `test_devices_view.cjs` and `test_dashboard_model.cjs` (the words on screen, the three
places), `test_wearable_real.py` (the same-PC test client as before), `test_inspection_browser.py` (the inspection
renderer serves the new page files).

Sandbox preview Core (synthetic data, both provider keys blank), in a real window: Settings > Devices lists this
PC and the test client; PAIR A DEVICE shows a code with its remaining time; a made-up device on this PC handed the
code over and appeared with its tick boxes; unticking the camera made its next picture refused with a plain
sentence; its stop held and the banner said "from Halo test"; the activity log showed the device's name; the
dashboard's Glasses place said Online for a paired pair of glasses; REVOKE (two clicks) made its key refused; REMOVE
FROM LIST took it off the list. After the review, again in the window: RENAME with CANCEL and with SAVE NAME (the
list kept updating afterwards); two tick boxes clicked in quick succession (the second waits for the first); a
double click on REVOKE did not revoke, a second deliberate click did.

Not checked: a real phone or real glasses (none can reach the Core until the owner's networking decision); the
panel at full window size (seen in the small preview pane only); the desktop app itself.

## 8. Independent review (one reviewer, 2026-10-06): no high finding; 5 medium and 7 low, all applied

The reviewer read this document and the code (the device book and the gateway in full: they had never been
reviewed), ran the tests and its own experiments in temporary folders with an isolated Core. The fixes of this
section were not reviewed again.

**Medium**

1. A device's emergency stop could be turned away: the stop words with a picture from a device without the camera
   were refused, and a device's stop waited for the database (11 seconds during a backup) and then failed (run).
   **Fixed:** a stop is handled first; "last seen" is written at most once a minute and never fails a request.
2. The Devices panel froze after RENAME: the text box was never taken away, so the list stopped updating (run with
   a stand-in page). **Fixed** (SAVE NAME, CANCEL, Enter and Escape), and seen working in a real window.
3. Putting an older copy of the database back into the same installation revived a revoked device (run).
   **Fixed:** revoked devices are also listed beside the secret (section 1).
4. The check of a proposed style sheet (`docs/PERMISSIONS.md` section 4) did not refuse what its sentence said: tiny
   or huge sizes written with exponents or unusual units, a transparent colour hidden in a variable, the program's
   own layout variables, names reached by attribute selectors (run). **Fixed:** every number must be in a known unit
   and range, variables may hold colours only, attribute selectors are refused; the sentence was rewritten.
5. The same-PC glasses client refused a WAV voice (the Qwen voice) after the speech reply started to say what the
   sound really is (run). **Fixed:** it accepts and plays WAV as well as MP3.

**Low**

1. An isolated instance keeps the secret with its data, and its backups were then refused. **Fixed:** a backup
   leaves the key files out.
2. Devices shared one conversation. **Fixed:** each device's conversations start with its own id.
3. A revoke between the key check and the start of a question let that question through; a removed device could
   leave a row named by its id. **Fixed** (section 3); removing a device also ends its session.
4. Any "permission" error was answered with "key invalid, pair again"; a secret that could not be written used up
   the pairing; an unreadable secret was written over at the next pairing. **Fixed** (sections 1 and 3).
5. Two tick boxes clicked in quick succession: the second undid the first. **Fixed.**
6. Harmless style sheets were refused (a pill-shaped corner, a shadow to the upper left, a comment with the word
   "approval"), and Undo could be refused when the earlier sheet failed today's check. **Fixed:** those are
   accepted, and Undo always works.
7. A pairing can be ended or delayed without the code. **Said in section 2** as a limit to change before the Core
   is reachable from other machines.

Also fixed: raw program messages reaching a device; a picture that is not a picture answered as a service failure;
a fast double click on REVOKE; the sentence about the code on the pairing screen.

**Checked by the reviewer and found correct:** every device route except pairing needs a valid key before anything
else is looked at; a device's key opens none of eleven owner routes, and the owner's session and the test client's
token do not open the device door; a device cannot read or cancel anyone else's question; the key, the code, the
secret and the key's hash appear in no state, listing, tool result, export or activity row; pairing needs the
owner's session, works once, runs out, and is refused while stopped without using up attempts; a device's question
changes nothing saved; no device can resume; a missing or garbled secret means every key is refused; no test or
build can put the secret into the repository or a release.

**Not reached by the review:** the panel in a real browser (done afterwards by the author, section 7); real audio
playback of a WAV voice by the glasses client; the full test set (run by the author); timing of the key check.
