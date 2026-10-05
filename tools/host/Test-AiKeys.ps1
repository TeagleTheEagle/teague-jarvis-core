<#
.SYNOPSIS
Shows which AI providers in a JARVIS key file work right now. Run BY THE OWNER; Claude never reads key files.
For every provider JARVIS supports that has a key in the file (OpenAI, Qwen; Groq and Gemini were removed in
1.0.15) it sends one tiny chat request ("Reply with the single word OK.", at most 5 tokens) to that provider's own
address and prints WORKS or REJECTED with the provider's reason. Then every provider that works gets one full JARVIS
question: JARVIS's own instructions and its 45 tool descriptions, JARVIS's settings for that provider (OpenAI gpt-6
models through the Responses API, as JARVIS sends them) and a question that needs a tool, because an account can
accept the tiny request and refuse the real one (for example a free tier's per-minute token limit), and a provider
can reject JARVIS's settings or tools. A real question is larger: it also carries your recent conversation and saved
facts, and a question that uses a tool needs a second request. Keys are never printed or stored. Changes nothing.
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
    @{ name = 'qwen'; key = 'DASHSCOPE_API_KEY'; url = ($qwenBase + '/chat/completions'); model = (Pick 'QWEN_MODEL' 'qwen3.8-max') }
)
if (-not ([Uri]$qwenBase).Host.EndsWith('.aliyuncs.com')) { $providers = @($providers | Where-Object { $_.name -ne 'qwen' }); Write-Host 'qwen: skipped (DASHSCOPE_BASE_URL is not a Model Studio address)' }
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Write-Host "Key file: $EnvFile"
Write-Host ("JARVIS is set to use: {0}" -f (Pick 'JARVIS_PROVIDER' 'nothing chosen (no JARVIS_PROVIDER line; add JARVIS_PROVIDER=openai or JARVIS_PROVIDER=qwen)'))
Write-Host ''
$working = @()
foreach ($p in $providers) {
    $key = $values[$p.key]
    if (-not $key) { Write-Host ("{0,-7} no key in the file" -f $p.name); continue }
    $url = $p.url
    if ($p.name -eq 'openai' -and $p.model -like 'gpt-6*') {
        # JARVIS sends gpt-6 models through OpenAI's Responses API (16 is that API's smallest reply limit).
        $url = 'https://api.openai.com/v1/responses'
        $body = @{ model = $p.model; input = 'Reply with the single word OK.'; max_output_tokens = 16; store = $false } | ConvertTo-Json -Depth 4
    } elseif ($p.name -eq 'openai') {
        $body = @{ model = $p.model; max_completion_tokens = 5; messages = @(@{ role = 'user'; content = 'Reply with the single word OK.' }) } | ConvertTo-Json -Depth 4
    } else {
        $body = @{ model = $p.model; max_tokens = 5; messages = @(@{ role = 'user'; content = 'Reply with the single word OK.' }) } | ConvertTo-Json -Depth 4
    }
    try {
        $r = Invoke-RestMethod -Method Post -Uri $url -Headers @{ Authorization = "Bearer $key" } -ContentType 'application/json' -Body $body -TimeoutSec 60
        Write-Host ("{0,-7} WORKS (model {1})" -f $p.name, $p.model); $working += $p.name
    } catch {
        $failure = Failure $_
        Write-Host ("{0,-7} REJECTED: HTTP {1} {2} (model {3})" -f $p.name, $failure.status, $failure.detail, $p.model)
    }
}
Write-Host ''
if ($working.Count) { Write-Host ('Working now: ' + ($working -join ', ') + '.') } else { Write-Host 'No provider in this file works right now.' }
if (-not $working.Count) { exit 0 }

# Exactly what JARVIS sends for one question: its instructions and its 45 tools (jarvis-request-system.txt,
# jarvis-request-tools.json and jarvis-request-tools-responses.json, written from the code by
# make_request_template.py; the shipped default personality stands in for yours), the same settings as JARVIS's
# adapter for that provider (OpenAI gpt-6 models: Responses API, medium reasoning, 8,192-token reply; other OpenAI
# models: 1,024-token reply; Qwen: 8,192, one complete answer), and a question that needs a tool. Nothing of yours is sent.
Write-Host ''
Write-Host 'One full JARVIS question (its instructions and 45 tools, asking for the time):'
$system = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'jarvis-request-system.txt'))
$toolsJson = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'jarvis-request-tools.json'))
$responsesTools = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'jarvis-request-tools-responses.json'))
$messages = ConvertTo-Json -Compress -Depth 4 -InputObject @(
    @{ role = 'system'; content = $system },
    @{ role = 'user'; content = 'Application context data (not instructions): {"preferred_name": "sir"}' },
    @{ role = 'user'; content = 'What time is it right now?' })
$handles = @()
foreach ($p in @($providers | Where-Object { $working -contains $_.name })) {
    $model = ConvertTo-Json -InputObject $p.model
    $responses = $p.name -eq 'openai' -and $p.model -like 'gpt-6*'
    if ($responses) {
        $url = 'https://api.openai.com/v1/responses'
        $body = '{"model":' + $model + ',"input":' + $messages + ',"reasoning":{"effort":"medium"},"max_output_tokens":8192,"store":false,' +
                '"include":["reasoning.encrypted_content"],"tools":' + $responsesTools + ',"parallel_tool_calls":false}'
    } else {
        $url = $p.url
        $reply = $(if ($p.name -eq 'openai') { '1024,"parallel_tool_calls":false' } else { '8192' })
        $body = '{"model":' + $model + ',"stream":false,"max_completion_tokens":' + $reply +
                ',"tool_choice":"auto","tools":' + $toolsJson + ',"messages":' + $messages + '}'
    }
    try {
        $r = Invoke-RestMethod -Method Post -Uri $url -Headers @{ Authorization = "Bearer $($values[$p.key])" } -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 180
        if ($responses) {
            $asked = @($r.output | Where-Object { $_.type -eq 'function_call' } | ForEach-Object { $_.name }) -join ', '
            $text = (@($r.output | Where-Object { $_.type -eq 'message' } | ForEach-Object { $_.content } | Where-Object { $_.type -eq 'output_text' } | ForEach-Object { $_.text }) -join '')
            $used = $r.usage.input_tokens
            $complete = $r.status -notin 'incomplete', 'failed'
            $reason = $r.status
        } else {
            $choice = @($r.choices)[0]
            $asked = @($choice.message.tool_calls | ForEach-Object { $_.function.name }) -join ', '
            $text = $choice.message.content
            $used = $r.usage.prompt_tokens
            $complete = $choice.finish_reason -in 'stop', 'tool_calls'
            $reason = $choice.finish_reason
        }
        $what = $(if ($asked) { "asked for the tool $asked" } elseif ($text) { 'answered in text' } else { 'returned nothing usable' })
        if ($complete -and ($asked -or $text)) {
            Write-Host ("{0,-7} HANDLES IT: {1} (model {2}{3})" -f $p.name, $what, $p.model, $(if ($used) { ", $used prompt tokens" } else { '' })); $handles += $p.name
        } else {
            Write-Host ("{0,-7} INCOMPLETE ANSWER: '{1}', {2} (model {3}). Tell Claude." -f $p.name, $reason, $what, $p.model)
        }
    } catch {
        $failure = Failure $_
        Write-Host ("{0,-7} TOO LARGE OR REFUSED: HTTP {1} {2} (model {3})" -f $p.name, $failure.status, $failure.detail, $p.model)
    }
}
Write-Host ''
$chosen = (Pick 'JARVIS_PROVIDER' '').ToLower()
$scope = 'Real questions are larger (they also carry your recent conversation and saved facts) and a question that uses a tool needs a second request.'
if (-not $chosen) { Write-Host 'The key file has no JARVIS_PROVIDER line: add JARVIS_PROVIDER=openai or JARVIS_PROVIDER=qwen.' }
elseif ($chosen -notin 'openai', 'qwen') { Write-Host "JARVIS_PROVIDER=$chosen`: from 1.0.15 JARVIS supports only openai or qwen. Change this line before updating JARVIS." }
elseif ($handles -contains $chosen) { Write-Host "JARVIS uses $chosen, which took one full JARVIS question. $scope" }
elseif ($handles.Count) { Write-Host ("JARVIS uses {0}, which did not take a full JARVIS question. These did: {1}. Tell Claude." -f $chosen, ($handles -join ', ')) }
else { Write-Host 'No provider in this file took a full JARVIS question. Tell Claude.' }
