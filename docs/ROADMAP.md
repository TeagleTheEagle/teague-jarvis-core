# JARVIS roadmap (proposed 2026-10-02, for the owner's approval)

Status: **PROPOSAL, not approved.** Written by Claude Code at the owner's request ("everything
you would change"). Nothing here changes the rules in `CLAUDE.md` or the Stage 6 governing
records. Each phase starts only when the owner says so. Edit anything; approve by replying
"approve roadmap" (with changes if any), and the approval is recorded here.

## What stays as it is

- **One Core on the owner's PC, every device a client, one memory, one identity.** Not negotiable.
- Local-first voice (Whisper and wake word on the machine; the cloud only for the brain and the
  cloned voice).
- A release that carries its own Python, Electron and models, installs per user without
  administrator rights, and is hash-verified file by file.
- The backup/restore path (`recovery.py`, `switch_over.py`) and the clean-machine test idea.
- The preservation checkpoints (P0 to P5) and the stop rules of Stage 6: cheap, and the point.

## Phases, in order

### Phase 0: finish Stage 6 on the frozen build (now)

Gate 16R to the end, then Gates 17 to 20 on 1.0.11 (or the owner's FINAL), under the lean
procedure in `docs/stage6-freshvm/SIMPLIFIED-ACCEPTANCE-PROPOSAL.md` once approved. The code
is frozen: no source change until cutover, so that the tested build is the shipped build.

Owner acts: FINAL selection; approval of the simplified procedure; `RESUME_STAGE6_RECOVERY`;
the cutover decision after `STAGE_6_COMPLETE`.

### Phase 1: cutover and Stage 7, lean (next)

Switch the everyday JARVIS to the FINAL release (owner decision, owner-run `switch_over.py`
from a verified backup). Then Stage 7 as one scripted pass on the same VM and snapshots:
install, first launch from the icon, update A to B, interrupted update, rollback, uninstall,
reinstall, data preserved, Desktop and Startup shortcuts. Two known rough edges fixed in the
first post-cutover release: the "Core stopped" dialog after shutdown, and the installer not
excluding its own process when it stops JARVIS.

Result for the owner: JARVIS starts from an icon, with voice ready, and updates from a package.

### Phase 2: codebase clean-up (after cutover; one release)

- Reorganise the flat top level into a package: `jarvis/core`, `providers`, `voice`,
  `devices`, `installer`, `tools`. Experiments (stage4_*, probe_*, shadow_*, repair_*) and the
  Codex-era scripts (`AGENTS.md`, `Sync-TeagueIndustries.ps1`, the Start/Stop .cmd and .ps1
  files) leave the shipped release; kept in `archive/` or deleted with the owner's say-so.
- Ship exactly two providers: Qwen (primary) and one local model (offline fallback). OpenAI
  and Gemini paths retired from the release (code kept in history).
- No behaviour change; the full regression must pass unchanged before and after.

### Phase 3: automatic backups (after cutover; small)

A scheduled nightly backup of the Core's data to the backup drive with the shipped
`recovery.py`, hash-recorded, with a monthly restore drill into a sandbox. The owner
approves the schedule and the drive path; E: stays write-only for the backup task.

### Phase 4: device pairing and the phone client (the real engineering)

Before any device outside the PC connects: device pairing with per-device keys, per-capability
permissions (the capability contract in the master document), encrypted transport, revocation.
Then the iPhone client over a private network (Tailscale-style), as the master document already
leans. Networking changes are owner decisions at every step (`CLAUDE.md`).

### Phase 5: glasses, then everything else

Halo glasses as an endpoint of the phone client. Tesla, Home Assistant, Mark I and ESP32 nodes
stay parked until the owner has used JARVIS daily for a month and chooses the next one.

## Paperwork

Three living documents from now on: `CLAUDE.md` (rules), `docs/CURRENT-STATUS.md` (where we
are), and `docs/EVIDENCE-INDEX.md` (where each record lives; to be created at Stage 6 close).
Historical reports stay where they are and are not rewritten.

## What needs the owner, what does not

| Needs the owner's word | Claude does under standing authority |
|---|---|
| Approve this roadmap; FINAL; simplified acceptance; cutover; Stage 7 start; deleting old code; backup schedule; any networking | Write plans and tools; code changes on a branch after cutover; tests; builds; evidence; status |

## Approval

(not yet approved)
