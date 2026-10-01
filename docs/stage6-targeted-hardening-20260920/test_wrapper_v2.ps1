param([string]$Code)
$ErrorActionPreference='Stop';$tokens=$null;$errors=$null;$ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $Code 'timed_monitor.ps1'),[ref]$tokens,[ref]$errors)
if($errors){throw ($errors|Out-String)}
Add-Type -Path (Join-Path $Code 'LoopTiming.cs')
$fn=$ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Invoke-J6TimedStage'},$true)
if($fn.Count -ne 1){throw 'Unique timing wrapper missing'}
. ([scriptblock]::Create($fn[0].Extent.Text))
[LoopTiming]::BeginLoop()
$out=Invoke-J6TimedStage 'normal.test' {'EXPECTED'}
if($out -ne 'EXPECTED'){throw 'Wrapper did not execute supplied diagnostic stage'}
$caught=$false
try{Invoke-J6TimedStage 'exception.test' {throw 'EXPECTED FAILURE'}}catch{$caught=$true}
$spans=[LoopTiming]::SpanSnapshot()
if(!$caught -or $spans.Count -ne 2 -or @($spans|Where-Object {$_.loop -ne 1 -or $_.end -lt $_.start}).Count){throw 'Timing closure failure'}
@{status='PASS';checks=5;wrapper=(Get-Command Invoke-J6TimedStage).CommandType.ToString();spans=$spans}|ConvertTo-Json -Depth 5
