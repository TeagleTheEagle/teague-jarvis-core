<#
.SYNOPSIS
Builds the Gate 17 package disc for one release: run BY THE OWNER, own account, non-elevated.
Assembles D:\JARVIS-release-work\package-payload-<id>\ (the release zip, its release record, the guest script
tools\guest\Invoke-Gate17.ps1 from the repo, a README) and images it with tools\New-PackageIso.ps1 into
D:\JARVIS-release-work\stage6-media\JARVIS-PACKAGE-<id>.iso, hash-verified, with <iso>.sha256.json beside it.
Building the disc does not make the release FINAL; FINAL selection is the owner's separate act.
#>
param(
    [string] $ReleaseId = '1.0.11-60d406fb6398',
    [string] $ReleaseDir = 'D:\JARVIS-release-work\release',
    [string] $Repo = 'C:\Users\jonny\JARVIS-claude-workspace\repo',
    [string] $Media = 'D:\JARVIS-release-work\stage6-media'
)
$ErrorActionPreference = 'Stop'
if (([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Elevated session: STOP' }
$zip = Join-Path $ReleaseDir "JARVIS-$ReleaseId.zip"; $rec = Join-Path $ReleaseDir "JARVIS-$ReleaseId.release.json"
$guest = Join-Path $Repo 'tools\guest\Invoke-Gate17.ps1'; $builder = Join-Path $Repo 'tools\New-PackageIso.ps1'
foreach ($p in $zip, $rec, $guest, $builder) { if (-not (Test-Path -LiteralPath $p)) { throw "missing: $p" } }
$payload = Join-Path (Split-Path -Parent $ReleaseDir) "package-payload-$ReleaseId"
$out = Join-Path $Media "JARVIS-PACKAGE-$ReleaseId.iso"
if (Test-Path -LiteralPath $payload) { throw "already exists, not touched: $payload" }
if (Test-Path -LiteralPath $out) { throw "already exists, not touched: $out" }
$release = Get-Content -LiteralPath $rec -Raw | ConvertFrom-Json
$zipHash = (Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash.ToLower()
if ($zipHash -ne $release.zip_sha256) { throw "release zip hash $zipHash does not equal the release record $($release.zip_sha256); STOP" }
New-Item -ItemType Directory -Path (Join-Path $payload 'guest') | Out-Null
Copy-Item -LiteralPath $zip -Destination $payload
Copy-Item -LiteralPath $rec -Destination $payload
Copy-Item -LiteralPath $guest -Destination (Join-Path $payload 'guest')
$readme = @"
JARVIS package disc for Stage 6 Gate 17. Release $ReleaseId (candidate; FINAL selection is the owner's act, and this disc does not make it FINAL).
Contents: JARVIS-$ReleaseId.zip (the release, sha256 $zipHash), JARVIS-$ReleaseId.release.json (its release record), guest\Invoke-Gate17.ps1, PAYLOAD-MANIFEST.json (SHA-256 of every file).
Inside the VM (account jarvis-s6-guest), with the egress folder mapped as Z: and this disc at drive <disc>:
  powershell -NoProfile -ExecutionPolicy Bypass -File <disc>:\guest\Invoke-Gate17.ps1 -Phase Install -Package <disc>:\ -Evidence Z:\
Nothing on this disc contains credentials. Built by the owner with tools\New-PackageIso.ps1 (New-Gate17PackageDisc.ps1).
"@
[IO.File]::WriteAllText((Join-Path $payload 'README.txt'), $readme, (New-Object Text.UTF8Encoding $false))
& $builder -Payload $payload -Out $out -Label JARVIS_PKG
Write-Host ''
Write-Host "Package disc: $out"
Get-ChildItem -LiteralPath $Media | Where-Object { $_.Name -like "JARVIS-PACKAGE-$ReleaseId*" } | ForEach-Object { "{0}  {1:N0} bytes" -f $_.Name, $_.Length }
