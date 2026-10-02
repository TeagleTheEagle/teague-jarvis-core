# Simplified acceptance for the rest of Stage 6 (proposal, 2026-10-02)

Status: **PROPOSAL, not approved.** `CLAUDE.md` asks Claude to "propose a simplified
acceptance process to the owner if justified". This keeps every protection and removes the
ceremony. Approve by replying "approve simplified acceptance" (edit anything first); the
approval is then recorded as a Stage 6 amendment record in `../governance/`.

## What does not change

- The preservation checkpoints P2 to P5, each run only on the owner's "run Pn".
- The stop rules: any failure stops; no silent retry; a UAC prompt stops.
- `RESUME_STAGE6_RECOVERY` before Gate 18; FINAL selection; cutover and Stage 7 as separate
  owner decisions.
- The two accounts (owner and `jarvis-s6-val`), the single evidence egress, the hash records.

## What changes

1. **Records instead of photographs.** Every owner-run tool writes a JSON record to the
   evidence folder on D:, and Claude reads it there. The owner photographs a screen only when
   a tool says STOP or when a screen is the only record (a Windows dialog).
2. **One command per gate inside the VM.** The tools disc carries one guest script per gate
   that runs the whole in-VM sequence; the owner types one line and waits.
3. **One "next step" launcher on the host.** `next-step.cmd` reads the evidence folder and
   runs whatever is next in the account it is started from, refusing anything out of order.
   The individual step launchers stay for recovery.
4. **Every VM start through the start launcher** (re-applies the localhost setting, records
   the VM's own log value), as already decided on 2026-10-02.
5. **Hang rule.** If Windows or a gate script shows no progress for 15 minutes, the owner
   resets and the rerun is recorded as such. No case-by-case debate.
6. **Gate 19 in the same VM session as Gate 17**, before Gate 18: install the previous build
   from a second package disc, update to FINAL, verify, roll back, verify; per-phase seconds
   recorded. Gate 18 follows after `RESUME_STAGE6_RECOVERY`. Nothing in Gate 19 depends on
   Gate 18.
7. **Owner decisions batched.** FINAL selection, this proposal and the Gates 17 to 20 prompt
   approved in one sitting, so the route does not stop three times.
8. **Stage 7 as one scripted pass** on the same VM and snapshots, scoped in `docs/ROADMAP.md`
   Phase 1, instead of a new gate structure.

## Why this is safe

Nothing that protects the protected original, the backup source or the owner's accounts is
removed. The changes remove waiting, typing and photographing, which is where today's time
went, and they remove the "which launcher" mistakes by having one entry point.

## Approval

(not yet approved)
