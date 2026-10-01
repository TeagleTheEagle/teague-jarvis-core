# Updates from the local project

The desktop shortcut runs this project directly. No reinstall is needed for edits to these application files.

The desktop process checks application source hashes every two seconds. After files remain unchanged for twenty seconds, it announces an available update. Static interface changes can reload automatically after fifteen seconds without interaction. Backend and desktop code changes require the Restart to update button, which uses the existing graceful shutdown and Electron relaunch flow.

Reloads wait while the microphone is enabled, a request or screen capture is active, media is playing, a dialog/report is open, an attachment is selected, or an edited field/draft remains. Changed form fields are treated conservatively: restoring their original values releases the guard; saving a field may still require quitting and reopening manually. The update banner explains how to proceed. Saved application data stays in the existing database. No images, audio or credentials are sent by update detection.

Only files in this project's top-level Python source, static directory and desktop runtime are checked. Dependencies still require installation; this is not a download service, package manager or guarantee that new code passes tests. Changes in another checkout do not update this installation. The browser version has no desktop update controls.

Rollback: remove the local-updates watcher and update IPC handlers from main.cjs, remove the three update bridge methods from preload.cjs, and remove the desktop-updates.js script tag and server route. Quit from the tray and reopen the shortcut. The new standalone watcher, UI script and tests can then be removed without affecting saved data.
