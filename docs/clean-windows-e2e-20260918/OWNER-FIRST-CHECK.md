# Disposable clone first check

Use only JARVIS-E2E-DISPOSABLE-20260918. Do not restore or boot the protected original for this validation.
Open Windows PowerShell as the ordinary guest user. Run this read-only block and return its output (no passwords/keys):

```powershell
Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber
Get-ExecutionPolicy -List
Get-Command py,python,node -ErrorAction SilentlyContinue | Select-Object Name,Source
Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64' -ErrorAction SilentlyContinue | Select-Object Installed,Version
Test-Path "$env:USERPROFILE\JARVIS-E2E"
Test-Path '\\VBOXSVR\JARVIS-E2E-PREFLIGHT'
```

A missing Python command means the Python checker cannot run yet, not PASS.
The documented setup requires manual official Python 3.12 x64, Node 24.x and VC++ x64 installers before the PS script. Do not install them until initial state is recorded. Do not change execution policy. If the documented direct PS invocation is blocked, preserve the error and STOP.

The read-only shared folder contains five explicitly selected setup/requirements files only, no .env, data, credentials, old venv or package caches. It is a prerequisite probe bundle, not the complete application installation.
