$ErrorActionPreference='Stop'
function Assert-LiveCode {
 $p=[IO.Path]::GetFullPath($PSScriptRoot)
 if($p -notmatch '^D:\\JARVIS-STAGE6-LIVE\\[a-f0-9]{32}\\code$'){throw 'D-only bounded code workspace required'}
 $item=Get-Item -LiteralPath $p
 while($null -ne $item){if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Reparse path forbidden'};$item=$item.Parent}
}
function Get-LiveRun([string]$Name) {
 Assert-LiveCode
 if($Name -notmatch '^[a-z0-9][a-z0-9-]{0,79}$'){throw 'Invalid run ID'}
 $p=Join-Path $PSScriptRoot $Name
 $item=Get-Item -LiteralPath $p
 if(-not $item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Prepared non-reparse run required'}
 return $p
}
function Set-LiveTemp([string]$Root) {
 $p=Join-Path $Root 'temp';$item=Get-Item -LiteralPath $p
 if(-not $item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Prepared D temp required'}
 $env:TEMP=$p;$env:TMP=$p
}
