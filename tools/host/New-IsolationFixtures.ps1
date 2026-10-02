<#
.SYNOPSIS
AMENDMENT-v2 section 7(e) synthetic fixtures, created BY THE OWNER under the owner account,
non-elevated, as new objects only (BOOTSTRAP-PROPOSAL.md design). -Phase Create builds the
fixtures and writes owner-preflight.json; -Phase Postflight (after Invoke-IsolationCheck.ps1
ran in the validation session) re-hashes everything and writes owner-postflight.json. No
existing folder's permissions are changed; nothing under the protected paths is touched.

Layout (S = D:\JARVIS-S6-FRESHVM\synthetic\isolation-01):
  S, S\runner, S\aliases        owner + SYSTEM full control, jarvis-s6-val read/execute
  S\restricted(\nested)         explicit DENY jarvis-s6-val full control; owner + SYSTEM full control
  S\scratch, <Evidence>         owner + SYSTEM full control, jarvis-s6-val modify (positive control, results)
  S\restricted\sentinel.bin, S\restricted\nested\sentinel.bin   4096 fixed public bytes
  S\aliases\hardlink.bin        hard link to S\restricted\sentinel.bin
  S\aliases\junction            junction to S\restricted
#>
param(
    [Parameter(Mandatory)] [ValidateSet('Create', 'Postflight')] [string] $Phase,
    [Parameter(Mandatory)] [string] $Evidence,
    [string] $Root = 'D:\JARVIS-S6-FRESHVM\synthetic\isolation-01',
    [string] $ValidationAccount = 'jarvis-s6-val'
)
$ErrorActionPreference = 'Stop'
if (([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Elevated session: STOP (no elevation anywhere on this route)' }
$Utf8 = New-Object Text.UTF8Encoding $false
$owner = [Security.Principal.WindowsIdentity]::GetCurrent().Name
$validation = (New-Object Security.Principal.NTAccount($ValidationAccount)).Translate([Security.Principal.SecurityIdentifier])
$FA = [Security.AccessControl.FileSystemRights]::FullControl
$RX = [Security.AccessControl.FileSystemRights]::ReadAndExecute
$MOD = [Security.AccessControl.FileSystemRights]::Modify
$inherit = [Security.AccessControl.InheritanceFlags]'ContainerInherit, ObjectInherit'
function Rule($who, $rights, $type) { New-Object Security.AccessControl.FileSystemAccessRule($who, $rights, $inherit, [Security.AccessControl.PropagationFlags]::None, $type) }
function Protect($path, [Security.AccessControl.FileSystemAccessRule[]] $rules) {
    # New object: protected DACL (no inheritance from the parent), explicit rules only.
    $acl = Get-Acl -LiteralPath $path
    $acl.SetAccessRuleProtection($true, $false)
    foreach ($r in @($acl.Access)) { $null = $acl.RemoveAccessRule($r) }
    foreach ($r in $rules) { $acl.AddAccessRule($r) }
    Set-Acl -LiteralPath $path -AclObject $acl
}
function Sha256($p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower() }
function Snapshot {
    $items = foreach ($rel in '', 'runner', 'aliases', 'restricted', 'restricted\nested', 'scratch', 'restricted\sentinel.bin', 'restricted\nested\sentinel.bin', 'aliases\hardlink.bin', 'aliases\junction') {
        $p = if ($rel) { Join-Path $Root $rel } else { $Root }
        $item = Get-Item -LiteralPath $p -Force -ErrorAction SilentlyContinue
        if (-not $item) { [ordered]@{ path = $rel; exists = $false; sddl = $null; owner = $null; sha256 = $null; link_type = $null; link_target = $null }; continue }
        [ordered]@{ path = $rel; exists = $true; sddl = (Get-Acl -LiteralPath $p).Sddl; owner = (Get-Acl -LiteralPath $p).Owner
                    sha256 = $(if (-not $item.PSIsContainer -and -not $item.LinkType) { Sha256 $p } elseif ($item.LinkType -eq 'HardLink') { Sha256 $p } else { $null })
                    link_type = $item.LinkType; link_target = $(if ($item.LinkType) { @($item.Target) -join ';' } else { $null }) }
    }
    $restrictedListing = @(Get-ChildItem -LiteralPath (Join-Path $Root 'restricted') -Recurse -Force | ForEach-Object { $_.FullName.Substring($Root.Length + 1) })
    [ordered]@{ utc = (Get-Date).ToUniversalTime().ToString('o'); owner_account = $owner; validation_sid = $validation.Value; items = @($items); restricted_contents = $restrictedListing
                short_names = (cmd /c "dir /x `"$(Join-Path $Root 'restricted')`"" 2>&1 | Out-String)
                ntfs_8dot3_policy = (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem').NtfsDisable8dot3NameCreation
                fsutil_8dot3_query = (cmd /c 'fsutil 8dot3name query D:' 2>&1 | Out-String) }
}

$evidenceIsNew = -not (Test-Path -LiteralPath $Evidence)
New-Item -ItemType Directory -Path $Evidence -Force | Out-Null
if ($Phase -eq 'Create') {
    if (Test-Path -LiteralPath $Root) { throw "fixture root already exists: $Root (no overwrite, no repair)" }
    foreach ($rel in '', 'runner', 'aliases', 'restricted', 'restricted\nested', 'scratch') { New-Item -ItemType Directory -Path (Join-Path $Root $rel) | Out-Null }
    $bytes = New-Object byte[] 4096; for ($i = 0; $i -lt 4096; $i++) { $bytes[$i] = [byte]($i % 251) }   # fixed public synthetic content
    [IO.File]::WriteAllBytes((Join-Path $Root 'restricted\sentinel.bin'), $bytes)
    [IO.File]::WriteAllBytes((Join-Path $Root 'restricted\nested\sentinel.bin'), $bytes)
    New-Item -ItemType HardLink -Path (Join-Path $Root 'aliases\hardlink.bin') -Target (Join-Path $Root 'restricted\sentinel.bin') | Out-Null
    New-Item -ItemType Junction -Path (Join-Path $Root 'aliases\junction') -Target (Join-Path $Root 'restricted') | Out-Null
    $full = @((Rule 'NT AUTHORITY\SYSTEM' $FA 'Allow'), (Rule $owner $FA 'Allow'))
    Protect $Root ($full + (Rule $validation $RX 'Allow'))
    Protect (Join-Path $Root 'runner') ($full + (Rule $validation $RX 'Allow'))
    Protect (Join-Path $Root 'aliases') ($full + (Rule $validation $RX 'Allow'))
    Protect (Join-Path $Root 'restricted') (@((Rule $validation $FA 'Deny')) + $full)   # explicit deny first, inherited by its contents
    Protect (Join-Path $Root 'scratch') ($full + (Rule $validation $MOD 'Allow'))
    if ($evidenceIsNew) { Protect $Evidence ($full + (Rule $validation $MOD 'Allow')) }   # an existing evidence folder (owner-created with its own grant) is never re-permissioned
    $pre = Snapshot
    [IO.File]::WriteAllText((Join-Path $Evidence 'owner-preflight.json'), ($pre | ConvertTo-Json -Depth 5), $Utf8)
    "fixtures created under $Root; owner-preflight.json written. Next: Invoke-IsolationCheck.ps1 in the $ValidationAccount session."
} else {
    $pre = Get-Content -LiteralPath (Join-Path $Evidence 'owner-preflight.json') -Raw | ConvertFrom-Json
    $post = Snapshot
    $findings = @()
    for ($i = 0; $i -lt $pre.items.Count; $i++) {
        $a = $pre.items[$i]; $b = $post.items[$i]
        foreach ($k in 'exists', 'sddl', 'owner', 'sha256', 'link_type', 'link_target') { if ("$($a.$k)" -ne "$($b.$k)") { $findings += "$($a.path): $k changed" } }
    }
    if (($pre.restricted_contents -join '|') -ne ($post.restricted_contents -join '|')) { $findings += 'restricted contents changed (created, deleted or renamed)' }
    $post.findings = $findings; $post.status = $(if ($findings.Count -eq 0) { 'PASS' } else { 'FIRST_FAIL_STOP' })
    [IO.File]::WriteAllText((Join-Path $Evidence 'owner-postflight.json'), ($post | ConvertTo-Json -Depth 5), $Utf8)
    "$($post.status)  $($findings -join '; ')"
    if ($findings.Count) { exit 2 }
}
