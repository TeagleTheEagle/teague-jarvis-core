<#
.SYNOPSIS
Create the Gate 16R acceptance VM exactly as AMENDMENT-v2 section 6(d) and v3 D4 require.
Run BY THE OWNER in the jarvis-s6-val session (never under the owner account), after
VBOX_USER_HOME is set for that account and the folders of step 4 exist. Every command is
VBoxManage under that account; the GUI equivalent is noted in comments. Refuses to run as
any other user, elevated, or with the wrong VirtualBox home. Records showvminfo and the
.vbox hash into the evidence folder.
#>
param(
    [string] $Name = 'JARVIS-S6-FRESH',
    [string] $Root = 'D:\JARVIS-S6-FRESHVM',
    [string] $WindowsIso = 'D:\JARVIS-S6-FRESHVM\media\Win11_25H2_English_x64_v2.iso',
    [string] $UnattendIso = 'D:\JARVIS-S6-FRESHVM\media\UNATTEND.iso',
    [Parameter(Mandatory)] [string] $Evidence
)
$ErrorActionPreference = 'Stop'
if ($env:USERNAME -ne 'jarvis-s6-val') { throw "Run this in the jarvis-s6-val session, not as $env:USERNAME" }
if (([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Elevated session: STOP' }
if ($env:VBOX_USER_HOME -ne "$Root\vbox-home") { throw "VBOX_USER_HOME must be $Root\vbox-home for this account" }
$vbm = 'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe'
foreach ($p in $WindowsIso, $UnattendIso, "$Root\machines", "$Root\evidence\guest-egress-01") { if (-not (Test-Path -LiteralPath $p)) { throw "missing: $p" } }
New-Item -ItemType Directory -Path $Evidence -Force | Out-Null
function VBM { param([Parameter(ValueFromRemainingArguments)] $a) & $vbm @a; if ($LASTEXITCODE) { throw "VBoxManage failed: $($a -join ' ')" } }

# New VM, new disk; no clone, import, reused .vbox, snapshot or disk from any existing VM.
VBM createvm --name $Name --ostype Windows11_64 --basefolder "$Root\machines" --register
# System: 4 vCPU, 8 GiB, EFI with TPM 2.0 (GUI: System > Motherboard: EFI, TPM 2.0, Secure Boot).
VBM modifyvm $Name --cpus 4 --memory 8192 --vram 128 --graphicscontroller vboxsvga --firmware efi --tpm-type 2.0 --boot1 dvd --boot2 disk --boot3 none --boot4 none
# Secure Boot: initialise the UEFI variable store and enrol the Microsoft and Oracle keys (the GUI's "Enable Secure Boot" does the same).
VBM modifynvram $Name inituefivarstore
VBM modifynvram $Name enrollmssignatures
VBM modifynvram $Name enrollorclpk
# Networking: NAT only, localhost not reachable from the guest; nothing else.
VBM modifyvm $Name --nic1 nat --nat-localhostreachable1 off --nic2 none --nic3 none --nic4 none
# Isolation: no clipboard, no drag-and-drop, no USB passthrough, no audio device (v3 D6: offline STT uses synthetic speech, no device needed).
VBM modifyvm $Name --clipboard-mode disabled --draganddrop disabled --usb-ohci off --usb-ehci off --usb-xhci off --audio-driver none
# Storage: one new 96 GiB dynamic disk; optical drives for the Windows ISO and the answer-file ISO (Guest Additions ISO is attached later, step 7).
VBM createmedium disk --filename "$Root\machines\$Name\$Name.vdi" --size 98304 --format VDI --variant Standard
VBM storagectl $Name --name SATA --add sata --controller IntelAhci --portcount 4 --bootable on
VBM storageattach $Name --storagectl SATA --port 0 --device 0 --type hdd --medium "$Root\machines\$Name\$Name.vdi"
VBM storageattach $Name --storagectl SATA --port 1 --device 0 --type dvddrive --medium $WindowsIso
VBM storageattach $Name --storagectl SATA --port 2 --device 0 --type dvddrive --medium $UnattendIso
# The single evidence egress: one shared folder, not auto-mounted, mapped only to guest-egress-01.
VBM sharedfolder add $Name --name guest-egress-01 --hostpath "$Root\evidence\guest-egress-01"

# Identity record for section 6(i): machine-readable info, .vbox path and hash, registration location.
$info = & $vbm showvminfo $Name --machinereadable
[IO.File]::WriteAllLines((Join-Path $Evidence 'showvminfo.txt'), $info)
$vbox = ($info | Where-Object { $_ -like 'CfgFile=*' }) -replace '^CfgFile="(.*)"$', '$1'
$uuid = ($info | Where-Object { $_ -like 'UUID=*' }) -replace '^UUID="(.*)"$', '$1'
$registry = Join-Path $env:VBOX_USER_HOME 'VirtualBox.xml'
$record = [ordered]@{
    schema = 'stage6-fresh-vm-creation-v1'; utc = (Get-Date).ToUniversalTime().ToString('o'); account = $env:USERNAME
    vm_name = $Name; vm_uuid = $uuid; vbox_file = $vbox; vbox_sha256 = (Get-FileHash -LiteralPath $vbox -Algorithm SHA256).Hash.ToLower()
    registered_in = $registry; registry_mentions_vm = ((Get-Content -LiteralPath $registry -Raw) -match [regex]::Escape($vbox))
    windows_iso_sha256 = (Get-FileHash -LiteralPath $WindowsIso -Algorithm SHA256).Hash.ToLower(); unattend_iso_sha256 = (Get-FileHash -LiteralPath $UnattendIso -Algorithm SHA256).Hash.ToLower()
    virtualbox_version = (& $vbm --version)
}
[IO.File]::WriteAllText((Join-Path $Evidence 'vm-creation.json'), ($record | ConvertTo-Json -Depth 3), (New-Object Text.UTF8Encoding $false))
$record | ConvertTo-Json -Depth 3
