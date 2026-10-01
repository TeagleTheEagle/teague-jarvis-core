<#
.SYNOPSIS
Protected-original preservation checkpoint P0..P5 (AMENDMENT-v2 section 8), run under the
owner account, non-elevated. DRAFT FOR OWNER REVIEW. NOT TO BE RUN until the owner resumes
the route: reading the protected paths is owner-authorized per checkpoint, never inferred.

Performs ONLY the permitted reads of section 8(c): directory enumeration of both protected
paths (name, size, LastWriteTimeUtc); SHA-256 of exactly the .vbox, .vbox-prev and the
normal VirtualBox.xml; DACL reads of both roots. Plus a per-user VirtualBox process census
before and after (section 7(f)), and the installed VirtualBox version (section 7(g)). It
never boots, mounts, registers, lists through VirtualBox, modifies, repairs or hashes any
disk image. One attempt; any mismatch stops the route (no retry, no repair).

.PARAMETER Checkpoint  P0 | P1 | P2 | P3 | P4 | P5
.PARAMETER Evidence    Folder that receives <checkpoint>-<run id>\CHECKPOINT.json and inventories.
.PARAMETER Reference   A previous checkpoint folder to compare against exactly (P1..P5). P0 compares
                       against the historical constants only.
.PARAMETER OwnerAuthorized  Without this switch the script prints what it would read and exits.
#>
param(
    [Parameter(Mandatory)] [ValidateSet('P0', 'P1', 'P2', 'P3', 'P4', 'P5')] [string] $Checkpoint,
    [Parameter(Mandatory)] [string] $Evidence,
    [string] $Reference,
    [switch] $OwnerAuthorized
)
$ErrorActionPreference = 'Stop'
$ProtectedVm = 'C:\Users\jonny\VirtualBox VMs\JARVIS-CLEAN-WIN11'
$ProtectedConfig = 'C:\Users\jonny\.VirtualBox'
$Historical = @{   # AMENDMENT-v2 section 8(b), from the 2026-09-18 recorded artifacts
    vbox = '98a89e62fd19ba49dc316b6e9c902fb6ba18fe4c66ec0ba8bf20deb3a892e93c'
    vbox_prev = '9d69cc14a480aac13c9c03817aeeb4bc4d068a6fc27a81fc15ff2bc91de2c797'
    virtualbox_xml = 'f05da097d96f073a2569488a0fffc1682d7034e69069bab51b4409d88c2bdf0d'
    vm_files = 12; vm_bytes = 59665402098
}
$VBoxBinaries = 'VirtualBox.exe', 'VBoxManage.exe', 'VBoxSVC.exe', 'VBoxSDS.exe', 'VirtualBoxVM.exe', 'VBoxHeadless.exe'
$Utf8 = New-Object Text.UTF8Encoding $false

if (-not $OwnerAuthorized) {
    Write-Host "DRY: $Checkpoint would read (non-elevated, as $env:USERNAME):"
    Write-Host "  enumerate   $ProtectedVm  and  $ProtectedConfig  (name, size, LastWriteTimeUtc)"
    Write-Host "  sha256      <vm>\*.vbox, <vm>\*.vbox-prev, $ProtectedConfig\VirtualBox.xml"
    Write-Host "  dacl        both roots;  census: VirtualBox processes by owner, before and after"
    Write-Host 'Nothing was read. Re-run with -OwnerAuthorized only under the owner''s explicit checkpoint authorization.'
    exit 0
}

$runId = "$($Checkpoint.ToLower())-$((Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss'))"
$dir = Join-Path $Evidence $runId
if (Test-Path -LiteralPath $dir) { throw "Checkpoint folder already exists: $dir" }
New-Item -ItemType Directory -Path $dir | Out-Null
function Save($name, $obj) { [IO.File]::WriteAllText((Join-Path $dir "$name.json"), ($obj | ConvertTo-Json -Depth 6), $Utf8) }
function Census {
    @(Get-CimInstance Win32_Process | Where-Object { $_.Name -in $VBoxBinaries } | ForEach-Object {
        $o = Invoke-CimMethod -InputObject $_ -MethodName GetOwner
        [ordered]@{ name = $_.Name; pid = $_.ProcessId; owner = "$($o.Domain)\$($o.User)" } })
}
function Inventory($root) {
    @(Get-ChildItem -LiteralPath $root -Recurse -File -Force | Sort-Object FullName | ForEach-Object {
        [ordered]@{ path = $_.FullName.Substring($root.Length + 1); bytes = $_.Length; last_write_utc = $_.LastWriteTimeUtc.ToString('o') } })
}
function Sha256($path) { (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower() }

$result = [ordered]@{ schema = 'stage6-preservation-checkpoint-v1'; checkpoint = $Checkpoint; run_id = $runId; utc = (Get-Date).ToUniversalTime().ToString('o')
                      account = "$env:USERDOMAIN\$env:USERNAME"; elevated = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
                      status = 'INCOMPLETE'; findings = @() }
$findings = New-Object Collections.ArrayList
try {
    # 7(f): no VirtualBox binary under the owner account before any read.
    $before = Census; Save 'census-before' $before
    $ownerProcs = @($before | Where-Object { $_.owner -eq "$env:USERDOMAIN\$env:USERNAME" })
    if ($ownerProcs) { $findings.Add("VirtualBox process under the owner account before reads: $(($ownerProcs | ForEach-Object { $_.name }) -join ', ')") | Out-Null; throw 'owner-account VirtualBox process present' }

    # 7(g): installation freeze (static file metadata only; no VirtualBox is executed).
    $vbm = Get-Item -LiteralPath 'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe'
    $result.virtualbox_version = $vbm.VersionInfo.ProductVersion; $result.vboxmanage_sha256 = Sha256 $vbm.FullName

    # 8(c) permitted reads.
    $vmInv = Inventory $ProtectedVm; $cfgInv = Inventory $ProtectedConfig
    Save 'protected-vm-inventory' $vmInv; Save 'protected-config-inventory' $cfgInv
    $vbox = @(Get-ChildItem -LiteralPath $ProtectedVm -File -Force | Where-Object { $_.Extension -eq '.vbox' })
    $vboxPrev = @(Get-ChildItem -LiteralPath $ProtectedVm -File -Force | Where-Object { $_.Name -like '*.vbox-prev' })
    $xml = Join-Path $ProtectedConfig 'VirtualBox.xml'
    if ($vbox.Count -ne 1 -or $vboxPrev.Count -ne 1 -or -not (Test-Path -LiteralPath $xml)) { throw 'control files not found exactly once' }
    $hashes = [ordered]@{ vbox = Sha256 $vbox[0].FullName; vbox_prev = Sha256 $vboxPrev[0].FullName; virtualbox_xml = Sha256 $xml }
    $dacl = [ordered]@{ protected_vm = (Get-Acl -LiteralPath $ProtectedVm).Sddl; protected_config = (Get-Acl -LiteralPath $ProtectedConfig).Sddl }
    Save 'control-hashes' $hashes; Save 'dacl' $dacl
    $result.vm_files = $vmInv.Count; $result.vm_bytes = ($vmInv | Measure-Object bytes -Sum).Sum; $result.control_hashes = $hashes

    # Historical constants (every checkpoint) and exact equality with the reference checkpoint (P1..P5).
    foreach ($k in 'vbox', 'vbox_prev', 'virtualbox_xml') { if ($hashes[$k] -ne $Historical[$k]) { $findings.Add("$k hash differs from the 2026-09-18 reference") | Out-Null } }
    if ($result.vm_files -ne $Historical.vm_files -or $result.vm_bytes -ne $Historical.vm_bytes) { $findings.Add("protected VM inventory is $($result.vm_files) files / $($result.vm_bytes) bytes, reference 12 / 59665402098") | Out-Null }
    if ($Reference) {
        foreach ($pair in @(@('protected-vm-inventory', $vmInv), @('protected-config-inventory', $cfgInv))) {
            $ref = Get-Content -LiteralPath (Join-Path $Reference "$($pair[0]).json") -Raw
            if ($ref -ne ($pair[1] | ConvertTo-Json -Depth 6)) { $findings.Add("$($pair[0]) differs from reference $Reference") | Out-Null }
        }
        $refDacl = Get-Content -LiteralPath (Join-Path $Reference 'dacl.json') -Raw | ConvertFrom-Json
        if ($refDacl.protected_vm -ne $dacl.protected_vm -or $refDacl.protected_config -ne $dacl.protected_config) { $findings.Add('DACL differs from reference') | Out-Null }
        $refCp = Get-Content -LiteralPath (Join-Path $Reference 'CHECKPOINT.json') -Raw | ConvertFrom-Json
        if ($refCp.virtualbox_version -ne $result.virtualbox_version -or $refCp.vboxmanage_sha256 -ne $result.vboxmanage_sha256) { $findings.Add('VirtualBox installation changed since reference (7(g) freeze)') | Out-Null }
    } elseif ($Checkpoint -ne 'P0') { throw 'P1..P5 require -Reference (the previous checkpoint folder)' }

    $after = Census; Save 'census-after' $after
    if (@($after | Where-Object { $_.owner -eq "$env:USERDOMAIN\$env:USERNAME" })) { $findings.Add('VirtualBox process under the owner account after reads') | Out-Null }
    $result.findings = @($findings)
    $result.status = if ($findings.Count -eq 0) { 'PASS' } elseif ($Checkpoint -eq 'P0') { 'P0_MISMATCH_PRE_EXISTING_STOP' } else { 'PRESERVATION_FAILURE_STOP' }
} catch {
    $result.findings = @($findings) + @("stopped: $($_.Exception.Message)")
    $result.status = 'STOPPED'
}
Save 'CHECKPOINT' $result
$result | ConvertTo-Json -Depth 4
if ($result.status -ne 'PASS') { exit 2 }
