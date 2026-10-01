# JARVIS Intelligence prototype

This is a separate visual shell for the JARVIS Intelligence product direction. It is intentionally prototype-only: it does not start a second JARVIS, create a second memory store, or make AI/provider requests. The existing Teague Industries Command Center remains the functional application and shared-Core host.

Run from the repository with the existing Electron runtime:

```powershell
desktop\node_modules\electron\dist\electron.exe intelligence
```

The command layout is based on the supplied Teague Industries/JARVIS Intelligence reference. Live, historical and prototype surfaces are labelled in the UI. Shared Core wiring is a later gated milestone.
