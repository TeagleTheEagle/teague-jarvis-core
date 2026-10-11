<#
.SYNOPSIS
Gate 16R step 6 preparation (AMENDMENT-v2 section 6(d); approved prompt step 6): run BY THE OWNER,
own account, non-elevated, any time before the VM is created. Creates, as a NEW object only,
D:\JARVIS-S6-FRESHVM\evidence\guest-egress-01 (the host side of the acceptance VM's single shared
folder) and grants jarvis-s6-val Modify on it. No existing folder's permissions are changed.
Writes step6-egress-folder.json into the evidence run folder.
#>
param(
    [string] $Root = 'D:\JARVIS-S6-FRESHVM',
    [string] $EvidenceRun = 'gate16r-20261002',
    [string] $ValidationAccount = 'jarvis-s6-val'
)
$ErrorActionPreference = 'Stop'
if (([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Elevated session: STOP' }
$validation = (New-Object Security.Principal.NTAccount($ValidationAccount)).Translate([Security.Principal.SecurityIdentifier])
$egress = Join-Path $Root 'evidence\guest-egress-01'
if (Test-Path -LiteralPath $egress) { throw "already exists, not touched: $egress" }
New-Item -ItemType Directory -Path $egress | Out-Null
$acl = Get-Acl -LiteralPath $egress
$acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule($validation, 'Modify', 'ContainerInherit, ObjectInherit', 'None', 'Allow')))
Set-Acl -LiteralPath $egress -AclObject $acl
$record = [ordered]@{
    schema = 'stage6-gate16r-step6-egress-folder-v1'; utc = (Get-Date).ToUniversalTime().ToString('o'); created_by = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    path = $egress; validation_sid = $validation.Value
    acl = @((Get-Acl -LiteralPath $egress).Access | ForEach-Object { "$($_.AccessControlType) $($_.IdentityReference) $($_.FileSystemRights)" })
    purpose = 'host side of the single shared folder guest-egress-01 of VM JARVIS-S6-FRESH (not auto-mounted, writable); the only evidence path out of the guest'
    next = 'P1 on the owner''s "run P1" (if not yet run), then step6-create-vm.cmd in the jarvis-s6-val session'
}
[IO.File]::WriteAllText((Join-Path $Root "evidence\$EvidenceRun\step6-egress-folder.json"), (ConvertTo-Json -InputObject $record -Depth 4), (New-Object Text.UTF8Encoding $false))
ConvertTo-Json -InputObject $record -Depth 4
