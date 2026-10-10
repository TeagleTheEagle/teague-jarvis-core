# JARVIS on a Mac mini at home (plan for your approval)

Status: **WRITTEN, WAITING FOR YOUR DECISIONS AND APPROVAL (2026-10-10, Claude Code).** Owner, 2026-10-10: "all i want is
that the app doesn't need the pc to be on ... and also all future devices", then, after the cloud comparison and the
Mac mini prices: "so no cloud I would run jarvis's core fully on the mac mini and we'd use it as like everything". This
plan replaces the cloud plan (`docs/CLOUD-CORE-PLAN.md`, kept as the record of the comparison). Nothing has started,
and nothing changes on your PC until you approve.

## In plain words

A Mac mini at home becomes JARVIS's home. His Core (his memory, his conversations, his tools, the door your devices
use) runs on it day and night, and so do the things he does himself: speaking, music through its speakers, "Hey
JARVIS" (with a microphone attached), the Workshop's missions, the routine and the reminders. Your phone and every
future device connect to the Mac mini exactly as the phone connects to your PC today, so **the app works with your PC
off**. Your PC becomes a client: you use JARVIS on it in a window that opens the Mac mini over your home network. There
is still ONE Core and ONE memory; it only moves house.

## What changes and what does not

| | Today | After the move |
|---|---|---|
| Where the Core runs | your PC, while it is on and you are signed in | the Mac mini, always on, starting by itself after a restart or a power cut |
| The phone app | pairs with the PC's Tailscale name | pairs again with the Mac mini's name (its pairing screen already takes any address); works with the PC off |
| Future devices | pair with the PC | pair with the Mac mini from Settings > Devices with a code, the same way |
| Speaking aloud, music, "Hey JARVIS", the Workshop, reminders, routines, mail, calendar, web | on the PC | on the Mac mini (a microphone and speakers attached to it if you want to talk to it directly) |
| Your PC | the Core and the window | a client: a window on the Mac mini over the home network, typing and press to talk |
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
2. **D2, how I work on it:** from this PC, over SSH through your Tailscale network only (the Mac's own Remote Login,
   limited to Tailscale, with a key you create from my steps), as an ordinary user without administrator rights. The repository and all writing of the Core stay here (one writer, as now); the Mac mini is where the Mac
   version is built, tested and run. The one-time administrator setup is yours, from written steps. Alternative: you
   run every command on the Mac mini yourself (much slower).
3. **D3, always on:** the Core as a background service that starts when the Mac mini starts, before anyone signs in;
   the Mac mini set never to sleep and to start by itself after a power cut; it signs in to a JARVIS user by itself so
   that speaking, music and "Hey JARVIS" work after a restart (anyone in your home who reaches its keyboard can then
   use it; the Mac mini's own screen lock still applies when you walk away from it).
4. **D4, the Workshop on the Mac mini:** missions and commands run there (macOS commands and Python), as a separate
   restricted user that cannot reach the Core's own address, with the same switches (commands "ask first").
5. **D5, what the Mac mini does itself:** music through its speakers, speaking nudges and announcements aloud, "Hey
   JARVIS" and speech recognition, opening its own apps and pages, analysing its own screen, the home-network list,
   its own hardware readings. All of JARVIS's 56 tools have a home on it.
6. **D6, your PC as a client:** a JARVIS window on the PC that opens the Mac mini over your home network (Tailscale's
   HTTPS address, so the microphone works), typing and press to talk. Your PC's own screen and apps from JARVIS only in
   a later stage, if you want them.
7. **D7, checks before anything moves:** on the Mac mini itself while it is still empty, the same kind of pass as
   Stage 7: install, restart with automatic start, update while running, rollback, an update killed midway, uninstall
   and reinstall, backup and restore, the phone paired. Its plan comes to you for approval first.
8. **D8, the move:** like the switch-over of 2026-10-04: a verified backup on the PC, restored on the Mac mini and
   checked table by table; the phone pairs again with the Mac mini's address (device keys never travel in a backup);
   your PC's JARVIS stops starting at sign-in but stays installed for a month, as the way back.
9. **D9, backups:** daily on the Mac mini (as Settings > Backups now), a copy to `D:\JARVIS-backups` whenever the PC
   is on, and, if you like, Time Machine to an external drive.
10. **D10, the Mac app unsigned for now**, as the Windows app is (installed by me over SSH, so macOS does not stop it);
    signing it with your Apple Developer membership later is your step.

## The stages

| Stage | Who | What | Roughly |
|---|---|---|---|
| 0 | You | Answer D0 to D10 (or "accept all"), approve this plan | now |
| 1 | You | Buy the Mac mini; set it up with the steps I write: your administrator account, a JARVIS user, Tailscale, Remote Login limited to Tailscale, the power and sign-in settings, a microphone and speakers if wanted | an hour |
| 2 | Me | JARVIS for Mac: the Core and the window on macOS (its own Python and Electron for Apple silicon, the speech and wake-word models), the Mac versions of music, speaking aloud, opening apps, the screen, the home-network list, the hardware readings and the Workshop's runner; the installer with the same verify, update and rollback; the background service; one reviewer per item | 3 sessions |
| 3 | Me, then you | The check on the empty Mac mini (plan for your approval, then the pass); the PC's window as a client; the move plan for your approval | 1 to 2 sessions, about an hour of yours |
| 4 | You | The move: backup, restore, the phone paired again, the PC's JARVIS off at sign-in. **From here the app works with the PC off.** A month later the PC's old JARVIS removed, on your word | an hour |

The project's binding rule "The Core lives on the owner's PC" (CLAUDE.md) changes with your approval to: the Core
lives on your Mac mini at home; the PC, the phone and every other device are clients. Owner-only gains: the Mac mini's
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
