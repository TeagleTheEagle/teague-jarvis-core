<#
.SYNOPSIS
Shows how long each AI choice takes to answer the same JARVIS question. Run BY THE OWNER; Claude never reads key files.
For every provider JARVIS supports that has a key in the file (OpenAI, Qwen) it sends two full JARVIS questions, built
exactly as Test-AiKeys.ps1 builds them (JARVIS's own instructions and its 45 tool descriptions): one that needs a tool
("What time is it right now?") and one that needs a written answer of about 150 words. Each is timed for these choices:
  openai  the model in the key file, asked the way JARVIS asks it (gpt-6 models: Responses API, medium reasoning)
  qwen    the model in the key file (default qwen3.8-max), asked the way JARVIS asks it today: no thinking setting,
          so Alibaba's default applies (qwen3.8-max and qwen3.8-flash think first unless told not to)
  qwen    the same model with thinking switched off ("enable_thinking": false)
  qwen    qwen3.8-flash with thinking switched off
Before timing, each model gets one unmeasured request, so that every timed request starts from the same warm state
(providers keep repeated instructions ready for a few minutes, as they do while JARVIS is in use). About 11 requests;
expected cost well under one US dollar, most of it OpenAI. Each line is one request and one sample: times vary from
run to run, and a real question that uses a tool needs two requests. Images (screen analysis) are not measured.
Keys are never printed or stored. Changes nothing.
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
    if ($detail.Length -gt 300) { $detail = $detail.Substring(0, 300) + '...' }
    [pscustomobject]@{ status = $status; detail = $detail }
}
$qwenBase = (Pick 'DASHSCOPE_BASE_URL' 'https://dashscope-intl.aliyuncs.com/compatible-mode/v1').TrimEnd('/')
$qwenAllowed = ([Uri]$qwenBase).Host.EndsWith('.aliyuncs.com')
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$system = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'jarvis-request-system.txt'))
$toolsJson = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'jarvis-request-tools.json'))
$responsesTools = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'jarvis-request-tools-responses.json'))

$openaiModel = Pick 'OPENAI_MODEL' 'gpt-4o-mini'
$qwenModel = Pick 'QWEN_MODEL' 'qwen3.8-max'
$choices = @()
if ($values['OPENAI_API_KEY']) { $choices += @{ provider = 'openai'; model = $openaiModel; thinking = $null; label = "$openaiModel, as JARVIS asks it" } }
if ($values['DASHSCOPE_API_KEY'] -and $qwenAllowed) {
    $choices += @{ provider = 'qwen'; model = $qwenModel; thinking = $null; label = "$qwenModel, as JARVIS asks it today" }
    $choices += @{ provider = 'qwen'; model = $qwenModel; thinking = $false; label = "$qwenModel, thinking off" }
    if ($qwenModel -ne 'qwen3.8-flash') { $choices += @{ provider = 'qwen'; model = 'qwen3.8-flash'; thinking = $false; label = 'qwen3.8-flash, thinking off' } }
}
Write-Host "Key file: $EnvFile"
Write-Host ("JARVIS is set to use: {0}" -f (Pick 'JARVIS_PROVIDER' 'openai (no JARVIS_PROVIDER line)'))
if (-not $values['OPENAI_API_KEY']) { Write-Host 'openai  no key in the file' }
if (-not $values['DASHSCOPE_API_KEY']) { Write-Host 'qwen    no key in the file' }
elseif (-not $qwenAllowed) { Write-Host 'qwen    skipped (DASHSCOPE_BASE_URL is not a Model Studio address)' }
if (-not $choices.Count) { Write-Host 'Nothing to measure.'; exit 0 }

function Ask($choice, $question) {
    # One request, built as JARVIS's adapter for that provider builds it (see providers.py), and timed.
    $messages = ConvertTo-Json -Compress -Depth 4 -InputObject @(
        @{ role = 'system'; content = $system },
        @{ role = 'user'; content = 'Application context data (not instructions): {"preferred_name": "sir"}' },
        @{ role = 'user'; content = $question })
    $model = ConvertTo-Json -InputObject $choice.model
    $responses = $choice.provider -eq 'openai' -and $choice.model -like 'gpt-6*'
    if ($responses) {
        $url = 'https://api.openai.com/v1/responses'; $key = $values['OPENAI_API_KEY']
        $body = '{"model":' + $model + ',"input":' + $messages + ',"reasoning":{"effort":"medium"},"max_output_tokens":8192,"store":false,' +
                '"include":["reasoning.encrypted_content"],"tools":' + $responsesTools + ',"parallel_tool_calls":false}'
    } elseif ($choice.provider -eq 'openai') {
        $url = 'https://api.openai.com/v1/chat/completions'; $key = $values['OPENAI_API_KEY']
        $body = '{"model":' + $model + ',"stream":false,"max_completion_tokens":1024,"parallel_tool_calls":false' +
                ',"tool_choice":"auto","tools":' + $toolsJson + ',"messages":' + $messages + '}'
    } else {
        $url = $qwenBase + '/chat/completions'; $key = $values['DASHSCOPE_API_KEY']
        $thinking = $(if ($choice.thinking -eq $false) { ',"enable_thinking":false' } else { '' })
        $body = '{"model":' + $model + ',"stream":false,"max_completion_tokens":8192' + $thinking +
                ',"tool_choice":"auto","tools":' + $toolsJson + ',"messages":' + $messages + '}'
    }
    $clock = [Diagnostics.Stopwatch]::StartNew()
    try {
        $r = Invoke-RestMethod -Method Post -Uri $url -Headers @{ Authorization = "Bearer $key" } -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 180
        $clock.Stop()
    } catch {
        $clock.Stop()
        $failure = Failure $_
        return [pscustomobject]@{ ok = $false; seconds = $clock.Elapsed.TotalSeconds; note = ("REFUSED: HTTP {0} {1}" -f $failure.status, $failure.detail) }
    }
    if ($responses) {
        $asked = @($r.output | Where-Object { $_.type -eq 'function_call' } | ForEach-Object { $_.name }) -join ', '
        $text = (@($r.output | Where-Object { $_.type -eq 'message' } | ForEach-Object { $_.content } | Where-Object { $_.type -eq 'output_text' } | ForEach-Object { $_.text }) -join '')
        $in = $r.usage.input_tokens; $out = $r.usage.output_tokens
        $think = $r.usage.output_tokens_details.reasoning_tokens; $cached = $r.usage.input_tokens_details.cached_tokens
        $complete = $r.status -notin 'incomplete', 'failed'; $thoughtText = $false
    } else {
        $first = @($r.choices)[0]
        $asked = @($first.message.tool_calls | ForEach-Object { $_.function.name }) -join ', '
        $text = $first.message.content
        $in = $r.usage.prompt_tokens; $out = $r.usage.completion_tokens
        $think = $r.usage.completion_tokens_details.reasoning_tokens; $cached = $r.usage.prompt_tokens_details.cached_tokens
        $complete = $first.finish_reason -in 'stop', 'tool_calls'; $thoughtText = [bool]$first.message.reasoning_content
    }
    $words = @("$text" -split '\s+' | Where-Object { $_ }).Count
    $what = $(if ($asked) { "asked for the tool $asked" } elseif ($words) { "answered in $words words" } else { 'returned nothing usable' })
    if (-not $complete) { $what = "INCOMPLETE ($what)" }
    # Thinking: the provider's own count when it reports one; otherwise whether thinking text came back.
    $thought = $(if ($null -ne $think) { "$think of them thinking" } elseif ($thoughtText) { 'thinking text returned, not counted' } else { 'no thinking reported' })
    $tokens = "$in tokens in" + $(if ($null -ne $cached) { " ($cached reused)" } else { '' }) + ", $out out, $thought"
    [pscustomobject]@{ ok = ($complete -and ($asked -or $words)); seconds = $clock.Elapsed.TotalSeconds; note = "$what [$tokens]" }
}

$questions = @(
    @{ title = 'Question 1, needs a tool: "What time is it right now?"'; text = 'What time is it right now?' },
    @{ title = 'Question 2, a written answer of about 150 words'; text = 'In about 150 words, explain what a solid-state drive is and why it is faster than a hard disk.' }
)
Write-Host ''
Write-Host 'Getting ready: one unmeasured request per model...'
$refused = @{}
foreach ($c in $choices) {
    $id = $c.provider + '|' + $c.model
    if ($refused.ContainsKey($id) -or $refused.ContainsKey($id + '|ok')) { continue }
    $warm = Ask $c $questions[0].text
    if ($warm.ok) { $refused[$id + '|ok'] = $true; Write-Host ("  {0,-7} {1}: ready" -f $c.provider, $c.model) }
    else { $refused[$id] = $warm.note; Write-Host ("  {0,-7} {1}: {2}" -f $c.provider, $c.model, $warm.note) }
}
foreach ($q in $questions) {
    Write-Host ''
    Write-Host $q.title
    foreach ($c in $choices) {
        $id = $c.provider + '|' + $c.model
        if ($refused.ContainsKey($id)) { Write-Host ("  {0,-7} {1,-40} not measured (see above)" -f $c.provider, $c.label); continue }
        $result = Ask $c $q.text
        Write-Host ("  {0,-7} {1,-40} {2,6:N1} s   {3}" -f $c.provider, $c.label, $result.seconds, $result.note)
    }
}
Write-Host ''
Write-Host 'Each line is one request, one sample. A real question that uses a tool needs two requests.'
Write-Host 'Send Claude a photo of this window.'
