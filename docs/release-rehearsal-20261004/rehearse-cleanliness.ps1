# Rehearsal of the Cleanliness phase of tools\guest\Invoke-Gate17.ps1 on the host WITHOUT touching the owner's
# profile or credential store: the profile, AppData and Program Files variables point into a sandbox on D:, the
# account and computer names are the VM's, PATH is the Windows default, and cmdkey is replaced by a stub.
# Expected result here: FAIL, naming only the planted items (.env files outside the install, a stray JARVIS folder)
# and whatever is real on this PC (for example OneDrive signed in); never JARVIS's own install or package folder.
$ErrorActionPreference = 'Stop'
$base = 'D:\JARVIS-release-work\gate19-local'
$fake = Join-Path $base 'cleanliness-test'
foreach ($d in 'AppData\Local\Microsoft\WindowsApps', 'AppData\Local\Temp', 'AppData\Local\JARVIS-stray', 'AppData\Roaming', 'ProgramFiles', 'ProgramFilesX86', 'evidence') { New-Item -ItemType Directory -Path (Join-Path $fake $d) -Force | Out-Null }
$env:USERPROFILE = $base
$env:LOCALAPPDATA = Join-Path $fake 'AppData\Local'
$env:APPDATA = Join-Path $fake 'AppData\Roaming'
$env:ProgramFiles = Join-Path $fake 'ProgramFiles'
${env:ProgramFiles(x86)} = Join-Path $fake 'ProgramFilesX86'
$env:USERNAME = 'jarvis-s6-guest'
$env:COMPUTERNAME = 'JARVIS-S6-FRESH'
$env:PATH = 'C:\WINDOWS\system32;C:\WINDOWS;C:\WINDOWS\System32\Wbem;C:\WINDOWS\System32\WindowsPowerShell\v1.0\;C:\WINDOWS\System32\OpenSSH\;' + (Join-Path $env:LOCALAPPDATA 'Microsoft\WindowsApps') + ';'
function global:cmdkey { 'Currently stored credentials:'; ''; '* NONE *' }
& 'C:\Users\jonny\JARVIS-claude-workspace\repo\tools\guest\Invoke-Gate17.ps1' -Phase Cleanliness -Package 'D:\JARVIS-release-work\pkg-1.0.11' -Evidence (Join-Path $fake 'evidence') -InstallHome (Join-Path $base 'home') -Staging (Join-Path $base 'staging') -NoShortcuts
