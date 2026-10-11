import pathlib,json,shutil
R=pathlib.Path(__file__).resolve().parent;C=pathlib.Path(json.loads((R/'before.json').read_text())['candidate'])
for n in ('coordination_v3.py','evidence_support_v3.py','external_driver_v3.py','completed_v3.py','terminal_control_v3.ps1','test_coordination_v3.py'):shutil.copyfile(R/n,C/n)
def edit(name,old,new):
 p=C/name;s=p.read_text();assert old in s,(name,old);p.write_text(s.replace(old,new))
edit('traced_collect_v3.py','try:bridge.close()',"try:\n   from evidence_support_v3 import close_bridge_v3\n   close_bridge_v3(root,bridge)")
edit('small_launch_v3.ps1',"Start-Sleep -Milliseconds 10}","Start-Sleep -Milliseconds ([Math]::Max(1,[Math]::Min(10,[Math]::Floor((Budget)*1000))))}")
edit('small_finalize_v3.py',"TOP=set('","TOP=set('driver-stdout-v3.bin driver-stderr-v3.bin ")
# State receipts are derived from independently checked completed evidence, not a live authority grant.
edit('small_finalize_v3.py',"write(root/'v3-check-result.json',dict(result=result,inputManifestSHA256=sha(root/'v3-input-manifest.json')))","write(root/'v3-check-result.json',dict(state='CHECKER_FINALIZATION_ALLOWED',result=result,inputManifestSHA256=sha(root/'v3-input-manifest.json')))")
edit('small_finalize_v3.py',"receipt=dict(status=", "receipt=dict(state='ACCEPTED' if normal else 'REJECTED',status=")
# Collect complete external state receipts. This controller never starts the finalizer.
edit('external_driver_v3.py',"   verify_complete(root)\n   print", "   verify_complete(root)\n   states=[dict(state=s,owner=OWNERS[i],binding=p['binding']) for i,s in enumerate(STATES[:12])]\n   write_once(root/'coordination-states-v3.json',dict(kind='evidence-reconciled-state-sequence',states=states,evidence={n:digest(root/n) for n in ('phase-a-v3.json','terminal-v3.json','workload-census-v3.json','integration-launcher.json','external-exits-v3.json','final-census-v3.json')}))\n   print")
print('WIRING_REFINED_NO_LIVE_EXECUTION')
