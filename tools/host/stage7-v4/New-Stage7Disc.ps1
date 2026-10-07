<#
.SYNOPSIS
Builds the Stage 7 disc for one check (version 4): run BY THE OWNER, own account, non-elevated. The disc carries
the build under acceptance (release zip and record, and, new in version 4, its JARVIS-Setup-<id>.exe with its
record JARVIS-Setup-<id>.setup.json, checked against each other here), stage7.cmd and the version 4 guest scripts
(tools\guest\stage7-v4 in the repo), and stage7-target.json naming this check's own folder in the VM's egress share
(stage7-<label>). The previous build comes from its existing package or Stage 7 disc.
A copy of tools\host\stage7-v3\New-Stage7Disc.ps1 (used for 1.0.15 and 1.0.16; unchanged, evidence) with the Setup
added and the disc image sized for a DVD (the version 4 copy of the disc builder in this folder: zip and Setup
together are about 930 MB, more than a CD):
  D:\JARVIS-release-work\stage7-payload-<label>\  ->  D:\JARVIS-release-work\stage7-media\JARVIS-STAGE7-<label>.iso
  (hash-verified, <iso>.sha256.json beside it), copied to D:\JARVIS-S6-FRESHVM\media and checked, and the record
  <Evidence>\stage7-disc-<label>.json. Nothing that already exists is overwritten.
#>
param(
    [Parameter(Mandatory)] [string] $ReleaseId,
    [string] $Label = $ReleaseId,
    [string] $ReleaseDir = 'D:\JARVIS-release-work\release',
    [string] $Repo = 'C:\Users\jonny\JARVIS-claude-workspace\repo',
    [string] $Media = 'D:\JARVIS-release-work\stage7-media',
    [string] $Dest = 'D:\JARVIS-S6-FRESHVM\media',
    [Parameter(Mandatory)] [string] $Evidence
)
$ErrorActionPreference = 'Stop'
if (([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Elevated session: STOP' }
if ($Label -notmatch '^[A-Za-z0-9._-]+$') { throw "label '$Label' may only use letters, digits, dot, dash and underscore; STOP" }
function Sha256($p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower() }
$zip = Join-Path $ReleaseDir "JARVIS-$ReleaseId.zip"; $rec = Join-Path $ReleaseDir "JARVIS-$ReleaseId.release.json"
$setup = Join-Path $ReleaseDir "JARVIS-Setup-$ReleaseId.exe"; $setupRec = Join-Path $ReleaseDir "JARVIS-Setup-$ReleaseId.setup.json"
# The version 4 copy of the disc builder (DVD-sized image): beside this script in the launcher folder the owner runs
# from, or, when the launcher folder was placed without it, the one in the repo.
$builder = Join-Path $PSScriptRoot 'New-PackageIso.ps1'
if (-not (Test-Path -LiteralPath $builder)) { $builder = Join-Path $Repo 'tools\host\stage7-v4\New-PackageIso.ps1' }
$guestDir = Join-Path $Repo 'tools\guest\stage7-v4'
$guest = 'Invoke-Stage7.ps1', 'Invoke-Stage7Pass.ps1' | ForEach-Object { Join-Path $guestDir $_ }
$cmd = Join-Path $guestDir 'stage7.cmd'
foreach ($p in @($zip, $rec, $setup, $setupRec, $builder, $cmd) + $guest) { if (-not (Test-Path -LiteralPath $p)) { throw "missing: $p" } }
$name = "JARVIS-STAGE7-$Label.iso"
$payload = Join-Path (Split-Path -Parent $ReleaseDir) "stage7-payload-$Label"
$out = Join-Path $Media $name; $copy = Join-Path $Dest $name; $record = Join-Path $Evidence "stage7-disc-$Label.json"
foreach ($p in $payload, $out, $copy, $record) { if (Test-Path -LiteralPath $p) { throw "already exists, not touched: $p" } }
$release = Get-Content -LiteralPath $rec -Raw | ConvertFrom-Json
if ($release.release_id -ne $ReleaseId) { throw "the release record names $($release.release_id), not $ReleaseId; STOP" }
Write-Host "Checking the release zip of $ReleaseId ..."
$zipHash = Sha256 $zip
if ($zipHash -ne $release.zip_sha256) { throw "release zip hash $zipHash does not equal the release record $($release.zip_sha256); STOP" }
# Version 4: the Setup against its own record, and that record against the release (same release id, same package manifest).
$setupRecord = Get-Content -LiteralPath $setupRec -Raw | ConvertFrom-Json
if ($setupRecord.release_id -ne $ReleaseId) { throw "the Setup record names $($setupRecord.release_id), not $ReleaseId; STOP" }
if ($setupRecord.manifest_sha256 -ne $release.manifest_sha256) { throw "the Setup was built from a package whose manifest ($($setupRecord.manifest_sha256)) is not this release's ($($release.manifest_sha256)); STOP" }
Write-Host "Checking the Setup of $ReleaseId ..."
$setupHash = Sha256 $setup
if ($setupHash -ne $setupRecord.setup_sha256) { throw "Setup hash $setupHash does not equal its record $($setupRecord.setup_sha256); STOP" }
New-Item -ItemType Directory -Path $Media -Force | Out-Null
New-Item -ItemType Directory -Path $payload | Out-Null
Copy-Item -LiteralPath $zip -Destination $payload
Copy-Item -LiteralPath $rec -Destination $payload
Copy-Item -LiteralPath $setup -Destination $payload
Copy-Item -LiteralPath $setupRec -Destination $payload
New-Item -ItemType Directory -Path (Join-Path $payload 'guest') | Out-Null
$guest | ForEach-Object { Copy-Item -LiteralPath $_ -Destination (Join-Path $payload 'guest') }
Copy-Item -LiteralPath $cmd -Destination $payload
$target = [ordered]@{ schema = 'jarvis-stage7-target-v1'; release_id = $ReleaseId; label = $Label; egress_folder = "stage7-$Label" }
[IO.File]::WriteAllText((Join-Path $payload 'stage7-target.json'), (ConvertTo-Json -InputObject $target), (New-Object Text.UTF8Encoding $false))
$readme = @"
JARVIS Stage 7 disc. Release $ReleaseId (the build under acceptance), check $Label.
Contents: JARVIS-$ReleaseId.zip (sha256 $zipHash), JARVIS-$ReleaseId.release.json, JARVIS-Setup-$ReleaseId.exe (sha256 $setupHash; the check installs from it), JARVIS-Setup-$ReleaseId.setup.json, stage7.cmd, guest\Invoke-Stage7Pass.ps1, guest\Invoke-Stage7.ps1 (version 4), stage7-target.json (records go to the egress folder stage7-$Label), PAYLOAD-MANIFEST.json (SHA-256 of every file).
Inside the VM (account jarvis-s6-guest): open this disc in File Explorer and double-click stage7. It runs the next step and says what to do afterwards.
Nothing on this disc contains credentials. Built by the owner with tools\host\stage7-v4\New-Stage7Disc.ps1.
"@
[IO.File]::WriteAllText((Join-Path $payload 'README.txt'), $readme, (New-Object Text.UTF8Encoding $false))
Write-Host "Building $name (this takes a few minutes; the disc is opened once to check it) ..."
& $builder -Payload $payload -Out $out -Label 'JARVIS_S7' | Out-Null
$built = Get-Content -LiteralPath "$out.sha256.json" -Raw | ConvertFrom-Json
Write-Host "Copying the disc to $Dest ..."
Copy-Item -LiteralPath $out -Destination $Dest
Copy-Item -LiteralPath "$out.sha256.json" -Destination $Dest
$copyHash = Sha256 $copy
if ($copyHash -ne $built.sha256) { throw "copy hash $copyHash differs from the build record $($built.sha256); STOP" }
if (-not (Test-Path -LiteralPath $Evidence)) { New-Item -ItemType Directory -Path $Evidence -Force | Out-Null }
$result = [ordered]@{
    schema = 'jarvis-stage7-disc-v4'; utc = (Get-Date).ToUniversalTime().ToString('o'); performed_by = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    release_id = $ReleaseId; label = $Label; target = $target; commit = $release.commit; zip = $release.zip; zip_bytes = (Get-Item -LiteralPath $zip).Length; zip_sha256 = $zipHash
    setup = (Split-Path -Leaf $setup); setup_bytes = (Get-Item -LiteralPath $setup).Length; setup_sha256 = $setupHash; setup_record = (Split-Path -Leaf $setupRec); setup_record_sha256 = (Sha256 $setupRec); setup_version = $setupRecord.version
    guest_version = 4; disc_builder = (Split-Path -Leaf $builder); disc_builder_sha256 = (Sha256 $builder)
    guest_files = @($guest + @($cmd) | ForEach-Object { [ordered]@{ name = (Split-Path -Leaf $_); sha256 = (Sha256 $_) } })
    iso = $out; iso_sha256 = $built.sha256; iso_bytes = $built.bytes; payload_files = $built.payload_files; payload_manifest_sha256 = $built.payload_manifest_sha256; readback = $built.readback
    copy = $copy; copy_sha256 = $copyHash
}
[IO.File]::WriteAllText($record, (ConvertTo-Json -InputObject $result -Depth 4), (New-Object Text.UTF8Encoding $false))
Write-Host ''
Write-Host "Stage 7 disc: $copy"
Write-Host ("{0}  {1:N0} bytes  sha256 {2}" -f $name, $built.bytes, $built.sha256)
