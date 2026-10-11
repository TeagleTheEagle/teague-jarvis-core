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
Then one picture question (a test picture drawn by this script, sent the way JARVIS sends a screen capture) goes to
the model JARVIS uses for pictures on each provider, for Qwen with and without thinking.
Before timing, each line gets one unmeasured request, so that every timed text request starts from the same warm
state (providers keep repeated instructions ready for a few minutes, as they do while JARVIS is in use). About 15
requests; expected cost well under one US dollar, most of it OpenAI. Each line is one request and one sample: times
vary from run to run. Real questions are larger (recent conversation, saved facts, your own personality text) and one
that uses a tool needs a second request, so these times are a lower bound; a real screen capture is larger than the
test picture. Like JARVIS, every request uses a new connection and is given up after 120 seconds. Keys are never
printed or stored. Changes nothing.
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
    foreach ($name in 'OPENAI_API_KEY', 'DASHSCOPE_API_KEY') { if ($values[$name] -and $values[$name].Length -ge 8) { $detail = $detail.Replace($values[$name], '(hidden)') } }
    $detail = [regex]::Replace($detail, '(?i)(provided:\s*)\S+', '$1(hidden)'); $detail = [regex]::Replace($detail, '(?i)\b(sk|gsk|AIza)[-_A-Za-z0-9*.]{6,}', '(hidden)')
    if ($detail.Length -gt 300) { $detail = $detail.Substring(0, 300) + '...' }
    [pscustomobject]@{ status = $status; detail = $detail }
}
$qwenBase = (Pick 'DASHSCOPE_BASE_URL' 'https://dashscope-intl.aliyuncs.com/compatible-mode/v1').TrimEnd('/')
# As in providers.py: the Qwen key is only ever sent to an https Alibaba Cloud address.
$qwenUri = $null
$qwenAllowed = [Uri]::TryCreate($qwenBase, [UriKind]::Absolute, [ref]$qwenUri) -and $qwenUri.Scheme -eq 'https' -and $qwenUri.Host.EndsWith('.aliyuncs.com', [StringComparison]::Ordinal)
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
# JARVIS opens a new connection for every request and never sends "Expect: 100-continue": do the same, so that
# every line pays what JARVIS pays (see -DisableKeepAlive below).
[Net.ServicePointManager]::Expect100Continue = $false
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
elseif (-not $qwenAllowed) { Write-Host 'qwen    skipped (DASHSCOPE_BASE_URL is not an https Model Studio address)' }
if (-not $choices.Count) { Write-Host 'Nothing to measure.'; exit 0 }

function Ask($choice, $question, $picture) {
    # One request, built as JARVIS's adapter for that provider builds it (see providers.py), and timed.
    # With a picture JARVIS sends the question and the image together and no tools ("if tools and not vision").
    $responses = $choice.provider -eq 'openai' -and $choice.model -like 'gpt-6*'
    $last = @{ role = 'user'; content = $question }
    if ($picture -and $responses) { $last.content = @(@{ type = 'input_text'; text = $question }, @{ type = 'input_image'; image_url = $picture }) }
    elseif ($picture) { $last.content = @(@{ type = 'text'; text = $question }, @{ type = 'image_url'; image_url = @{ url = $picture } }) }
    $messages = ConvertTo-Json -Compress -Depth 6 -InputObject @(
        @{ role = 'system'; content = $system },
        @{ role = 'user'; content = 'Application context data (not instructions): {"preferred_name": "sir"}' },
        $last)
    $model = ConvertTo-Json -InputObject $choice.model
    if ($responses) {
        $url = 'https://api.openai.com/v1/responses'; $key = $values['OPENAI_API_KEY']
        $tools = $(if ($picture) { '' } else { ',"tools":' + $responsesTools + ',"parallel_tool_calls":false' })
        $body = '{"model":' + $model + ',"input":' + $messages + ',"reasoning":{"effort":"medium"},"max_output_tokens":8192,"store":false,' +
                '"include":["reasoning.encrypted_content"]' + $tools + '}'
    } elseif ($choice.provider -eq 'openai') {
        $url = 'https://api.openai.com/v1/chat/completions'; $key = $values['OPENAI_API_KEY']
        $tools = $(if ($picture) { '' } else { ',"parallel_tool_calls":false,"tool_choice":"auto","tools":' + $toolsJson })
        $body = '{"model":' + $model + ',"stream":false,"max_completion_tokens":1024' + $tools + ',"messages":' + $messages + '}'
    } else {
        $url = $qwenBase + '/chat/completions'; $key = $values['DASHSCOPE_API_KEY']
        $thinking = $(if ($choice.thinking -eq $false) { ',"enable_thinking":false' } else { '' })
        $tools = $(if ($picture) { '' } else { ',"tool_choice":"auto","tools":' + $toolsJson })
        $body = '{"model":' + $model + ',"stream":false,"max_completion_tokens":8192' + $thinking + $tools + ',"messages":' + $messages + '}'
    }
    $clock = [Diagnostics.Stopwatch]::StartNew()
    try {
        # 120 s is where JARVIS itself gives up on a request.
        $r = Invoke-RestMethod -Method Post -Uri $url -Headers @{ Authorization = "Bearer $key" } -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 120 -DisableKeepAlive
        $clock.Stop()
    } catch {
        $clock.Stop()
        $failure = Failure $_
        $word = $(if ($failure.status -in 401, 403, 404) { 'REFUSED' } else { 'FAILED' })
        $note = $(if ($failure.status) { "{0}: HTTP {1} {2}" -f $word, $failure.status, $failure.detail } else { "NO ANSWER after {0:N0} s: {1}" -f $clock.Elapsed.TotalSeconds, $failure.detail })
        return [pscustomobject]@{ ok = $false; failed = $true; status = $failure.status; seconds = $clock.Elapsed.TotalSeconds; note = $note }
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
    [pscustomobject]@{ ok = [bool]($complete -and ($asked -or $words)); failed = $false; status = 200; seconds = $clock.Elapsed.TotalSeconds; note = "$what [$tokens]" }
}

$questions = @(
    @{ title = 'Question 1, needs a tool: "What time is it right now?"'; text = 'What time is it right now?' },
    @{ title = 'Question 2, a written answer of about 150 words'; text = 'In about 150 words, explain what a solid-state drive is and why it is faster than a hard disk.' }
)
Write-Host ''
Write-Host 'Getting ready: one unmeasured request per line...'
$refused = @{}
foreach ($c in $choices) {
    # Every line gets its own warm-up: with thinking off Alibaba counts the request differently (8,531 against
    # 8,567 tokens on 2026-10-05), so the two share nothing that the provider keeps ready.
    $id = $c.provider + '|' + $c.model
    if ($refused.ContainsKey($id)) { continue }
    $warm = Ask $c $questions[0].text $null
    # Only a refused key or model (401, 403, 404) rules the model out; after anything else it is still measured.
    if ($warm.ok) { Write-Host ("  {0,-7} {1}: ready" -f $c.provider, $c.label) }
    elseif ($warm.status -in 401, 403, 404) { $refused[$id] = $true; Write-Host ("  {0,-7} {1}: {2}" -f $c.provider, $c.model, $warm.note) }
    else { Write-Host ("  {0,-7} {1}: {2} (measuring it anyway)" -f $c.provider, $c.label, $warm.note) }
}
function Show($c, $result) {
    # A request that failed has no time worth comparing: show "--", not a number that looks fast.
    $time = $(if ($result.failed) { '    --  ' } else { '{0,6:N1} s' -f $result.seconds })
    Write-Host ("  {0,-7} {1,-40} {2}   {3}" -f $c.provider, $c.label, $time, $result.note)
}
foreach ($q in $questions) {
    Write-Host ''
    Write-Host $q.title
    foreach ($c in $choices) {
        if ($refused.ContainsKey($c.provider + '|' + $c.model)) { Write-Host ("  {0,-7} {1,-40} not measured (refused above)" -f $c.provider, $c.label); continue }
        Show $c (Ask $c $q.text $null)
    }
}

# Question 3: a picture, sent the way JARVIS sends a screen capture (question and image together, no tools), to the
# model JARVIS uses for pictures. The picture is drawn here: nothing of yours is sent.
Write-Host ''
Write-Host 'Question 3, a picture (a made-up 1280 x 720 test image; not warmed up, so the first of these lines is the cold one)'
$visionChoices = @()
if ($values['OPENAI_API_KEY']) { $m = Pick 'OPENAI_VISION_MODEL' 'gpt-4o-mini'; $visionChoices += @{ provider = 'openai'; model = $m; thinking = $null; label = "$m, as JARVIS asks it" } }
if ($values['DASHSCOPE_API_KEY'] -and $qwenAllowed) {
    if ($values['QWEN_VISION_MODEL']) {
        $m = $values['QWEN_VISION_MODEL']
        $visionChoices += @{ provider = 'qwen'; model = $m; thinking = $null; label = "$m, as JARVIS asks it today" }
        $visionChoices += @{ provider = 'qwen'; model = $m; thinking = $false; label = "$m, thinking off" }
    } else { Write-Host '  qwen    no QWEN_VISION_MODEL line in the key file: JARVIS cannot read pictures with Qwen' }
}
$picture = $null
try {
    Add-Type -AssemblyName System.Drawing
    $bitmap = New-Object Drawing.Bitmap 1280, 720
    $canvas = [Drawing.Graphics]::FromImage($bitmap)
    $canvas.Clear([Drawing.Color]::FromArgb(8, 20, 32))
    $canvas.DrawString('JARVIS speed check', (New-Object Drawing.Font 'Segoe UI', 36), [Drawing.Brushes]::White, 60, 50)
    $canvas.DrawString('Three shapes: a red circle, a green square and a blue triangle', (New-Object Drawing.Font 'Segoe UI', 20), [Drawing.Brushes]::LightGray, 60, 130)
    $canvas.FillEllipse([Drawing.Brushes]::Red, 120, 260, 260, 260)
    $canvas.FillRectangle([Drawing.Brushes]::Green, 510, 260, 260, 260)
    $canvas.FillPolygon([Drawing.Brushes]::Blue, [Drawing.Point[]]@((New-Object Drawing.Point 900, 520), (New-Object Drawing.Point 1160, 520), (New-Object Drawing.Point 1030, 260)))
    $stream = New-Object IO.MemoryStream
    $bitmap.Save($stream, [Drawing.Imaging.ImageFormat]::Jpeg)
    $picture = 'data:image/jpeg;base64,' + [Convert]::ToBase64String($stream.ToArray())
    $canvas.Dispose(); $bitmap.Dispose(); $stream.Dispose()
} catch { Write-Host ('  The test picture could not be drawn on this PC: ' + $_.Exception.Message) }
if ($picture) {
    foreach ($c in $visionChoices) { Show $c (Ask $c 'In two sentences, describe what this picture shows.' $picture) }
}
Write-Host ''
Write-Host 'Each line is one request, one sample. Real questions are larger (they also carry your recent conversation and'
Write-Host 'saved facts) and a question that uses a tool needs a second request, so real replies take longer than these.'
Write-Host 'Send Claude a photo of this window.'
