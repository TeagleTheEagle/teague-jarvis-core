# Teague Industries desktop release audit

Date: 11 September 2026

Status: audit complete; installer preparation blocked by Core ownership and data-location requirements. No installer built or installed. Existing application, launcher, shortcut, security and data unchanged by this audit.

## Verified source findings

- desktop/package.json identifies the Electron application as jarvis-desktop 0.1.0 with Electron 44.2.0. It contains start/test scripts but no installer configuration.
- desktop/main.cjs requests an Electron single-instance lock and unconditionally calls startBackend from its parent source directory. It does not attach to an independently running canonical Core. A lock within the current application does not establish mutual exclusion across differently packaged application identities.
- desktop/backend.cjs spawns the source .venv/Scripts/python.exe with server.py and an ephemeral localhost port. It generates the existing desktop authentication token, owns the child lifecycle and shuts its child down on quit. This source-relative runtime cannot simply be relocated into an installer.
- server.py defaults source data to ROOT/data. Frozen execution may instead use APP_ROOT/data. Copying or freezing the current backend can therefore change the canonical database location. No migration was attempted.
- desktop/main.cjs writes preferences and the transient authentication session beside its source. A release needs explicit writable application-state locations without copying credentials or overwriting existing preferences.
- Build-JARVIS.ps1 targets the older desktop_launcher.py PyInstaller application, not this Electron application. It is not a suitable unchanged installer pipeline for the current desktop.
- desktop/local-updates.cjs provides local source-change detection and user-triggered reload/restart. It is not an installed-release distribution or signature-verification mechanism.

These are source-inspection findings. No claim is made that two production Cores are currently running. The conflict is the risk of duplicating ownership if the existing application is packaged and launched alongside the source application unchanged.

## Required release gate

Before a runnable installed release, review a single canonical Core ownership/attachment design that covers source and installed launchers together. Specify the authoritative data/configuration location, authentication, start/attach behavior, concurrent-launch exclusion, shutdown ownership and recovery after crashes. Preserve the existing Core instead of creating a replacement assistant. Respect the earlier requirement for architecture review before independent Core-service or production Gateway changes.

Then build the matching release runtime with an explicit source manifest, version and branded icon; test installation, relaunch, upgrade/rollback and preservation of memory/preferences using isolated test data. Never bundle production .env files, databases, transient tokens or caches. Keep the working shortcut until installed-runtime verification passes. No signing certificate, purchases, update servers or administrative installation has been authorized by this audit.

## User-reported manual test

The user reported that keyboard tests all worked without issues in the maximized TEAGUE INDUSTRIES desktop application:

- Tab forward navigation and visible focus.
- Shift+Tab backward navigation.
- Ctrl+K opens the command interface.
- Escape dismisses it.

Result: PASS, user-reported manual verification. Exact application binary version and pixel dimensions were not independently captured. This does not establish narrow-window, zoom, measured contrast, complete accessibility, or packaged-build acceptance.

## Checks in this audit

Read-only inspection of the named source files and existing desktop test definitions. No runtime restart, microphone activation, capture, live provider call or database mutation. No code changed, so regression suites were not rerun for this documentation-only audit. Earlier test totals are not claimed as fresh results.
