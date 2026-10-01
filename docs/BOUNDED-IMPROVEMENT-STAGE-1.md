# JARVIS improvement capability — first bounded experiment

2026-09-11. User direction: eventually diagnose, repair and build improvements with minimal manual direction, under ONE JARVIS Core.

## Audit and reuse

- `server.App` remains authoritative. `Run.cancel`, tool dispatch and approval records already handle cancellation, expiry and execution decisions.
- `development.py` already stages diffs, validates syntax, records before/candidate hashes and supports reviewed rollback. Reused directly; no new proposal store or canonical memory.
- Existing production policy applies certain CSS/personality changes immediately. This experiment does not use that route or change existing policy; all experiment results are review-only.
- `device_registry.py` already plans capability routing; it is not a general software-improvement planner.
- `computer_tools.run_tests` already provides a bounded regression command. Production-generated candidate execution needs stronger isolation than a subprocess before it can be enabled.
- Inspected components do not establish a durable autonomous improvement scheduler, independent evaluation/promotion controller, or enforced resource-allocation ledger. A complete Core 2.0 gap audit must precede adding replacements for overlapping systems.

## Implemented now

`improvement_experiment.py` is a TEST ONLY development harness. It imports the existing proposal utility but never instantiates App, Store, AI, voice, registry or an assistant. It runs a fixed, explicitly labelled delay-handling fixture in a temporary directory. The filename wake.py is used solely to reuse the existing source allowlist; production wake.py is never read or changed.

Sequence: fixed approved objective → four predetermined subgoals → failing baseline → staged fixed candidate → unchanged independent behavioral checks → reviewable diff. Baseline 3/4; candidate 4/4; original fixture remains unchanged. No deployment entry point. No production runtime integration, autonomous goal generation, model training or live patch generation is claimed.

Limits: 10-second default / 30-second maximum wall-time budget; two sequential child invocations, no retries; cancellation checks between steps and during child execution; killed children are reaped. Keyboard interruption also runs cleanup. Provider calls and purchases are absent. Child environment omits inherited provider credentials; command is fixed and shell-free. This process separation is NOT a security sandbox for arbitrary code, and CPU/memory/network are not OS-restricted. Therefore only the fixed reviewed fixture is supported.

Run from the authoritative repository:

```powershell
.venv\Scripts\python.exe improvement_experiment.py
.venv\Scripts\python.exe -m unittest test_improvement_experiment
```

No automatic resume: a stopped process cannot deploy anything; a fresh run creates a fresh temporary experiment. No background monitor or service is installed.

## Verified results

- Fixed local experiment: READY_FOR_REVIEW; baseline 3/4, candidate 4/4; source unchanged; about 0.156 seconds in the recorded first run.
- Targeted experiment/development/automatic-action tests: 13 passed.
- Full Python discovery: 173 passed in 14.219 seconds.
- Root JavaScript and desktop checks: 29 passed in 27.709 seconds.
- Cancellation during child execution, pre-cancel, exhausted budget, invalid budgets, failed candidate and forbidden deployment covered by the new five-test suite.
- No live provider or voice test performed; production code and runtime were not restarted for this isolated harness.

## Proposed path to greater autonomy

1. Core-owned issue intake from approved diagnostics and user objectives; deduplicate against existing tasks and keep one conversation/memory owner.
2. Candidate generation on isolated worktrees using the existing provider path, with protected independent tests and an OS-restricted execution environment. No credentials or production databases in that environment.
3. Evidence-based review of candidates against baseline, security checks, PC voice/vision regressions and resource limits; failed candidates cannot promote themselves or modify their own gates.
4. User-approved automatic promotion scope for routine reversible fixes, with checkpoint, health checks, rollback and maximum attempts. Broader Core architecture, authorization, identity/memory migrations and security changes remain reviewed. Existing Astra/Core review gates remain applicable.
5. Budgeted use of already-approved compute/storage; separately authorize purchases, credentials or expanded access. Resource acquisition serves the user's approved objectives, not an assistant objective of expanding itself.

These stages are planned, not activated. Stronger models can improve candidate quality but cannot guarantee safe repairs, correctness or unlimited recursive gains. The immediate next gate is review of this experiment and the isolation/promotion design before executing model-generated candidates.
