# Pre-change validation-only defect
The archived source paths and SHA-256 values are in source-before.json. All originals remain untouched.

monitor.ps1: Register-CimIndicationEvent creates local Win32_ProcessStartTrace / Win32_ProcessStopTrace subscriptions. Callback source is Microsoft.Management.Infrastructure.CimCmdlets.CimIndicationWatcher.CimIndicationArrived. PowerShell queues PSEventArgs in System.Management.Automation.PSEventArgsCollection, exposed through ExecutionContext.Events.ReceivedEvents; its enqueue notification is PSEventReceived. EventTap.AttachSource/AttachQueue observe these without consuming them.

Drain obtains Get-Event snapshots, serializes the selected PSEventArgs.SourceEventArgs.NewEvent using ConvertTo-Json and writes it using System.IO.File.AppendAllText. It then executes the defective destructive operation:

    Remove-Event -EventIdentifier $ev.EventIdentifier

This removes every matching external number, not just the successfully written object. The finally cleanup also pipes pending entries into Remove-Event. Both destructive numeric-key paths must disappear from the candidate. JARVIS runtime code is not involved.
