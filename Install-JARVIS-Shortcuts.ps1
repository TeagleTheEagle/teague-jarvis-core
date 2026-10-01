$ErrorActionPreference = 'Stop'
$root = (Resolve-Path $PSScriptRoot).Path
$launcher = Join-Path $root 'Start-Desktop.ps1'
if (!(Test-Path -LiteralPath $launcher)) { throw 'JARVIS desktop launcher was not found.' }
$shell = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')
$startup = [Environment]::GetFolderPath('Startup')
function New-JarvisShortcut([string]$path, [bool]$login) {
  $s = $shell.CreateShortcut($path)
  $s.TargetPath = (Get-Command powershell.exe).Source
  $s.Arguments = '-NoProfile -File "' + $launcher + '"' + $(if($login){' -LoginLaunch'}else{''})
  $s.WindowStyle = 7
  $s.WorkingDirectory = $root
  $s.Description = 'JARVIS personal assistant desktop app'
  $s.Save()
}
New-JarvisShortcut (Join-Path $desktop 'JARVIS Desktop.lnk') $false
New-JarvisShortcut (Join-Path $startup 'JARVIS Desktop.lnk') $true
Write-Host 'Created the JARVIS Desktop shortcut and optional login-start shortcut.'
