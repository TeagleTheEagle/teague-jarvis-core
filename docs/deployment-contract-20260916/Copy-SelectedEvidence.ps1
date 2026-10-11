$ErrorActionPreference = 'Stop'
$reviewRoot = $PSScriptRoot
$bundleRoot = Join-Path $reviewRoot 'selected-records'
$manifestPath = Join-Path $reviewRoot 'manifest.json'
$archiveRoot = 'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\CANONICAL CORE DEPLOYMENT CONTRACT\REVIEW 2026-09-16'
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$archiveManifest = Join-Path $archiveRoot 'PACKAGE-MANIFEST.json'
$archiveProof = Join-Path $archiveRoot 'ARCHIVE-VERIFICATION.json'
$proofPath = Join-Path $reviewRoot 'archive-verification.json'
if ((Test-Path -LiteralPath $archiveProof) -or (Test-Path -LiteralPath $proofPath)) { throw 'Preserve existing completed verification' }
$manifestHash = (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ((Test-Path -LiteralPath $archiveManifest) -and ((Get-FileHash -LiteralPath $archiveManifest).Hash.ToLowerInvariant() -ne $manifestHash)) { throw 'Existing archive manifest differs' }
$prepared = @()
foreach ($entry in $manifest.files) {
    $source = [IO.Path]::GetFullPath((Join-Path $bundleRoot $entry.path))
    $target = [IO.Path]::GetFullPath((Join-Path $archiveRoot $entry.path))
    if (-not $source.StartsWith($bundleRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Source escape' }
    if (-not $target.StartsWith($archiveRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Target escape' }
    $hash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($hash -ne $entry.sha256) { throw "Prepared source mismatch: $($entry.path)" }
    if ((Test-Path -LiteralPath $target) -and ((Get-FileHash -LiteralPath $target).Hash.ToLowerInvariant() -ne $hash)) { throw "Refuse archive overwrite: $($entry.path)" }
    $prepared += [pscustomobject]@{ source = $source; target = $target; path = $entry.path; sha256 = $hash }
}
$verified = @()
foreach ($item in $prepared) {
    New-Item -ItemType Directory -Path (Split-Path -Parent $item.target) -Force | Out-Null
    if (-not (Test-Path -LiteralPath $item.target)) { Copy-Item -LiteralPath $item.source -Destination $item.target }
    $actual = (Get-FileHash -LiteralPath $item.target -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $item.sha256) { throw "Archive hash mismatch: $($item.path)" }
    $verified += [pscustomobject]@{ path = $item.path; sha256 = $actual; matched = $true }
}
if (-not (Test-Path -LiteralPath $archiveManifest)) { Copy-Item -LiteralPath $manifestPath -Destination $archiveManifest }
if ((Get-FileHash -LiteralPath $archiveManifest).Hash.ToLowerInvariant() -ne $manifestHash) { throw 'Manifest mismatch' }
$proof = [ordered]@{
    timestamp_utc = (Get-Date).ToUniversalTime().ToString('o')
    destination = $archiveRoot
    files = $verified.Count
    all_matched = $true
    manifest_sha256 = $manifestHash
    production_changed = $false
    deployment_runtime_validated = $false
    acceptance_commit_created = $false
    entries = $verified
}
$proof | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $proofPath -Encoding UTF8
Copy-Item -LiteralPath $proofPath -Destination $archiveProof
if ((Get-FileHash -LiteralPath $proofPath).Hash -ne (Get-FileHash -LiteralPath $archiveProof).Hash) { throw 'Verification copy mismatch' }
[pscustomobject]@{files = $verified.Count; all_matched = $true; destination = $archiveRoot; manifest_sha256 = $manifestHash} | ConvertTo-Json
