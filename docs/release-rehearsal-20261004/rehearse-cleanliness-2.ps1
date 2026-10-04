# Second Cleanliness rehearsal: the install and package folders sit under the (fake) LOCALAPPDATA exactly as on the
# VM, each holding a planted .env file that must NOT be reported, plus one stray .env file and one stray JARVIS
# folder that MUST be reported. Dummy folders only; nothing real is read from the owner's profile.
$ErrorActionPreference = 'Stop'
$fake = 'D:\JARVIS-release-work\gate19-local\cleanliness-test-2'
foreach ($d in 'AppData\Local\Microsoft\WindowsApps', 'AppData\Local\Temp', 'AppData\Local\JARVIS\releases\x\app', 'AppData\Local\JARVIS-package\release\app', 'AppData\Local\JARVIS-stray', 'AppData\Roaming', 'Documents', 'ProgramFiles', 'ProgramFilesX86', 'evidence') { New-Item -ItemType Directory -Path (Join-Path $fake $d) -Force | Out-Null }
'x' | Set-Content -LiteralPath (Join-Path $fake 'AppData\Local\JARVIS\releases\x\app\.env.example')
'x' | Set-Content -LiteralPath (Join-Path $fake 'AppData\Local\JARVIS-package\release\app\.env.example')
'x' | Set-Content -LiteralPath (Join-Path $fake 'Documents\.env')
$env:USERPROFILE = $fake
$env:LOCALAPPDATA = Join-Path $fake 'AppData\Local'
$env:APPDATA = Join-Path $fake 'AppData\Roaming'
$env:ProgramFiles = Join-Path $fake 'ProgramFiles'
${env:ProgramFiles(x86)} = Join-Path $fake 'ProgramFilesX86'
$env:USERNAME = 'jarvis-s6-guest'
$env:COMPUTERNAME = 'JARVIS-S6-FRESH'
$env:PATH = 'C:\WINDOWS\system32;C:\WINDOWS;C:\WINDOWS\System32\Wbem;C:\WINDOWS\System32\WindowsPowerShell\v1.0\;C:\WINDOWS\System32\OpenSSH\;' + (Join-Path $env:LOCALAPPDATA 'Microsoft\WindowsApps') + ';'
function global:cmdkey { 'Currently stored credentials:'; ''; '* NONE *' }
# Default -InstallHome and -Staging, as on the VM: %LOCALAPPDATA%\JARVIS and %LOCALAPPDATA%\JARVIS-package.
& 'C:\Users\jonny\JARVIS-claude-workspace\repo\tools\guest\Invoke-Gate17.ps1' -Phase Cleanliness -Package 'D:\JARVIS-release-work\pkg-1.0.11' -Evidence (Join-Path $fake 'evidence') -NoShortcuts
