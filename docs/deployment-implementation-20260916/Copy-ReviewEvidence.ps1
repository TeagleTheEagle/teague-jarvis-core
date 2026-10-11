param([Parameter(Mandatory=$true)][string]$Destination)
$ErrorActionPreference = 'Stop'
$taskManifestPath = Join-Path $PSScriptRoot 'archive-manifest.json'
$taskManifest = Get-Content -LiteralPath $taskManifestPath -Raw | ConvertFrom-Json
$taskExpected = 'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\DEPLOYMENT TEST 20260916'
if ([IO.Path]::GetFullPath($Destination) -ne $taskExpected) { throw 'Unexpected archive destination' }
if (Test-Path -LiteralPath $Destination) { throw 'Archive destination already exists; preserve it' }
New-Item -ItemType Directory -Path $Destination | Out-Null
$taskCopied = @()
foreach ($taskEntry in $taskManifest.files) {
    $taskSource = [IO.Path]::GetFullPath((Join-Path $taskManifest.source_root $taskEntry.path))
    $taskTarget = [IO.Path]::GetFullPath((Join-Path $Destination $taskEntry.path))
    if (-not $taskSource.StartsWith($taskManifest.source_root+'\',[StringComparison]::OrdinalIgnoreCase) -or -not $taskTarget.StartsWith($Destination+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Archive path escape' }
    if ((Get-FileHash -LiteralPath $taskSource -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskEntry.sha256) { throw 'Source changed after manifest' }
    New-Item -ItemType Directory -Path (Split-Path -Parent $taskTarget) -Force | Out-Null
    Copy-Item -LiteralPath $taskSource -Destination $taskTarget
    if ((Get-FileHash -LiteralPath $taskTarget -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskEntry.sha256) { throw 'Copied hash mismatch' }
    $taskCopied += [ordered]@{ path=$taskEntry.path; sha256=$taskEntry.sha256; verified=$true }
}
Copy-Item -LiteralPath $taskManifestPath -Destination (Join-Path $Destination 'archive-manifest.json')
if ((Get-FileHash -LiteralPath $taskManifestPath).Hash -ne (Get-FileHash -LiteralPath (Join-Path $Destination 'archive-manifest.json')).Hash) { throw 'Manifest copy mismatch' }
$taskReceipt = [ordered]@{ destination=$Destination; files=$taskCopied.Count; manifest_sha256=(Get-FileHash -LiteralPath $taskManifestPath).Hash.ToLowerInvariant(); verified=$true; copied=$taskCopied; production_changed=$false }
$taskReceipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'archive-receipt.json') -Encoding utf8
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'archive-receipt.json') -Destination (Join-Path $Destination 'archive-receipt.json')
if ((Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'archive-receipt.json')).Hash -ne (Get-FileHash -LiteralPath (Join-Path $Destination 'archive-receipt.json')).Hash) { throw 'Receipt mismatch' }
"Verified $($taskCopied.Count) selected files plus manifest and receipt."
