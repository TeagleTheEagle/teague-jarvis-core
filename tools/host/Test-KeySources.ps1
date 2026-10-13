<#
.SYNOPSIS
Shows whether Windows holds variables with the same names as lines in the JARVIS key file, and whether the two values
are the same. Run BY THE OWNER; Claude never reads key files. Values are never printed or stored: only names and the
words SAME or DIFFERENT. Changes nothing.

Why it matters: JARVIS keeps a value that Windows already holds (server.load_env uses "set only if not set"). A
Windows variable called OPENROUTER_API_KEY therefore wins over the OPENROUTER_API_KEY line in the key file, and editing
that line changes nothing for JARVIS while the Windows variable exists.
#>
param(
    [string] $EnvFile = (Join-Path $env:LOCALAPPDATA 'JARVIS\config\.env')
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $EnvFile -PathType Leaf)) { Write-Host "STOPPED: no key file at $EnvFile"; exit 2 }
$values = @{}
foreach ($line in [IO.File]::ReadAllLines($EnvFile)) {
    $l = $line.Trim().TrimStart([char]0xFEFF)
    if (-not $l -or $l.StartsWith('#') -or -not $l.Contains('=')) { continue }
    $k, $v = $l.Split('=', 2); $k = $k.Trim()
    if ($k -cmatch '^[A-Z][A-Z0-9_]*$' -and -not $values.ContainsKey($k)) { $values[$k] = $v.Trim().Trim('"', "'") }
}
# The names JARVIS knows (env.template beside the program lists them), so a Windows variable that is not in the key
# file at all is seen too.
$known = @()
$template = Join-Path $PSScriptRoot '..\..\env.template'
if (Test-Path -LiteralPath $template -PathType Leaf) {
    $known = @([IO.File]::ReadAllLines($template) | ForEach-Object { $_.Trim() } | Where-Object { $_ -cmatch '^[A-Z][A-Z0-9_]*$' })
}
$names = @(@($values.Keys) + $known | Sort-Object -Unique)
Write-Host "Key file: $EnvFile"
Write-Host 'Names only. No value is shown.'
Write-Host ''
$different = 0; $shadowed = 0; $fileOnly = 0
foreach ($name in $names) {
    $user = [Environment]::GetEnvironmentVariable($name, 'User')
    $machine = [Environment]::GetEnvironmentVariable($name, 'Machine')
    $window = [Environment]::GetEnvironmentVariable($name, 'Process')
    # A program started from its icon gets the account's variable, or else the PC-wide one.
    $windows = $(if ($user) { $user } else { $machine })
    $where = $(if ($user) { 'your Windows account' } elseif ($machine) { 'this PC, all accounts' } else { $null })
    $inFile = $values.ContainsKey($name) -and $values[$name]
    if ($inFile -and $windows) {
        $shadowed++
        if ($values[$name] -ceq $windows) {
            Write-Host ("{0,-22} in the key file and in Windows ({1}): SAME value." -f $name, $where)
        } else {
            $different++
            Write-Host ("{0,-22} in the key file and in Windows ({1}): DIFFERENT values. JARVIS uses the Windows one, not the key file." -f $name, $where)
        }
    } elseif ($windows) {
        Write-Host ("{0,-22} only in Windows ({1}), not in the key file. JARVIS uses it." -f $name, $where)
    } elseif ($inFile) {
        $fileOnly++
        if ($window) { Write-Host ("{0,-22} in the key file, and set in this window only (JARVIS started from its icon does not see that one)." -f $name) }
    } elseif ($window) {
        Write-Host ("{0,-22} set in this window only, not in the key file (JARVIS started from its icon does not see it)." -f $name)
    }
}
Write-Host ''
Write-Host ("{0} name(s) are only in the key file: JARVIS uses the key file for those." -f $fileOnly)
if ($different) { Write-Host ("{0} name(s) say DIFFERENT: for those JARVIS is not using what the key file says. Tell Claude which." -f $different) }
elseif ($shadowed) { Write-Host 'Where a name is in both places the values are the same, but the Windows one is still the one JARVIS uses.' }
else { Write-Host 'No name is in both places.' }
Write-Host 'Send Claude a photo of this window.'
