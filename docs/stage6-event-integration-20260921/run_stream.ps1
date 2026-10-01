param([Parameter(Mandatory=$true)][string]$Code,[Parameter(Mandatory=$true)][string]$Run,[int]$Events=12000,[int]$Padding=0)
$ErrorActionPreference='Stop'
if($Code -notmatch '^D:\\JARVIS-STAGE6-LIVE\\[a-f0-9]{32}\\code$'){throw 'Invalid candidate path'}
$root=Join-Path $Code $Run
if(!(Test-Path -LiteralPath $root -PathType Container)){throw 'Prepared fresh run required'}
$env:TEMP=Join-Path $root 'temp';$env:TMP=$env:TEMP
Add-Type -Path @((Join-Path $Code 'AuthoritativeEvents.cs'),(Join-Path $Code 'LoopTiming.cs'),(Join-Path $Code 'EventTap.cs'),(Join-Path $Code 'IntegratedStreamTests.cs'))
[IntegratedStreamTests]::Run($root,$Events,$Padding)
if([EventTap]::StreamFailure){exit 1}
