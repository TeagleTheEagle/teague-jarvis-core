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
- `wearables.service.Service`: `devices` is a light read, counted with `conversations`, `history`, `metrics`,
  `overview`, `approvals` and `notices` (120 a minute per paired device; the same-PC test client does not get it).
  Request `{}` only. It answers also while the emergency stop holds, as the other reads do.
- `server.App.devices_for_device(device_id)`: built from `App.device_rows`, the same rows as the owner's
  Settings > Devices, so the phone and the PC never disagree. `devices`: the paired devices that are not revoked, in
  pairing order, each with exactly `id`, `name`, `kind`, `online` (talked to the Core in the last two minutes),
  `last_seen`, `allowed`, `writes` (either saving tick, as in `hello`), `tools`, `approve`, `this_device`. `pc`: the
  PC's own name (`server.pc_name`: Windows' host name, else `COMPUTERNAME`, else "This PC"; at most 60 printable
  characters), `core_version` (the installed release, as in `metrics`), `online: true`. `simulated`: the same-PC test
  clients as the PC lists them, with `name`, `kind`, `online`.
- Never a key, a pairing code, a revoked device, what a device declared but the owner did not allow, or anything
  about a device's conversations.
- The form gained section 7 with the route as built (the example now shows `online` on a simulated item and the PC's
  real name in lower case); the Mac brief says 1.0.17 refuses it and 1.0.18 serves it; `docs/DEVICES.md` section 3
  lists the reads; the 1.0.18 release note says it in one sentence.

## 2. Tests (`test_device_list.py`, 5)

Through a real local Core: a phone, a pair of glasses and a revoked phone, with the ticks set on the PC; the phone's
list has the two that are not revoked, in pairing order, with exactly the ten fields, itself online and marked, the
glasses offline until they talk and then online for every device's list, the ticks as set (`writes` true with the
tools tick), the PC with `pc_name()` and the Core's release, the glasses test client as simulated; no key, no revoked
id or name, no `key_valid`, `declared`, `revoked` or `pairing` in the answer. A body with a field: "Unknown fields.";
after 120 reads in a minute: the limit sentence; no key or a revoked key: 401; the same-PC test client: 400. While the
emergency stop holds the list still answers and nothing changes. Through the private-network door (the test door on
127.0.0.2): the list answers with the device marked. `pc_name`: the host name, `COMPUTERNAME` when the host name is
blank, "This PC" when neither is there or the name is not printable, cut to 60 characters. The device, phone and door
modules (82 tests) pass unchanged.

## 3. Independent review

(one reviewer agent; filled in when it returns)
