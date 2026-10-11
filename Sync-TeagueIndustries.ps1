param(
    [string]$Destination = 'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE'
)

$ErrorActionPreference = 'Stop'
$Source = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not (Test-Path -LiteralPath $Destination)) {
    throw "Teague Industries folder not found: $Destination"
}

# Project records and source snapshots belong in the Teague folder. Runtime-heavy
# directories, generated databases, caches and credentials stay local.
$snapshot = Join-Path $Destination '06 SOURCE RECORDS\JARVIS SOURCE SNAPSHOT'
$docs = Join-Path $Destination '06 SOURCE RECORDS\JARVIS DOCUMENTATION'
New-Item -ItemType Directory -Force -Path $snapshot,$docs | Out-Null

$excludeDirs = @('.git','.venv','data','build','release','review','__pycache__','node_modules','.pnpm-store','.electron-cache')
$excludeFiles = @('.env','.env.*','*.db','*.sqlite','*.sqlite3','*.pem','*.key','*.token')

function Copy-Tree($relative, $target) {
    $from = Join-Path $Source $relative
    if (-not (Test-Path -LiteralPath $from)) { return }
    $args = @($from,$target,'/E','/NFL','/NDL','/NJH','/NJS','/NP','/R:1','/W:1')
    foreach($dir in $excludeDirs){ $args += '/XD'; $args += (Join-Path $from $dir) }
    foreach($file in $excludeFiles){ $args += '/XF'; $args += (Join-Path $from $file) }
    & robocopy @args | Out-Null
    if ($LASTEXITCODE -gt 7) { throw "Snapshot copy failed for $relative (robocopy code $LASTEXITCODE)." }
}

Copy-Tree 'static' (Join-Path $snapshot 'static')
Copy-Tree 'phone' (Join-Path $snapshot 'phone')
Copy-Tree 'wearables' (Join-Path $snapshot 'wearables')
Copy-Tree 'ios' (Join-Path $snapshot 'ios')
Copy-Tree 'desktop' (Join-Path $snapshot 'desktop')
Copy-Tree 'docs' (Join-Path $docs 'docs')

Get-ChildItem -LiteralPath $Source -File -Force |
    Where-Object { $_.Extension -in '.py','.md','.ps1','.cmd','.json' -and $_.Name -notmatch '^\.env' } |
    Copy-Item -Destination $snapshot -Force

$manifest = [ordered]@{
    generated_at = (Get-Date).ToUniversalTime().ToString('o')
    source = $Source
    destination = $Destination
    excluded = @('.env', 'credentials', 'runtime data', 'dependency caches')
    purpose = 'Teague Industries source and project-record snapshot; local runtime remains authoritative for execution.'
}
$manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $Destination 'DOCUMENT MANIFEST.json') -Encoding UTF8
Write-Output "Teague Industries snapshot written to $Destination"
