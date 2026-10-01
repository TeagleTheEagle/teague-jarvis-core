param([string]$OutputDirectory)
$ErrorActionPreference='Stop'
if(-not $OutputDirectory.StartsWith($PSScriptRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Synthetic child directory only'}
Add-Type -Path (Join-Path $PSScriptRoot 'event_queue.cs')
$s='SyntheticCrash-'+[guid]::NewGuid();$x=[ExactEventQueue]::new($ExecutionContext.Events.ReceivedEvents,[string[]]@($s))
1..8|ForEach-Object {New-Event -SourceIdentifier $s|Out-Null}
$selected=$x.Select()
@{identity=@{pid=$PID;created=(Get-Process -Id $PID).StartTime.ToUniversalTime().ToFileTimeUtc().ToString()};queue=$x.Stats();selectedSequence=$selected.QueueSequence;scenario='consumer selected entry before persistence'}|ConvertTo-Json -Depth 6|Set-Content -LiteralPath (Join-Path $OutputDirectory 'ready.json')
Start-Sleep -Seconds 60
throw 'Parent did not perform bounded injection'
