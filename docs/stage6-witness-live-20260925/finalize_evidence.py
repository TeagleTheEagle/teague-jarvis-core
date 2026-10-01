import pathlib,json,hashlib,sys,zipfile,contextlib
R=pathlib.Path(__file__).parent;load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2)
v=load(R/'preflight-result.json');C=pathlib.Path(v['candidate']);root=pathlib.Path(v['runRoot']);P=R.parent/'stage6-lifecycle-witness-20260925';S=P/'candidate'
sys.path.insert(0,str(C));import failure_preserve_v4 as f
assert load(R/'postrun-census.json')['status']=='PASS' and load(R/'recorded-instance-postrun.json')['clean']
comparisons=[]
for base,name,expected in [(C,'small-source-v3.json',v['sourceManifestSHA256']),(C,'witness-source-v1.json',v['witnessManifestSHA256']),(S,'small-source-v3.json','3c8efb4e22ed98ef4e6a5e63a7a0040f36d10fbe40e1cb427eba760fc9e46576'),(pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\ea85ed4b4ef14769acbe0b5e750aaed2\code'),'small-source-v3.json','5966bdb43ed1efaa85f6956dd0552c7459f2eef4e1d7970e5143ac1376b316ef')]:
 assert sha(base/name)==expected
 rows=load(base/name)
 for row in rows:
  p=base/row['name'];assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes']
 comparisons.append(dict(base=str(base),manifest=name,sha256=expected,files=len(rows),status='PASS'))
for receipt in v['archives']:assert sha(pathlib.Path(receipt['archive']))==receipt['sha256']
assert sha(root/'workspace-binding-v4.json')==v['workspaceBindingSHA256']
one=load(root/'hash-pass-1.json')['files'];two=load(root/'hash-pass-2.json')['files'];assert one==two and len(one)==12
for row in one.values():
 p=pathlib.Path(row['fullPath']);assert p.stat().st_mtime_ns==row['mtime_ns'] and p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
save(R/'preservation-verification.json',dict(status='PASS',manifests=comparisons,historicalArchives='UNCHANGED',datasetFiles=12,datasetBytes=786432,hashPassesMatch=True,metadataUnchanged=True,candidateChangesDuringRun=False,frozenCheckerChanged=False,protectedVMAccess=False,productionChange=False))
summary=load(R/'analysis-summary.json');targets=load(R/'independent-targets.json')['instances']
lines=['# One lifecycle-witness diagnostic — REJECTED run','',
'Final diagnosis: **ETW_SESSION_LOSS_PRIMARY**. This identifies the strongest supported mechanism for this run; it does not prove the precise lost payload identities or the underlying cause of session loss. Historical ETW-loss cause remains UNCONFIRMED.',
'',f"Run: `{v['run']}`",f"Workspace: `{C}`",'Exactly one normal small run; three existing observer prompts; no retry, rebuild, setting change or code correction.',
'','## Outcome','Both 12-file / 786,432-byte SHA-256 passes matched; source metadata unchanged. Phase A completed. First terminal failure: `terminal trace loss/query`; launcher: `Authority terminal failure`; driver: `LAUNCHER_FAILED`. Authority and detailed observers exited 95; application observer exited 0. Terminal receipt was not accepted; checker and success finalizer were not invoked.',
'','## Witness and exact target correlation',
'Both witness sidecars are quiesced, sequence-complete and non-overflowed: authority 42 records; detailed 28 records. Both approved analyzers completed with zero missing roles. Correlation uses creator-owned native handles for direct processes and independent creation-verified tracker handles/images for consoles. It is diagnostic correlation, not kernel qualification. Windows are independently bounded by process creation/retention and kernel-handle signal observations; no witness-derived timestamps or PID-only matching.',
'','| Role | PID | Creation FILETIME | Authority START / STOP | Detailed START / STOP |','|---|---:|---|---|---|']
for t in targets:
 lines.append(f"| {t['role']} | {t['pid']} | {t['created']} | NOT OBSERVED / NOT OBSERVED | NOT OBSERVED / NOT OBSERVED |")
lines+=['','For every listed target, selector disposition, parentKnown, instanceKnown, admission, exact event QPC and callback-arrival QPC are **UNKNOWN / unavailable** because neither callback observation exists. Each independently bounded START/STOP window overlaps increases in both sessions. Full bounds, all counter increments and observation fields are in `independent-targets.json`, the two `*-analysis.json` files and `*-loss-increments.json`. No callback absence is converted into proof of an exact lost payload.',
'','The collector (PID 9036, creation 134347961765298403) was admitted in both channels: authority START event/arrival QPC 6290014286604 / 6290031998114 and STOP 6290043463031 / 6290054387266; detailed START 6290014286607 / 6290029874972 and STOP 6290043463033 / 6290049923030. No target UNKNOWN_PARENT/UNKNOWN_INSTANCE rejection was observed. A parent-filter cascade is therefore not established by this run. No target was witnessed admitted, so no target-specific downstream persistence defect is established.',
'','## Loss / persistence','| Channel | Final EventsLost | Minimum sampled FreeBuffers | Maximum NumberOfBuffers | Writer queue high items / bytes |','|---|---:|---:|---:|---:|']
for ch,x in summary.items():lines.append(f"| {ch} | {x['finalEventsLost']} | {x['minFreeBuffers']} | {x['maxBuffers']} | {x['queueHighItems']} / {x['queueHighBytes']} |")
for ch,x in summary.items():
 lines+=['',f'### {ch} observed increment windows (QPC; frequency 10,000,000)']
 for inc in x['incrementWindows']:lines.append(f"- {inc['beginQpc']}–{inc['endQpc']}: {inc['fromCount']} → {inc['toCount']}")
lines+=['','Counter sampling did not observe zero free buffers; it cannot rule out a transient between samples. The detailed writer backlog and delayed callbacks are observations, not proof of the underlying loss cause. Telemetry reported zero errors/overflow in both channels. Authority and detail stop/consumer results were 0, but EventsLost invalidates acceptance. Supporting CIM remains preserved and is not substituted for authoritative evidence.',
'','## Cleanup and preservation limitation','Original absolute cleanup origin/deadline: 6290028948913 / 6290228948913 (20 seconds, never reset). Launcher FINAL_SHUTDOWN at 6290199478863: 17.053 seconds after origin. This is not full acceptance cleanup proof: terminal evidence failed and normal census/checker path was never reached.',
'The original failure-preserver returned CLEANUP_UNPROVEN / FAILURE_EVIDENCE_PARTIAL and archived two metadata members with no run-content members. Its first census detected pwsh PID 2236, creation 134347961971886233, during the assistant’s concurrent read-only status inspection. That historical result is unchanged. No second live attempt or success sealing occurred.',
'A subsequent host census found zero matching diagnostics/VirtualBox processes and zero traces. The independent recorded-instance check covered 16 identities, with zero remaining/unknown. This establishes eventual cleanup only. A separate post-quiescence NON-ACCEPTANCE archive preserves the full raw run, original partial preservation output, sidecars, analysis, candidate and source verification under deny-write/delete read locks; it does not repair acceptance.',
'Maximum recorded application heartbeat interval: 1.1667263 seconds (<10). Both probe hard-deadline flags were false. No observer/trace remains. Protected VM/configuration was never accessed; production unchanged. Only the two explicitly approved fresh-workspace path JSONs were rebound before launch; all other candidate bytes and frozen sources remain unchanged.',
'','An offline read-only summary command had a SyntaxError (unmatched closing parenthesis); it did not run or alter any diagnostic. The corrected read used Get-Content only. No failed live evidence was changed.',
'','## Disposition','Stage 6 remains incomplete. No medium, large, protected-baseline or production operation performed. No acceptance commit. Stop for owner review; any correction requires separate authorization.','HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.']
(R/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
sources=[]
for p in root.rglob('*'):
 if p.is_file():sources.append(('raw-run/'+p.relative_to(root).as_posix(),p))
pres=C.parent/'preservation-v4'/('FAILURE-EVIDENCE-'+v['run'])
for p in pres.iterdir():
 if p.is_file():sources.append(('original-partial-preservation/'+p.name,p))
for p in C.glob(v['run']+'.*lifecycle-witness*.json'):sources.append(('witness/'+p.name,p))
for row in load(C/'small-source-v3.json'):sources.append(('candidate/'+pathlib.PureWindowsPath(row['name']).as_posix(),C/row['name']))
for name in ('small-source-v3.json','witness-source-v1.json'):sources.append(('candidate/'+name,C/name))
for p in R.iterdir():
 if p.is_file() and p.name not in ('evidence.zip','archive-manifest.json','archive-receipt.json'):sources.append(('report/'+p.name,p))
manifest=[]
with contextlib.ExitStack() as stack:
 held=[]
 for name,p in sorted(sources):
  stream=stack.enter_context(f.locked_read(p));data=stream.read();digest=hashlib.sha256(data).hexdigest();held.append((name,p,stream,digest));manifest.append(dict(member=name,path=str(p),bytes=len(data),sha256=digest))
 with zipfile.ZipFile(R/'evidence.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
  for name,p,stream,digest in held:stream.seek(0);z.writestr(name,stream.read())
  z.writestr('archive-manifest.json',json.dumps(manifest,indent=2))
 with zipfile.ZipFile(R/'evidence.zip') as z:
  assert len(z.namelist())==len(manifest)+1 and z.testzip() is None
  for row in manifest:assert hashlib.sha256(z.read(row['member'])).hexdigest()==row['sha256']
 for name,p,stream,digest in held:stream.seek(0);assert hashlib.file_digest(stream,'sha256').hexdigest()==digest
save(R/'archive-manifest.json',manifest)
receipt=dict(status='PASS',label='NON-ACCEPTANCE POST-QUIESCENCE DIAGNOSTIC EVIDENCE',archive=str(R/'evidence.zip'),sha256=sha(R/'evidence.zip'),verifiedMembers=len(manifest)+1,bytes=(R/'evidence.zip').stat().st_size,runOutcome='REJECTED',diagnosis='ETW_SESSION_LOSS_PRIMARY',originalPartialArchiveUnchanged=True)
save(R/'archive-receipt.json',receipt);print(json.dumps(receipt))
