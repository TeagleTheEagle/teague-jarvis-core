# Pre-build review

Runtime source changed: deployment_test/package.py — only ELECTRON_ENTRY and NODE_LAUNCHER templates. Added tests/deployment_contract/test_electron_startup.cjs (8 focused checks passed). The actual Core/client/renderer/preload implementation is unchanged.

Before: fork Electron → asynchronously receive configuration → launchTestClient → apply TEST paths/rendering/scheme settings → authenticate → create window.
After: launcher receives configuration → fork Electron with bounded nonsecret clientId/deployment metadata → synchronous launchTestClient sets existing TEST paths/rendering/scheme settings → private IPC delivers original full configuration → existing identity/authentication validation → window.

No new rendering flags. Private credentials never enter argv, environment, reports or screenshots. Existing deployment-root/manifest/native identity validation still precedes profile creation; client/session/Core authentication still precedes BrowserWindow creation. TEST profile policy is unchanged; its timing moves earlier. Production and Stage 4 lifecycle authority are unchanged.

The previous retained Core was identity-verified and shut down normally by its retained authenticated controller (visible-test-session-4cea89950d7d4ccf94513841834f66de.json). No blind process termination.

Controlled candidate: use the previously validated immutable release as the source baseline, replace only the two packaging templates, and use that baseline's established packaging function with the same Electron/Python/Node/native inputs. Exclude unrelated pending working-tree/native-upgrade changes. A new build UUID/manifest identifies the candidate; no Electron version/resource upgrade. Compare all candidate payload hashes against the baseline before execution. Preserve the old release and all failed evidence.

A build alone is not acceptance. Actual visible pixels, authenticated roundtrips, child profiles, live renderer, cleanup and directly affected regressions are required. If blank pixels remain, stop without another speculative correction.

