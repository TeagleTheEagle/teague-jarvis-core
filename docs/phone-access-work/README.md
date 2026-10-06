# Prepared, not applied: items C and D of docs/PHONE-ACCESS-PLAN.md

Written in the PC session of 2026-10-07 (about 02:20 local) while item A was under review, and left here when the
owner ended the session ("finish what your doing then shut down my pc"). **Nothing in this folder has been applied,
run or reviewed.** The next session applies it, tests it, has it reviewed, records it, and then deletes this folder.

- `edit_items_cd.py`: byte-exact edits against the tree at the item A commit (asserts every anchor matches once;
  server.py and assistant_capabilities.py are CRLF, static/app.js is mixed and edited at the byte level, the rest
  LF). Item D: `wearables.service._location`, `start.location` to `run.location`, `device_location` in the model's
  context, `maps.directions(location=)`, the showable sentence "Invalid location." Item C: `Controls.DEVICE_TIMEOUT`,
  `Controls.for_window`, `result.attachment` accepted by `acknowledge`, `GET /api/control-requests`,
  `App.device_control_result` and `App.describe_picture`, and the window's three-second poll that captures, uploads
  and answers (`static/app.js`). Run from the repo root with `.venv\Scripts\python.exe docs\phone-access-work\edit_items_cd.py`.
- `tests_cd.py`: `LocationTests` and `ScreenTests`, to be appended to `test_phone_access.py`; that file then also
  needs `import base64` and `import assistant_capabilities` at the top.
- `docs_cd.py`: sections 2 and 3 for `docs/PHONE-ACCESS-1.0.17.md`, appended once the tests pass.

The design each script follows is in `docs/PHONE-ACCESS-PLAN.md` (items C and D) and `docs/MAC-REQUESTS-20261007.md`
(`start.location`; R7). If an anchor no longer matches, the script stops before writing anything: read the file and
adjust the anchor, never force it.
