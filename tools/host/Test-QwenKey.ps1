<#
.SYNOPSIS
Checks that the Qwen (Alibaba Cloud Model Studio) key in a JARVIS .env file works. Run BY THE OWNER; Claude never
reads key files or handles keys. The key is never printed, stored or sent anywhere except to the Model Studio
address in the same file (default https://dashscope-intl.aliyuncs.com/compatible-mode/v1), exactly as JARVIS does.

Reads DASHSCOPE_API_KEY, DASHSCOPE_BASE_URL and QWEN_MODEL the way JARVIS's server.py reads .env, sends one tiny
chat request ("Reply with the single word OK.", at most 5 tokens) and prints WORKS or REJECTED with the reason.
Changes nothing.
#>
param(
    [string] $EnvFile = 'C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\.env',
    [string] $Model   # optional: try this model instead of QWEN_MODEL / the default, without editing the file
)
$ErrorActionPreference = 'Stop'
function Done($m) { Write-Host ''; Write-Host $m; exit $(if ($m -like 'WORKS*') { 0 } else { 2 }) }
if (-not (Test-Path -LiteralPath $EnvFile -PathType Leaf)) { Done "STOPPED: no key file at $EnvFile" }
$values = @{}
foreach ($line in [IO.File]::ReadAllLines($EnvFile)) {
    $l = $line.Trim().TrimStart([char]0xFEFF)
    if (-not $l -or $l.StartsWith('#') -or -not $l.Contains('=')) { continue }
    $k, $v = $l.Split('=', 2); $k = $k.Trim()
    if ($k -cmatch '^[A-Z][A-Z0-9_]*$' -and -not $values.ContainsKey($k)) { $values[$k] = $v.Trim().Trim('"', "'") }
}
$key = $values['DASHSCOPE_API_KEY']
if (-not $key) { Done 'STOPPED: the file has no DASHSCOPE_API_KEY line (it must read DASHSCOPE_API_KEY=<your key>, on one line).' }
$base = if ($values['DASHSCOPE_BASE_URL']) { $values['DASHSCOPE_BASE_URL'].TrimEnd('/') } else { 'https://dashscope-intl.aliyuncs.com/compatible-mode/v1' }
$model = if ($Model) { $Model } elseif ($values['QWEN_MODEL']) { $values['QWEN_MODEL'] } else { 'qwen3.8-max' }
$uri = [Uri]$base
if ($uri.Scheme -ne 'https' -or -not $uri.Host.EndsWith('.aliyuncs.com')) { Done "STOPPED: DASHSCOPE_BASE_URL is not an https://...aliyuncs.com Model Studio address: $base" }
Write-Host "Key file : $EnvFile"
Write-Host 'Key      : found (not shown)'
Write-Host "Address  : $base"
Write-Host "Model    : $model"
Write-Host 'Asking Qwen for a one-word reply ...'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$body = @{ model = $model; max_tokens = 5; messages = @(@{ role = 'user'; content = 'Reply with the single word OK.' }) } | ConvertTo-Json -Depth 4
try {
    $r = Invoke-RestMethod -Method Post -Uri ($base + '/chat/completions') -Headers @{ Authorization = "Bearer $key" } -ContentType 'application/json' -Body $body -TimeoutSec 60
    $reply = ($r.choices | Select-Object -First 1).message.content
    Done ("WORKS: Qwen answered '{0}' (model {1})." -f ([string]$reply).Trim(), $r.model)
} catch {
    $status = $null; $detail = ''
    if ($_.Exception.Response) {
        $status = [int]$_.Exception.Response.StatusCode
        try { $raw = if ($_.ErrorDetails.Message) { $_.ErrorDetails.Message } else { (New-Object IO.StreamReader($_.Exception.Response.GetResponseStream())).ReadToEnd() }; $j = $raw | ConvertFrom-Json; $detail = (@($j.error.code, $j.error.message, $j.code, $j.message) | Where-Object { $_ }) -join ': ' } catch { }
    } else { $detail = $_.Exception.Message }
    $hint = switch ($status) { 401 { ' (the key is wrong, expired, or belongs to another region: keys from the China console need DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1)' } 403 { ' (the key has no access to this model or the account has no balance)' } 404 { ' (the model name or address is wrong)' } default { '' } }
    Done ("REJECTED: HTTP {0} {1}{2}" -f $status, $detail, $hint)
}
