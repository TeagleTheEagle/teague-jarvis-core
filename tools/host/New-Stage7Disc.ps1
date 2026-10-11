<#
.SYNOPSIS
Builds the Stage 7 disc: run BY THE OWNER, own account, non-elevated. The disc carries the build under
acceptance (release zip and record) with stage7.cmd and the Stage 7 guest scripts (tools\guest in the repo).
The previous build comes from its existing package disc (built for Stage 6 Gate 19, unchanged).
Same method as New-Gate17PackageDisc.ps1: assembles D:\JARVIS-release-work\stage7-payload-<id>\, images it with
tools\New-PackageIso.ps1 into D:\JARVIS-release-work\stage7-media\JARVIS-STAGE7-<id>.iso (hash-verified,
<iso>.sha256.json beside it), copies both into D:\JARVIS-S6-FRESHVM\media and checks the copy, and writes
D:\JARVIS-stage7\evidence\stage7-disc-<id>.json. Nothing that already exists is overwritten.
#>
param(
    [string] $ReleaseId = '1.0.11-60d406fb6398',
    [string] $ReleaseDir = 'D:\JARVIS-release-work\release',
    [string] $Repo = 'C:\Users\jonny\JARVIS-claude-workspace\repo',
    [string] $Media = 'D:\JARVIS-release-work\stage7-media',
    [string] $Dest = 'D:\JARVIS-S6-FRESHVM\media',
    [string] $Evidence = 'D:\JARVIS-stage7\evidence'
)
$ErrorActionPreference = 'Stop'
if (([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Elevated session: STOP' }
function Sha256($p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower() }
$zip = Join-Path $ReleaseDir "JARVIS-$ReleaseId.zip"; $rec = Join-Path $ReleaseDir "JARVIS-$ReleaseId.release.json"
$builder = Join-Path $Repo 'tools\New-PackageIso.ps1'
$guest = 'Invoke-Stage7.ps1', 'Invoke-Stage7Pass.ps1' | ForEach-Object { Join-Path $Repo "tools\guest\$_" }
$cmd = Join-Path $Repo 'tools\guest\stage7.cmd'
foreach ($p in @($zip, $rec, $builder, $cmd) + $guest) { if (-not (Test-Path -LiteralPath $p)) { throw "missing: $p" } }
$name = "JARVIS-STAGE7-$ReleaseId.iso"
$payload = Join-Path (Split-Path -Parent $ReleaseDir) "stage7-payload-$ReleaseId"
$out = Join-Path $Media $name; $copy = Join-Path $Dest $name; $record = Join-Path $Evidence "stage7-disc-$ReleaseId.json"
foreach ($p in $payload, $out, $copy, $record) { if (Test-Path -LiteralPath $p) { throw "already exists, not touched: $p" } }
$release = Get-Content -LiteralPath $rec -Raw | ConvertFrom-Json
Write-Host "Checking the release zip of $ReleaseId ..."
$zipHash = Sha256 $zip
if ($zipHash -ne $release.zip_sha256) { throw "release zip hash $zipHash does not equal the release record $($release.zip_sha256); STOP" }
New-Item -ItemType Directory -Path $Media -Force | Out-Null
New-Item -ItemType Directory -Path $payload | Out-Null
Copy-Item -LiteralPath $zip -Destination $payload
Copy-Item -LiteralPath $rec -Destination $payload
New-Item -ItemType Directory -Path (Join-Path $payload 'guest') | Out-Null
$guest | ForEach-Object { Copy-Item -LiteralPath $_ -Destination (Join-Path $payload 'guest') }
Copy-Item -LiteralPath $cmd -Destination $payload
$readme = @"
JARVIS Stage 7 disc. Release $ReleaseId (the build under acceptance).
Contents: JARVIS-$ReleaseId.zip (sha256 $zipHash), JARVIS-$ReleaseId.release.json, stage7.cmd, guest\Invoke-Stage7Pass.ps1, guest\Invoke-Stage7.ps1, PAYLOAD-MANIFEST.json (SHA-256 of every file).
Inside the VM (account jarvis-s6-guest): open this disc in File Explorer and double-click stage7. It runs the next step and says what to do afterwards.
Nothing on this disc contains credentials. Built by the owner with tools\host\New-Stage7Disc.ps1.
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
    schema = 'jarvis-stage7-disc-v1'; utc = (Get-Date).ToUniversalTime().ToString('o'); performed_by = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    release_id = $ReleaseId; commit = $release.commit; zip = $release.zip; zip_bytes = (Get-Item -LiteralPath $zip).Length; zip_sha256 = $zipHash
    guest_files = @($guest + @($cmd) | ForEach-Object { [ordered]@{ name = (Split-Path -Leaf $_); sha256 = (Sha256 $_) } })
    iso = $out; iso_sha256 = $built.sha256; iso_bytes = $built.bytes; payload_files = $built.payload_files; payload_manifest_sha256 = $built.payload_manifest_sha256; readback = $built.readback
    copy = $copy; copy_sha256 = $copyHash
}
[IO.File]::WriteAllText($record, (ConvertTo-Json -InputObject $result -Depth 4), (New-Object Text.UTF8Encoding $false))
Write-Host ''
Write-Host "Stage 7 disc: $copy"
Write-Host ("{0}  {1:N0} bytes  sha256 {2}" -f $name, $built.bytes, $built.sha256)
