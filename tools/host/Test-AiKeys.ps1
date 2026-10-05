<#
.SYNOPSIS
Shows which AI providers in a JARVIS key file work right now. Run BY THE OWNER; Claude never reads key files.
For every provider that has a key in the file (OpenAI, Groq, Gemini, Qwen) it sends one tiny chat request
("Reply with the single word OK.", at most 5 tokens) to that provider's own address, exactly as JARVIS would,
and prints WORKS or REJECTED with the provider's reason. Then every provider that works gets one full JARVIS
request: JARVIS's own instructions and its 45 tool descriptions (about 11,000 tokens), JARVIS's settings for that
provider and a question that needs a tool, because a free tier can accept the tiny request and refuse the real one
(Groq: HTTP 413, request larger than the account's tokens-per-minute limit), and a provider can reject JARVIS's
settings or tools. Keys are never printed or stored. Changes nothing.
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
function Failure($err) {
    # The HTTP status and the provider's own reason, with any echoed part of a key removed.
    $status = $null; $detail = ''
    if ($err.Exception.Response) {
        $status = [int]$err.Exception.Response.StatusCode
        try { $raw = if ($err.ErrorDetails.Message) { $err.ErrorDetails.Message } else { (New-Object IO.StreamReader($err.Exception.Response.GetResponseStream())).ReadToEnd() }
              $j = $raw | ConvertFrom-Json; if ($j -is [array]) { $j = $j[0] }
              $detail = (@($j.error.code, $j.error.type, $j.error.status, $j.error.message, $j.code, $j.message) | Where-Object { $_ } | Select-Object -Unique) -join ': ' } catch { }
    } else { $detail = $err.Exception.Message }
    # Providers echo part of a rejected key in their message: never show it.
    $detail = [regex]::Replace($detail, '(?i)(provided:\s*)\S+', '$1(hidden)'); $detail = [regex]::Replace($detail, '(?i)\b(sk|gsk|AIza)[-_A-Za-z0-9*]{6,}', '(hidden)')
    # Groq names the organisation in a size refusal: not needed here.
    $detail = [regex]::Replace($detail, '(?i)in organization `?[A-Za-z0-9_]+`?', 'in your organisation')
    if ($detail.Length -gt 400) { $detail = $detail.Substring(0, 400) + '...' }
    [pscustomobject]@{ status = $status; detail = $detail }
}
$qwenBase = (Pick 'DASHSCOPE_BASE_URL' 'https://dashscope-intl.aliyuncs.com/compatible-mode/v1').TrimEnd('/')
$providers = @(
    @{ name = 'openai'; key = 'OPENAI_API_KEY'; url = 'https://api.openai.com/v1/chat/completions'; model = (Pick 'OPENAI_MODEL' 'gpt-4o-mini') },
    @{ name = 'groq'; key = 'GROQ_API_KEY'; url = 'https://api.groq.com/openai/v1/chat/completions'; model = (Pick 'GROQ_MODEL' 'openai/gpt-oss-120b') },
    # The Gemini fallback is the INSTALLED build's default: gemini-3.8-flash since the everyday JARVIS is 1.0.14
    # (2026-10-05; 1.0.11 used gemini-2.5-flash).
    @{ name = 'gemini'; key = 'GEMINI_API_KEY'; url = 'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions'; model = (Pick 'GEMINI_MODEL' 'gemini-3.8-flash') },
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
        $failure = Failure $_
        Write-Host ("{0,-7} REJECTED: HTTP {1} {2} (model {3})" -f $p.name, $failure.status, $failure.detail, $p.model)
        if ($p.name -eq 'gemini' -and $p.model -like 'gemini-2*') {
            Write-Host '        Hint: since 2026-09-18 Google serves gemini-2 models only to projects that used them before. Put the line GEMINI_MODEL=gemini-3.8-flash in the key file, then run this check again.'
        }
    }
}
Write-Host ''
if ($working.Count) { Write-Host ('Working now: ' + ($working -join ', ') + '.') } else { Write-Host 'No provider in this file works right now.' }
if (-not $working.Count) { exit 0 }

# Exactly what JARVIS sends for one question: its instructions and its 45 tools (jarvis-request-system.txt and
# jarvis-request-tools.json, written from the code by make_request_template.py; the shipped default personality
# stands in for yours), the same settings as JARVIS's adapter for that provider (Groq: 1,024-token reply; Gemini and
# Qwen: 8,192, one complete answer), and a question that needs a tool. Nothing of yours is sent.
Write-Host ''
Write-Host 'A full JARVIS request (its instructions and 45 tools, about 11,000 tokens, asking for the time):'
$system = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'jarvis-request-system.txt'))
$toolsJson = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'jarvis-request-tools.json'))
$messages = ConvertTo-Json -Compress -Depth 4 -InputObject @(
    @{ role = 'system'; content = $system },
    @{ role = 'user'; content = 'Application context data (not instructions): {"preferred_name": "sir"}' },
    @{ role = 'user'; content = 'What time is it right now?' })
$handles = @()
foreach ($p in @($providers | Where-Object { $working -contains $_.name })) {
    if ($p.name -eq 'openai') { Write-Host 'openai  not tested here (JARVIS talks to OpenAI through a different interface)'; continue }
    $reply = $(if ($p.name -eq 'groq') { 1024 } else { 8192 })
    $body = '{"model":' + (ConvertTo-Json -InputObject $p.model) + ',"stream":false,"max_completion_tokens":' + $reply +
            ',"tool_choice":"auto","tools":' + $toolsJson + ',"messages":' + $messages + '}'
    try {
        $r = Invoke-RestMethod -Method Post -Uri $p.url -Headers @{ Authorization = "Bearer $($values[$p.key])" } -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 180
        $choice = @($r.choices)[0]
        $asked = @($choice.message.tool_calls | ForEach-Object { $_.function.name }) -join ', '
        $used = $r.usage.prompt_tokens
        $what = $(if ($asked) { "asked for the tool $asked" } elseif ($choice.message.content) { 'answered in text' } else { 'returned nothing usable' })
        if ($choice.finish_reason -in 'stop', 'tool_calls' -and ($asked -or $choice.message.content)) {
            Write-Host ("{0,-7} HANDLES IT: {1} (model {2}{3})" -f $p.name, $what, $p.model, $(if ($used) { ", $used prompt tokens" } else { '' })); $handles += $p.name
        } else {
            Write-Host ("{0,-7} INCOMPLETE ANSWER: finish reason '{1}', {2} (model {3}). Tell Claude." -f $p.name, $choice.finish_reason, $what, $p.model)
        }
    } catch {
        $failure = Failure $_
        Write-Host ("{0,-7} TOO LARGE OR REFUSED: HTTP {1} {2} (model {3})" -f $p.name, $failure.status, $failure.detail, $p.model)
        if ($failure.status -eq 413 -and $p.name -eq 'groq') {
            Write-Host '        Groq refuses any single request larger than your account''s tokens-per-minute limit for this model (see the'
            Write-Host '        numbers above). A model with a higher limit (Groq console > Settings > Limits), a paid Groq tier, or another'
            Write-Host '        provider is needed for JARVIS''s full requests.'
        }
    }
}
Write-Host ''
$chosen = (Pick 'JARVIS_PROVIDER' 'groq').ToLower()
if ($handles -contains $chosen) { Write-Host "JARVIS uses $chosen, which handles a full JARVIS request." }
elseif ($handles.Count) { Write-Host ("JARVIS uses {0}, which cannot take a full JARVIS request right now. These can: {1}. Tell Claude." -f $chosen, ($handles -join ', ')) }
else { Write-Host 'No provider in this file takes a full JARVIS request right now. Tell Claude.' }
