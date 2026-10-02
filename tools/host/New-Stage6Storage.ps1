<#
.SYNOPSIS
Gate 16R step 4 (AMENDMENT-v2 section 7(c),(d); v3 D4): run BY THE OWNER, own account, non-elevated.
Creates, as NEW objects only, D:\JARVIS-S6-FRESHVM\vbox-home, machines and media, grants
jarvis-s6-val modify on those three folders, copies the four discs into media\ and verifies
each copy's SHA-256 against the step-0 records (the Guest Additions disc from the installed
VirtualBox is hashed and recorded here for the first time). Writes step4-storage.json.
Nothing under C:\Users\jonny is written; E: is not used; no VirtualBox is executed.
#>
param(
    [string] $Root = 'D:\JARVIS-S6-FRESHVM',
    [string] $EvidenceRun = 'gate16r-20261002',
    [string] $Media = 'D:\JARVIS-release-work\stage6-media',
    [string] $ValidationAccount = 'jarvis-s6-val'
)
$ErrorActionPreference = 'Stop'
if (([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Elevated session: STOP' }
$validation = (New-Object Security.Principal.NTAccount($ValidationAccount)).Translate([Security.Principal.SecurityIdentifier])
function Sha256($p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower() }
function Grant($path) {
    $acl = Get-Acl -LiteralPath $path
    $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule($validation, 'Modify', 'ContainerInherit, ObjectInherit', 'None', 'Allow')))
    Set-Acl -LiteralPath $path -AclObject $acl
}
$folders = @('vbox-home', 'machines', 'media') | ForEach-Object { Join-Path $Root $_ }
foreach ($f in $folders) { if (Test-Path -LiteralPath $f) { throw "already exists, not touched: $f" } }
# Discs and the hashes recorded at step 0 (windows-iso-26H2-acquisition.json, UNATTEND.iso.sha256.json, JARVIS-TOOLS.iso.sha256.json).
$discs = @(
    @{ name = 'Windows11_Client_x64_en-us_26300_9457.iso'; from = (Join-Path $Media 'Windows11_Client_x64_en-us_26300_9457.iso'); expected = 'bd4307df32bc8af33b39ccecb1174aeb345386630f89a2b86c7a4e36b55ea650' },
    @{ name = 'UNATTEND.iso'; from = (Join-Path $Media 'UNATTEND.iso'); expected = (Get-Content -LiteralPath (Join-Path $Media 'UNATTEND.iso.sha256.json') -Raw | ConvertFrom-Json).sha256 },
    @{ name = 'JARVIS-TOOLS.iso'; from = (Join-Path $Media 'JARVIS-TOOLS.iso'); expected = (Get-Content -LiteralPath (Join-Path $Media 'JARVIS-TOOLS.iso.sha256.json') -Raw | ConvertFrom-Json).sha256 },
    @{ name = 'VBoxGuestAdditions.iso'; from = 'C:\Program Files\Oracle\VirtualBox\VBoxGuestAdditions.iso'; expected = $null }
)
foreach ($d in $discs) { if (-not (Test-Path -LiteralPath $d.from)) { throw "missing: $($d.from)" } }
foreach ($f in $folders) { New-Item -ItemType Directory -Path $f | Out-Null; Grant $f }
$media = Join-Path $Root 'media'
$copied = foreach ($d in $discs) {
    $to = Join-Path $media $d.name
    Copy-Item -LiteralPath $d.from -Destination $to
    $hash = Sha256 $to
    if ($d.expected -and $hash -ne $d.expected) { throw "hash mismatch after copy: $($d.name) ($hash, expected $($d.expected)); STOP" }
    [ordered]@{ name = $d.name; bytes = (Get-Item -LiteralPath $to).Length; sha256 = $hash; expected = $d.expected; verified = $(if ($d.expected) { $hash -eq $d.expected } else { 'recorded (first measurement)' }); source = $d.from }
}
$record = [ordered]@{
    schema = 'stage6-gate16r-step4-storage-v1'; utc = (Get-Date).ToUniversalTime().ToString('o'); created_by = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    folders = @(foreach ($f in $folders) { [ordered]@{ path = $f; acl = @((Get-Acl -LiteralPath $f).Access | ForEach-Object { "$($_.AccessControlType) $($_.IdentityReference) $($_.FileSystemRights)" }) } })
    discs = @($copied)
    virtualbox_guest_additions_version_note = 'from the installed VirtualBox 7.2.18.175117 (host frozen since P0); version recorded again from inside the guest when installed'
    next = "in the jarvis-s6-val session run step4b-set-vbox-home.cmd (sets the user-scoped VBOX_USER_HOME and re-runs the account check)"
}
[IO.File]::WriteAllText((Join-Path $Root "evidence\$EvidenceRun\step4-storage.json"), (ConvertTo-Json -InputObject $record -Depth 5), (New-Object Text.UTF8Encoding $false))
ConvertTo-Json -InputObject $record -Depth 5
