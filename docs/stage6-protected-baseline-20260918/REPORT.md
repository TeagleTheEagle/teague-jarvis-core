# Protected baseline capture — BLOCKED

The elevated monitoring capability was established, but the collector aborted during the first base-VDI hash when its monitoring heartbeat became stale. No baseline manifest was completed. Do not accept this attempt or retry/increase thresholds without diagnosing the monitoring reliability issue.

## Elevated method and attempts

The monitor uses temporary WMI Win32_ProcessStartTrace/Win32_ProcessStopTrace subscriptions for names beginning VBox or VirtualBox. It queries process/service state and writes only task-local monitoring evidence. No protected VM files are read by the elevated helper. The hash collector runs unelevated. No execution policy override, account/ACL change, permanent event consumer, VirtualBox invocation or VM operation occurred.

Installed executables covered: VirtualBox.exe, VirtualBoxVM.exe, VBoxHeadless.exe, VBoxManage.exe, VBoxSVC.exe, VBoxSDS.exe, VBoxAudioTest.exe, VBoxAutostartSvc.exe, VBoxBalloonCtrl.exe, VBoxBugReport.exe, VBoxDrvInst.exe, VBoxDTrace.exe, VBoxExtPackHelperApp.exe, VBoxNetDHCP.exe, VBoxNetNAT.exe, VBoxWebSrv.exe. Prefix matching also covers future similarly named helpers.

1. Windows PowerShell launch PID 9460 exited without a readiness record. Windows PowerShell showed all execution-policy scopes Undefined, whereas the PowerShell 7 host showed LocalMachine RemoteSigned. No policy was changed. No redirected startup error was available; exact first-launch exit cause is not proven.
2. Microsoft-signed installed PowerShell 7 launch PID 7280 established both subscriptions and found zero processes, but the evidence writer failed on File.Replace with a null backup path marshalled as empty. Failure preserved in root monitor-failure.json. No protected hashing began during that attempt.
3. A separate run2 helper used File.Move(temp,target,true) for its own evidence heartbeat replacement. Original attempt files were retained. PID 17248 established monitoring at 2026-09-18T03:09:32.5689892Z, zero initial processes, VBoxSDS stopped. Hash collection then began unelevated.

The elevated token has administrator capabilities; read-only monitoring is a reviewed-code restriction, not a claim that Windows enforces a read-only administrator token.

## Exact capture failure

Collector progressed through the small machine NVRAM and two .vbox files, then began JARVIS-CLEAN-WIN11.vdi. It stopped inside digest() → monitor() with:
RuntimeError: Monitoring heartbeat stale or violation

The recorded heartbeat was 2026-09-18T03:13:01.8805176Z, events=0, violations=0, ACTIVE. Collector failure timestamp was 2026-09-18T03:13:15.554634Z: about 13.674 seconds later, beyond the collector's 10-second health threshold. This establishes stale health evidence, not a VirtualBox start, and not a protected-source defect. The reason for the heartbeat delay is UNCONFIRMED. No arbitrary threshold increase or automatic hash retry performed.

Collector wrote BLOCKED completion at 03:13:15.557027Z. Monitor completed at 03:13:17.6805023Z with zero recorded events and empty final process list, then exited; PID 17248 was absent on follow-up. Its monitor-final.json Status=PASS only describes its event-count/final-process check; it DOES NOT override the collector failure or constitute baseline acceptance.

## Preservation and inventory

Protected inventory: 12 files, 59,665,402,098 bytes.
Normal .VirtualBox tree inventory: 17 files, including VirtualBox.xml, VirtualBox.xml-prev and existing logs. No contents copied into this evidence bundle; inventories contain paths, sizes and timestamps.
After failure, all 29 files retain size and LastWriteTimeUtc. Small hashes remain equal to prior evidence:
- original .vbox: 98a89e62fd19ba49dc316b6e9c902fb6ba18fe4c66ec0ba8bf20deb3a892e93c
- original .vbox-prev: 9d69cc14a480aac13c9c03817aeeb4bc4d068a6fc27a81fc15ff2bc91de2c797
- normal VirtualBox.xml: f05da097d96f073a2569488a0fffc1682d7034e69069bab51b4409d88c2bdf0d

This is not full content-preservation proof. The interrupted base-VDI hash did not complete and the second full pass did not run. No completed SHA-256 manifest exists; no manifest hash can be reported as a baseline.

Networking remains three distinct facts: protected POST-INCIDENT=1; historical/pre-incident evidence=0; required future validation-copy=0. No repair, normalization, XML edit or .vbox-prev restoration occurred.

Read-only XML inspection confirmed the known machine UUID, two-snapshot chain, three-disk chain, snapshot NVRAM references and external ISO references. A complete baseline relationship manifest is not claimed because capture did not finish.

## Next step

Diagnose the monitor's heartbeat publication/observation delay using only disposable monitoring evidence; do not start VirtualBox as a test stimulus or touch the protected VM. Preserve this attempt. Establish reliable health signalling before another full capture. No owner VM action is needed now; keep VirtualBox closed.

Production unchanged. No account creation, ACLs, VM copy, guest validation or later phase begun. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
