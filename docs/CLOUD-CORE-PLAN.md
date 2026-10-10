# JARVIS's Core in the cloud (plan for your approval)

Status: **WRITTEN, WAITING FOR YOUR DECISIONS AND APPROVAL (2026-10-10, Claude Code).** Owner, 2026-10-10: "im looking
to move to cloud and run everything there so my pc doesn't need to be on to use the app and the core runs on a cloud
find me the best fit for jarvis's core", then "write the cloud plan" after the comparison of providers. Nothing in this
plan has started. Release 1.0.18 (the Workshop and the device list) carries on through its checks meanwhile; this move
comes after it, as release 1.1.0.

## Your goal, and the shortest way to it

Owner, 2026-10-10: "all i want is that the app doesn't need the pc to be on ... and also all future devices". For that,
JARVIS's Core has to live on something that is always on, and your PC cannot be that while it is off. So the Core
moves, and the phone and every later device connect to it exactly as the phone connects to your PC today. The plan is
in two stages so that your goal comes first:

- **Stage 1, your goal:** the Core on the server; the phone paired with it; any later device paired the same way; your
  PC's JARVIS window opens the server instead of starting its own Core, and on the PC you type or press to talk. After
  Stage 1 the app works with the PC off. About four sessions of my work and about two hours of yours.
- **Stage 2, the PC's extras:** "Hey JARVIS" on the PC again, music through the PC's speakers, opening apps and pages,
  screen analysis, the home-network list and the PC's hardware details, through a small helper on the PC (D5, D9).
  About two sessions, delivered as an update after the move. Until then those wait.

**Every future device** pairs with the server from Settings > Devices with a code, like the phone: a second phone, the
glasses (through the phone, as planned), a Mac or another computer, a watch. Nothing in the Core changes per device;
each device needs only its own app, and a computer can use the same JARVIS window as your PC.

**The other way to the same goal:** a small always-on computer at home instead of a cloud server. Today's Windows
build runs on it unchanged (no Linux version needed), your data stays at home and there is no monthly fee, for a
one-off purchase and its power. Your phone, your future devices and your PC would connect to it the same way, so
everything else in this plan stays. Say so if you prefer it; the comparison of cloud providers is at the end.

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
| "Hey JARVIS" and the window's speech recognition | the window streams the microphone to the Core on the PC, which listens for the wake word and turns speech into text | stay on the PC, in the helper: the microphone never streams to the server; only the text of what you said (or the recording of one question) goes there |
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
9. **D9, speech:** on the PC, the wake word and the recognition of what you say to the window run in the helper, as
   fast as today, and the microphone never streams to the server (today the window streams it to the Core on the PC
   all the time to listen for "Hey JARVIS"; to a server that would cost speed, data and privacy). Recordings from the
   phone are recognised on the server with the same small model (`base.en`), private and at no extra cost, but on two
   shared server processors rather than your PC's: a little slower, measured in the check (D7). If it is too slow,
   Qwen's cloud recognition (built in 1.0.15, not yet tried with the real service) or a larger server size.
10. **D10, offline answers (Ollama):** not on the server. It is always online, and a phone without internet cannot
    reach it anyway. The PC keeps Ollama for the time being; nothing uses it after the move.

## The phases

| Phase | Who | What | Roughly |
|---|---|---|---|
| 0 | You | Answer D1 to D10 (or "accept all"), approve this plan | now |
| 1 | You | DigitalOcean account with two-step sign-in, payment; the temporary check server (exact settings from me); run my setup script in its web console: Tailscale with its SSH, the `jarvis` user, the firewall, your time zone (Sydney, so routines, quiet hours and greetings keep your time) | about 45 minutes |
| 2 (Stage 1) | Me | The server version of the Core: a Linux release (no Electron, its own Python), paths, the server's health readings, the Workshop's Linux runner, a service that starts at boot, the installer's Linux side with the same verify, update and rollback; the seven PC and window tools answering "This needs the JARVIS helper on your PC, which comes in Stage 2."; rehearsed on the check server; one reviewer | 2 sessions |
| 3 (Stage 1) | Me | Your screens over Tailscale's HTTPS address; the desktop app's cloud mode (the window opens the server, typing and press to talk; its always-on listening for "Hey JARVIS" off, because it would stream the microphone to the server); the backup copy to the PC; the Mac brief for the new address; one reviewer per item | 1 session |
| 4 (Stage 1) | Me, then you | The check on the check server (plan for your approval, then the pass); then the live server (your setup script again); then the move plan for your approval | 1 session, about 2 hours of yours |
| 5 (Stage 1) | You | The move: backup, restore, the phone paired again, the PC's JARVIS off at sign-in. **From here the app works with the PC off.** A week of use; then the check server deleted, and after a month the PC's old Core removed on your word | an hour, then a month |
| 6 (Stage 2) | Me, then you | The PC helper (D5, D9): "Hey JARVIS" and speech recognition on the PC, the seven PC and window tools, speaking aloud on the PC, the "PC is off" answers; reviewed, checked, installed as an update on your approval | 2 sessions |

The project's binding rule "The Core lives on the owner's PC" (CLAUDE.md) changes with your approval to: the Core lives
on your server at DigitalOcean Sydney, reachable only over your Tailscale network; the PC is a client with a helper.
Owner-only gains: the server account, billing, administrator access, its firewall and Tailscale, deleting a server.

## What performs worse, the same, or better

| Function | After the move | Why |
|---|---|---|
| Recognising what you say into the phone | a little slower on the US$24 server (measured in the check) | two shared server processors instead of the PC's Ryzen 7 3700X (8 cores); the CPU-Optimized server (about US$42) or Qwen's cloud recognition should close the gap |
| The JARVIS window | slightly slower to open and answer; nothing at all if your internet is down | every request crosses the internet to Sydney (tens of milliseconds) instead of staying on the PC |
| Screen analysis | a moment slower | the screenshot is sent from the PC to the server before it goes to the vision model; still needs the PC on |
| The Workshop | slower for heavy jobs, Linux instead of Windows, your PC's files out of reach | it runs on the small server; in exchange missions run with the PC off |
| The dashboard's processor, memory and disk readings | show the server, not your PC | the Core reads the machine it runs on (the helper could add the PC's later) |
| Offline answers, and a voice model of your own on the PC's graphics card later | not on the server | the server has no graphics card; such a model would run on the PC through the helper, only while it is on |
| Music, speaking aloud on the PC, opening apps and pages, the home-network list | the same, a fraction of a second later | one more hop from the server to the PC helper; PC on, as today |
| Chat answers, the voice of the replies, web, news, mail, calendar, directions, Spotify | the same | the AI and those services are on the internet either way; Sydney reaches Singapore about as fast as your PC does |
| Memory, tasks, reminders, conversations | the same | the database is small |
| The phone app, reminders and timers, routine nudges, Workshop missions | better: they work with the PC off | the Core never sleeps |
| JARVIS after your PC restarts | better: no wait | today JARVIS starts about four minutes after you sign in; the server is already running |

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
- **No JARVIS at home when your internet is down.** Today the PC's JARVIS keeps working without the internet (with
  local answers from Ollama); after the move the window and the phone both need the internet to reach the server.
- **Some things get slower (next section).**
- **Latency.** Sydney keeps the phone quick; each AI call adds a trip to Singapore of well under a second. Not
  measured yet: the check pass measures it.
- **The amount of work.** About four long sessions of mine for Stage 1 (your goal), plus your steps above, and about
  two more for Stage 2. Release 1.0.18 finishes first.
- **Between the stages the PC is plainer.** On the PC you type or press to talk, and the seven PC and window tools say
  they need the helper; everything else works, on the PC and from the phone.
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
| DigitalOcean CPU-Optimized, 2 dedicated vCPU / 4 GB / 25 GB | about 42 | The closest match to the PC's speed: processors not shared with other customers, so speech recognition and the Workshop should come close to the PC's (measured in the check); 4 dedicated vCPUs about 84 if not |
| AWS Lightsail, Sydney, 2 vCPU / 4 GB / 80 GB | about 24 | Works; an AWS account is more to manage |
| Google Cloud, Sydney or Melbourne, e2-medium (2 shared vCPU / 4 GB) | about 35, plus its disk and outgoing traffic | Works and is fast, but about half as dear again for the same size, a bill in several parts and a much harder console; one Google account would then carry Gmail, Calendar, Nest and the Core together. A one-year commitment brings it to about 22, a three-year one to about 16 |
| Google Cloud free tier (e2-micro) | free | Not suitable: US regions only, 1 GB of memory, and traffic to Australia is not in the free allowance |
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
[Oracle Always Free resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm),
[e2-medium prices by region (cloudprice.net)](https://cloudprice.net/gcp/compute/instances/e2-medium),
[e2-medium (gcloud-compute.com)](https://gcloud-compute.com/e2-medium.html),
[Google Cloud free features](https://docs.cloud.google.com/free/docs/free-cloud-features),
[DigitalOcean Droplet pricing (official)](https://www.digitalocean.com/pricing/droplets).
