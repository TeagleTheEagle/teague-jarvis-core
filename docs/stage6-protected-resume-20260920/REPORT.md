# Synthetic protected-collector resume — BLOCKED at preflight

No UAC prompt was issued by this attempt. No tracer, application observer or monitored hash worker was launched. No retry, calibration repeat, protected VM/configuration access, VirtualBox launch or production change occurred.

## Exact failure

The new report-only `preflight.py` attempted to re-read **every original source path** represented in the prior archive, including generated historical test fixtures. That extra check was broader than the requested frozen collector/calibration/archive checks.

It stopped with `PermissionError: [Errno 13] Permission denied` reading:

`D:\JARVIS-STAGE6-LIVE\1c1f5d0c390b42cc9ba9f4f6221dabc6\code\final-test-1kkhohf2\collector-finished.json`

This is a generated test artifact, not one of the frozen collector source files. The denial's underlying Windows/sandbox/ACL cause has not been diagnosed. It does not establish collector source drift, archive corruption or a monitor defect.

Before that failure, the canonical ZIP SHA-256 and archive-manifest SHA-256 matched their preserved receipts. The archive member/current-original-path loop did not complete. The subsequent 84-file candidate verification, calibration verification, dataset metadata check and process/trace preflight were not reached. No complete preflight PASS is claimed.

## Required narrow correction for the next attempt

Keep the candidate and thresholds unchanged. Correct the report-only preflight to verify historical test evidence from the hash-verified ZIP, rather than requiring read access to each live historical fixture. Separately verify the 84 frozen candidate files, calibration records, synthetic dataset metadata and process/trace state as requested. Do not change ACLs, weaken UAC or reopen historical test fixtures merely to validate an intact archive.

The owner's instruction requires stopping if preflight fails, so that corrected check and the monitored run were not executed in this attempt. The failed helper and this report are retained separately from all previously archived evidence.

Final disposition: **BLOCKED**. The collector remains unvalidated for real protected capture. Per-run UAC behavior remains unchanged. Real protected baseline capture is not performed or authorized by this result.
