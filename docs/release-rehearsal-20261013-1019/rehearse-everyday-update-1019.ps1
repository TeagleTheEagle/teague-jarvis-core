# Rehearsal of tools\host\update-1.0.19\Invoke-EverydayUpdate.ps1 (version 3: 1.0.17 to 1.0.19, the OpenRouter release)
# in a sandbox on D:, mirroring the owner's PC: 1.0.17 is installed into a sandbox home BY ITS OWN SETUP with the
# sandbox switches (/DIR, /HOME, /NOSHORTCUTS: the entry "JARVIS (sandbox)" 1.0.17 under the sandbox id, which both
# Setups share, and the package folder with its uninstaller, as %LOCALAPPDATA%\JARVIS-package is on the owner's PC) and
# started once so it has a database. Then the launcher runs with a test approval: refusals (no approval; JARVIS
# running; a key file 1.0.19 would refuse, planted as JARVIS_PROVIDER=qwen with no OpenRouter key), check (the key file
# rewritten for OpenRouter with a fake key: accepted, its names recorded, a copy made; 1.0.17's package folder moved
# aside), backup, update through 1.0.19's Setup (the entry now 1.0.19, the new uninstaller), 1.0.19 started on the same
# data through its own JARVIS.exe, a rerun that changes nothing, rollback (only with its approval file; the key file
# put back from the copy, the file as it stood kept beside it), 1.0.17 running again, a final rerun, and the sandbox
# uninstalled through its own entry. The owner's real Desktop and Startup shortcuts are hashed before, after every step
# and at the end and must not change; the owner's installed JARVIS (%LOCALAPPDATA%\JARVIS) is never addressed, and the
# number of its processes is recorded before and after. The owner's real Installed-apps entry (JARVIS 1.0.17) is
# recorded at the start and must be the same at the end, and the cleanup (the sandbox JARVIS ended, the sandbox
# uninstalled through its own entry) runs whatever happened above, a thrown stop included.
param(
    [string] $Base = 'D:\JARVIS-release-work\update-rehearsal-1.0.19-3',
    [string] $PreviousSetup = 'D:\JARVIS-release-work\pkg-1.0.17\JARVIS-Setup-1.0.17-0d38218c4e1d.exe',
    [string] $PreviousId = '1.0.17-0d38218c4e1d',
    [string] $FinalZip = 'D:\JARVIS-release-work\pkg-1.0.19\JARVIS-1.0.19-629bb5621d34.zip',
    [string] $FinalSetup = 'D:\JARVIS-release-work\pkg-1.0.19\JARVIS-Setup-1.0.19-629bb5621d34.exe',
    [string] $FinalId = '1.0.19-629bb5621d34',
    [string] $Launcher = ''
)
$ErrorActionPreference = 'Stop'
# Set here, not as the parameter default: PowerShell 5.1 can leave $PSScriptRoot empty in a parameter default.
if (-not $Launcher) { $Launcher = Join-Path $PSScriptRoot '..\..\tools\host\update-1.0.19\Invoke-EverydayUpdate.ps1' }
if (Test-Path -LiteralPath $Base) { throw "$Base exists" }
$sandboxHome = Join-Path $Base 'home'; $root = Join-Path $Base 'update'; $auth = Join-Path $Base 'update-authorized.json'; $staging = Join-Path $Base 'staging'
$setupRecord = Get-Content -LiteralPath ($FinalSetup -replace '\.exe$', '.setup.json') -Raw | ConvertFrom-Json
$previousRecord = Get-Content -LiteralPath ($PreviousSetup -replace '\.exe$', '.setup.json') -Raw | ConvertFrom-Json
if (-not $setupRecord.sandbox_app_id) { throw 'the Setup record names no sandbox_app_id. STOP' }
if ($previousRecord.sandbox_app_id -ne $setupRecord.sandbox_app_id -or $previousRecord.app_id -ne $setupRecord.app_id) { throw 'the two Setups do not share their application ids. STOP' }
$key = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\' + $setupRecord.sandbox_app_id + '_is1'
$realKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\' + $setupRecord.app_id + '_is1'
if (Test-Path -LiteralPath $key) { throw 'a sandbox entry exists already. STOP' }
New-Item -ItemType Directory -Path $Base | Out-Null
$log = Join-Path $Base 'rehearsal.output.txt'
$results = New-Object Collections.ArrayList
$switches = '/DIR=' + $staging + ';/HOME=' + $sandboxHome + ';/NOSHORTCUTS'
function Note($text) { Add-Content -LiteralPath $log -Value $text; Write-Host $text }
function LiveCount { @(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -like "$env:LOCALAPPDATA\JARVIS\releases\*" }).Count }
function SandboxProcesses { @(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -and $_.ExecutablePath.StartsWith("$sandboxHome\releases\", [StringComparison]::OrdinalIgnoreCase) }) }
function RealShortcuts {
    $r = [ordered]@{}
    foreach ($pair in @(@('desktop', [Environment]::GetFolderPath('Desktop')), @('startup', [Environment]::GetFolderPath('Startup')))) {
        $p = Join-Path $pair[1] 'JARVIS.lnk'
        $r[$pair[0]] = $(if (Test-Path -LiteralPath $p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower() } else { 'ABSENT' })
    }
    $r
}
$shortcutsBefore = RealShortcuts
function ShortcutsUnchanged { $now = RealShortcuts; ($now.desktop -eq $shortcutsBefore.desktop) -and ($now.startup -eq $shortcutsBefore.startup) }
function Check($name, [bool] $ok, $detail) { $results.Add([ordered]@{ check = $name; passed = $ok; detail = $detail }) | Out-Null; Note ("{0}  {1}  {2}" -f $(if ($ok) { 'PASS' } else { 'FAIL' }), $name, $detail) }
function Step([string] $title, [string] $authorizedFile) {
    # 'Continue': a line on the launcher's error output must be recorded, not end this harness.
    $ErrorActionPreference = 'Continue'
    Note "===== $title  $(Get-Date -Format 'HH:mm:ss')"
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $Launcher -Root $root -InstallHome $sandboxHome -Staging $staging -SetupSwitches $switches -Authorized $authorizedFile 2>&1 | Out-String
    $code = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    Note $out.Trim(); Note "exit=$code"
    if (-not (ShortcutsUnchanged)) { Note 'STOPPED: the real shortcuts changed'; throw 'the real shortcuts changed. STOP' }
    [pscustomobject]@{ exit = $code; text = $out }
}
function Records { if (Test-Path -LiteralPath (Join-Path $root 'evidence')) { @(Get-ChildItem -LiteralPath (Join-Path $root 'evidence') -File | ForEach-Object { $_.Name } | Sort-Object) } else { @() } }
$coreLinkFile = Join-Path $sandboxHome 'data\core-connection.json'
function CoreLink {
    # $null when the file is absent or cannot be read at this instant (the Core writes it at start and removes it at
    # shutdown; a read in that moment is denied): the callers poll.
    if (-not (Test-Path -LiteralPath $coreLinkFile)) { return $null }
    try { Get-Content -LiteralPath $coreLinkFile -Raw -ErrorAction Stop | ConvertFrom-Json } catch { $null }
}
function StartSandbox {
    # 1.0.16 through its JARVIS.ps1; 1.0.17 through its own JARVIS.exe (the launcher script is gone once it is current).
    $script = Join-Path $sandboxHome 'JARVIS.ps1'
    if (Test-Path -LiteralPath $script) { & powershell -NoProfile -ExecutionPolicy Bypass -File $script }
    else {
        $current = Get-Content -LiteralPath (Join-Path $sandboxHome 'current.json') -Raw | ConvertFrom-Json
        $exe = Join-Path $sandboxHome ('releases\' + $current.release + '\electron\JARVIS.exe')
        $null = Start-Process -FilePath $exe -WorkingDirectory (Split-Path $exe) -PassThru
    }
    for ($i = 0; $i -lt 240; $i++) {
        $link = CoreLink
        if ($link) { try { $r = Invoke-WebRequest -UseBasicParsing -Uri ($link.origin + '/') -Headers @{ 'X-Jarvis-Desktop' = $link.token } -TimeoutSec 5; if ($r.StatusCode -eq 200) { return $link } } catch {} }
        Start-Sleep -Milliseconds 500
    }
    throw 'the sandbox JARVIS did not become ready'
}
function Session($link) {
    $null = Invoke-WebRequest -UseBasicParsing -Uri ($link.origin + '/') -Headers @{ 'X-Jarvis-Desktop' = $link.token } -SessionVariable s -TimeoutSec 15
    $s
}
function StateOf($link) {
    $s = Session $link
    Invoke-RestMethod -Uri ($link.origin + '/api/state') -Headers @{ 'X-Jarvis-Desktop' = $link.token } -WebSession $s -TimeoutSec 30
}
function StopSandbox {
    $link = CoreLink
    if ($link) {
        try {
            $s = Session $link
            Invoke-RestMethod -Method Post -Uri ($link.origin + '/api/shutdown') -Body '{}' -ContentType 'application/json' -Headers @{ 'X-Jarvis-Desktop' = $link.token } -WebSession $s -TimeoutSec 10 | Out-Null
        } catch {}
        for ($i = 0; $i -lt 60 -and (Test-Path -LiteralPath $coreLinkFile); $i++) { Start-Sleep -Milliseconds 500 }
    }
    for ($round = 0; $round -lt 5 -and (SandboxProcesses).Count; $round++) {
        SandboxProcesses | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
        Start-Sleep -Seconds 2
    }
    if ((SandboxProcesses).Count) { throw 'sandbox JARVIS processes did not end' }
}
function Entry { if (Test-Path -LiteralPath $key) { $e = Get-ItemProperty -LiteralPath $key; [ordered]@{ present = $true; name = $e.DisplayName; version = $e.DisplayVersion; uninstall = $e.UninstallString } } else { @{ present = $false } } }
function RealEntry { if (Test-Path -LiteralPath $realKey) { $e = Get-ItemProperty -LiteralPath $realKey; "$($e.DisplayName) $($e.DisplayVersion) $($e.UninstallString)" } else { 'ABSENT' } }
$keyFile = Join-Path $sandboxHome 'config\.env'
function KeyFileText($t) { New-Item -ItemType Directory -Path (Split-Path $keyFile) -Force | Out-Null; [IO.File]::WriteAllText($keyFile, $t, (New-Object Text.UTF8Encoding $false)) }
function Hash($p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower() }
function RunSetup([string] $setup, [string] $logName) {
    # A Setup run silently with the sandbox switches, as the launcher runs the final one; its answer read back.
    $log = Join-Path $Base $logName
    $p = Start-Process -FilePath $setup -ArgumentList @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', ('/LOG="' + $log + '"'), ('/DIR="' + $staging + '"'), ('/HOME="' + $sandboxHome + '"'), '/NOSHORTCUTS') -PassThru -Wait
    $null = $p.Handle
    $answer = Join-Path $staging 'setup-result.json'
    [pscustomobject]@{ exit = $p.ExitCode; answer = $(if (Test-Path -LiteralPath $answer) { Get-Content -LiteralPath $answer -Raw | ConvertFrom-Json } else { $null }) }
}

# The launcher's own rule (review of 2026-10-13, finding 1): a Halt message built with + must be in parentheses.
$slips = @(Select-String -LiteralPath $Launcher -Pattern 'Halt ("[^"]*"|''[^'']*'') \+')
Check 'the launcher has no Halt message that would drop its state (static)' (-not $slips.Count) "$($slips.Count) line(s)"
$liveBefore = LiveCount
$realEntryAtStart = RealEntry
Note "live JARVIS processes at the start: $liveBefore; real shortcuts: $($shortcutsBefore.desktop) $($shortcutsBefore.startup); real entry: $realEntryAtStart"
Check 'the real entry recorded at the start (JARVIS 1.0.17 expected)' ($realEntryAtStart -like 'JARVIS 1.0.17 *') $realEntryAtStart

# Sections 1 to 5 run inside one try: a thrown stop (the real shortcuts changed, a sandbox JARVIS that never became
# ready) is recorded as a failed check and the cleanup of section 6 still runs.
$aborted = $null
try {
# 1. The everyday JARVIS of the sandbox, as on the owner's PC: 1.0.17 installed BY ITS OWN SETUP with the sandbox
#    switches (the sandbox entry 1.0.17, the package folder with its uninstaller), started once.
Note '===== install 1.0.17 into the sandbox home through its own Setup'
$first = RunSetup $PreviousSetup 'setup-install-1.0.17.log'
Check 'sandbox: 1.0.17 installed by its Setup' ($first.exit -eq 0 -and $first.answer -and $first.answer.status -eq 'installed' -and $first.answer.release -eq $PreviousId) "exit $($first.exit) $($first.answer.status)"
$entry = Entry
Check 'sandbox: the entry JARVIS (sandbox) 1.0.17 with its uninstaller in the package folder' ($entry.present -and $entry.version -eq $previousRecord.version -and $entry.uninstall -like ('*' + (Join-Path $staging 'unins000.exe') + '*')) "$($entry.name) $($entry.version)"
$previousUninstaller = Hash (Join-Path $staging 'unins000.exe')
$link = StartSandbox
$state = StateOf $link
Check 'sandbox: 1.0.17 running on its data' ($state.updates.installed_release -eq $PreviousId) $state.updates.installed_release

# 2. Refusals.
$r = Step 'no approval: refused' (Join-Path $Base 'no-such-approval.json')
Check 'refused without approval' ($r.exit -eq 2 -and $r.text -like '*not been approved*' -and -not (Records).Count) "exit $($r.exit)"
$authorization = [ordered]@{ schema = 'jarvis-everyday-update-authorized-v3'; final = $FinalId; previous = $PreviousId; final_zip = $FinalZip
    final_zip_sha256 = (Get-FileHash -LiteralPath $FinalZip -Algorithm SHA256).Hash.ToLower(); final_setup = $FinalSetup
    final_setup_sha256 = (Get-FileHash -LiteralPath $FinalSetup -Algorithm SHA256).Hash.ToLower(); note = 'rehearsal approval, sandbox only' }
[IO.File]::WriteAllText($auth, (ConvertTo-Json -InputObject $authorization), (New-Object Text.UTF8Encoding $false))
$r = Step 'JARVIS running: refused' $auth
Check 'refused while JARVIS runs' ($r.exit -eq 2 -and $r.text -like '*JARVIS is running*' -and -not ((Records) -contains 'check.json')) "exit $($r.exit)"
StopSandbox
# A key file 1.0.19 would refuse (the owner's PC before he edits it): provider qwen, no OpenRouter key. Fake values.
KeyFileText "JARVIS_PROVIDER=qwen`nDASHSCOPE_API_KEY=rehearsal-not-a-key`nOPENAI_API_KEY=rehearsal-not-a-key`n"
$r = Step 'key file for qwen: refused' $auth
Check 'refused on a key file 1.0.19 would refuse (names only in the message)' ($r.exit -eq 2 -and $r.text -like "*would refuse your key file*provider line says 'qwen'*OPENROUTER_API_KEY is missing*" -and $r.text -notlike '*rehearsal-not-a-key*' -and -not ((Records) -contains 'check.json') -and -not (Test-Path -LiteralPath ($keyFile + '.before-' + $FinalId))) "exit $($r.exit)"
# The owner's edit: OpenRouter, the old lines kept.
KeyFileText "JARVIS_PROVIDER=openrouter`nOPENROUTER_API_KEY=rehearsal-not-a-key`nDASHSCOPE_API_KEY=rehearsal-not-a-key`nOPENAI_API_KEY=rehearsal-not-a-key`n"
$keyHashBefore = Hash $keyFile

# 3. The three steps.
$r = Step 'step 1 check' $auth
$check = $(if ((Records) -contains 'check.json') { Get-Content -LiteralPath (Join-Path $root 'evidence\check.json') -Raw | ConvertFrom-Json } else { $null })
Check 'step 1 check (no key value in the output)' ($r.exit -eq 0 -and $null -ne $check -and $r.text -notlike '*rehearsal-not-a-key*') "exit $($r.exit)"
Check 'step 1: 1.0.17 package folder seen (its uninstaller inside), not yet moved' ($null -ne $check -and $check.staging_before.present -and $check.staging_before.uninstaller_sha256 -eq $previousUninstaller -and $check.staging_before.answer_release -eq $PreviousId -and $check.staging_to_be_moved_aside -and (Test-Path -LiteralPath $staging) -and (Entry).uninstall -like ('*' + (Join-Path $staging 'unins000.exe') + '*')) "$($check.staging_to_be_moved_aside)"
Check 'step 1: the entry 1.0.17 before' ($null -ne $check -and $check.entry_before.present -and $check.entry_before.version -eq $previousRecord.version) "$($check.entry_before.version)"
Check 'step 1: the key file accepted, names only recorded, a copy made' ($null -ne $check -and $check.key_file.provider -eq 'openrouter' -and [bool]$check.key_file.has_openrouter_key -and (@($check.key_file.names) -contains 'OPENROUTER_API_KEY') -and (@($check.key_file.names) -contains 'DASHSCOPE_API_KEY') -and $check.key_file.sha256 -eq $keyHashBefore -and (Test-Path -LiteralPath $check.key_file.copy) -and (Hash $check.key_file.copy) -eq $keyHashBefore -and ((Get-Content -LiteralPath (Join-Path $root 'evidence\check.json') -Raw) -notlike '*rehearsal-not-a-key*')) "$($check.key_file.names -join ',')"
$r = Step 'step 2 backup' $auth
Check 'step 2 backup' ($r.exit -eq 0 -and ((Records) -contains 'backup.json')) "exit $($r.exit)"
$r = Step 'step 3 update through the Setup' $auth
Check 'step 3 update' ($r.exit -eq 0 -and ((Records) -contains 'update.json')) "exit $($r.exit)"
$update = $(if ((Records) -contains 'update.json') { Get-Content -LiteralPath (Join-Path $root 'evidence\update.json') -Raw | ConvertFrom-Json } else { $null })
Check 'update: database unchanged' ($null -ne $update -and [bool]$update.database_unchanged) "$($update.database_sha256_before)"
Check 'update: 1.0.17 package folder moved aside at step 3, nothing deleted (its uninstaller inside)' ($null -ne $update -and $update.staging_moved_aside -and (Test-Path -LiteralPath (Join-Path $update.staging_moved_aside 'unins000.exe')) -and (Hash (Join-Path $update.staging_moved_aside 'unins000.exe')) -eq $previousUninstaller -and (Test-Path -LiteralPath (Join-Path $update.staging_moved_aside 'setup-result.json'))) "$($update.staging_moved_aside)"
Check 'update: current is 1.0.19, previous 1.0.17' ($null -ne $update -and $update.current.release -eq $FinalId -and $update.current.previous -eq $PreviousId) "$($update.current.release)"
Check 'update: the installer inside the Setup withheld the shortcuts (sandbox)' ($null -ne $update -and "$($update.installer.shortcuts)" -like 'withheld*') "$($update.installer.shortcuts)"
$entry = Entry
Check 'update: the entry JARVIS (sandbox) now 1.0.19, the new uninstaller' ($entry.present -and $entry.name -eq $setupRecord.sandbox_display_name -and $entry.version -eq $setupRecord.version -and $entry.uninstall -like ('*' + (Join-Path $staging 'unins000.exe') + '*') -and (Hash (Join-Path $staging 'unins000.exe')) -ne $previousUninstaller) "$($entry.name) $($entry.version)"
Check 'update: the real entry untouched' ((RealEntry) -eq $realEntryAtStart) (RealEntry)
Check 'update: the key file untouched by the update' ((Hash $keyFile) -eq $keyHashBefore) (Hash $keyFile)
Check 'update: the Setup logged --no-shortcuts' ($null -ne $update -and $update.setup_log -and (Test-Path -LiteralPath $update.setup_log) -and ((Get-Content -LiteralPath $update.setup_log -Raw) -like '*--no-shortcuts*')) $(if ($null -ne $update -and $update.setup_log) { Split-Path -Leaf $update.setup_log } else { 'no setup_log in update.json' })

# 4. 1.0.19 on the same data, through its own JARVIS.exe (a fake OpenRouter key: no AI answer is asked for).
$link = StartSandbox
$state = StateOf $link
Check 'sandbox: 1.0.19 running on the same data through JARVIS.exe' ($state.updates.installed_release -eq $FinalId) $state.updates.installed_release
$names = @(SandboxProcesses | ForEach-Object { $_.Name } | Sort-Object -Unique)
Check 'sandbox: only JARVIS.exe and python.exe run' (($names -join ',') -eq 'JARVIS.exe,python.exe') ($names -join ',')
StopSandbox
$before = Records
$r = Step 'rerun after the update: nothing to do' $auth
Check 'rerun changes nothing' ($r.exit -eq 0 -and $r.text -like '*complete and recorded*' -and ((Records) -join ',') -eq ($before -join ',')) "exit $($r.exit)"
# A second attempt of step 3 after the update (the record renamed aside for the test): refused with the state said
# in full (review of 2026-10-13, finding 1: the state line was being dropped; finding 4: the entry is part of it).
Rename-Item -LiteralPath (Join-Path $root 'evidence\update.json') -NewName 'update.json.aside-for-the-test'
$r = Step 'step 3 again after the update: refused with the state' $auth
Rename-Item -LiteralPath (Join-Path $root 'evidence\update.json.aside-for-the-test') -NewName 'update.json'
$current = Get-Content -LiteralPath (Join-Path $sandboxHome 'current.json') -Raw | ConvertFrom-Json
Check 'step 3 again: refused, the state said in full (release, shortcuts, the entry)' ($r.exit -eq 2 -and $r.text -like "*your JARVIS is on $FinalId, not $PreviousId*" -and $r.text -like "*Your JARVIS is on $FinalId;*" -and $r.text -like "*Settings > Apps lists $($setupRecord.sandbox_display_name) $($setupRecord.version), uninstaller*" -and $current.release -eq $FinalId) "exit $($r.exit)"

# 5. Rollback, only with its approval file. The key file is changed first (as the owner might have, on 1.0.19), so the
#    rollback's restore from the step 1 copy is seen to do something, and the changed file is kept beside it.
KeyFileText "JARVIS_PROVIDER=openrouter`nOPENROUTER_API_KEY=rehearsal-not-a-key-changed`n"
[IO.File]::WriteAllText((Join-Path $root 'evidence\rollback-approved.json'), '{"note": "rehearsal"}', (New-Object Text.UTF8Encoding $false))
$r = Step 'rollback (approved)' $auth
$current = Get-Content -LiteralPath (Join-Path $sandboxHome 'current.json') -Raw | ConvertFrom-Json
Check 'rollback to 1.0.17 (no key value in the output)' ($r.exit -eq 0 -and ((Records) -contains 'rollback.json') -and $current.release -eq $PreviousId -and $r.text -notlike '*rehearsal-not-a-key*') "$($current.release)"
Check 'rollback: the attempt recorded before the switch' ((@(Records) | Where-Object { $_ -like 'rollback-attempt-*.json' }).Count -eq 1) ((Records) -join ',')
Check 'rollback: the final line says the provider line is one 1.0.17 does not know' ($r.text -like "*provider line says 'openrouter'*does not know*set JARVIS_PROVIDER=qwen or openai*") 'said'
Check 'rollback: the entry still says 1.0.19 (as the plan says)' ((Entry).present -and (Entry).version -eq $setupRecord.version) "$((Entry).version)"
$rollback = $(if ((Records) -contains 'rollback.json') { Get-Content -LiteralPath (Join-Path $root 'evidence\rollback.json') -Raw | ConvertFrom-Json } else { $null })
Check 'rollback: the key file put back from the step 1 copy, the changed file kept beside it' ($null -ne $rollback -and [bool]$rollback.key_file.restored -and (Hash $keyFile) -eq $keyHashBefore -and $rollback.key_file.kept_as -and (Test-Path -LiteralPath $rollback.key_file.kept_as) -and ((Get-Content -LiteralPath $rollback.key_file.kept_as -Raw) -like '*changed*') -and ((Get-Content -LiteralPath (Join-Path $root 'evidence\rollback.json') -Raw) -notlike '*rehearsal-not-a-key*')) "$($rollback.key_file.kept_as)"
$link = StartSandbox
$state = StateOf $link
Check 'sandbox: 1.0.17 running again on the same data' ($state.updates.installed_release -eq $PreviousId) $state.updates.installed_release
StopSandbox
$r = Step 'rerun after the rollback: nothing to do' $auth
Check 'rerun after rollback changes nothing' ($r.exit -eq 0 -and $r.text -like '*complete and recorded*') "exit $($r.exit)"
# A rollback entered again after one that switched back but left no record (the record renamed aside for the test):
# nothing is switched forward again (review of 2026-10-13, finding 2), the state said in full.
Rename-Item -LiteralPath (Join-Path $root 'evidence\rollback.json') -NewName 'rollback.json.aside-for-the-test'
$attemptsBefore = (@(Records) | Where-Object { $_ -like 'rollback-attempt-*.json' }).Count
$r = Step 'rollback again without its record: refused, nothing switched' $auth
Rename-Item -LiteralPath (Join-Path $root 'evidence\rollback.json.aside-for-the-test') -NewName 'rollback.json'
$current = Get-Content -LiteralPath (Join-Path $sandboxHome 'current.json') -Raw | ConvertFrom-Json
Check 'rollback again: refused, still on 1.0.17, no new attempt, the state said' ($r.exit -eq 2 -and $r.text -like '*already switched your JARVIS back*nothing is switched again*' -and $r.text -like "*Your JARVIS is on $PreviousId;*" -and $current.release -eq $PreviousId -and $current.previous -eq $FinalId -and (@(Records) | Where-Object { $_ -like 'rollback-attempt-*.json' }).Count -eq $attemptsBefore) "$($current.release) exit $($r.exit)"
} catch { $aborted = $_.Exception.Message }

# 6. Cleanup, whatever happened above: the sandbox JARVIS ended, then the sandbox uninstalled through its own entry
#    (both releases removed, data kept, the entry and the staging gone).
if ($aborted) { Note "STOPPED: $aborted"; Check 'the harness ran to the end' $false $aborted }
try { StopSandbox } catch { Note "cleanup: $($_.Exception.Message)"; Check 'cleanup: the sandbox JARVIS ended' $false $_.Exception.Message }
$uninstaller = Join-Path $staging 'unins000.exe'
if (Test-Path -LiteralPath $uninstaller) {
    $u = Start-Process -FilePath $uninstaller -ArgumentList @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART') -PassThru -Wait
    $null = $u.Handle
    $deadline = (Get-Date).AddSeconds(30)
    while ((Get-Date) -lt $deadline -and ((Test-Path -LiteralPath $staging) -or (Test-Path -LiteralPath $key))) { Start-Sleep -Milliseconds 500 }
    Check 'cleanup: the sandbox uninstalled through its own entry' ($u.ExitCode -eq 0 -and -not (Test-Path -LiteralPath $key) -and -not (Test-Path -LiteralPath $staging) -and (Test-Path -LiteralPath (Join-Path $sandboxHome 'data\jarvis.sqlite3')) -and -not (Test-Path -LiteralPath (Join-Path $sandboxHome 'releases'))) "exit $($u.ExitCode)"
} else {
    # The Setup never ran (an earlier step stopped): no entry to clean up; the sandbox JARVIS was ended above.
    Check 'cleanup: the sandbox uninstalled through its own entry' $false 'no uninstaller: the update step never ran'
}
Check 'the owner real shortcuts unchanged throughout' (ShortcutsUnchanged) "$((RealShortcuts).desktop) $((RealShortcuts).startup)"
Check 'the real entry the same at the end' ((RealEntry) -eq $realEntryAtStart) (RealEntry)

$liveAfter = LiveCount
Note "live JARVIS processes at the end: $liveAfter (start: $liveBefore); sandbox processes at the end: $((SandboxProcesses).Count)"
$failed = @($results | Where-Object { -not $_.passed }).Count
$summary = [ordered]@{ base = $Base; launcher_sha256 = (Get-FileHash -LiteralPath $Launcher -Algorithm SHA256).Hash.ToLower(); setup_sha256 = $authorization.final_setup_sha256; checks = @($results); failed = $failed
    real_shortcuts_before = $shortcutsBefore; real_shortcuts_after = (RealShortcuts); live_processes_before = $liveBefore; live_processes_after = $liveAfter; sandbox_processes_after = (SandboxProcesses).Count
    real_entry_at_start = $realEntryAtStart; real_entry_at_end = (RealEntry); aborted = $aborted }
[IO.File]::WriteAllText((Join-Path $Base 'rehearsal-summary.json'), (ConvertTo-Json -InputObject $summary -Depth 5), (New-Object Text.UTF8Encoding $false))
Note ("{0} checks, {1} failed" -f $results.Count, $failed)
exit $(if ($failed) { 1 } else { 0 })
