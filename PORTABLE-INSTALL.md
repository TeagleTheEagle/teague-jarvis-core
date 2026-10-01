# Portable Windows build

Run `Build-JARVIS.ps1` from PowerShell. It creates `release/JARVIS-Windows-Portable.zip`.

Extract the ZIP, copy `.env.example` to `.env`, add your provider keys locally, and launch `JARVIS.exe`. The build includes the Python runtime, HUD, backend, and local wake-word models. Your credentials and personal database are excluded from the archive.

The first build downloads PyInstaller and packages the wake-word runtime. The resulting ZIP does not require Python to be installed.
