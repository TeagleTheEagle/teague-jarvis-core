$ErrorActionPreference='Stop'
$files=@('D:\JARVIS-STAGE6-LIVE\7f204e14c90a497a8476be0e9927e074\code\small_launch_v3.ps1','D:\JARVIS-STAGE6-LIVE\7f204e14c90a497a8476be0e9927e074\code\terminal_control_v3.ps1')
foreach($file in $files){$tokens=$null;$errors=$null;[void][Management.Automation.Language.Parser]::ParseFile($file,[ref]$tokens,[ref]$errors);if($errors.Count){$errors|Out-String|Write-Output;throw 'Syntax failure'}}
'SYNTAX_PASS'
