function Set-J6RuntimeScope {
 $p=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'shared-runtime-v4.json') -Raw|ConvertFrom-Json
 foreach($n in @('PATH','PSModulePath','PYTHONPATH','PYTHONHOME','TEMP','TMP')) {
  foreach($v in ([Environment]::GetEnvironmentVariable($n) -split ';')) {
   if($v -match '(?i)JARVIS-STAGE6' -and !$v.StartsWith($PSScriptRoot+'\',[StringComparison]::OrdinalIgnoreCase) -and $v -cne $PSScriptRoot){throw 'Old workspace environment'}
  }
 }
 $env:PSModulePath=$p.moduleRoots -join ';'
 $env:PYTHONNOUSERSITE='1'
 Import-Module -Name (Join-Path $PSHOME 'Modules\CimCmdlets\CimCmdlets.psd1') -ErrorAction Stop
}
