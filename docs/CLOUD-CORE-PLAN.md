# JARVIS's Core in the cloud (plan for your approval)

Status: **WRITTEN, WAITING FOR YOUR DECISIONS AND APPROVAL (2026-10-10, Claude Code).** Owner, 2026-10-10: "im looking
to move to cloud and run everything there so my pc doesn't need to be on to use the app and the core runs on a cloud
find me the best fit for jarvis's core", then "write the cloud plan" after the comparison of providers. Nothing in this
plan has started. Release 1.0.18 (the Workshop and the device list) carries on through its checks meanwhile; this move
comes after it, as release 1.1.0.

## In plain words

JARVIS's Core (his memory, his conversations, his tools and the door your phone uses) moves from your PC to a small
server of your own at DigitalOcean in Sydney, reachable only through your Tailscale network, never from the open
internet. It runs day and night, so the phone app works with your PC switched off. There is still ONE Core and ONE
memory: it only changes address. Your PC becomes a client like your phone: the JARVIS window opens the cloud Core, and
a small helper on the PC does the few things that need the PC itself (music through its speakers, speaking aloud near
you, opening apps and pages, looking at its screen, the home-network list) while the PC is on. With the PC off those
few things say plainly that the PC is off; everything else keeps working from the phone.

## What changes and what does not

| | Today | After the move |
|---|---|---|
| Where the Core runs | your PC, while it is on and you are signed in | your server in Sydney, always on |
| The phone app | pairs with the PC's Tailscale name, works while the PC is on | pairs again with the server's Tailscale name (the pairing screen already takes any address), works any time |
| The JARVIS window on the PC | starts its own Core | opens the cloud Core over Tailscale's HTTPS address and starts the PC helper |
| Chat, memory, tasks, reminders, routines, notices, approvals, mail, calendar, web, the Workshop | on the PC | on the server (the Workshop's missions run with the PC off) |
| Music through the PC's speakers, speaking aloud on the PC, opening apps and pages, screen analysis, the home-network list, the PC's hardware details | on the PC | through the PC helper, only while the PC is on |
| AI providers (Qwen, OpenAI, Fish Audio) and their keys | key file on the PC | the same keys in the server's key file, typed by you |
| Backups | daily to `D:\JARVIS-backups` | daily on the server, DigitalOcean's weekly backups, and a copy to `D:\JARVIS-backups` whenever the PC is on |
| Updates | your Setup, on your approval | a Linux release on the server, on your approval, with rollback as today |

Of JARVIS's 56 tools, 44 act on his own data, the internet or himself and run on the server unchanged. 12 act on "this
PC" or "the JARVIS window" (Settings > Permissions shows each one's reach): the four Workshop tools move to the server,
`computer_run_tests` runs there too, and the other seven go through the PC helper.

## Your decisions (my recommendation first)

1. **D1, provider and size:** DigitalOcean, Sydney, Basic Droplet 2 vCPU / 4 GB / 80 GB, Ubuntu 24.04 LTS, about US$24
   a month, plus about US$5 for weekly backups (prices from third-party listings, confirmed at checkout). Alternative:
   Vultr Sydney or Melbourne, about US$20. Not Alibaba (one billing problem would stop both the AI and the Core), not
   the Oracle free tier (it takes back idle servers). The comparison is at the end of this plan.
2. **D2, how I work on the server:** through Tailscale's own SSH, as an ordinary user `jarvis` without administrator
   rights: your Tailscale network decides who may connect, so there is no password or key file to look after. The
   one-time administrator setup is yours, from a script I write and you run in DigitalOcean's web console. Alternative:
   you run every server command yourself from written steps (much slower). Every step that touches the live Core
   still waits for your approval, as releases do now.
3. **D3, your own screens:** the Core keeps listening on its own machine only; Tailscale's HTTPS address
   (`tailscale serve`) brings your window to it, and the Core accepts your screens only with your Tailscale login
   attached. HTTPS also keeps the window's microphone working. No public address, ever: the server's firewall refuses
   every connection from the internet.
4. **D4, the Workshop on the server:** missions and commands run on the server (they then work with the PC off), as a
   separate restricted user that cannot reach the Core's own address, inside the workshop folder, with the same switches
   (commands "ask first"). Your PC's folders are not reachable from the server in this release.
5. **D5, the PC helper:** part of the desktop app. While the PC is on it connects to the cloud Core like a paired
   device (kind "computer") and carries out those seven tools: five that act on the PC (music, opening apps, opening
   pages, the PC's hardware details, the home-network list) and two that act on the JARVIS window (its controls, among
   them screen analysis, and its sections). It also speaks nudges and announcements aloud on the PC. While the PC is
   off, those tools answer "Your PC is off, so I can't do that now." (never a silent fallback). Your music files stay
   on the PC.
6. **D6, backups:** the daily backup on the server (as Settings > Backups now), DigitalOcean's weekly backups of the
   whole server, and the PC helper copying the newest backup to `D:\JARVIS-backups` whenever the PC is on.
7. **D7, checks before anything moves:** on a temporary second server you create for the checks and delete afterwards
   (a few dollars in all), never on the live one; the same kind of pass as Stage 7: install, restart, update while
   running, rollback, an update killed midway, backup and restore, the phone paired, nothing reachable from the
   internet. Its plan comes to you for approval first, as for every release.
8. **D8, the move itself (cutover):** like the switch-over of 2026-10-04: a verified backup on the PC, restored into
   the cloud Core and checked table by table; the phone pairs again with the new address (device keys are tied to an
   installation, so they never travel in a backup); the PC's JARVIS stops starting at sign-in but stays installed for a
   month, as the way back.
9. **D9, speech:** speech recognition stays local on the server (the same small model as today, private, no extra
   cost); Qwen's cloud recognition (built in 1.0.15, not yet tried with the real service) stays the choice you can
   switch to.
10. **D10, offline answers (Ollama):** not on the server. It is always online, and a phone without internet cannot
    reach it anyway. The PC keeps Ollama for the time being; nothing uses it after the move.

## The phases

| Phase | Who | What | Roughly |
|---|---|---|---|
| 0 | You | Answer D1 to D10 (or "accept all"), approve this plan | now |
| 1 | You | DigitalOcean account with two-step sign-in, payment; the temporary check server (exact settings from me); run my setup script in its web console: Tailscale with its SSH, the `jarvis` user, the firewall, your time zone (Sydney, so routines, quiet hours and greetings keep your time) | about 45 minutes |
| 2 | Me | The server version of the Core: a Linux release (no Electron, its own Python), paths, the server's health readings, the Workshop's Linux runner, a service that starts at boot, the installer's Linux side with the same verify, update and rollback; rehearsed on the check server; one reviewer | 2 sessions |
| 3 | Me | Your screens over Tailscale's HTTPS address, the PC helper and the desktop app's cloud mode, the backup copy to the PC, the "PC is off" answers; the Mac brief for the new address; one reviewer per item | 2 to 3 sessions |
| 4 | Me, then you | The check on the check server (plan for your approval, then the pass); then the live server (your setup script again); then the move plan for your approval | 1 session, about 2 hours of yours |
| 5 | You | The move: backup, restore, the phone paired again, the PC's JARVIS off at sign-in; a week of use; then the check server deleted, and after a month the PC's old Core removed on your word | an hour, then a month |

The project's binding rule "The Core lives on the owner's PC" (CLAUDE.md) changes with your approval to: the Core lives
on your server at DigitalOcean Sydney, reachable only over your Tailscale network; the PC is a client with a helper.
Owner-only gains: the server account, billing, administrator access, its firewall and Tailscale, deleting a server.

## Costs

| Item | About |
|---|---|
| The server (2 vCPU / 4 GB / 80 GB, Sydney) | US$24 a month |
| DigitalOcean's weekly backups | US$5 a month |
| The temporary check server, for the checks only | a few US dollars in all |
| AI providers | unchanged |

## Risks and limits, said before you decide

- **Your data lives with a provider.** Memories, conversations and keys are stored on DigitalOcean's machine. Only your
  Tailscale devices reach it; the provider's staff and systems are outside my control. Your conversations already go
  to Qwen today.
- **One place to fail.** If DigitalOcean, the server or Tailscale is down, JARVIS is down everywhere (today: if the PC
  is off). The way back stays open for a month (D8), and the backups reach your PC.
- **PC features need the PC.** The seven PC tools and the window work only while the PC is on and signed in.
- **Latency.** Sydney keeps the phone quick; each AI call adds a trip to Singapore of well under a second. Not
  measured yet: the check pass measures it.
- **The amount of work.** About five to seven long sessions of mine before the move, plus your steps above. Release
  1.0.18 finishes first.
- **Not part of this plan:** your PC's own folders reachable from the server's Workshop, a second Core of any kind
  (never), the Mac and the phone app beyond the new address (the Mac session checks its pairing screen; no change is
  expected).

## Approval

Reply in your own words, for example: "I approve the cloud plan, accept all decisions", or name a decision to change
("D2: I'll run the commands myself"). I then record it, change the binding rule in CLAUDE.md, and give you Phase 1's
exact steps. Release 1.0.18's checks and your Stage 7 approval of it carry on independently.

## Providers compared (2026-10-10)

Prices from third-party listings found on 2026-10-10, in US dollars a month, to be confirmed at checkout.

| Option | Monthly | Fit for JARVIS |
|---|---|---|
| DigitalOcean, Sydney, 2 vCPU / 4 GB / 80 GB | about 24 | Best fit: simplest to set up, the same price in every region, easy backups (+20%) |
| Vultr, Sydney or Melbourne, 2 vCPU / 4 GB / 80 GB | about 20 to 21 | Close second: slightly cheaper, slightly less beginner-friendly |
| AWS Lightsail, Sydney, 2 vCPU / 4 GB / 80 GB | about 24 | Works; an AWS account is more to manage |
| Alibaba Cloud Simple Application Server, Singapore, 2 vCPU / 4 GB | about 19 | Next door to Qwen, but one billing problem would stop both the AI and the Core, as the overdue bill did in October 2026 |
| Hetzner, Singapore | raised on 15 June 2026 | Not recommended: higher prices, 0.5 TB of traffic included |
| Oracle Cloud free tier | free | Not suitable: halved in 2026, and idle servers may be reclaimed |

What the Core needs: it is a Python service with a SQLite database and a 145 MB speech model; the AI runs at the
providers. Two virtual processors and 4 GB leave room for speech recognition and the Workshop. Sydney keeps the phone
quick; the AI calls to Singapore add well under a second each.

Sources: [DigitalOcean pricing (Fluence)](https://fluence.ai/blog/digitalocean-droplets-vs-fluence/),
[DigitalOcean regions](https://github.com/gatqrwl/digitalocean-region-pricing),
[AU/APAC comparison (Onidel)](https://onidel.com/blog/onidel-vs-vultr-vs-digitalocean-australia-apac-comparison),
[Vultr calculator](https://cloudpricecalculators.com/vultr-calculator/),
[Lightsail bundles (AWS)](https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-bundles.html),
[Simple Application Server pricing (Alibaba Cloud)](https://www.alibabacloud.com/en/product/swas/pricing?_p_lc=1),
[Hetzner price adjustment](https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/),
[Hetzner Singapore](https://www.hetzner.com/pressroom/new-location-singapore/),
[Oracle free tier halved (InfoQ)](https://www.infoq.com/news/2026/07/oracle-cloud-free-tier-limits/),
[Oracle Always Free resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm).
