$ErrorActionPreference='Stop'
Add-Type -Path @((Join-Path $PSScriptRoot 'AuthoritativeEvents.cs'),(Join-Path $PSScriptRoot 'WriterTiming.cs'),(Join-Path $PSScriptRoot 'WriterFaults.cs'),(Join-Path $PSScriptRoot 'EventTap.cs'),(Join-Path $PSScriptRoot 'LoopTiming.cs'),(Join-Path $PSScriptRoot 'IntegratedStreamTests.cs'))
$run=Join-Path $PSScriptRoot ('focused-'+[guid]::NewGuid().ToString('N'));[void][IO.Directory]::CreateDirectory($run)
[WriterFaults]::Run($run)
$tap=Join-Path $run 'actual-tap';[void][IO.Directory]::CreateDirectory($tap)
[IntegratedStreamTests]::Run($tap,12000,0)
Write-Output $run
