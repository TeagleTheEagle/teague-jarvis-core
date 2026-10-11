# Shared-Core repair workflow and project planning — 11 September 2026

ONE JARVIS. ONE CORE. ONE IDENTITY. ONE MEMORY.

## Implemented and verified

repair_workflow.py orchestrates the fixed delay fixture: baseline runtime -> observed failures -> fresh existing Core diagnosis/candidate -> schema and numeric syntax validation -> independent AST and real sandbox checks -> diff for review. No apply/deploy call exists. The supplied Core object is reused; the CLI constructs only RealCore, the existing authenticated loopback client. No server.App, Store, provider or voice owner is created. The container holds Python and fixture text only.

Live result READY_FOR_REVIEW in 8.016 seconds. Baseline 4/6; two negative inputs were observed failing. Existing JARVIS diagnosed negative delays passing through and generated `return max(seconds, 0)`. Fresh patch passed 6/6 in the real rootless container. Core diagnosis/generation phase approximately 5.047 seconds; baseline including preflight 1.687 seconds; final verification including preflight 1.282 seconds. No saved-answer substitution. One Core request, two container checks, no workflow retries, no purchases. Provider usage/cost unknown; Core may retain its own established retries and tool routing, so a Core-request count is not a guaranteed external API-call count or monetary cap.

The existing Core may save this exercise as an ordinary shared conversation and add its normal relevant context. No credentials leave Core for the runner. Diagnosis is model text, not trusted authority. Only validated numeric source proceeds. Cancellation is forwarded to the existing Core client and sandbox. Deadline blocks new work; cleanup and existing network timeouts may extend return time beyond 180 seconds. No hard real-time cancellation promise.

workspaces.py now supports plan_task through the existing authenticated workspace change endpoint. It annotates existing project-linked task records in workspace_links.content with objective, success_criteria, blocker and depends_on. No new database, task copy or schema migration. Existing task completion is authoritative. Project listings include read-only task_plan results: READY, BLOCKED, COMPLETED or MISSING. All entries explicitly have execution_authorized=false. Self/cyclic/duplicate/unknown dependencies are rejected; unlinked or missing dependencies fail closed. Relinking preserves planning metadata. Unlinking deliberately removes the project association and its annotation, not the canonical task.

This is structured planning metadata and readiness, not autonomous subgoal generation. No new UI editor or execution scheduler was added. Live application was not restarted to load the workspace change, and live user records were not edited. Temporary Store instances existed only in regression fixtures.

## Tests

8 new workflow tests: one supplied Core/request, no deployment, baseline failure stops generation, invalid code stops sandbox, failed verification rejects, pre-cancel, provider failure/no raw error/no retry, provider cancellation, schema/budget rejection (some combined).

3 new workspace-plan tests cover shared task/memory preservation, restart persistence, readiness without authority, relinking, invalid/cyclic dependencies, blocked/unlinked dependencies and explicit blockers.

Full Python suite: 193/193 passed in 13.856 seconds. Desktop: 13/13 passed in 26.003 seconds. Final relink-preservation adjustment tested separately afterward. Prior repair-controller isolation evidence remains in REPAIR-CONTROLLER-STAGE-1.md and repair-sandbox-results.json. No new live voice/vision or physical-device test.

Run from repository: `.venv\Scripts\python.exe repair_workflow.py` for a live fixture request through the running Core (normal provider charges apply), or `.venv\Scripts\python.exe -m unittest test_repair_workflow test_workspace_plans` for deterministic tests. Workflow results overwrite docs/repair-workflow-results.json; report files are experiment evidence, not canonical JARVIS memory.

## Program still incomplete

Next: explicit approved objective adoption and scoped generated subgoal validation; common verification and provider-health contracts; measured usage ledger and shared budgets; bounded tool execution and crash/restart recovery; reviewed deployment/rollback. General self-repair, arbitrary feature generation, automatic production changes, true streaming, memory retention expansion and production gateway remain unfinished. Physical iPhone/Meta/iOS gates require actual device/build access; purchases, expanded system permissions and external account setup need specific authorization. Ollama Phase 2 still requires its evidence/review gate. Existing PC behavior, provider routing and authorization remain authoritative.

Created: repair_workflow.py, test_repair_workflow.py, test_workspace_plans.py, docs/repair-workflow-results.json, this report. Modified: workspaces.py. Earlier unrelated UI edits are preserved.
