# Moving JARVIS fully from the PC to a Mac mini (plan for your approval)

Status: **WRITTEN, WAITING FOR YOUR DECISIONS AND APPROVAL (2026-10-10, Claude Code).** Owner, 2026-10-10: "all i want is
that the app doesn't need the pc to be on ... and also all future devices", then, after the cloud comparison and the
Mac mini prices: "so no cloud I would run jarvis's core fully on the mac mini and we'd use it as like everything", and
then: "no I don;y just want to run it for just phone purposes I want to take the core on this pc and move it fully to
the mac mini", and "and the mac mini will become my main computer for everything". This
plan replaces the cloud plan (`docs/CLOUD-CORE-PLAN.md`, kept as the record of the comparison). Nothing has started,
and nothing changes on your PC until you approve.

## In plain words

**All of JARVIS moves from your PC to the Mac mini, not just what the phone needs.** The Core that runs on your PC today
(his memory, his conversations, his settings and personality, his tools, the Workshop, the door your devices use) is
taken off the PC and runs on the Mac mini from then on, day and night, and so does everything he does himself:
speaking, music through its speakers, "Hey JARVIS" (with a microphone attached), the Workshop's missions, the routine
and the reminders. You use him on the Mac mini itself, on your phone, and on every future device, and the app works
with your PC off. Afterwards the PC holds no JARVIS Core: only its old copy, kept switched off for a month as the way
back and then removed on your word. If you also want JARVIS on the PC, a window there opens the Mac mini (D6); you do
not have to. There is still ONE Core and ONE memory; it moves house completely.

**The Mac mini is also your main computer for everything.** So JARVIS runs on it the way he runs on your PC today: in
your own account, his window and voice opening when you sign in, while his Core runs in the background from the
moment the Mac mini starts, so your phone and devices reach him even before you sign in. And I move with him: the
JARVIS repository and my work go to the Mac mini (D2), and this PC session hands over and stops.

## What moves from the PC to the Mac mini

Everything that is JARVIS: the database (memories, conversations, tasks, projects, reminders, the routine, notices,
the activity log, the music nicknames, the Workshop's missions and lessons), the config folder (your personality text,
your style, your settings), your music files, the Workshop's folder and its files, and the backups history. Your keys
move too, typed by you into the Mac mini's key file (I never read them). The phone and any other device pair again
with the Mac mini (their keys belong to an installation and are never copied). Nothing of JARVIS stays running on the
PC.

## What changes and what does not

| | Today | After the move |
|---|---|---|
| Where the Core runs | your PC, while it is on and you are signed in | the Mac mini, always on, starting by itself after a restart or a power cut |
| The phone app | pairs with the PC's Tailscale name | pairs again with the Mac mini's name (its pairing screen already takes any address); works with the PC off |
| Future devices | pair with the PC | pair with the Mac mini from Settings > Devices with a code, the same way |
| Speaking aloud, music, "Hey JARVIS", the Workshop, reminders, routines, mail, calendar, web | on the PC | on the Mac mini (a microphone and speakers attached to it if you want to talk to it directly) |
| Your PC | the Core and the window | no Core; if you want, a window on the Mac mini over the home network (D6) |
| Your data, keys, personality | on the PC | moved to the Mac mini by one backup and restore; your keys typed by you into its key file |
| Backups | daily to `D:\JARVIS-backups` | daily on the Mac mini, and a copy to `D:\JARVIS-backups` whenever the PC is on |
| Updates | your Setup, on your approval | a Mac release, on your approval, with the same check and rollback |

## Your decisions (my recommendation first)

0. **D0, release 1.0.18 on the PC meanwhile:** the PC checks I am running finish without your time; the VM check and
   the update of your PC (about two and a half hours of yours) only if you want the Workshop and the phone's device
   list before the Mac mini is ready. They come with the Mac mini anyway. My recommendation: skip the PC's VM check and
   update, unless you want the Workshop sooner.
1. **D1, the Mac mini:** M6, 24 GB memory, 512 GB storage, about A$2,049 (the base 16 GB / 256 GB, A$1,449, is enough
   for JARVIS as he is today; the 24 GB leaves room for an offline AI model and a voice of his own later; the storage
   cannot be upgraded after purchase). If you want to talk to it directly: a USB speakerphone or a microphone and
   speakers (the Mac mini has a small speaker and no microphone). Buying it is yours.
2. **D2, where I work:** on the Mac mini itself, since it becomes your main computer. You install Claude Code there
   (as on the PC; steps from me); I prepare a handover from this PC: the whole JARVIS repository with its history, the
   governance records, my notes and the status, in one bundle you copy across; the Claude Code session on the Mac mini
   then becomes JARVIS's only writer and builds the Mac version where it runs, and this PC session stops (one writer,
   as now). The iPhone app's own Mac session is not affected. Alternative: I stay on this PC and reach the Mac mini over
   SSH through Tailscale (slower, and the PC must stay on while I work).
3. **D3, always on:** the Core as a background service that starts when the Mac mini starts, before anyone signs in,
   so the phone and your devices reach JARVIS even after a restart or a power cut; the Mac mini set never to sleep
   (its screen may) and to start by itself after a power cut. JARVIS's window, voice, music and "Hey JARVIS" run in
   your own account and open when you sign in, as on your PC today. Signing in by itself after a restart stays your
   choice in macOS's settings (off is safer for a main computer).
4. **D4, the Workshop on the Mac mini:** missions and commands run there (macOS commands and Python), as a separate
   restricted user that cannot reach the Core's own address, with the same switches (commands "ask first").
5. **D5, what the Mac mini does itself:** music through its speakers, speaking nudges and announcements aloud, "Hey
   JARVIS" and speech recognition, opening its own apps and pages, analysing its own screen, the home-network list,
   its own hardware readings. All of JARVIS's 56 tools have a home on it.
6. **D6, your PC afterwards, optional:** if you want JARVIS on the PC too, a JARVIS window there opens the Mac mini
   over your home network (Tailscale's HTTPS address, so the microphone works), typing and press to talk; otherwise
   the PC has no JARVIS at all. Your PC's own screen and apps from JARVIS only in a later stage, if you want them.
7. **D7, checks before anything moves:** on the Mac mini, in a separate test user and test folders that your own
   account never sees, before your data moves; the same kind of pass as Stage 7: install, restart with automatic start, update while running, rollback, an update killed midway, uninstall
   and reinstall, backup and restore, the phone paired. Its plan comes to you for approval first.
8. **D8, the move:** like the switch-over of 2026-10-04: a verified backup on the PC, restored on the Mac mini and
   checked table by table; the phone pairs again with the Mac mini's address (device keys never travel in a backup);
   your PC's JARVIS stops starting at sign-in but stays installed for a month, as the way back.
9. **D9, backups:** daily on the Mac mini (as Settings > Backups now), a copy to `D:\JARVIS-backups` whenever the PC
   is on, and, if you like, Time Machine to an external drive.
10. **D10, the Mac app unsigned for now**, as the Windows app is (built and installed on the Mac mini itself, so
    macOS does not stop it); signing it with your Apple Developer membership later is your step.

## The stages

| Stage | Who | What | Roughly |
|---|---|---|---|
| 0 | You | Answer D0 to D10 (or "accept all"), approve this plan | now |
| 1 | You, then me | Buy the Mac mini and set it up as your main computer, with my steps for JARVIS's part: Tailscale, the power settings, a microphone and speakers if wanted, Claude Code; then the handover bundle from this PC copied across and opened in Claude Code there | an hour |
| 2 | Me, on the Mac mini | JARVIS for Mac: the Core and the window on macOS (its own Python and Electron for Apple silicon, the speech and wake-word models), the Mac versions of music, speaking aloud, opening apps, the screen, the home-network list, the hardware readings and the Workshop's runner; the installer with the same verify, update and rollback; the background service; one reviewer per item | 3 sessions |
| 3 | Me, then you | The check on the Mac mini in its test user (plan for your approval, then the pass); the PC's window as a client if you want one (D6); the move plan for your approval | 1 to 2 sessions, about an hour of yours |
| 4 | You | The move: backup, restore, the phone paired again, the PC's JARVIS off at sign-in. **From here the app works with the PC off.** A month later the PC's old JARVIS removed, on your word | an hour |

The project's binding rule "The Core lives on the owner's PC" (CLAUDE.md) changes with your approval to: the Core
lives on your Mac mini at home, your main computer; the phone, the PC if used and every other device are clients;
JARVIS's repository and its one writer move to the Mac mini with the handover. Owner-only gains: the Mac mini's
administrator account, its macOS and sign-in settings, its Apple ID, Tailscale on it.

## What performs worse, the same, or better

| Function | After the move | Why |
|---|---|---|
| Speech recognition, the Workshop, everything the Core computes | faster | the M6 is quicker per core than the PC's Ryzen 7 3700X |
| Offline answers and a voice of JARVIS's own later | possible on the Mac mini | its memory and graphics run local AI models well |
| The phone app, future devices, reminders, routines, missions | better: work with the PC off | the Mac mini is always on |
| JARVIS on your PC | a little plainer: a window, typing and press to talk; the PC's own screen and apps not reachable from JARVIS until a later stage | the Core is on the Mac mini |
| At home without internet | the PC should still reach the Mac mini over your home network (proved in the check pass) | nothing has to cross the internet at home |
| The phone away from home | the same as today | it reaches your home through your internet, as now |
| Chat answers, the voice of the replies, web, news, mail, calendar, Spotify | the same | those are on the internet either way |

## Costs

| Item | About |
|---|---|
| Mac mini M6, 24 GB / 512 GB | A$2,049 once (A$1,449 for 16 GB / 256 GB) |
| A USB speakerphone or a microphone and speakers, if wanted | from about A$100 |
| Power | very little: the Mac mini idles at a few watts |
| Monthly fees | none |

## Risks and limits, said before you decide

- **Home power or internet down:** the phone cannot reach JARVIS away from home, as today. A small battery backup
  (UPS) keeps the Mac mini and the router up through short cuts, if you want one.
- **One machine:** if the Mac mini fails, JARVIS stops until it is repaired or replaced; the backups on your PC bring
  everything back.
- **The work:** about four to five sessions of mine before the move, and your steps above.
- **A new operating system for JARVIS:** the Mac version is new code in places (sound, the Workshop's runner, the
  service). The check pass on the empty Mac mini proves it before your data moves.
- **Not in this plan:** your PC's own screen and apps from JARVIS (a later stage if wanted), a second Core of any kind
  (never), the iPhone app beyond pairing again (the Mac session needs no change).

## Approval

Reply in your own words, for example: "I approve the Mac mini plan, accept all decisions", or name a decision to
change (for example "D1: the base model" or "D0: finish 1.0.18 on the PC"). I then record it, change the binding rule in
CLAUDE.md, and write your Stage 1 steps for when the Mac mini arrives.

Prices (2026-10-10): Apple's base price from [GadgetGuy](https://www.gadgetguy.com.au/apple-mac-mini-m5-pro-m6-launch-australia-price/)
and [The PC Doctor](https://thepcdoctor.com.au/new-mac-mini-m6-australia-price-soldered-ssd-should-you-buy); the
24 GB / 512 GB and 16 GB / 512 GB prices from [Amazon Australia](https://www.amazon.com.au/Apple-2026-Mac-mini-chip/dp/B0HGGCZFJL);
the line-up from [MacRumors](https://www.macrumors.com/2026/08/25/apple-announces-2026-mac-mini/). Confirm on
apple.com/au before buying.
