# Stage 4 controller expiry — isolated diagnosis for review

2026-09-15. **Diagnosis complete; correction NOT implemented. Stage 4 remains incomplete.**

## Evidence and limits

The no-Core diagnostic exercised the actual `Ownership`, `Lifecycle` and `Authority.operation` methods with an injected clock, a memory journal and a stub device-registration object. All **27 expected-behavior checks passed**. No App, Store, Core, provider, socket listener or physical media was created. The Stage 2 pipe handshake was not exercised; this tests the trusted post-authentication dispatcher, not a new end-to-end authentication PASS. Synthetic lifecycle calls created only this evidence directory's empty `stop` latch.

Source behavior confirmed:

1. Session expiry removes the old session, cancels its work/media and removes its management capabilities. STATUS, SHUTDOWN and RENEW with that expired token are denied.
2. A fresh attach with no old token works while RUNNING. The same dispatcher identity/epoch is returned, but the new session gets a different ownership family. It cannot inspect/cancel the prior family's repair. No request is replayed. A before-expiry renewal instead preserves the family and invalidates the old token.
3. The retained TEST controller accepts only STATUS and SHUTDOWN. Both use its saved session token; it has no explicit fresh-authentication command.
4. `Ownership.attach_verified` and `renew_verified` require RUNNING. Fresh attachment after expiry is denied in SUSPENDED, DRAINING, CANCELLING, RECOVERY_REQUIRED and FINALIZING, for both ordinary and management clients.
5. Therefore, after an authorized emergency stop enters SUSPENDED, a controller that later expires cannot reattach and cannot authorize shutdown. This is reproduced without changing clocks/expiry in a live Core.
6. With a valid fresh RUNNING controller, emergency stop and separately requested shutdown work through the actual dispatcher. The synthetic never-started work drains without replay. This is a model/dispatcher check, not proof of OS process exit.

The prior long-interruption run remains distinct: its broken pipe, NEVER_STARTED journal, zero reservations and denied controller are preserved in the September 13 checkpoint. This diagnosis establishes current expiry/reattachment behavior; it does not independently establish the cause of the historical interruption or recover its uncaptured state/traceback.

## Minimum corrections proposed — approval required

### A. TEST controller recovery while RUNNING

In `tests/lifecycle_stage4/fixtures.py`, add an explicit operator REAUTH command that performs the existing Stage 2 authenticated attachment with `token=None`, using only the retained in-memory enrollment credentials and the already pinned Core peer/identity. Verify the same namespace, instance/epoch, process creation time and executable identity. Do not start a Core, renew an expired token, retry a repair, inherit an old request family or persist credentials. STATUS and SHUTDOWN remain separate explicit commands. Denial or uncertain identity remains a stop condition.

Test this in `tests/lifecycle_stage4/test_stage4.py` and the existing TEST fixture. This narrowly fixes the retained driver's missing command for RUNNING; it does not solve non-RUNNING recovery.

### B. Expired lifecycle controller in a non-RUNNING state

This needs a reviewed Core session-policy addition, not a general relaxation of `attach_verified`:

- A distinct, freshly Stage-2-authenticated management recovery attachment for already enrolled lifecycle controllers only.
- New session/family with only the explicitly reviewed lifecycle-status/shutdown recovery permissions. No ordinary request, repair, media, memory or prior-operation ownership.
- Permit only reviewed recovery states (SUSPENDED, DRAINING, CANCELLING, RECOVERY_REQUIRED); continue refusing FINALIZING and ordinary attachments outside RUNNING.
- Preserve existing lifecycle rules: attachment itself does not restart a drain deadline, turn UNKNOWN into known, clear quarantine, replay an operation or authorize termination. An unresolved UNKNOWN must still refuse shutdown.
- Keep expiry, identity checks, enrollment revocation, protocol and authentication protections unchanged.

Proposed file scope: `stage4_sessions.py`, `stage4_runtime.py`, `tests/lifecycle_stage4/fixtures.py`, `tests/lifecycle_stage4/test_stage4.py`. No Store/schema, Stage 1–3, provider, production launcher or production authentication change. Precise management-recovery scope and permitted operations require approval before implementation. No special renderer access is proposed.

## Validation after approval

First add focused offline tests for explicit fresh authentication, fresh family, expired/revoked/wrong-client/wrong-identity denial, no repair replay, restricted recovery scopes, non-RUNNING ordinary-client denial, FINALIZING denial, unchanged UNKNOWN quarantine and no drain-deadline reset. Then use bounded authenticated TEST IPC tests with safe lifecycle cleanup to verify the same existing TEST Core identity across expiry/reattachment. Exercise emergency-stop then expiry then explicit management recovery, known shutdown, and unresolved-work refusal. Do not launch a replacement Core or force cleanup without separately applicable authorization.

Rerun relevant Stage 1–4 and desktop regressions after the correction. These end-to-end tests were **not run in this diagnosis** because a policy change is now indicated and requires review. No automatic retries or production tests were performed.

## Rollback, provenance and boundaries

No runtime/source correction exists to roll back in this checkpoint. Six inspected source snapshots/hashes and the diagnostic script/results are retained. The diagnostic only writes its own evidence and synthetic stop latch. After any approved correction, capture an exact pre-edit snapshot and reverse only those reviewed files if rollback is required; retain all failures and do not reset unrelated work.

Historical Stage 1 PermissionError remains ROOT CAUSE UNCONFIRMED / FAIL-SAFE / REVIEW REQUIRED. No newer finding is used to fill its missing evidence.

PRODUCTION SOURCE MODIFIED: NO  
PRODUCTION DATA MODIFIED: NO  
PRODUCTION CORE RESTARTED: NO  
NEW CORE LAUNCHED: NO  
AUTHENTICATION CORRECTION IMPLEMENTED: NO  
ACCEPTANCE COMMIT CREATED: NO  
STAGE 5 STARTED: NO

**Requested review:** approve A (explicit TEST controller REAUTH using existing authentication) and separately B (restricted management recovery attachment with the state/authority limits above). The user required any correction to be presented for review before implementation; this checkpoint stops at that gate.
