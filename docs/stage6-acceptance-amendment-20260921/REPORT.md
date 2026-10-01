# Stage 6 acceptance amendment applied

Status: **CONTRACT_AMENDMENT_APPLIED — IMPLEMENTATION / VALIDATION PENDING**

The owner's ten-condition approval is recorded as the versioned TEST contract [CONTRACT.md](CONTRACT.md). The earlier immutable review remains untouched.

The sole changed acceptance requirement is the mandatory one-to-one independently instance-bound CIM START/STOP mapping. Kernel process-instance lifecycle becomes authoritative conditionally on proven completeness, uniqueness, sequence integrity and independent persistent-evidence verification. Supporting CIM remains collected and independently persisted; ambiguity/unmatched results stay explicit. Positive contradictions, collector loss/corruption, missing kernel records, ETW loss, missing segments, sequence gaps, handle/native contradictions and incomplete cleanup continue to block acceptance.

No collector, checker, writer, production runtime or configuration source was edited. In particular, the old checker remains a frozen implementation of the old contract; its rejection paths were not deleted. Applying this normative amendment is not a claim that a revised checker or durable writer exists or passes acceptance.

The exact next proposed durability step is [NEXT-STEP.md](NEXT-STEP.md). The design remains unvalidated. No sacrificial campaigns, medium/large runs, 59.7 GB hashing, protected VM access, protected hashing, VirtualBox launch or production operation occurred in this pass.

## Preservation and verification

`verification-before.json` and `verification-after.json` record hash verification of the frozen candidate/reference set, all prior review archive members, and the source files preserved by the previous review. Counts and actual results are in those records. `archive-verification.json` records the new archive's independently reread member count and hashes. These are integrity checks, not runtime acceptance tests.

New files only: this report, the versioned contract, next-step proposal, the narrow evidence verification/archive helper, and their generated integrity records/manifest/receipt. The archive is a fresh directory in TEAGUE INDUSTRIES DATABASE; no previous archive is overwritten. No commit is created.

Historical 21 AMBIGUOUS / 1 UNMATCHED remain unchanged. Historical delay causes remain UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

Stage 6 is not complete and protected-baseline capture remains unauthorized. Stop here; no further gate is run.
