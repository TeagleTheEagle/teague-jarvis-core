# TEST-only complete-record publication. Caller supplies its validated D: run root.
function New-J6HealthPublisher($Root, $Identity) {
    $path = Join-Path $Root 'app-health.jsonl'
    $stream = [IO.FileStream]::new($path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
    return @{Stream=$stream; Identity=$Identity; Sequence=0; Failed=$false; Closed=$false}
}
function Write-J6HealthRecord($Publisher, [long]$Ticks) {
    if($Publisher.Failed -or $Publisher.Closed){throw 'Health publisher unavailable'}
    try {
        $i=$Publisher.Identity; $next=$Publisher.Sequence+1
        $row=@{run=$i.run;pid=$i.pid;created=$i.created;frequency=$i.frequency;seq=$next;pump=$next;ticks=$Ticks;utc=[DateTime]::UtcNow.ToString('o');state='ACTIVE';violations=0}
        $bytes=[Text.Encoding]::UTF8.GetBytes((($row|ConvertTo-Json -Compress)+"`n"))
        if($bytes.Length -gt 4096 -or $Publisher.Stream.Length+$bytes.Length -gt 1048576){throw 'Health journal capacity reached'}
        $Publisher.Stream.Write($bytes,0,$bytes.Length)
        $Publisher.Stream.Flush($true)
        $Publisher.Sequence=$next
    } catch {$Publisher.Failed=$true;throw}
}
function Publish-J6Ready($Root, $Publisher, $Ready) {
    if($Publisher.Failed -or $Publisher.Closed -or $Publisher.Sequence -lt 1){throw 'No completed initial health publication'}
    $temp=Join-Path $Root 'app-ready.pending'
    $final=Join-Path $Root 'app-ready.json'
    $bytes=[Text.Encoding]::UTF8.GetBytes(($Ready|ConvertTo-Json -Depth 12))
    if($bytes.Length -gt 4096){throw 'Ready record exceeds bound'}
    $f=[IO.FileStream]::new($temp,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try {$f.Write($bytes,0,$bytes.Length);$f.Flush($true)} finally {$f.Dispose()}
    [IO.File]::Move($temp,$final) # Destination must be absent; never overwrite.
}
function Close-J6HealthPublisher($Publisher) {
    if($Publisher.Closed){return}
    try {
        if($Publisher.Failed){throw 'Health publisher failed'}
        $Publisher.Stream.Flush($true)
    } catch {$Publisher.Failed=$true;throw}
    finally {$Publisher.Stream.Dispose();$Publisher.Closed=$true}
}
