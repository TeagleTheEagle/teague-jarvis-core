<#
.SYNOPSIS
Builds one package disc for Stage 6 Gates 17 and 19: run BY THE OWNER, own account, non-elevated.
Role Final: the build under acceptance, with gate.cmd and the guest scripts (tools\guest in the repo).
Role Previous: the build before it, used only by the Gate 19 update test (release zip and record, no scripts).
Assembles D:\JARVIS-release-work\package-payload-<id>\, images it with tools\New-PackageIso.ps1 into
D:\JARVIS-release-work\stage6-media\JARVIS-PACKAGE-<id>.iso (hash-verified, <iso>.sha256.json beside it), copies
the disc and its hash record into D:\JARVIS-S6-FRESHVM\media and checks the copy, and writes
evidence\gate17\package-disc-<id>.json. Nothing that already exists is overwritten.
Building a disc does not make a release FINAL; FINAL selection is the owner's separate act.
#>
param(
    [string] $ReleaseId = '1.0.11-60d406fb6398',
    [ValidateSet('Final', 'Previous')] [string] $Role = 'Final',
    [string] $ReleaseDir = 'D:\JARVIS-release-work\release',
    [string] $Repo = 'C:\Users\jonny\JARVIS-claude-workspace\repo',
    [string] $Media = 'D:\JARVIS-release-work\stage6-media',
    [string] $Dest = 'D:\JARVIS-S6-FRESHVM\media',
    [string] $Evidence = 'D:\JARVIS-S6-FRESHVM\evidence\gate17'
)
$ErrorActionPreference = 'Stop'
if (([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Elevated session: STOP' }
function Sha256($p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower() }
$zip = Join-Path $ReleaseDir "JARVIS-$ReleaseId.zip"; $rec = Join-Path $ReleaseDir "JARVIS-$ReleaseId.release.json"
$builder = Join-Path $Repo 'tools\New-PackageIso.ps1'
$guest = @(if ($Role -eq 'Final') { 'Invoke-Gate17.ps1', 'Invoke-Gate.ps1' | ForEach-Object { Join-Path $Repo "tools\guest\$_" } })
$gateCmd = Join-Path $Repo 'tools\guest\gate.cmd'
foreach ($p in @($zip, $rec, $builder) + $guest + @(if ($Role -eq 'Final') { $gateCmd })) { if (-not (Test-Path -LiteralPath $p)) { throw "missing: $p" } }
$name = "JARVIS-PACKAGE-$ReleaseId.iso"
$payload = Join-Path (Split-Path -Parent $ReleaseDir) "package-payload-$ReleaseId"
$out = Join-Path $Media $name; $copy = Join-Path $Dest $name; $record = Join-Path $Evidence "package-disc-$ReleaseId.json"
foreach ($p in $payload, $out, $copy, $record) { if (Test-Path -LiteralPath $p) { throw "already exists, not touched: $p" } }
$release = Get-Content -LiteralPath $rec -Raw | ConvertFrom-Json
Write-Host "Checking the release zip of $ReleaseId ..."
$zipHash = Sha256 $zip
if ($zipHash -ne $release.zip_sha256) { throw "release zip hash $zipHash does not equal the release record $($release.zip_sha256); STOP" }
New-Item -ItemType Directory -Path $payload | Out-Null
Copy-Item -LiteralPath $zip -Destination $payload
Copy-Item -LiteralPath $rec -Destination $payload
if ($Role -eq 'Final') {
    New-Item -ItemType Directory -Path (Join-Path $payload 'guest') | Out-Null
    $guest | ForEach-Object { Copy-Item -LiteralPath $_ -Destination (Join-Path $payload 'guest') }
    Copy-Item -LiteralPath $gateCmd -Destination $payload
    $readme = @"
JARVIS package disc for Stage 6 Gates 17 and 19. Release $ReleaseId, the build under acceptance (FINAL selection is the owner's act; this disc does not make it FINAL).
Contents: JARVIS-$ReleaseId.zip (the release, sha256 $zipHash), JARVIS-$ReleaseId.release.json (its release record), gate.cmd, guest\Invoke-Gate.ps1, guest\Invoke-Gate17.ps1, PAYLOAD-MANIFEST.json (SHA-256 of every file).
Inside the VM (account jarvis-s6-guest): open this disc in File Explorer and double-click gate. It runs the next step and says what to do afterwards.
Nothing on this disc contains credentials. Built by the owner with tools\host\New-Gate17PackageDisc.ps1.
"@
} else {
    $readme = @"
JARVIS package disc with the PREVIOUS build, $ReleaseId, for the Stage 6 Gate 19 update test only. It is installed first, updated to the build under acceptance, rolled back to, and updated again.
Contents: JARVIS-$ReleaseId.zip (sha256 $zipHash), JARVIS-$ReleaseId.release.json, PAYLOAD-MANIFEST.json. Nothing is started from this disc; gate.cmd on the other disc finds it.
Nothing on this disc contains credentials. Built by the owner with tools\host\New-Gate17PackageDisc.ps1.
"@
}
[IO.File]::WriteAllText((Join-Path $payload 'README.txt'), $readme, (New-Object Text.UTF8Encoding $false))
Write-Host "Building $name (this takes a few minutes; the disc is opened once to check it) ..."
& $builder -Payload $payload -Out $out -Label $(if ($Role -eq 'Final') { 'JARVIS_PKG' } else { 'JARVIS_PREV' }) | Out-Null
$built = Get-Content -LiteralPath "$out.sha256.json" -Raw | ConvertFrom-Json
Write-Host "Copying the disc to $Dest ..."
Copy-Item -LiteralPath $out -Destination $Dest
Copy-Item -LiteralPath "$out.sha256.json" -Destination $Dest
$copyHash = Sha256 $copy
if ($copyHash -ne $built.sha256) { throw "copy hash $copyHash differs from the build record $($built.sha256); STOP" }
if (-not (Test-Path -LiteralPath $Evidence)) { New-Item -ItemType Directory -Path $Evidence | Out-Null }
$result = [ordered]@{
    schema = 'stage6-gate17-package-disc-v1'; utc = (Get-Date).ToUniversalTime().ToString('o'); performed_by = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    role = $Role; release_id = $ReleaseId; commit = $release.commit; zip = $release.zip; zip_bytes = (Get-Item -LiteralPath $zip).Length; zip_sha256 = $zipHash
    guest_files = @($guest + @(if ($Role -eq 'Final') { $gateCmd }) | ForEach-Object { [ordered]@{ name = (Split-Path -Leaf $_); sha256 = (Sha256 $_) } })
    iso = $out; iso_sha256 = $built.sha256; iso_bytes = $built.bytes; payload_files = $built.payload_files; payload_manifest_sha256 = $built.payload_manifest_sha256; readback = $built.readback
    copy = $copy; copy_sha256 = $copyHash
}
[IO.File]::WriteAllText($record, (ConvertTo-Json -InputObject $result -Depth 4), (New-Object Text.UTF8Encoding $false))
Write-Host ''
Write-Host "Package disc ($Role): $copy"
Write-Host ("{0}  {1:N0} bytes  sha256 {2}" -f $name, $built.bytes, $built.sha256)
