# Shared project budgets and reservation lifecycle — 11 September 2026

Status: implementation and deterministic regressions PASSED. Not yet wired into autonomous repair/provider/device execution. Not a financial billing ledger.

## Ownership and scope

ONE JARVIS Core retains its existing Store. project_budgets.py accepts that Store as an argument; it creates no database, Core, provider, listener or worker of its own. Two additive tables live in the existing jarvis.sqlite3: project_budget_limits and project_budget_reservations. workspaces.setup initializes them; workspace listings expose budget summaries. Existing authenticated workspace actions support budget_configure and budget_reserve. No new endpoint or model tool is added.

Budgets count core_requests and container_checks per project. Reservations for all linked tasks share that project's total. Projects currently have independent budgets; no global account-wide cap exists. No limit is configured implicitly. Existing provider calls, retries, devices and repair CLI are NOT intercepted yet. A Core request is not necessarily one provider API call. No currency prices or token-cost estimates are invented: cost_usd remains null.

## Lifecycle contract

Reservations hold capacity before work. Stable (project, operation) identity provides idempotency: an exact duplicate reports replay=true and new_reservation=false. Changed inputs under the same ID are rejected. BEGIN IMMEDIATE serializes capacity checks and mutations. Configuration cannot reduce limits below charged capacity or reset history.

States: held -> started -> settled, or held -> released. Expired held/started records require recovery. The default lease is 300 seconds. Expiry is visible in snapshots and rejects new start; internal expire records recovery_required. Expiry never automatically refunds or repeats work.

Internal lifecycle() uses expected revision for compare-and-update semantics. Its methods are NOT exposed through the workspace HTTP action handler or a model tool:

- start: one caller wins; start_granted denotes a reservation transition only, never tool permission.
- consume: cumulative measured usage can only increase within the allocation. Partial usage does not release outstanding held capacity.
- settle: trusted caller must independently verify outcome and supply cumulative actual usage plus an audit evidence reference. Success or failure preserves consumed units and releases the unused remainder. The evidence string is NOT independently verified by this module: integration must connect it to real Core verification before relying on refunds.
- release: only an operation never marked started and with zero consumption can be released. Started or ambiguous work needs verified settlement.
- terminal retries: exact matching settlement/release returns replay; no second refund/start. Different terminal outcomes/usage are rejected.

All returns set execution_authorized=false. Budget availability, objective readiness and a lifecycle start grant do not authorize tool execution, provider routing, resource purchases or deployment. Existing authorization must be checked independently at execution time.

Restart preserves held/consumed capacity. Legacy rows without lifecycle metadata migrate conservatively to recovery_required with started=true and their full allocation retained. Corrupt numeric counts, states, revisions or inconsistent totals fail closed. No automatic DB repair or destructive history cleanup. This is not cryptographic tamper protection against someone able to rewrite the canonical database.

Snapshot fields: reserved is total charged capacity (held plus consumed); consumed is recorded usage; held is the remaining outstanding reservation; remaining is unallocated project capacity; recovery_required identifies stale/uncertain operations.

## Tests actually run

12 budget tests, plus project-plan and workspace tests (16 targeted tests total), passed. Coverage includes:

1. Eight simultaneous unique reservations competing for one unit: exactly one success.
2. Reopening Store preserves reservations and canonical memory/task records.
3. Held reservation expiry blocks start, retains capacity, permits explicit unstarted recovery release.
4. Started expiry retains capacity across restart; blind release rejected; independently supplied failed settlement permits reconciliation.
5. Over-budget rejection, unknown projects/tasks or missing configuration, invalid/negative/non-integer counts.
6. Partial consumption remains charged; failed-operation settlement releases only unused capacity; backwards consumption rejected.
7. Exact duplicate reservations return no new grant; conflicting duplicate identity rejected; eight concurrent identical requests yield one new reservation and seven replays.
8. Duplicate final settlement/release does not refund twice; changed terminal result rejected.
9. Corrupted negative reservation blocks allocation/listing; stale revisions block mutation.
10. Concurrent start versus release: exactly one succeeds.

Full Python discovery: **205/205 passed in 15.593 seconds**. Desktop: **13/13 passed in 26.214 seconds**. Python compilation and git diff whitespace checks passed (normal CRLF warnings only). Tests used temporary Stores and concurrent threads with distinct SQLite connections. These are not production multi-device load tests, abrupt OS-kill recovery tests or physical device validation. Production desktop was not restarted and no live project budgets were configured. No live API call or image upload occurred in this stage.

## Files and next work

Created project_budgets.py, test_project_budgets.py and this report. Modified workspaces.py to initialize/expose budgets and dispatch the two authenticated actions. Other existing working-tree changes preserved.

Next integration gate: trusted Core execution adapter must reserve/start before authorized work, reject replay as a fresh execution, record measured usage and verify completion before settlement. Add real provider usage reporting and a global ledger before calling this an economic boundary across providers/projects. Confirm crash reconciliation, process-level concurrency, lease clock behavior, operator recovery UX and live multi-device execution before activating autonomous actions. No scheduler or runtime wiring is claimed by this stage.
