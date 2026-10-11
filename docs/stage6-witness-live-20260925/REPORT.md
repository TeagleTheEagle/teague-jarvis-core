# One lifecycle-witness diagnostic — REJECTED run

Final diagnosis: **ETW_SESSION_LOSS_PRIMARY**. This identifies the strongest supported mechanism for this run; it does not prove the precise lost payload identities or the underlying cause of session loss. Historical ETW-loss cause remains UNCONFIRMED.

Run: `protected-8c2a630033954d25bfbf3a8e03f3269c`
Workspace: `D:\JARVIS-STAGE6-LIVE\892cb90fc72b4980af6d847b3122de6f\code`
Exactly one normal small run; three existing observer prompts; no retry, rebuild, setting change or code correction.

## Outcome
Both 12-file / 786,432-byte SHA-256 passes matched; source metadata unchanged. Phase A completed. First terminal failure: `terminal trace loss/query`; launcher: `Authority terminal failure`; driver: `LAUNCHER_FAILED`. Authority and detailed observers exited 95; application observer exited 0. Terminal receipt was not accepted; checker and success finalizer were not invoked.

## Witness and exact target correlation
Both witness sidecars are quiesced, sequence-complete and non-overflowed: authority 42 records; detailed 28 records. Both approved analyzers completed with zero missing roles. Correlation uses creator-owned native handles for direct processes and independent creation-verified tracker handles/images for consoles. It is diagnostic correlation, not kernel qualification. Windows are independently bounded by process creation/retention and kernel-handle signal observations; no witness-derived timestamps or PID-only matching.

| Role | PID | Creation FILETIME | Authority START / STOP | Detailed START / STOP |
|---|---:|---|---|---|
| sampler | 25160 | 134347961770442812 | NOT OBSERVED / NOT OBSERVED | NOT OBSERVED / NOT OBSERVED |
| sampler_console | 14260 | 134347961771109248 | NOT OBSERVED / NOT OBSERVED | NOT OBSERVED / NOT OBSERVED |
| hash_worker | 23960 | 134347961770442839 | NOT OBSERVED / NOT OBSERVED | NOT OBSERVED / NOT OBSERVED |
| hash_console | 21372 | 134347961771422178 | NOT OBSERVED / NOT OBSERVED | NOT OBSERVED / NOT OBSERVED |
| probe_1 | 7256 | 134347961771093737 | NOT OBSERVED / NOT OBSERVED | NOT OBSERVED / NOT OBSERVED |
| probe_1_console | 20756 | 134347961771839759 | NOT OBSERVED / NOT OBSERVED | NOT OBSERVED / NOT OBSERVED |
| probe_2 | 3196 | 134347961775259229 | NOT OBSERVED / NOT OBSERVED | NOT OBSERVED / NOT OBSERVED |
| probe_2_console | 17892 | 134347961776085199 | NOT OBSERVED / NOT OBSERVED | NOT OBSERVED / NOT OBSERVED |

For every listed target, selector disposition, parentKnown, instanceKnown, admission, exact event QPC and callback-arrival QPC are **UNKNOWN / unavailable** because neither callback observation exists. Each independently bounded START/STOP window overlaps increases in both sessions. Full bounds, all counter increments and observation fields are in `independent-targets.json`, the two `*-analysis.json` files and `*-loss-increments.json`. No callback absence is converted into proof of an exact lost payload.

The collector (PID 9036, creation 134347961765298403) was admitted in both channels: authority START event/arrival QPC 6290014286604 / 6290031998114 and STOP 6290043463031 / 6290054387266; detailed START 6290014286607 / 6290029874972 and STOP 6290043463033 / 6290049923030. No target UNKNOWN_PARENT/UNKNOWN_INSTANCE rejection was observed. A parent-filter cascade is therefore not established by this run. No target was witnessed admitted, so no target-specific downstream persistence defect is established.

## Loss / persistence
| Channel | Final EventsLost | Minimum sampled FreeBuffers | Maximum NumberOfBuffers | Writer queue high items / bytes |
|---|---:|---:|---:|---:|
| authority | 16 | 24 | 32 | 2 / 822 |
| detailed | 136196 | 12 | 45 | 29760 / 10105748 |

### authority observed increment windows (QPC; frequency 10,000,000)
- 6290018476154–6290019534258: 0 → 2
- 6290019533822–6290020639368: 2 → 5
- 6290020639034–6290021736550: 5 → 9
- 6290021735657–6290022773294: 9 → 10
- 6290023925024–6290025080401: 10 → 12
- 6290025080091–6290026101962: 12 → 14
- 6290027204635–6290028300827: 14 → 16

### detailed observed increment windows (QPC; frequency 10,000,000)
- 6290017402657–6290018476503: 0 → 11675
- 6290018476006–6290019534443: 11675 → 35240
- 6290019534088–6290020639373: 35240 → 63978
- 6290020638935–6290021736309: 63978 → 90816
- 6290021735804–6290022773322: 90816 → 96631
- 6290022772802–6290023925551: 96631 → 103079
- 6290023924985–6290025080572: 103079 → 121682
- 6290025080077–6290026102019: 121682 → 128775
- 6290026101584–6290027204778: 128775 → 133129
- 6290027204269–6290028301081: 133129 → 135329
- 6290028300504–6290029316706: 135329 → 136196

Counter sampling did not observe zero free buffers; it cannot rule out a transient between samples. The detailed writer backlog and delayed callbacks are observations, not proof of the underlying loss cause. Telemetry reported zero errors/overflow in both channels. Authority and detail stop/consumer results were 0, but EventsLost invalidates acceptance. Supporting CIM remains preserved and is not substituted for authoritative evidence.

## Cleanup and preservation limitation
Original absolute cleanup origin/deadline: 6290028948913 / 6290228948913 (20 seconds, never reset). Launcher FINAL_SHUTDOWN at 6290199478863: 17.053 seconds after origin. This is not full acceptance cleanup proof: terminal evidence failed and normal census/checker path was never reached.
The original failure-preserver returned CLEANUP_UNPROVEN / FAILURE_EVIDENCE_PARTIAL and archived two metadata members with no run-content members. Its first census detected pwsh PID 2236, creation 134347961971886233, during the assistant’s concurrent read-only status inspection. That historical result is unchanged. No second live attempt or success sealing occurred.
A subsequent host census found zero matching diagnostics/VirtualBox processes and zero traces. The independent recorded-instance check covered 16 identities, with zero remaining/unknown. This establishes eventual cleanup only. A separate post-quiescence NON-ACCEPTANCE archive preserves the full raw run, original partial preservation output, sidecars, analysis, candidate and source verification under deny-write/delete read locks; it does not repair acceptance.
Maximum recorded application heartbeat interval: 1.1667263 seconds (<10). Both probe hard-deadline flags were false. No observer/trace remains. Protected VM/configuration was never accessed; production unchanged. Only the two explicitly approved fresh-workspace path JSONs were rebound before launch; all other candidate bytes and frozen sources remain unchanged.

An offline read-only summary command had a SyntaxError (unmatched closing parenthesis); it did not run or alter any diagnostic. The corrected read used Get-Content only. No failed live evidence was changed.

## Disposition
Stage 6 remains incomplete. No medium, large, protected-baseline or production operation performed. No acceptance commit. Stop for owner review; any correction requires separate authorization.
HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
