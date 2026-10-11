param([int]$Rate=0,[int]$Count=200000,[int]$Padding=220,[switch]$Raw,[int]$Batch=1)
$ErrorActionPreference='Stop'
Add-Type -Path @((Join-Path $PSScriptRoot 'AuthoritativeEvents.cs'),(Join-Path $PSScriptRoot 'WriterTiming.cs'),(Join-Path $PSScriptRoot 'WriterBench.cs'))
$run=Join-Path $PSScriptRoot ('writer-'+[guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($run)
Write-Output $run
if($Raw){[WriterBench]::Raw($run)}else{[WriterBench]::Run($run,$Rate,$Count,$Padding,$Batch)}
