<#
.SYNOPSIS
The Qwen cloned voice for JARVIS: checked, and created if you ask. Run BY THE OWNER; Claude never reads key files.

  (no switch)          Lists the cloned voices on the Alibaba account of the key in the key file, says which one the
                       key file names (QWEN_TTS_VOICE), and makes one short spoken test with it, saved as a sound
                       file you can play. Two or three requests; the spoken test costs well under one US cent.
  -Enroll <recording>  Creates a new cloned voice from a recording of the voice: 10 to 20 seconds of clear speech by
                       one speaker, no music or noise; WAV (16-bit), MP3 or M4A; mono; 24 kHz or better; at most 60
                       seconds and 10 MB (Alibaba's rules as read on 2026-10-06). Alibaba charges for creating a
                       voice, so you are asked to type YES first. Prints the new voice ID and the lines for the key
                       file. -Name gives the voice a name on the account (letters, digits, underscore).

The recording is sent to Alibaba Cloud Model Studio and nowhere else. Keys are never printed or stored. Nothing on
this PC is changed except the test sound file in your Temp folder. JARVIS itself is not touched.
#>
param(
    [string] $EnvFile = (Join-Path $env:LOCALAPPDATA 'JARVIS\config\.env'),
    [string] $Enroll,
    [string] $Name = 'jarvis',
    # For this script's own tests only: a stand-in on 127.0.0.1. Accepted only with a made-up key ("jarvis-test-...").
    [string] $TestEndpoint
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
    # The HTTP status and Alibaba's own reason, with any echoed part of the key removed.
    $status = $null; $detail = ''
    if ($err.Exception.Response) {
        $status = [int]$err.Exception.Response.StatusCode
        try { $raw = if ($err.ErrorDetails.Message) { $err.ErrorDetails.Message } else { (New-Object IO.StreamReader($err.Exception.Response.GetResponseStream())).ReadToEnd() }
              $j = $raw | ConvertFrom-Json
              $detail = (@($j.code, $j.message, $j.error.code, $j.error.message) | Where-Object { $_ } | Select-Object -Unique) -join ': ' } catch { }
    } else { $detail = $err.Exception.Message }
    if ($values['DASHSCOPE_API_KEY'] -and $values['DASHSCOPE_API_KEY'].Length -ge 8) { $detail = $detail.Replace($values['DASHSCOPE_API_KEY'], '(hidden)') }
    $detail = [regex]::Replace($detail, '(?i)(provided:\s*)\S+', '$1(hidden)'); $detail = [regex]::Replace($detail, '(?i)\bsk[-_A-Za-z0-9*.]{6,}', '(hidden)')
    if ($detail.Length -gt 300) { $detail = $detail.Substring(0, 300) + '...' }
    if ($status) { "HTTP $status $detail" } else { "no answer: $detail" }
}
function Alibaba($address) {
    # As in providers.py: the Qwen key is only ever sent to an https Alibaba Cloud address.
    $uri = $null
    [Uri]::TryCreate($address, [UriKind]::Absolute, [ref]$uri) -and $uri.Scheme -eq 'https' -and $uri.Host.EndsWith('.aliyuncs.com', [StringComparison]::Ordinal)
}

$key = $values['DASHSCOPE_API_KEY']
Write-Host "Key file: $EnvFile"
if (-not $key) { Write-Host 'STOPPED: the key file has no DASHSCOPE_API_KEY line.'; exit 2 }
$base = (Pick 'DASHSCOPE_BASE_URL' 'https://dashscope-intl.aliyuncs.com/compatible-mode/v1').TrimEnd('/')
if ($TestEndpoint) {
    $standIn = $null
    if (-not ([Uri]::TryCreate($TestEndpoint, [UriKind]::Absolute, [ref]$standIn) -and $standIn.Host -eq '127.0.0.1' -and $key.StartsWith('jarvis-test-', [StringComparison]::Ordinal))) {
        Write-Host 'STOPPED: -TestEndpoint is for this script''s own tests (127.0.0.1 and a made-up key only).'; exit 2
    }
    $root = $TestEndpoint.TrimEnd('/'); $speakUrl = $root + '/api/v1/services/aigc/multimodal-generation/generation'
} else {
    if (-not (Alibaba $base)) { Write-Host 'STOPPED: DASHSCOPE_BASE_URL is not an https Model Studio address (*.aliyuncs.com).'; exit 2 }
    if (-not $base.EndsWith('/compatible-mode/v1', [StringComparison]::Ordinal)) { Write-Host 'STOPPED: DASHSCOPE_BASE_URL does not end with /compatible-mode/v1.'; exit 2 }
    $root = $base.Substring(0, $base.Length - '/compatible-mode/v1'.Length)
    $speakUrl = Pick 'DASHSCOPE_TTS_URL' ($root + '/api/v1/services/aigc/multimodal-generation/generation')
    if (-not (Alibaba $speakUrl)) { Write-Host 'STOPPED: DASHSCOPE_TTS_URL is not an https Model Studio address (*.aliyuncs.com).'; exit 2 }
}
$voicesUrl = $root + '/api/v1/services/audio/tts/customization'
$model = Pick 'QWEN_TTS_MODEL' 'qwen3-tts-vc-2026-01-22'   # the default JARVIS uses (providers.QWEN_TTS_DEFAULT_MODEL)
$voice = $values['QWEN_TTS_VOICE']
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
[Net.ServicePointManager]::Expect100Continue = $false
function Send($url, $body) {
    # -MaximumRedirection 0: a redirect answer ends the request. Neither the key nor the recording is ever sent on
    # to whatever address such an answer names.
    Invoke-RestMethod -Method Post -Uri $url -Headers @{ Authorization = "Bearer $key" } -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 120 -DisableKeepAlive -MaximumRedirection 0
}
# JARVIS prefers a Windows variable named DASHSCOPE_API_KEY over the line in the key file (server.load_env), and this
# tool always uses the key file. When the two differ, the voice would be listed from, or created on, another Alibaba
# account than the one JARVIS speaks with: say so. Neither value is ever shown.
$otherKey = [bool]($env:DASHSCOPE_API_KEY -and $env:DASHSCOPE_API_KEY -cne $key)
$otherKeyNote = 'ATTENTION: Windows also holds a DASHSCOPE_API_KEY variable, and its value is DIFFERENT from the key file. JARVIS uses the Windows variable; this tool uses the key file. If they belong to two Alibaba accounts, JARVIS will not find a voice made here.'
if ($otherKey) { Write-Host $otherKeyNote }

if ($Enroll) {
    # ---- create a new cloned voice from a recording ----
    if ($Name -cnotmatch '^[A-Za-z0-9_]{1,16}$') { Write-Host 'STOPPED: -Name has 1 to 16 letters, digits or underscores.'; exit 2 }
    if (-not (Test-Path -LiteralPath $Enroll -PathType Leaf)) { Write-Host "STOPPED: no recording at $Enroll"; exit 2 }
    $file = Get-Item -LiteralPath $Enroll
    $mime = @{ '.wav' = 'audio/wav'; '.mp3' = 'audio/mpeg'; '.m4a' = 'audio/mp4' }[$file.Extension.ToLowerInvariant()]
    if (-not $mime) { Write-Host 'STOPPED: the recording must be a .wav, .mp3 or .m4a file.'; exit 2 }
    if ($file.Length -gt 10MB) { Write-Host 'STOPPED: the recording is larger than 10 MB.'; exit 2 }
    if ($file.Length -lt 20000) { Write-Host 'STOPPED: the recording is too small to hold a few seconds of speech.'; exit 2 }
    $bytes = [IO.File]::ReadAllBytes($file.FullName)
    Write-Host ("Recording: {0} ({1:N0} KB)" -f $file.Name, ($file.Length / 1KB))
    if ($mime -eq 'audio/wav') {
        # A WAV file says what it is: check it against Alibaba's rules before anything is sent.
        $ascii = [Text.Encoding]::ASCII
        if ($bytes.Length -lt 44 -or $ascii.GetString($bytes, 0, 4) -cne 'RIFF' -or $ascii.GetString($bytes, 8, 4) -cne 'WAVE') { Write-Host 'STOPPED: this is not a readable WAV file.'; exit 2 }
        $at = 12; $channels = 0; $rate = 0; $bits = 0; $dataBytes = 0
        while ($at + 8 -le $bytes.Length) {
            $id = $ascii.GetString($bytes, $at, 4); $size = [BitConverter]::ToUInt32($bytes, $at + 4)
            if ($id -ceq 'fmt ' -and $at + 24 -le $bytes.Length) { $channels = [BitConverter]::ToUInt16($bytes, $at + 10); $rate = [BitConverter]::ToUInt32($bytes, $at + 12); $bits = [BitConverter]::ToUInt16($bytes, $at + 22) }
            # The names of the parts are exact (a part called DATA is not the sound). A size of 0 or of all ones is
            # what a recorder writes when it does not go back to fill it in: the sound is then the rest of the file.
            if ($id -ceq 'data') { $rest = [long]($bytes.Length - $at - 8); $dataBytes = $(if ($size -eq 0 -or $size -eq 4294967295) { $rest } else { [Math]::Min([long]$size, $rest) }); break }
            $at += 8 + $size + ($size % 2)
        }
        if (-not ($channels -and $rate -and $bits -and $dataBytes)) { Write-Host 'STOPPED: this WAV file could not be read (no format or no sound in it).'; exit 2 }
        $seconds = $dataBytes / ($rate * $channels * ($bits / 8))
        Write-Host ("           {0:N1} seconds, {1:N0} Hz, {2}, {3}-bit" -f $seconds, $rate, $(if ($channels -eq 1) { 'mono' } else { "$channels channels" }), $bits)
        $wrong = @()
        if ($channels -ne 1) { $wrong += 'it must be mono (one channel)' }
        if ($rate -lt 24000) { $wrong += 'it must be 24,000 Hz or better' }
        if ($bits -ne 16) { $wrong += 'it must be 16-bit' }
        if ($seconds -gt 60) { $wrong += 'it must be 60 seconds at most' }
        if ($seconds -lt 3) { $wrong += 'it must hold at least 3 seconds of speech' }
        if ($wrong) { Write-Host ('STOPPED: Alibaba would refuse this recording: ' + ($wrong -join '; ') + '.'); exit 2 }
        if ($seconds -lt 10 -or $seconds -gt 20) { Write-Host '           Note: 10 to 20 seconds is what Alibaba recommends for a good voice.' }
    } else {
        Write-Host '           (not a WAV file: its length and quality are not checked here; Alibaba checks them)'
    }
    Write-Host "This creates a new cloned voice named '$Name' for the model $model on the Alibaba account of your key."
    Write-Host 'Alibaba charges for creating a voice (a small one-off amount: see Billing in the Model Studio console).'
    if ($otherKey) { Write-Host $otherKeyNote }
    if (-not $TestEndpoint) {
        if ((Read-Host 'Type YES to send the recording to Alibaba and create the voice') -cne 'YES') { Write-Host 'Nothing was sent.'; exit 0 }
    }
    $body = '{"model":"qwen-voice-enrollment","input":{"action":"create","target_model":' + (ConvertTo-Json -InputObject $model) + ',"preferred_name":' + (ConvertTo-Json -InputObject $Name) +
            ',"language":"en","audio":{"data":"data:' + $mime + ';base64,' + [Convert]::ToBase64String($bytes) + '"}}}'
    try { $made = Send $voicesUrl $body } catch { Write-Host ('NOT CREATED: ' + (Failure $_)); exit 1 }
    $new = $made.output.voice
    if (-not $new) { Write-Host 'NOT CREATED: Alibaba answered without a voice ID.'; exit 1 }
    Write-Host ''
    Write-Host "NEW VOICE ID: $new"
    Write-Host 'Put this line in the key file (replace an older QWEN_TTS_VOICE line if there is one):'
    Write-Host "QWEN_TTS_VOICE=$new"
    if ($model -ne 'qwen3-tts-vc-2026-01-22') { Write-Host "and keep this line, because the voice only works with the model it was made for:`nQWEN_TTS_MODEL=$model" }
    Write-Host 'Then quit JARVIS completely, start it again, and choose Settings > Voice > VOICE PREVIEW > Qwen.'
    Write-Host 'Run this script again without -Enroll to hear a test with the new voice (after the key file is changed).'
    exit 0
}

# ---- list the voices on the account, and try the one the key file names ----
try { $listed = Send $voicesUrl '{"model":"qwen-voice-enrollment","input":{"action":"list","page_size":50,"page_index":0}}' }
catch { Write-Host ('COULD NOT LIST THE VOICES: ' + (Failure $_)); exit 1 }
# An answer that is not the list is said to be that: it is never read as "no voices".
if (-not ($listed -is [pscustomobject] -and $listed.output -is [pscustomobject] -and ($listed.output.PSObject.Properties.Name -contains 'voice_list'))) {
    Write-Host 'COULD NOT LIST THE VOICES: Alibaba answered, but not with a list of voices.'; exit 1
}
$voices = @($listed.output.voice_list | Where-Object { $_ })
$total = 0; if ($listed.output.total_count -is [int] -or $listed.output.total_count -is [long]) { $total = [long]$listed.output.total_count }
$more = $total -gt $voices.Count
Write-Host ("Cloned voices on this Alibaba account: {0}{1}" -f $(if ($more) { $total } else { $voices.Count }), $(if ($more) { " (the first $($voices.Count) are shown)" } else { '' }))
foreach ($v in $voices) {
    $marks = @()
    if ($voice -and $v.voice -eq $voice) { $marks += 'the one in your key file' }
    if ($v.target_model -and $v.target_model -ne $model) { $marks += "made for $($v.target_model), not for $model" }
    Write-Host ("  {0}   created {1}{2}" -f $v.voice, $v.gmt_create, $(if ($marks) { '   <- ' + ($marks -join '; ') } else { '' }))
}
if (-not $voice) {
    Write-Host 'The key file has no QWEN_TTS_VOICE line, so JARVIS has no Qwen voice to speak with.'
    if ($voices.Count) { Write-Host 'To use one of the voices above, add the line QWEN_TTS_VOICE=<its ID> to the key file.' }
    else { Write-Host 'To create one: run this script with -Enroll <a recording of the voice>.' }
    exit 0
}
$known = @($voices | Where-Object { $_.voice -eq $voice })
if (-not $known.Count -and $more) { Write-Host "The voice in your key file ($voice) is not among the voices shown; the account has more than this tool lists." }
elseif (-not $known.Count) { Write-Host "The voice in your key file ($voice) is NOT on this account. It may belong to another Alibaba account or have been deleted." }
elseif ($known[0].target_model -and $known[0].target_model -ne $model) {
    Write-Host "The voice in your key file was made for the model $($known[0].target_model), but JARVIS would ask $model. Add this line to the key file:"
    Write-Host "QWEN_TTS_MODEL=$($known[0].target_model)"
    $model = $known[0].target_model
}
$speak = '{"model":' + (ConvertTo-Json -InputObject $model) + ',"input":{"text":"At your service, Mr. Teague. This is the Qwen voice test.","voice":' + (ConvertTo-Json -InputObject $voice) + ',"language_type":"English"}}'
$clock = [Diagnostics.Stopwatch]::StartNew()
try { $spoken = Send $speakUrl $speak } catch { Write-Host ('qwen voice  DOES NOT SPEAK: ' + (Failure $_)); exit 1 }
$sound = $null
if ($spoken.output.audio.data) { $sound = [Convert]::FromBase64String($spoken.output.audio.data) }
elseif ($spoken.output.audio.url) {
    # A link to the finished sound, good for a short time. Fetched without the key, and only from Alibaba.
    $link = [string]$spoken.output.audio.url
    if (-not ($TestEndpoint -or (Alibaba $link))) { Write-Host 'qwen voice  DOES NOT SPEAK: the answer held no usable sound link.'; exit 1 }
    try { $sound = (New-Object Net.WebClient).DownloadData($link) } catch { Write-Host ('qwen voice  DOES NOT SPEAK: the sound could not be fetched: ' + $_.Exception.Message); exit 1 }
}
$clock.Stop()
if (-not $sound -or $sound.Length -lt 100) { Write-Host 'qwen voice  DOES NOT SPEAK: the answer held no sound.'; exit 1 }
$isWav = $sound.Length -gt 4 -and [Text.Encoding]::ASCII.GetString($sound, 0, 4) -eq 'RIFF'
$out = Join-Path $env:TEMP ('jarvis-qwen-voice-test.' + $(if ($isWav) { 'wav' } else { 'mp3' }))
[IO.File]::WriteAllBytes($out, $sound)
Write-Host ("qwen voice  SPEAKS ({0}, {1:N1} s, {2:N0} KB)" -f $model, $clock.Elapsed.TotalSeconds, ($sound.Length / 1KB))
Write-Host "Listen to it: $out"
Write-Host 'This shows that Alibaba makes sound with this voice. Whether it sounds right is for your ears.'
