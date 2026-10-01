# Stage 3 future intelligence and autonomy compatibility

Recorded 2026-09-11 from the user's future-compatibility addendum. Design requirements only; not implementation or migration evidence. Stage 2 remains closed in commit aede1be. This addendum does not start Stage 3 or authorize production cutover.

## Scope precedence

Stage 3 remains DATA PRESERVATION / MIGRATION REHEARSAL / VERIFICATION / ROLLBACK TESTING only. If a future capability needs work outside that boundary, record the dependency and defer it. No new autonomy, goals, provider routing, production tables, client backends or deployment are implied by these classifications.

ONE JARVIS Core owns identity, canonical memory, projects/tasks, providers, authorization, capability registry and resource accounting. Source, installed and future clients must not establish separate canonical datasets. Client presentation state may be separate. Test fixtures and disposable repair containers are not JARVIS instances.

## Five future directions and Stage 3 obligations

| Direction | Preserve or accommodate | Explicitly deferred |
|---|---|---|
| Hybrid intelligence | Existing canonical provider configuration, telemetry/evaluation provenance and relevant resource records; provider orchestration remains Core-owned | Provider selection during migration, Ollama Phase 2, client-owned provider configuration. Qwen remains SHADOW ONLY |
| Planning and execution | Existing project/task records and stable relationships; permit later durable objective/plan state without treating it as authority | New autonomous planning or goals; automatic resumption, tool replay or restored execution permission |
| Evaluation / Challenge Mode | Separate classification for approved evaluation history and regression evidence, with provenance | Challenge Mode; importing arbitrary test evidence into personal memory |
| Controlled self-repair | Already-canonical repair operation identities, recovery/budget evidence and verification references | Automatic production repair, generated patch deployment or production data access for generated code |
| Canonical multi-client platform | One authoritative data identity and compatible client attachment design; separate UI preferences | Desktop/installed/Intelligence/mobile memory forks or device-specific Core ownership |

## Data classification contract

These are conceptual data classes, not instructions to create new tables or directories. Stage 3 inventory must establish which records actually exist and are canonical before assigning migration actions. Unknown ownership is an unresolved finding, not permission to copy or discard data.

| Class | Preservation and restart rule |
|---|---|
| Identity data | Preserve canonical installation/data identity and provenance; do not confuse persistent identity with a new startup epoch |
| Memory / conversations | Preserve content, relationships and retention semantics; no evaluation/test material silently imported |
| Projects / tasks | Preserve records and references; unfinished state does not authorize scheduling or execution after restart |
| Resource budgets | Preserve accounting, operation IDs and reservation/recovery evidence; restored records must not double-spend, automatically release or resurrect reservations without reviewed reconciliation |
| Authorization / approval records | Preserve audit provenance and scope; historical approval is not restoration of a live execution grant |
| Device identity / configuration | Preserve legitimate persistent configuration; ONLINE/readiness must be freshly authenticated and re-established |
| Provider configuration / telemetry | Keep Core-owned configuration and telemetry provenance; preserve existing routing behavior and shadow-only restrictions |
| Evaluation / regression evidence | Keep separate from personal memory and production authorization; retain only records approved for the intended canonical class |
| Repair / recovery evidence | Preserve existing canonical identities, candidate/verification references and recovery history; review-only stays review-only |
| Client UI state | Remains presentation-specific where appropriate; cannot define canonical Core or data ownership |
| Ephemeral runtime state | Do not restore active sessions, in-flight execution, microphone ownership, online presence or transient authority as live state |
| Secrets | Identify separately; never include in public evidence/source snapshots or move implicitly with ordinary records. Protected handling needs its own reviewed migration policy |

Preservation of historical evidence and invalidation of live authority are separate operations. A migration must not erase audit records simply because an active session or capability is invalid after restart.

## Independent control boundaries

- Intelligence: can JARVIS understand this?
- Planning: can it plan this, and should it continue?
- Capabilities: can it technically perform the step?
- Authorization: is that step permitted?
- Resources: is the cost within approved budgets?
- Verification: did the action occur and meet its criteria?
- Evaluation: how well did it perform?
- Repair: can a fault be corrected through the bounded review process?

Budget availability is not execution authorization. Client authentication is not tool authorization. Model intent is not an approved action. Sandbox PASS is not deployment permission. A persistent objective is not permission to resume after restart. Migration must not collapse these boundaries.

## Future rehearsal acceptance requirements — NOT RUN

When Stage 3 is separately authorized, apply these requirements alongside its approved migration/rollback plan:

1. Inventory canonical ownership and all related tables/artifacts without silently creating a missing production database. Map existing components rather than duplicate them under new names.
2. Verify copy/backup fidelity, relationships and evidence references using isolated fixtures. Keep source, installed and client identities consistent with one canonical data mapping.
3. Verify restart/copy never resumes a task, replays a tool call, deploys a candidate, changes provider authority, marks a device ONLINE or restores transient permission.
4. Preserve accounting and recovery history and test reservation consistency; migration itself cannot become authorization or spend resources on behalf of restored work.
5. Verify class separation: evaluation and repair evidence cannot become personal memory or an approval grant by copying it.
6. Test interrupted migration and rollback, including post-cutover new writes, without overwriting newer records with an older snapshot. Use the approved Stage 3 failure matrix and retain failed evidence.

No checks above have been executed as part of this documentation-only addendum. No runtime code, production data, schema, provider behavior, authentication or lifecycle changed. Stage 2's unverified other-user/session/remote-host gates remain recorded; this document does not resolve them.

The future target is more capability with less required supervision, stronger verification, preserved authorization and safe recovery. Stage 3 preserves those foundations; it does not implement the future subsystems.

## Governing principle — user clarification

We are not only migrating a database. We are protecting the persistent state of the future JARVIS platform.

- Stage 1: prove only one Core can own the namespace.
- Stage 2: prove clients can securely identify that Core.
- Stage 3: prove JARVIS can move to canonical storage without losing, duplicating or rolling back his state.

Stage 3 must account for all canonical persistent state and its relationships, not just the database file. Rollback testing must prove safe recovery without silently replacing newer state with an older snapshot.

The data model must remain compatible with future hybrid intelligence, controlled planning, evaluation/Challenge Mode, bounded self-repair and multi-client/multi-device JARVIS. None is authorized for implementation in Stage 3.

ONE JARVIS. ONE CORE. ONE IDENTITY. ONE CANONICAL MEMORY.

Increasing capability without collapsing control boundaries.
