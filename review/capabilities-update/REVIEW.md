# JARVIS capability update — ready for review

**Prepared and tested in an isolated candidate. Not installed in the running app.**

## Included

- Exact local activate/show/open/hide hologram, mute/unmute and stop-speaking
  commands, plus state checks. Registered `assistant_control` waits for an
  authenticated acknowledgement from the requesting interface. Merely opening
  the hologram does not enable the microphone or screen capture.
- Existing screen-sharing/capture functions are reused. Browser source approval
  remains required. Status distinguishes live capture, sampled analysis and a
  requested single screenshot. Analysis queued behind a current reply is
  reported as requested, never as already submitted or complete.
- Automatic local archiving of future terminal inspections, including partial,
  failed and cancelled jobs. Originals are dated Markdown files in
  `data/inspection-archive`, linked through the existing document storage to
  verified Project Jarvis ID `0383e8c2e67346b59c484a5766b581f4`.
- Separate structured SQLite archive/tracker tables; no personal-memory entries.
  Actual findings are extracted from structured panel analysis. If the model
  does not supply usable structured findings, the original review remains
  available and the missing tracker extraction is stated.
- An Inspection Archive control in Communications: latest/all reports,
  last-two comparison, tracker and explicit records of the user's testing or
  decisions. Archived text is rendered as text, never executable HTML.
- Stable finding IDs and original-report references; normalized exact recurring
  descriptions are linked instead of duplicated. Status changes are separate
  dated events. Linked development proposals are checked against actual saved
  history/current pending approvals. Applied is never automatically verified.
- Registered timer listing, exact-ID adjustment/cancellation and saved-fact
  update/deletion. Multiple matching timers or memories require clarification.
  Credentials and duplicate durable memories are rejected.
- Existing development history includes current approval availability and an
  explicit distinction from runtime verification. JARVIS cannot approve itself.
- Response timing metadata: queue/context time, provider first token/completion,
  tool durations, retry occurrence and overall run duration. The last 20 request
  samples live only in server memory and exclude transcript/audio/image data.

## Changed source files

`assistant_capabilities.py` adds storage, tracker, management and acknowledgement
logic. `actions.py` registers narrow schemas. `server.py` wires tools, authenticated
routes, archives and timing. `inspection_jobs.py` waits for archive results before
reporting a final job. `inspection_runtime.py` includes the new frontend asset.
`static/assistant-controls.js` contains commands and the archive UI;
`static/app.js`, `static/index.html` and `static/inspection-client.js` connect them.
`desktop/main.cjs` and `desktop/preload.cjs` add authenticated companion hide/status
and prevent a hidden loading companion from reappearing.

No edits to development.ALLOWED, credentials, microphone permission policies,
capture-consent policy, startup configuration or executable self-approval.

## Validation performed

- 11 focused backend capability tests passed: persistence, immutability,
  recurring findings, failure rollback, tracker status, timers, memory,
  acknowledgement timeout/cancellation, timing metadata and registry.
- 48 existing Python regression tests passed across core behavior, memory,
  workspaces, context, navigation, reliability, automatic actions and screen
  observations.
- 11 inspection runtime tests passed, including real isolated Chromium renders
  of all 13 panels, long content, private-data masking and state preservation.
- 4 inspection job lifecycle tests passed.
- 7 route tests passed, including three new capability checks; the command also
  reran four inherited baseline HTTP tests. Session/origin rejection and
  single-inspection-to-archive retrieval were exercised.
- One real Chromium browser test passed for frontend control routing and archive
  display, with fake devices/bridges and intercepted network requests. The
  archive screenshot was visually reviewed.
- Six existing Node regression scripts passed: navigation, screen intent,
  screen vision, voice diagnostics, conversation mode and speech cancellation.
- Mocked Electron test passed: trusted-sender checks, status, show/hide, singleton
  reuse and hiding while the companion loads. Native Electron is not implied.
- Python compilation and changed JavaScript syntax checks passed.
- Installation dry run passed. A temporary-directory test passed for explicit
  apply, rollback, and refusing to overwrite a subsequent source change.

## Remaining validation and limits

- Native Electron microphone/device permissions, screen selection and audible
  speech require a post-installation test. No screenshots/audio were sent to a
  cloud provider during development validation.
- Timing collection is implemented, but no live cloud latency sample has been
  collected and no speedup benchmark is claimed. First-response buffering is
  retained to preserve the existing retry behavior. Retry attempts are flagged;
  individual retry token timings are not yet measured.
- A muted microphone cannot receive an unmute voice command. Use the button,
  keyboard control or text command in that state.
- Previous expired in-memory inspections are not recovered. This archives new
  inspections after installation. Captures keep the existing five-minute TTL;
  the archive does not copy screenshots, raw DOM text or temporary image URLs.
- Original report files and database evidence are not edited by application
  tools. A Windows user with filesystem access can still alter their own files.
- Reports persist until deliberately removed through a future archive-deletion
  workflow or managed local-data cleanup. No automatic report deletion is added.
- Comparison does not mark absent findings fixed. Reworded findings may need
  manual correlation. A recorded user test is labelled user confirmation, not
  an automated test.
- Missing Project Jarvis, unavailable storage or invalid model output is
  reported; no substitute project, successful archive or finding is invented.
- Interface actions require a connected requesting renderer. Timeout produces an
  unconfirmed result. Screen contents cannot authorise these control tools.

## Review and installation

`changes.diff` contains the complete source diff; `before/` contains backups;
`manifest.json` records original and candidate hashes. `install_update.py` only
validates by default. After approval, `--apply` installs this exact package and
the desktop updater will request a restart. It will refuse to overwrite source
that changed after review. No installation has been performed.

Rollback uses `install_update.py --rollback --apply`, also guarded by exact
installed hashes. It restores source and leaves inspection evidence/data intact.
The implementation follows the supplied requirement to prepare executable
changes for review before applying them.

## Post-installation commands

- “Activate hologram”, “Hide hologram”, “Hologram status”.
- “Mute mic”, “Unmute mic” (typed while muted), “Stop speaking”.
- “Start screen sharing”, “Screen sharing status”, “Stop sharing”.
- “Analyse my screen” for one immediate analysis using existing consent.
- “Show the last interface inspection”, “Compare the last two inspections”.
- “What still needs attention?”, “Which changes are awaiting testing?”.
- “List active timers”, then cancel/adjust the named timer.
- “List saved memories”, then update/delete the exact fact or ID.
- “Show my response timings”.
