<#
.SYNOPSIS
Gate 16R step 8 rerun: run BY THE OWNER, own account, non-elevated. Builds the second tools disc
JARVIS-TOOLS-v2.iso from a copy of the first disc's payload with the corrected guest check script
(tools\guest\Invoke-Gate17.ps1 from the repo: Microsoft Store app execution aliases are recorded, not counted
as development tools; saved-credential targets listed), hash-verified by tools\New-PackageIso.ps1, and copies
the disc and its hash record into D:\JARVIS-S6-FRESHVM\media. The first disc and its payload are not touched.
Writes evidence\gate16r-20261002\step8-tools-disc-v2.json.
#>
param(
    [string] $Repo = 'C:\Users\jonny\JARVIS-claude-workspace\repo',
    [string] $Media = 'D:\JARVIS-release-work\stage6-media',
    [string] $Dest = 'D:\JARVIS-S6-FRESHVM\media',
    [string] $Evidence = 'D:\JARVIS-S6-FRESHVM\evidence\gate16r-20261002'
)
$ErrorActionPreference = 'Stop'
if (([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Elevated session: STOP' }
function Sha256($p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower() }
$src = Join-Path $Media 'tools-payload'; $payload = Join-Path $Media 'tools-payload-v2'; $out = Join-Path $Media 'JARVIS-TOOLS-v2.iso'
$guest = Join-Path $Repo 'tools\guest\Invoke-Gate17.ps1'; $builder = Join-Path $Repo 'tools\New-PackageIso.ps1'
foreach ($p in $src, $guest, $builder) { if (-not (Test-Path -LiteralPath $p)) { throw "missing: $p" } }
foreach ($p in $payload, $out, (Join-Path $Dest 'JARVIS-TOOLS-v2.iso')) { if (Test-Path -LiteralPath $p) { throw "already exists, not touched: $p" } }
Copy-Item -LiteralPath $src -Destination $payload -Recurse
Copy-Item -LiteralPath $guest -Destination (Join-Path $payload 'guest\Invoke-Gate17.ps1') -Force
$note = "`r`nv2 (2026-10-02): guest\Invoke-Gate17.ps1 corrected after step 8 run 1: Microsoft Store app execution aliases (zero-byte stubs under AppData\Local\Microsoft\WindowsApps) are recorded separately, not counted as development tools; saved-credential targets are listed. Nothing else changed.`r`n"
[IO.File]::AppendAllText((Join-Path $payload 'README.txt'), $note, (New-Object Text.UTF8Encoding $false))
& $builder -Payload $payload -Out $out -Label JARVIS_TOOLS
$record = Get-Content -LiteralPath "$out.sha256.json" -Raw | ConvertFrom-Json
Copy-Item -LiteralPath $out -Destination $Dest
Copy-Item -LiteralPath "$out.sha256.json" -Destination $Dest
$copyHash = Sha256 (Join-Path $Dest 'JARVIS-TOOLS-v2.iso')
if ($copyHash -ne $record.sha256) { throw "copy hash $copyHash differs from the build record $($record.sha256); STOP" }
$result = [ordered]@{
    schema = 'stage6-gate16r-step8-tools-disc-v2-v1'; utc = (Get-Date).ToUniversalTime().ToString('o'); performed_by = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    reason = 'step 8 run 1 (gate17-20261002-071120) reported FAIL on the Microsoft Store python.exe app execution alias, a harness false positive; the corrected guest script ships on a second tools disc; the first disc is unchanged'
    guest_script_sha256 = (Sha256 $guest); iso = $out; iso_sha256 = $record.sha256; iso_bytes = $record.bytes; payload_files = $record.payload_files; readback = $record.readback
    copy = (Join-Path $Dest 'JARVIS-TOOLS-v2.iso'); copy_sha256 = $copyHash
    first_disc_unchanged = ((Sha256 (Join-Path $Dest 'JARVIS-TOOLS.iso')) -eq '0c0d5de3b93f8338ffb3b8e0ef608cb21a935b61863c56a68ecef0d972fcde4b')
    next = 'validation session: Devices > Optical Drives > SATA Port 2 > Choose a Disk File > JARVIS-TOOLS-v2.iso; rerun the step 8 command (run 2); run 1 kept'
}
[IO.File]::WriteAllText((Join-Path $Evidence 'step8-tools-disc-v2.json'), (ConvertTo-Json -InputObject $result -Depth 3), (New-Object Text.UTF8Encoding $false))
ConvertTo-Json -InputObject $result -Depth 3
