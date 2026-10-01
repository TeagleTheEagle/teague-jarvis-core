# Task-page layout update

The previous companion used sticky positioning and could switch to a fixed
overlay. Task pages now reserve a companion row above their own scrollable
content. The Command dashboard retains its large hologram and existing dock.

Changed `static/pro.css` for the reserved layout, larger navigation/helper text,
and aligned checkbox labels. Changed `static/app.js` to skip fixed docking on
task pages. No provider, microphone, permission, or saved-data behavior changed.

Validation: `review/test_task_layout.py` passed using the real frontend with
synthetic state and intercepted network requests. It checks all 12 task pages at
1920x1080, 1366x768, 1024x768 and 390x844 for companion/content separation,
scroll reachability, document horizontal overflow, draft preservation and one
shared hologram. Desktop and narrow Settings screenshots were visually reviewed.
All 11 `review/test_inspection_runtime.py --browser` checks passed, including
all-panel rendering, bounded long captures and state preservation.
`node --check static/app.js` passed.

These are isolated browser checks, not native Electron, microphone or cloud
provider validation. Broader findings from the inspection remain separate work.
The running desktop instance must load the interface update before using it.
Rollback consists of reverting the final task-layout CSS block and the
jarvisCompanion early-return in updateCompanionScroll; no data migration exists.
