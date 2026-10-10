# The `devices` route for paired devices (release 1.0.18)

Owner, 2026-10-10: "add devices to 1.0.18". The form for the Mac session (`docs/MAC-REQUESTS-20261007.md`, R6, asked
by the Mac) promised paired devices a `devices` operation for the app's device panel, and the Mac built the panel
against it; the Core never got it (`device_gateway.OPS` lacked it), so 1.0.17 answers HTTP 400 "Operation
unavailable." and the panel shows "not on this Core yet". Found on 2026-10-10 while writing the Mac brief
(`docs/MAC-BRIEF-20261010.md`), after 1.0.18 build 1 (`1.0.18-4afd891c38f4`) had passed every check on this PC; the
owner chose to add it to 1.0.18, so 1.0.18 is built again (build 2) and every check runs again.

## 1. What was built

- `device_gateway.OPS` gains `devices`. The gateway's own rules are unchanged: the device's key on every request, a
  revoked device refused, the device's presence and "last seen" written as for every request.
- `wearables.service.Service.list_devices`: `devices` is a light read, counted with `conversations`, `history`,
  `metrics`, `overview`, `approvals` and `notices` (120 a minute per paired device; the same-PC test client does not
  get it), and read outside the device's session lock: it waits up to two seconds for the lock to count, instead of
  answering "Wearable service busy." at once (review L1). Request `{}` only. It answers also while the emergency stop
  holds, as `conversations`, `history`, `metrics`, `overview` and `notices` do (`approvals` is refused then).
- `server.App.devices_for_device(device_id)`: built from `App.device_rows`, the same rows as the owner's
  Settings > Devices. `devices`: the paired devices that are not revoked and whose key belongs to this installation
  (a restored device whose key was made for another one can never reach this Core; the PC's panel shows it with
  "pair it again", the phone's list leaves it out: review L2), in pairing order, each with exactly `id`, `name`, `kind`, `online` (talked to the Core in the last two minutes and not said `bye` since),
  `last_seen`, `allowed`, `writes` (either saving tick, as in `hello`), `tools`, `approve`, `this_device`. `pc`: the
  PC's own name (`server.pc_name`: Windows' host name, else `COMPUTERNAME`, else "This PC"; at most 60 printable
  characters), `core_version` (the installed release, as in `metrics`), `online: true`. `simulated`: the same-PC test
  clients as the PC lists them, with `name`, `kind`, `online`.
- Never a key, a pairing code, a revoked device, what a device declared but the owner did not allow, or anything
  about a device's conversations.
- The form gained section 7 with the route as built (the example now shows `online` on a simulated item and the PC's
  real name in lower case); the Mac brief says 1.0.17 refuses it and 1.0.18 serves it; `docs/DEVICES.md` section 3
  lists the reads; the 1.0.18 release note says it in one sentence.

## 2. Tests (`test_device_list.py`, 8)

Through a real local Core: a phone, a pair of glasses and a revoked phone, with the ticks set on the PC; the phone's
list has the two that are not revoked, in pairing order, with exactly the ten fields, itself online and marked, the
glasses offline until they talk and then online for every device's list, the ticks as set (`writes` true with the
tools tick), the PC with `pc_name()` and the Core's release, the glasses test client as simulated; no key, no revoked
id or name, no `key_valid`, `declared`, `revoked` or `pairing` in the answer. A body with a field: "Unknown fields.";
after 120 reads in a minute: the limit sentence; no key or a revoked key: 401; the same-PC test client: 400. While the
emergency stop holds the list still answers and nothing changes. Through the private-network door (the test door on
127.0.0.2): the list answers with the device marked. After the review: a capability declared later and not allowed
appears nowhere and `allowed` is unchanged; the saving tick alone gives `writes` without `tools`; `bye` makes a device
offline at once; a device whose key belongs to another installation is left out; with the device's session held by
another request the list waits for its turn (at least 0.25 s here) and answers. `pc_name`: the host name, `COMPUTERNAME` when the host name is
blank, "This PC" when neither is there or the name is not printable, cut to 60 characters. The device, phone, door and
wearable modules (109 tests, these 8 included) pass.

## 3. Independent review (one reviewer agent, 2026-10-10: no high, no medium, 5 low; all applied)

The reviewer read commit 381b1f5, ran `test_device_list` and 12 related modules (124 tests, all passing) and one
experiment of its own: 40 times `overview` and `devices` sent at the same moment by one phone through a real local
server gave 5 "Wearable service busy." answers in 80.

1. **Low, L1: two reads at once could answer "busy", and the form did not say so.** Fixed: `devices` counts under the
   session lock, waiting up to two seconds for it, and reads outside it (`Service.list_devices`, like
   `answer_approval`); section 0 of the form now says that a device's requests share one session, so two sent at the
   same moment can get "Wearable service busy.", and to send reads one after another or retry once. Test: the list
   waits while the session is held, then answers.
2. **Low, L2: a device whose key belongs to another installation was listed as a normal device**, while the PC's
   panel says "pair it again"; after a restore the phone would show a second, dead "My phone" with its old ticks.
   Fixed: left out of the phone's list (`key_valid`); said in section 7 and here. Test added.
3. **Low, L3: the form contradicted itself on the emergency stop.** Section 0 said everything but `stop`, `hello`,
   `status` and `bye` was refused while stopped; the Core has always answered the reads, `events` and `cancel`.
   Fixed: section 0 lists what is refused and what answers (checked in `wearables/service.py` and `server.App.
   start_run`); this record's sentence corrected (`approvals` is refused while stopped); the Mac brief lists the
   correction as change 10.
4. **Low, L4: the form did not list the `kind` values**, and the PC session's own helper pairs as `computer`. Fixed:
   section 7 lists `phone`, `glasses`, `computer`, `other` (simulated: `glasses` or `other`) and says to show any
   other value as "other"; and that `bye` makes a device offline at once.
5. **Low, L5: test gaps** (a capability declared but not allowed, the saving tick alone, offline after `bye`, L2's
   rows). Fixed: the tests above.

Checked and found right by the reviewer: the fields, types and order against sections 2 and 7; `writes` as in `hello`;
`core_version` as in `metrics`; revoked devices left out, also those known only from the list beside the secret;
nothing secret crossing; listing other devices' ticks to any paired device acceptable (every paired device is the
owner's, as for the notices); the 120-a-minute limit; a revoke landing mid-request lets at most one last list through,
as for every read; the refusals and the private-network door; `pc_name` (`thegrizzlybear` here, local, only `OSError`
caught); line endings.
