# TEAGUE INDUSTRIES — DATA & APPLICATION IDENTITY PROTOCOL 1.0

**Status:** PROTOTYPE / TESTED  
**Scope:** application identity, data-index design and safe Files/Data presentation  
**Boundary:** no repository move, production migration, JARVIS Core change or automatic capture in this phase.

## Identity

The existing desktop application is presented as **TEAGUE INDUSTRIES COMMAND CENTER**. JARVIS remains the shared intelligence inside it: JARVIS Core, Memory, Voice, Vision, Gateway, Personality and Capability Registry retain their existing names and behavior. The window title is `Teague Industries Command Center · JARVIS`; the existing shell still reports JARVIS online and shared Core.

The canonical approved mark is `static/assets/branding/teague/teague-mark.svg`. It is used by the application shell and is passed to the Electron window as its supported icon path. No low-resolution screenshot was introduced and the existing tray asset was retained until a verified native icon migration is available. A packaged Windows `.ico`/shortcut replacement remains a follow-up requiring packaging validation.

## Storage audit and safety boundary

The proposed persistent engineering-data root is:

`C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE`

That folder already contains `01 CORE` through `07 EXPERIMENTS`, plus `CURRENT STATUS.md`, `DECISIONS.md`, `DOCUMENT MANIFEST.json`, `EXPERIMENT LOG.md`, `HARDWARE LAB.md`, `INDEX.md`, `JARVIS MASTER OVERVIEW.md` and `ROADMAP.md`. The live runtime remains in `outputs/jarvis`; no files were moved, deleted or migrated. The current environment did not grant write access to the OneDrive folder, so no sync or migration was attempted.

Git remains the exact source history. The Teague database will index and contextualise commits, tests and decisions; it will not replace commits, branches, tags or rollback. The existing `Sync-TeagueIndustries.ps1` is a reviewed, secrets-excluding future sync mechanism and was not run in this phase.

The index must never contain API keys, passwords, tokens, `.env` contents, private keys or session credentials. It should record only safe facts such as “OPENAI_API_KEY configured”. Caches, environments, `node_modules`, build output and irrelevant OS files are excluded unless explicitly selected as evidence.

## Proposed authoritative structure

```text
TEAGUE INDUSTRIES DATABASE/
  01 CORE/          identity, architecture, decisions, JARVIS Core records
  02 DEVICES/       PC, phone, glasses and capability records
  03 SOFTWARE/      application, UI and service records
  04 HARDWARE/      lab notes, models and verified hardware evidence
  05 DELIVERY/      releases, validation and change records
  06 SOURCE RECORDS/ imported reports, manifests and provenance links
  07 EXPERIMENTS/   experiments, benchmarks and failure records
  INDEX.md          searchable category map
  DOCUMENT MANIFEST.json
```

Each indexed item carries `id`, `title`, `category`, `status`, `source_path`, `source_kind` (`git`, `teague-folder`, `workspace`), `commit_id` when available, `created_at`, `updated_at`, `related_project`, `related_decision`, `related_experiment`, `tests` and `notes`. Missing values remain unknown; they are not inferred.

Supported status values are: `PLANNED`, `PROTOTYPE`, `IMPLEMENTED`, `TESTED`, `VERIFIED`, `FAILED`, `BLOCKED`, `DEPRECATED`, `ARCHIVED`.

## Change-record schema

```json
{
  "change_id": "TI-YYYYMMDD-NNN",
  "timestamp": "ISO-8601",
  "project": "",
  "component": "",
  "description": "",
  "reason": "",
  "files_changed": [],
  "commit_id": "",
  "tests_run": [],
  "test_results": "",
  "status": "PROTOTYPE",
  "author_agent": "",
  "rollback_point": "",
  "related_decision": "",
  "related_experiment": "",
  "notes": ""
}
```

The safe future flow is **code → tests → Git commit → change record → Teague index → JARVIS retrieval**. A failed or unverified change must never be labelled `VERIFIED` automatically. Automatic capture, Core querying and Gateway/security integration are explicitly deferred to an Astra-reviewed phase.

## Historical indexing plan

1. Inventory repository documentation, `docs/`, wearable and iOS records, milestone reports, Core 2.0 audit, suite design, experiments, test reports, architecture documents and Git history.
2. Hash or reference each source without rewriting it; retain its original path and provenance.
3. Create one index entry per meaningful document, experiment, release and decision. Deduplicate by source path and commit ID.
4. Derive status only from explicit evidence (test output, verification report or decision); otherwise use `PROTOTYPE` or `UNKNOWN` in notes.
5. Review the generated manifest before any future write to the persistent root.

## Files / Data interface

The existing Files view now includes a presentation-only **TEAGUE INDUSTRIES DATABASE / AUTHORITATIVE DATA INDEX**. It exposes the planned category tree (Projects, JARVIS Core, Software, Hardware, Experiments, Research, Designs, Changes and Archives), three provenance-labelled example records, status badges, and the proposed persistent root. Category selection is a local UI interaction with no storage migration. Existing upload, local indexing, search, inspector and export handlers remain unchanged.

## Verification

After the identity and Files/Data presentation changes:

- Python regression suite: **147 passed**.
- Desktop Node suite: **13 passed**.
- JavaScript syntax check, Python compilation and Git whitespace check: **passed**.

The Teague folder was read for discovery only. No secrets were copied and no production data path was changed.

## Deferred / requires Astra or explicit approval

- packaged Windows `.ico` and desktop-shortcut migration validation;
- writing or migrating records into the OneDrive database root;
- automatic change-record capture and provenance indexing;
- JARVIS Core/database query integration;
- production database, backup/recovery and Gateway/security changes.

This phase stops here by design. It preserves one JARVIS, one memory and the current PC application while establishing the Teague Industries identity and a safe data-system contract.
