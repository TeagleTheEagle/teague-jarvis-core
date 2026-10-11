# Full baseline capture preflight — BLOCKED

2026-09-18. Full disk hashing and baseline manifest generation NOT STARTED.

The current brief requires preserved LocalhostReachable=0. Read-only parsing of the unchanged protected .vbox finds explicit localhost-reachable="true" in the current machine and both snapshots:
- CLEAN-WIN11-BASELINE: {2b0ebabc-7d4c-4ceb-bb5a-3f96d6e91992}
- JARVIS-CLEAN-DEPLOY-PASS: {3f6dbee0-faa2-446c-a426-04a57de387e7}

This is the known post-incident state. No new mutation is established. Do not repair the protected original or mislabel its current networking state as 0.

Inventory: 12 protected files, 59,665,402,098 bytes. Windows process query: zero VirtualBox processes; VBoxSDS Stopped, PID 0.

Small-file hashes match prior evidence:
- original .vbox: 98a89e62fd19ba49dc316b6e9c902fb6ba18fe4c66ec0ba8bf20deb3a892e93c
- original .vbox-prev: 9d69cc14a480aac13c9c03817aeeb4bc4d068a6fc27a81fc15ff2bc91de2c797
- C:\Users\jonny\.VirtualBox\VirtualBox.xml: f05da097d96f073a2569488a0fffc1682d7034e69069bab51b4409d88c2bdf0d

B2's C:\Users\jonny.VirtualBox path was interpreted as the previously verified C:\Users\jonny\.VirtualBox directory. No similarly named alternative path was used.

Preserved diagnostic error: the first read-only XML query assumed every NAT node had a Snapshot ancestor and raised a null-valued-expression error at the current machine node. Corrected only the ephemeral query to handle that node; no file or VM change occurred. The second query returned all three values shown above.

Required review: confirm the NEW POST-INCIDENT manifest must record observed LocalhostReachable=1, explicitly distinguish historical intended baseline=0, and retain required future disposable validation setting=0. This does not approve or require changing the protected original.

Full SHA-256 inventory, snapshot/disk/NVRAM relationship manifest and second full content verification remain NOT RUN. No baseline manifest path/hash exists. This report is a blocked preflight finding, not a completed baseline.

No VirtualBox commands, VM control/copy, account/ACL/security change, production change or guest validation occurred. Earlier evidence remains untouched. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
