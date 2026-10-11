# The phone away from home: the PC stays on

Owner decision of 2026-10-06 (about 23:20 local): "keep pc on".

## 1. The question and the decision

The owner asked how the iPhone app can stay ONE JARVIS, ONE CORE and still work
without the PC. Three ways that keep one Core were put to the owner:

| Way | Cost | What it gives | What it costs |
|---|---|---|---|
| A Windows mini PC at home, always on (recommended) | about $300 to $600 once, about 10 W | memory and keys stay at home; reachable anywhere through Tailscale | a purchase; a Core release (remote-Core mode for the desktop app, the PC's own abilities routed to the PC as a device); the rule "the Core lives on the owner's PC" changed by the owner |
| A Windows VM in the cloud | about $40 to $70 a month | nothing to buy; always on | memory, keys and data off-site; "this PC" tools act on the VM; the same Core release |
| Keep the desktop PC on | nothing | no code change, no purchase | the PC is the owner's daily machine: sleep, a restart or a sign-out cuts the phone off |

Two shortcuts were excluded because they break the binding rule (ONE CORE, ONE
MEMORY, never a second Core, Store or AI stack on a device): a Core on the phone
(iOS cannot run the Python Core either) and the app talking to Qwen directly when
the Core cannot be reached (a second AI stack, a second memory, keys on the phone).

A sleeping PC cannot be woken from the phone through Tailscale without some other
always-on device, so "without the PC" means another machine.

The owner chose to keep the PC on. Effect: the Core stays on the owner's PC, the
binding rule is unchanged, nothing is bought and nothing in the Core, the app or
the installed JARVIS changes for this decision. The phone reaches JARVIS whenever
all four of these hold on the PC.

## 2. What has to be true on the PC

1. The PC is on, not asleep and not hibernated. The screen may be off. The PC may be locked.
2. The owner is signed in. JARVIS runs inside the owner's session and starts by itself
   about five to six minutes after sign-in. A sign-out or a shutdown stops it.
3. JARVIS is running (the everyday 1.0.16 at `%LOCALAPPDATA%\JARVIS`) with
   Settings > Devices > Private network ticked.
4. Tailscale is connected on the PC and on the phone.

## 3. The owner's one-time steps (jonny account)

Claude runs none of these: power, update and Tailscale settings are the owner's.

**Step 1. Sleep off while plugged in.** In a PowerShell window (not elevated):

```
powercfg /change standby-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
```

The same can be done in Settings > System > Power > Screen, sleep & hibernate
timeouts: "Make my device sleep after" set to Never. Leave the screen timeout as
it is; a dark screen does not stop JARVIS. If PowerShell says access is denied,
use the Settings page instead.

**Step 2. Tailscale stays up without you.** Right-click the Tailscale icon in the
tray, open Preferences and tick "Run unattended". Then, in the Tailscale admin
console in a browser (Machines, the PC `thegrizzlybear`, the three dots), choose
"Disable key expiry", so the PC's connection does not lapse after 180 days. Do the
same for the phone `iphone-15` if offered. On the phone, leave the Tailscale VPN
switched on.

**Step 3. Windows Update restarts.** Settings > Windows Update > Advanced options:
turn on "Notify me when a restart is required" and leave "Get the latest updates as
soon as they're available" off. Windows 11 Home still restarts on its own after its
deadline; see section 4.

**Step 4. Lock, do not sign out.** When leaving the PC press Win+L. Never choose
Sign out or Shut down while the phone is meant to work.

**Step 5. Check from the phone.** Away from home with Wi-Fi off, open the app.
The Status screen says the Core is reached and shows the link time. If it says
CORE NOT REACHED, check Tailscale on the phone first, then the four points in
section 2.

## 4. Known gap and the two ways to close it later

After any restart (a Windows Update, a power cut) the PC waits at the sign-in
screen and JARVIS is off until the owner signs in. Two closers exist, each a
separate owner decision, neither started:

- **Automatic sign-in on the PC** (the Windows netplwiz setting; on Windows 11
  Home with Windows Hello the switch "only allow Windows Hello sign-in for
  Microsoft accounts" must be off first). Anyone at the PC could then open the
  owner's session. A system setting: owner-only.
- **A Core that starts at boot, before sign-in** (a scheduled task running the
  Core without the desktop window). It would serve the phone from the moment the
  PC is up, but not the screen or the PC's speakers until the owner signs in. A
  Core change plus a system change, a design of its own if wanted.

A small UPS for the PC and the router would cover short power cuts; not required.

## 5. Record

- Decision: owner, "keep pc on", 2026-10-06 about 23:20 local, in the Claude Code chat.
- Nothing changed in the Core, the app or the installed JARVIS.
- `docs/PHONE-PLAN.md` already recorded "the PC stays awake for the first version;
  an always-on mini PC is a later decision"; this decision confirms it.
