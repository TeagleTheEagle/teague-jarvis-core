$ErrorActionPreference = 'Stop'
$campaignRoot = $PSScriptRoot
$bundleRoot = Join-Path $campaignRoot 'selected-records'
$manifestFile = Join-Path $campaignRoot 'manifest.json'
$archiveRoot = 'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\CANONICAL CORE STAGE 4\HUMAN DENIAL DRIVER CORRECTION 2026-09-15'
$manifest = Get-Content -LiteralPath $manifestFile -Raw | ConvertFrom-Json
$prepared = @()
foreach ($entry in $manifest.files) {
    $sourceFile = [IO.Path]::GetFullPath((Join-Path $bundleRoot $entry.path))
    $targetFile = [IO.Path]::GetFullPath((Join-Path $archiveRoot $entry.path))
    if (-not $sourceFile.StartsWith($bundleRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Source escape' }
    if (-not $targetFile.StartsWith($archiveRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Destination escape' }
    $sourceHash = (Get-FileHash -LiteralPath $sourceFile -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($sourceHash -ne $entry.sha256) { throw "Prepared hash mismatch: $($entry.path)" }
    if (Test-Path -LiteralPath $targetFile) {
        if ((Get-FileHash -LiteralPath $targetFile -Algorithm SHA256).Hash.ToLowerInvariant() -ne $sourceHash) {
            throw "Existing archive differs; refusing overwrite: $($entry.path)"
        }
    }
    $prepared += [pscustomobject]@{ source = $sourceFile; target = $targetFile; path = $entry.path; sha256 = $sourceHash }
}
# No recursive copy, deletion, production access or runtime execution.
$verified = @()
foreach ($item in $prepared) {
    $targetDirectory = Split-Path -Parent $item.target
    New-Item -ItemType Directory -Path $targetDirectory -Force | Out-Null
    if (-not (Test-Path -LiteralPath $item.target)) { Copy-Item -LiteralPath $item.source -Destination $item.target }
    $actual = (Get-FileHash -LiteralPath $item.target -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $item.sha256) { throw "Archive hash mismatch: $($item.path)" }
    $verified += [pscustomobject]@{ path = $item.path; sha256 = $actual; matched = $true }
}
$manifestHash = (Get-FileHash -LiteralPath $manifestFile -Algorithm SHA256).Hash.ToLowerInvariant()
$archiveManifest = Join-Path $archiveRoot 'PACKAGE-MANIFEST.json'
if (Test-Path -LiteralPath $archiveManifest) {
    if ((Get-FileHash -LiteralPath $archiveManifest -Algorithm SHA256).Hash.ToLowerInvariant() -ne $manifestHash) { throw 'Existing manifest differs' }
} else { Copy-Item -LiteralPath $manifestFile -Destination $archiveManifest }
if ((Get-FileHash -LiteralPath $archiveManifest -Algorithm SHA256).Hash.ToLowerInvariant() -ne $manifestHash) { throw 'Manifest copy mismatch' }
$proof = [ordered]@{
    timestamp_utc = (Get-Date).ToUniversalTime().ToString('o')
    destination = $archiveRoot
    files = $verified.Count
    all_matched = $true
    manifest_sha256 = $manifestHash
    production_changed = $false
    acceptance_commit_created = $false
    entries = $verified
}
$proofFile = Join-Path $campaignRoot 'archive-verification.json'
$proof | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $proofFile -Encoding UTF8
$archiveProof = Join-Path $archiveRoot 'ARCHIVE-VERIFICATION.json'
if (Test-Path -LiteralPath $archiveProof) { throw 'Existing verification preserved; do not overwrite' }
Copy-Item -LiteralPath $proofFile -Destination $archiveProof
if ((Get-FileHash -LiteralPath $proofFile).Hash -ne (Get-FileHash -LiteralPath $archiveProof).Hash) { throw 'Verification copy mismatch' }
[pscustomobject]@{ files = $verified.Count; all_matched = $true; destination = $archiveRoot; manifest_sha256 = $manifestHash } | ConvertTo-Json
