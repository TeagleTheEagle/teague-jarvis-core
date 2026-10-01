<#
.SYNOPSIS
Write a read-only ISO from a payload folder, with every file's SHA-256 recorded inside and
the ISO's own SHA-256 beside it. Stage 6 packages enter the acceptance VM only this way
(AMENDMENT-v2 section 6(e)). Uses Windows' built-in IMAPI2; no installation, no elevation.

.EXAMPLE
tools\New-PackageIso.ps1 -Payload D:\JARVIS-release-work\iso-payload -Out D:\JARVIS-release-work\JARVIS-package.iso -Label JARVIS_PKG
#>
param(
    [Parameter(Mandatory)] [string] $Payload,
    [Parameter(Mandatory)] [string] $Out,
    [string] $Label = 'JARVIS_PKG'
)
$ErrorActionPreference = 'Stop'
$Payload = (Resolve-Path -LiteralPath $Payload).Path
if (Test-Path -LiteralPath $Out) { throw "Refusing to overwrite existing ISO: $Out" }
if (-not (Get-ChildItem -LiteralPath $Payload -Recurse -File)) { throw "Payload folder is empty: $Payload" }

# 1. Payload manifest (path, bytes, sha256) written into the payload itself, then imaged.
$files = Get-ChildItem -LiteralPath $Payload -Recurse -File | Where-Object { $_.Name -ne 'PAYLOAD-MANIFEST.json' } | Sort-Object FullName
$entries = foreach ($f in $files) {
    [ordered]@{ path = $f.FullName.Substring($Payload.Length + 1).Replace('\', '/'); bytes = $f.Length; sha256 = (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash.ToLower() }
}
$manifest = [ordered]@{ schema = 'jarvis-package-iso-payload-v1'; created_utc = (Get-Date).ToUniversalTime().ToString('o'); label = $Label; files = @($entries) }
$manifestPath = Join-Path $Payload 'PAYLOAD-MANIFEST.json'
[IO.File]::WriteAllText($manifestPath, ($manifest | ConvertTo-Json -Depth 5), (New-Object Text.UTF8Encoding $false))

# 2. Image it (UDF, single session) through IMAPI2FS; copy the COM IStream with a small compiled helper.
Add-Type -TypeDefinition @'
using System; using System.IO; using System.Runtime.InteropServices; using System.Runtime.InteropServices.ComTypes;
public static class IsoStreamWriter {
  public static long Write(object stream, string path) {
    IStream s = (IStream)stream; long total = 0;
    using (var f = File.Create(path)) {
      byte[] buf = new byte[1 << 20]; IntPtr pread = Marshal.AllocHGlobal(4);
      try { int read; do { s.Read(buf, buf.Length, pread); read = Marshal.ReadInt32(pread); f.Write(buf, 0, read); total += read; } while (read == buf.Length); }
      finally { Marshal.FreeHGlobal(pread); }
    }
    return total;
  }
}
'@
$image = New-Object -ComObject IMAPI2FS.MsftFileSystemImage
$image.FileSystemsToCreate = 4        # UDF only: files over 4 GiB and long names are fine
$image.UDFRevision = 0x102
$image.VolumeName = $Label
$image.Root.AddTree($Payload, $false)
$result = $image.CreateResultImage()
$written = [IsoStreamWriter]::Write($result.ImageStream, $Out)

# 3. Record the ISO's own hash beside it; re-read the image to prove it mounts and matches.
$isoHash = (Get-FileHash -LiteralPath $Out -Algorithm SHA256).Hash.ToLower()
$record = [ordered]@{ iso = (Split-Path -Leaf $Out); bytes = (Get-Item -LiteralPath $Out).Length; sha256 = $isoHash; label = $Label; payload_files = $entries.Count; payload_manifest_sha256 = (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLower() }
$mounted = Mount-DiskImage -ImagePath $Out -PassThru
try {
    $drive = ($mounted | Get-Volume).DriveLetter + ':\'
    $bad = foreach ($e in $entries) {
        $p = Join-Path $drive $e.path
        if (-not (Test-Path -LiteralPath $p) -or (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower() -ne $e.sha256) { $e.path }
    }
    $record.readback = if ($bad) { "MISMATCH: $($bad -join ', ')" } else { 'every payload file read back from the mounted ISO with its recorded SHA-256' }
} finally { Dismount-DiskImage -ImagePath $Out | Out-Null }
if ($record.readback -like 'MISMATCH*') { throw $record.readback }
[IO.File]::WriteAllText("$Out.sha256.json", ($record | ConvertTo-Json), (New-Object Text.UTF8Encoding $false))
$record | ConvertTo-Json
