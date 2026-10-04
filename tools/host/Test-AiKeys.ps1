<#
.SYNOPSIS
Shows which AI providers in a JARVIS key file work right now. Run BY THE OWNER; Claude never reads key files.
For every provider that has a key in the file (OpenAI, Groq, Gemini, Qwen) it sends one tiny chat request
("Reply with the single word OK.", at most 5 tokens) to that provider's own address, exactly as JARVIS would,
and prints WORKS or REJECTED with the provider's reason. Keys are never printed or stored. Changes nothing.
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
function Pick($name, $default) { if ($values[$name]) { $values[$name] } else { $default } }
$qwenBase = (Pick 'DASHSCOPE_BASE_URL' 'https://dashscope-intl.aliyuncs.com/compatible-mode/v1').TrimEnd('/')
$providers = @(
    @{ name = 'openai'; key = 'OPENAI_API_KEY'; url = 'https://api.openai.com/v1/chat/completions'; model = (Pick 'OPENAI_MODEL' 'gpt-4o-mini') },
    @{ name = 'groq'; key = 'GROQ_API_KEY'; url = 'https://api.groq.com/openai/v1/chat/completions'; model = (Pick 'GROQ_MODEL' 'openai/gpt-oss-120b') },
    # The Gemini fallback is the INSTALLED build's default: 1.0.11 uses gemini-2.5-flash; from 1.0.12 it is gemini-3.8-flash.
    @{ name = 'gemini'; key = 'GEMINI_API_KEY'; url = 'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions'; model = (Pick 'GEMINI_MODEL' 'gemini-2.5-flash') },
    @{ name = 'qwen'; key = 'DASHSCOPE_API_KEY'; url = ($qwenBase + '/chat/completions'); model = (Pick 'QWEN_MODEL' 'qwen3.8-max') }
)
if (-not ([Uri]$qwenBase).Host.EndsWith('.aliyuncs.com')) { $providers = @($providers | Where-Object { $_.name -ne 'qwen' }); Write-Host 'qwen: skipped (DASHSCOPE_BASE_URL is not a Model Studio address)' }
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Write-Host "Key file: $EnvFile"
Write-Host ("JARVIS is set to use: {0}" -f (Pick 'JARVIS_PROVIDER' 'groq (the default; no JARVIS_PROVIDER line)'))
Write-Host ''
$working = @()
foreach ($p in $providers) {
    $key = $values[$p.key]
    if (-not $key) { Write-Host ("{0,-7} no key in the file" -f $p.name); continue }
    $body = @{ model = $p.model; max_tokens = 5; messages = @(@{ role = 'user'; content = 'Reply with the single word OK.' }) } | ConvertTo-Json -Depth 4
    try {
        $r = Invoke-RestMethod -Method Post -Uri $p.url -Headers @{ Authorization = "Bearer $key" } -ContentType 'application/json' -Body $body -TimeoutSec 60
        Write-Host ("{0,-7} WORKS (model {1})" -f $p.name, $p.model); $working += $p.name
    } catch {
        $status = $null; $detail = ''
        if ($_.Exception.Response) {
            $status = [int]$_.Exception.Response.StatusCode
            try { $raw = if ($_.ErrorDetails.Message) { $_.ErrorDetails.Message } else { (New-Object IO.StreamReader($_.Exception.Response.GetResponseStream())).ReadToEnd() }
                  $j = $raw | ConvertFrom-Json; if ($j -is [array]) { $j = $j[0] }
                  $detail = (@($j.error.code, $j.error.type, $j.error.status, $j.error.message, $j.code, $j.message) | Where-Object { $_ } | Select-Object -Unique) -join ': ' } catch { }
        } else { $detail = $_.Exception.Message }
        # Providers echo part of a rejected key in their message: never show it.
        $detail = [regex]::Replace($detail, '(?i)(provided:\s*)\S+', '$1(hidden)'); $detail = [regex]::Replace($detail, '(?i)\b(sk|gsk|AIza)[-_A-Za-z0-9*]{6,}', '(hidden)')
        if ($detail.Length -gt 300) { $detail = $detail.Substring(0, 300) + '...' }
        Write-Host ("{0,-7} REJECTED: HTTP {1} {2} (model {3})" -f $p.name, $status, $detail, $p.model)
        if ($p.name -eq 'gemini' -and $p.model -like 'gemini-2*') {
            Write-Host '        Hint: since 2026-09-18 Google serves gemini-2 models only to projects that used them before. Put the line GEMINI_MODEL=gemini-3.8-flash in the key file, then run this check again.'
        }
    }
}
Write-Host ''
if ($working.Count) { Write-Host ('Working now: ' + ($working -join ', ') + '.') } else { Write-Host 'No provider in this file works right now.' }
