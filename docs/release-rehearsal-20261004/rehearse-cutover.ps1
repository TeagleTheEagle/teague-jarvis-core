# Rehearsal of tools\host\Invoke-Cutover.ps1 in a sandbox on D: (2026-10-04). Nothing here touches the real
# install location, the real Desktop or Startup folders, or the everyday JARVIS: every location is a sandbox
# folder, the "old JARVIS" is the repo-baseline copy with a made-up database from the Gate 18 old-format
# rehearsal, and the backup is the made-up backup made there. Run by Claude, owner account, non-elevated.
param([string] $Base = 'D:\JARVIS-release-work\cutover-rehearsal', [string] $Phase = 'all')
$ErrorActionPreference = 'Stop'
$script = 'C:\Users\jonny\JARVIS-claude-workspace\repo\tools\host\Invoke-Cutover.ps1'
$old = 'D:\JARVIS-release-work\gate18-oldbackup-rehearsal\outputs\jarvis'
$backup = 'D:\JARVIS-release-work\gate18-oldbackup-rehearsal\outputs\jarvis-backups\17ec0239aa51408b9acce37f8d07b35b.zip'
$root = Join-Path $Base 'root'; $installHome = Join-Path $Base 'home'; $desktop = Join-Path $Base 'fake-desktop'; $startup = Join-Path $Base 'fake-startup'
$auth = Join-Path $Base 'cutover-authorized.json'
$common = @('-Root', $root, '-InstallHome', $installHome, '-Old', $old, '-Backup', $backup, '-Authorized', $auth, '-DesktopDir', $desktop, '-StartupDir', $startup, '-NoShortcuts')
$backupHash = (Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash.ToLower()
function Step([string[]] $extra) {
    if ($extra -notcontains '-BackupSha256') { $extra = @($extra) + @('-BackupSha256', $backupHash) }
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $script @common @extra | Out-String
    $last = ($out.Trim() -split "`r?`n" | Where-Object { $_ -match 'STOPPED|PASSED|Waiting|complete|installed and has|test mode' } | Select-Object -Last 1)
    "exit=$LASTEXITCODE  $last"
}
if ($Phase -in 'all', 'setup') {
    if (Test-Path -LiteralPath $auth) { throw "$auth exists" }
    New-Item -ItemType Directory -Path $Base, $desktop, $startup -Force | Out-Null
    'case: not authorised            ' + (Step @())
    [IO.File]::WriteAllText($auth, '{"rehearsal":true}')
    $shell = New-Object -ComObject WScript.Shell
    foreach ($pair in @(@($desktop, 'JARVIS Desktop.lnk'), @($desktop, 'JARVIS INDUSTRIES.lnk'), @($startup, 'JARVIS Desktop.lnk'))) {
        $l = $shell.CreateShortcut((Join-Path $pair[0] $pair[1])); $l.TargetPath = "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe"
        $l.Arguments = '-NoProfile -File "' + (Join-Path $old 'Start-Desktop.ps1') + '"'; $l.Save()
    }
    'case: wrong backup hash         ' + (Step @('-BackupSha256', ('0' * 64)))
}
if ($Phase -in 'all', 'run') {
    'step 1 check                    ' + (Step @())
    'step 2 install                  ' + (Step @())
    'step 3 dry run                  ' + (Step @())
    'step 4 without approval         ' + (Step @())
    [IO.File]::WriteAllText((Join-Path $root 'evidence\import-approved.json'), '{"rehearsal":true}')
    'step 4 import                   ' + (Step @())
    'step 5 without approval         ' + (Step @())
    [IO.File]::WriteAllText((Join-Path $root 'evidence\retire-approved.json'), '{"rehearsal":true}')
    'step 5 retire                   ' + (Step @())
    'after completion                ' + (Step @())
    'fake desktop now: ' + ((Get-ChildItem $desktop | ForEach-Object { $_.Name }) -join ', ')
    'old-shortcuts: ' + ((Get-ChildItem (Join-Path $root 'old-shortcuts') -Recurse -File | ForEach-Object { $_.FullName.Substring($root.Length) }) -join ', ')
}
