<#
.SYNOPSIS
Builds a further tools disc JARVIS-TOOLS-v<N>.iso: run BY THE OWNER, own account, non-elevated. Takes a copy of
the first disc's payload, puts the current guest check script (tools\guest\Invoke-Gate17.ps1 from the repo) into
it, images it hash-verified with tools\New-PackageIso.ps1, and copies the disc and its hash record into
D:\JARVIS-S6-FRESHVM\media. Earlier discs and payloads are not touched.
Writes evidence\gate16r-20261002\step8-tools-disc-v<N>.json.
#>
param(
    [Parameter(Mandatory)] [int] $Version,
    [Parameter(Mandatory)] [string] $Reason,
    [string] $Repo = 'C:\Users\jonny\JARVIS-claude-workspace\repo',
    [string] $Media = 'D:\JARVIS-release-work\stage6-media',
    [string] $Dest = 'D:\JARVIS-S6-FRESHVM\media',
    [string] $Evidence = 'D:\JARVIS-S6-FRESHVM\evidence\gate16r-20261002'
)
$ErrorActionPreference = 'Stop'
if (([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Elevated session: STOP' }
if ($Version -lt 3) { throw 'versions 1 and 2 already exist' }
function Sha256($p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower() }
$name = "JARVIS-TOOLS-v$Version.iso"
$src = Join-Path $Media 'tools-payload'; $payload = Join-Path $Media "tools-payload-v$Version"; $out = Join-Path $Media $name
$guest = Join-Path $Repo 'tools\guest\Invoke-Gate17.ps1'; $builder = Join-Path $Repo 'tools\New-PackageIso.ps1'
foreach ($p in $src, $guest, $builder) { if (-not (Test-Path -LiteralPath $p)) { throw "missing: $p" } }
foreach ($p in $payload, $out, (Join-Path $Dest $name)) { if (Test-Path -LiteralPath $p) { throw "already exists, not touched: $p" } }
Copy-Item -LiteralPath $src -Destination $payload -Recurse
Copy-Item -LiteralPath $guest -Destination (Join-Path $payload 'guest\Invoke-Gate17.ps1') -Force
$note = "`r`nv$Version ($((Get-Date).ToUniversalTime().ToString('yyyy-MM-dd'))): guest\Invoke-Gate17.ps1 replaced by the current repo version. $Reason`r`n"
[IO.File]::AppendAllText((Join-Path $payload 'README.txt'), $note, (New-Object Text.UTF8Encoding $false))
& $builder -Payload $payload -Out $out -Label JARVIS_TOOLS
$record = Get-Content -LiteralPath "$out.sha256.json" -Raw | ConvertFrom-Json
Copy-Item -LiteralPath $out -Destination $Dest
Copy-Item -LiteralPath "$out.sha256.json" -Destination $Dest
$copyHash = Sha256 (Join-Path $Dest $name)
if ($copyHash -ne $record.sha256) { throw "copy hash $copyHash differs from the build record $($record.sha256); STOP" }
$result = [ordered]@{
    schema = 'stage6-gate16r-tools-disc-v1'; utc = (Get-Date).ToUniversalTime().ToString('o'); performed_by = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    version = $Version; reason = $Reason
    guest_script_sha256 = (Sha256 $guest); iso = $out; iso_sha256 = $record.sha256; iso_bytes = $record.bytes; payload_files = $record.payload_files; readback = $record.readback
    copy = (Join-Path $Dest $name); copy_sha256 = $copyHash
    earlier_discs = @(Get-ChildItem -LiteralPath $Dest -Filter 'JARVIS-TOOLS*.iso' | Where-Object { $_.Name -ne $name } | ForEach-Object { [ordered]@{ name = $_.Name; sha256 = (Sha256 $_.FullName) } })
    next = "validation session: Devices > Optical Drives > SATA Port 2 > Choose a Disk File > $name; rerun the step 8 command; earlier runs kept"
}
[IO.File]::WriteAllText((Join-Path $Evidence "step8-tools-disc-v$Version.json"), (ConvertTo-Json -InputObject $result -Depth 3), (New-Object Text.UTF8Encoding $false))
ConvertTo-Json -InputObject $result -Depth 3
