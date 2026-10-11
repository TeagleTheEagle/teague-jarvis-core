# Relocated TEST blank-window diagnostic — 16 September 2026

**Disposition: visible rendering FAIL; exact blank-pixel root cause UNCONFIRMED. A packaged-bootstrap initialization-order/profile discrepancy is established and is the strongest lead. No correction implemented.**

This report concerns the unchanged package below. Reopening the same ordinary TEST clients on the already-running TEST Core was explicitly authorized. No Core was started or restarted during this diagnosis.

## Exact package and entries

Relocated installation: `C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/deployment-test-releases/TEST-INSTALL-cd2c369ef5c94bc5bd23c20164e0cd70`

Release root R: `C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/deployment-test-releases/TEST-INSTALL-cd2c369ef5c94bc5bd23c20164e0cd70/releases/e2f97627586d4127a7952e1d845a076a`

Original build: `C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\deployment-test-releases\TEST-PACKAGE-8b61892cb3a44bca8035a6412b4892c7`

This is the most recent completed relocated validation used for the demonstration: [347-check installed evidence](../installed-2c6c91097ba9456f80c144eb0d5c2323.json). Later incomplete/failed builds were not substituted. Its manifest SHA-256 is `0a50be9481eb16cb88e59bc4b7492f33a46e42c74dd7ffc2c92a3ff749db9ceb`. All **796** manifest files matched at initial inspection and final reconciliation. All **74** files in the source Electron distribution also exist unchanged in this release; there were no missing or differing distribution files.

All paths in this table are relative to the fully qualified R above.

| Component | Exact path |
|---|---|
| Packaged owner/bootstrap interface | `app/deployment_test/bootstrap.py` |
| Node launcher executable / script | `node/node.exe` / `app/client-launcher.cjs` |
| Electron executable | `electron/electron.exe` — **44.2.0** |
| Electron main entry | `app/deployment-entry.cjs`, loading `app/stage4_client.cjs` |
| TEST Core executable | `python/python.exe` |
| TEST Core command | `python/python.exe -I -S -B app/deployment_test/bootstrap.py --core <installation>/binding.dpapi` (actual executable, script and descriptor arguments are absolute) |
| Teague HTML | `app/static/index.html` |
| Intelligence HTML | `app/intelligence/index.html` |
| Both preloads | `app/desktop/preload.cjs` |
| Both TEST renderer adapters | `app/intelligence/stage4-renderer.js` |
| CSS / branding | `app/static/{style,gallery,pro,teague}.css`, `app/intelligence/style.css`, `app/static/assets/branding/teague/` |

No React/Vue mount, dist bundle, dynamic chunks, app.asar or unpacked-ASAR directory is required by these TEST entries. Required HTML, adapter, preload, CSS, branding, manifest and deployment binding **EXIST**. [Inventory and exact asset hashes](inventory.json).

## Main JARVIS window

- BrowserWindow: **PASS**; visible content: **FAIL**. The user reported black originally; the foreground window capture during diagnosis was white.
- Exact load: `win.loadURL('stage4-test://app/index.html')`.
- Resolved HTML: `C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/deployment-test-releases/TEST-INSTALL-cd2c369ef5c94bc5bd23c20164e0cd70/releases/e2f97627586d4127a7952e1d845a076a/app/static/index.html`.
- HTML / preload / TEST renderer adapter: **EXISTS**; executed sufficiently to return ready=true, connection=attached, status=STAGE4_TEST / AUTHENTICATED.
- Expected contextBridge API: all seven fixed methods present. Node require remains undefined in renderer.
- TEST Core reachable: **PASS**, authenticated read-only shared roundtrip returned the expected canonical TEST data identity.
- First meaningful recorded failure: **TimeoutError: Electron capture** in the existing driver's receive operation. This is a diagnostic screenshot timeout, not a captured renderer-load exception.
- Cleanup of that timed-out probe later produced `TypeError: Object has been destroyed` at packaged stage4_client.cjs:386 and launcher `EPIPE`. These followed the capture timeout and close sequence; they do not establish the initial blank-window cause.
- Classification: **F — initialized and authenticated document, but no visible application frame; capture/presentation failure remains unresolved.** No evidence supports claiming HTML never loaded or IPC failed.
- [Foreground screenshot](teague-window.jpg), [accessibility observation](teague-accessibility.txt), [preserved failed capture](blank-ui-live-51a353b03081441d99e28e3082254d27.json).

## JARVIS Intelligence window

- BrowserWindow: **PASS**; visible content: **FAIL**, white foreground interior.
- Exact load: `win.loadURL('stage4-test://app/intelligence.html')`.
- Resolved HTML: `C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/deployment-test-releases/TEST-INSTALL-cd2c369ef5c94bc5bd23c20164e0cd70/releases/e2f97627586d4127a7952e1d845a076a/app/intelligence/index.html`.
- HTML / preload / TEST renderer adapter: **EXISTS** and initialization confirmed by live DOM.
- Accessibility exposed the real header, authenticated status, composer, TEST controls, and explicit unavailable physical voice text while the captured pixels remained white.
- TEST Core reachable: **PASS**, authenticated read-only shared roundtrip returned the same canonical TEST data identity as Teague.
- First renderer exception: **NOT CAPTURED**. No load/preload/Core failure was recorded. The earlier capture command timed out on Teague before an Intelligence capture command was sent.
- Classification: **F — document, TEST adapter and Core attachment active, but visible painting/presentation missing.** This is stronger than a missing-file hypothesis and does not prove a GPU crash.
- [Foreground screenshot](intelligence-window.jpg), [accessibility observation](intelligence-accessibility.txt), [live authentication/shared/DOM evidence](blank-ui-inspection-fd14137af6d648ab94db09e322604d64.json).

## Protocol, resources and relocation

The secure `stage4-test` scheme is served by the Electron main process through a session-specific, GET-only local allowlist. It is not a localhost HTTP server or Core-served webpage. The Core is reached through authenticated main-process IPC, not renderer HTTP.

Files resolve against packaged `__dirname = R/app`; the packaged launcher explicitly uses cwd=R. The renderer process command lines also show `--app-path=R/app`. No stale old-root/source-tree path was found in the active deployment branch. Source-relative test/native defaults are bypassed by validated deployment bindings. There is no active import.meta.url/dist/public/ASAR dependency in this path. app.getAppPath/resourcesPath were not separately queried live; the active loader does not use them.

- Stale absolute renderer path: **NO detected**.
- Missing required TEST packaged resource: **NO detected**.
- Required working-directory mismatch: **NO detected**.
- Legacy references unavailable in this TEST surface: **YES**. Teague HTML still requests 13 excluded production scripts (voice.js, latency.js, voice-core.js, assistant-controls.js, diagrams.js, workspaces.js, voice-preview.js, maps.js, reliability.js, recovery.js, inspection-client.js, desktop-updates.js, teague.js). The TEST allowlist rejects these; /app.js intentionally resolves to the TEST adapter. An old CSS /api/files background URL is also unsupported. Intelligence contains a legacy inline script incompatible with the strict script CSP. These are static findings, not captured first-error console entries, and do not explain both blank windows by themselves.

The existing package has no general console/devtools diagnostic driver. The existing Ctrl+Shift+I shortcut attempt did not open DevTools; the window menu is removed. No debug port, permissive CSP or new instrumentation was added. Existing logs lacked did-fail-load, preload or initial renderer exceptions; render-process-gone is handled without preserving its reason. A bounded Windows Application 1000/1001 query returned NoMatchingEventsFound, which is not proof that no underlying rendering problem occurred.

## Confirmed startup discrepancy and causal limits

The source TEST entry calls launchTestClient synchronously. The generated packaged entry instead waits in `process.once('message', cfg => ...)` before calling it. Only inside launchTestClient are the TEST profile paths, existing hardware-acceleration setting and privileged scheme configured.

Read-only process evidence from the second diagnostic reopening:

| Client | Main PID | GPU PID / created (local UTC+10) | GPU --user-data-dir | Renderer PID / profile |
|---|---:|---|---|---|
| Intelligence | 19600 | 1116 / 10:58:34.273750 | C:/Users/jonny/AppData/Roaming/Electron | 18388 / installation client-state/intelligence-f214e723-2265-4584-9e90-f5bbb113c48c |
| Teague | 24256 | 10996 / 10:58:37.409609 | C:/Users/jonny/AppData/Roaming/Electron | 18224 / installation client-state/teague-9cb2c8e3-99ed-4e6e-a276-6f11e533dc42 |

The Intelligence TEST profile directory was created at 10:58:34.2762323, **after** its GPU child creation timestamp. The Teague TEST profile was created at 10:58:37.4093589. Both GPU children had the generic profile argument; both renderer/NetworkService children had the later isolated profile. Renderer command lines included enable-sandbox and disable-gpu-compositing; a live GPU child still existed. Do not interpret that alone as a GPU crash.

Electron documents hardware-acceleration setup and privileged-scheme registration as pre-ready operations: [app contract](https://www.electronjs.org/docs/latest/api/app#appdisablehardwareacceleration), [protocol contract](https://www.electronjs.org/docs/latest/api/protocol#protocolregisterschemesasprivilegedcustomschemes).

**Established:** packaged initialization is deferred to asynchronous configuration, and actual GPU startup uses a different, generic profile. This is a TEST profile-isolation/startup-order finding.

**Leading inference:** late application of startup/rendering settings may leave GPU and renderer initialization inconsistent and contribute to the missing visible frame.

**Not established:** exact app-ready timing, first Chromium/GPU error, actual files accessed under the generic profile, an exact DLL fault, CSS/compositor internal state, or whether correcting initialization order resolves the blank frame. No renderer crash or missing Electron DLL was proven. No historical PermissionError or older Windows crash is reclassified.

## TEST Core, cleanup and preserved failures

Same existing Core throughout: PID **3864**, creation FILETIME **134339923015127134**, epoch **8d8cf17e382d49baa9aab79ba5f4de0f**, data **TEST-a1e600090b85437f9c91c1ee83744b11**. Named pipe: `\\.\pipe\TEAGUE-TEST-df1b4562410a4469a22b16f5784e7820`; no HTTP rendering port.

Python executable SHA-256: `372c2eae555b344520bf147be0096e009069aeca4e7f78d6aecea6d53158056a`.
Electron executable SHA-256: `07b043bf9b0a0ac14a82fac0b612b7b7ed13cde727d706d74e41a45278ab51f1`.

Package-filtered process snapshots showed one TEST Core, not an exhaustive audit of unrelated processes or historical ownership. Both clients' read-only shared requests succeeded; no chat/provider/media request was sent. Fresh diagnostic clients 19600/24256 closed through their existing control path with exit 0. Final process inventory contained only the original Core; no diagnostic Electron or Node launcher remained.

Preserved, not erased:
1. First capture timeout and its cleanup/destruction/EPIPE errors.
2. A subsequent diagnostic preflight incorrectly assumed a running restarted Core could not retain a durable stop file. It stopped before launching clients; identity was unchanged. That diagnostic-only assertion was removed after reading the existing restart semantics. The failed record is retained as blank-ui-inspection-ae4cd75eb4bb488aa1f1dd94f479dc60.json.
3. An evidence-export attempt assumed PNG; it stopped before writing an image. The original screenshots were then saved as returned JPEG bytes without editing.
4. Later successful authentication/normal cleanup does not erase the blank pixels or initial capture failure.

## Proposed minimum correction — NOT IMPLEMENTED

Review a narrow packaged-bootstrap initialization-order change: establish the validated nonsecret TEST client identity/path and existing profile/rendering/scheme settings synchronously before Electron readiness or child initialization; retain authenticated Core attachment and BrowserWindow creation behind the current verification boundary. Do not pass credentials in argv, weaken authentication, or add speculative GPU flags.

Likely source scope: deployment_test/package.py (generated deployment-entry.cjs/client-launcher.cjs templates), and only if required a narrow separation of early initialization from authenticated attachment in stage4_client.cjs. No HTML/CSS rewrite, provider change, Core lifecycle change or cache deletion is supported by present evidence. Add bounded, nonsecret first-failure/ready/profile observations to a reviewed TEST diagnostic surface if needed to test this lead.

The candidate must then prove both actual windows visibly paint, the existing capture command completes, all Electron children use the intended TEST profile, both clients attach to one Core, and normal close/detach leaves the Core unchanged. Repeat independently and together; validate renderer/IPC boundaries and package integrity. This is a proposed controlled validation, not a claim that a fix has passed.

Risk: no production change is intended; TEST profile isolation should improve. Any implementation changes package hashes and requires a new reviewed TEST package/integrity/enrollment validation. Stage 4 authentication, ownership and lifecycle controls must remain intact. Generic-profile command-line use is disclosed; no claim is made that this diagnostic proved absence of all generic-profile cache access.

Rollback: retain this immutable 796-file release and evidence, build any separately approved candidate as a new TEST release, and use the existing authorized TEST deployment/rollback process. Never patch the validated release in place.

Code/configuration/build/installation changes during diagnosis: **NONE**. Evidence and ordinary TEST runtime session/profile/log artifacts were created by the authorized diagnostic launches. Production Core/data/enrollment and paid providers were not used. No acceptance commit or later stage was begun.

**STOP FOR REVIEW.**

