param([switch]$LoginLaunch)
$ErrorActionPreference = 'Stop'
$desktopRoot = Join-Path $PSScriptRoot 'desktop'
$desktopExe = Join-Path $desktopRoot 'node_modules/electron/dist/electron.exe'
if (!(Test-Path -LiteralPath $desktopExe)) { throw 'Electron is not installed. See desktop/README.md.' }
$previousElectronMode = $env:ELECTRON_RUN_AS_NODE
try {
    Remove-Item Env:ELECTRON_RUN_AS_NODE -ErrorAction SilentlyContinue
    $arguments = @('"' + $desktopRoot + '"')
    if ($LoginLaunch) { $arguments += '--login-launch' }
    Start-Process -FilePath $desktopExe -ArgumentList $arguments -WorkingDirectory $desktopRoot -WindowStyle Hidden
} finally {
    if ($null -ne $previousElectronMode) { $env:ELECTRON_RUN_AS_NODE = $previousElectronMode }
}
