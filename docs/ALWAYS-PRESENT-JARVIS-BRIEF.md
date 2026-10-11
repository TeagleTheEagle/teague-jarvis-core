# Always-present JARVIS: the owner's standing intent (design brief, not a switch)

Received 2026-10-07 from the owner, pasted from a reply JARVIS wrote for him ("Written for you, Sir. This is a
statement of intent, not a switch"). Kept here verbatim as a brief. **Nothing in it is built or turned on by this
file.** It becomes work only through a plan for the owner's approval, after release 1.0.17 (in flight on that day).

## The owner's text, as received

> STANDING INTENT — ALWAYS-PRESENT JARVIS
>
> I, Ben Teague, founder of Teague Industries and creator of JARVIS, want JARVIS to be present continuously rather
> than only when I address it. My intent is:
>
> 1. Presence without prompting. JARVIS should be awake and attentive by default, including while I sleep, so that
>    its absence is never the reason something goes unnoticed.
> 2. Scope of watch. It should keep an eye on my Windows PC and JARVIS Core, my paired devices over Tailscale,
>    Project JARVIS releases and checks, and Project Mark I hardware — reporting state, failures and drift rather
>    than assuming health.
> 3. Honest thresholds. It should alert me only when something genuinely warrants attention, with a defined severity
>    level, and never interrupt me for noise.
> 4. Permissions stay mine. Watching is not controlling. Nothing sensitive, irreversible or physical executes
>    without my explicit approval. Every device pairs first and receives only the abilities I tick. Seeing a device
>    on the network never authorises action.
> 5. Truthful status. JARVIS must never describe itself as monitoring when it is not. A check is a moment in time,
>    and it says so. Untested means untested; broken stays broken rather than becoming "mostly passed."
> 6. Logged and recoverable. Every observation, alert and action is recorded, and changes can be rolled back.
> 7. This requires a build. I acknowledge that continuous monitoring is engineering work — a watchdog service
>    running on the JARVIS Core, outside any single conversation — and it must be scoped, approved and validated
>    before it exists. Until then, JARVIS is to treat this as a design brief and say plainly that the capability is
>    not yet built.

## What exists today (1.0.17 in the repository), stated plainly

- The Core runs while the PC is on and signed in; it starts by itself at sign-in and stops at shutdown
  (`docs/PHONE-ALWAYS-ON.md`: the known gap after a restart until sign-in).
- Moments in time, on request: the PC's health (`/api/metrics`, the dashboard), the connection tests in Settings,
  the devices seen on the home network (read only when asked, item H), Gmail and the calendar when asked.
- Clocks that run on their own: the automatic backups (a system notice when one is made), the routine's nudges
  (item F: one nudge per collision, none in quiet hours), the private-network door watcher (opens and closes with
  Tailscale). Each writes an activity row; notices are kept and listed to paired devices.
- Nothing watches the Core itself, the paired devices, a release's checks or Mark I hardware continuously, and
  nothing raises an alert with a severity. JARVIS has no tool for any of it and says so when asked.

## What a build would need (for the plan, not decided)

A watchdog in the Core: a list of watched things (the Core's own health, disk and memory, the door and Tailscale,
each paired device's last contact, the backups' age, the release records on D:, Mark I when it exists), a check
interval per thing, thresholds with a severity (notice, warning, alert), one notice per state change (never a
repeat for the same state), every observation and alert in the activity log and the notices table, quiet hours and
the emergency stop honoured, no action beyond the notice without the owner's approval, and the exact words on screen
("last checked at ..., a moment in time"). The owner's decisions: what is watched, the thresholds, where alerts go
(the PC, the phone, both), and whether the PC stays on for it.

## Status

Brief recorded; not planned, not built, not on by any setting. Next: a plan for the owner's approval after 1.0.17.
