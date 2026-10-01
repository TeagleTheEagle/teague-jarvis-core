import pathlib,json,hashlib,zipfile,os,re,datetime
R=pathlib.Path(__file__).parent
request=pathlib.Path(r'C:\Users\jonny\.codex\attachments\11368871-10bd-44b2-9e6d-8cae6486fbd1\Pasted text.txt').read_text(encoding='utf-8-sig')
section=request.split('MANDATORY REPORT',1)[1].split('HISTORICAL ACCURACY RULE',1)[0]
labels=re.findall(r'(?m)^(\d+)\. (.+)$',section);assert len(labels)==58
incident=json.loads((R/'preservation-incident.json').read_text())
values={1:'Inspection started, but map was not completed. No integration authorized to continue after Phase0 integrity failure.',2:'Not changed. All current required evidence roles retained.',3:'Not changed; current bounded tap remains acceptance-critical.',4:'Read-only inspection: EventTap.Add retains first20,000 rows, increments Overflow and discards subsequent rows. ExactEventQueue also caps cumulative identity count at20,000. Neither was changed.',5:'No new model implemented. Prior proposed composite remains unaccepted for full independent CIM correlation.',6:'No new API experiment performed. Earlier supported handle/snapshot results remain historical focused evidence.',7:'Not implemented.',8:'Unchanged:21 AMBIGUOUS,1 UNMATCHED,0 forced matches.',9:'0 new identity tests.',10:'Not measured in this pass; do not infer a PASS from no execution.',11:'NOT RUN.',12:'Not implemented.',13:'Not changed.',14:'Not changed.',15:'Not recalculated.',16:'Earlier failed larger-record queue-exhaustion evidence preserved in unchanged archive.',17:'Not changed or newly validated.',18:'NOT RUN.',19:'NOT MEASURED.',20:'NOT MEASURED.',21:'NOT MEASURED.',22:'NOT MEASURED.',23:'NOT MEASURED.',24:'NOT MEASURED; no tracer started.',25:'NOT MEASURED in a new run.',26:'Current implementation inspected only; still fatal to existing acceptance.',27:'Not changed.',28:'NOT RUN.',29:'NOT MEASURED.',30:'NOT MEASURED.',31:'NOT MEASURED.',32:'NOT MEASURED.',33:'No new distribution measured.',34:'No new measurement.',35:'No new authoritative segments generated.',36:'NOT MEASURED.',37:'NOT MEASURED; no monitor started.',38:'No probe run performed; no acceptance conclusion.',39:'NOT RUN.',40:'NOT RUN.',41:'Preflight host query found0 matching diagnostic/VirtualBox processes and0 trace sessions. No observer/hash worker launched.',42:'Prior143-member archive fully hash-reverified and unchanged; new incident archive receipt records its member count/hash.',43:'Not recalculated; no integrated evidence.',44:'Not recalculated.',45:'Not established.',46:'Not recalculated.',47:'Not recalculated.',48:'Not established.',49:'Not established for actual integrated harness.',50:'Not newly measured after stop.',51:'Not recalculated.',52:'Not established.',53:'116 frozen candidate hashes plus6 additional frozen checks unchanged. Exactly one prior local evidence file overwritten; details below.',54:'Protected VM/configuration NOT ACCESSED.',55:'Production JARVIS NOT CHANGED.',56:'Historical delay causes remain UNCONFIRMED. HISTORICAL STAGE1 CAUSE: UNCONFIRMED.',57:'NOT ELIGIBLE; stopped at mandatory preservation gate.',58:'BLOCKED — local historical evidence overwritten during preflight.'}
text='# Stage6 authoritative integration — preservation gate stop\n\n**BLOCKED**\n\nThe agent reused the previous `final_host.ps1` rather than creating a fresh destination. Its `Set-Content` replaced the previous local `final-host-state.json` with the new host check. This was an agent execution error. The user explicitly required stopping on any Phase0 integrity failure; integration has therefore stopped.\n\n'
text+='The canonical143-member archive remains byte-identical and every member reverified. The original host-state bytes were recovered into a **separate new evidence file**; no restoration or edit to the historical file was performed. Both original and replacement state report zero processes/traces, but their capture timestamps differ. Same result does not make the overwrite acceptable.\n\n'
text+='## Exact discrepancy\n\n'
for x in incident['localEvidenceMismatches']:text+=f"- Affected path: `{x['path']}`\n- Archived original SHA-256: `{x['expected']}`\n- Current replacement SHA-256: `{x['actual']}`\n"
text+='\nOriginal capture:2026-09-21T02:32:12.6286293Z. Replacement capture:2026-09-21T02:41:15.8810587Z. No other archived local payload mismatch found.\n\n'
text+='## Mandatory report dispositions\n\n'
for number,label in labels:text+=f'{number}. **{label.strip()}** — {values[int(number)]}\n\n'
text+='## Preserved files\n\n'
for name in ('preservation-incident.json','original-host-state-from-verified-archive.json','new-host-state-after-accidental-overwrite.json'):
 text+=f'- [{name}]({(R/name).as_posix()})\n'
text+='\n## Proposed next owner-reviewed action\n\nReview this preservation incident. If authorized, restore only the affected local evidence file byte-for-byte from the independently verified archive, keep both incident copies, and verify the original SHA-256. Future host checks must accept an explicit fresh run destination and use exclusive creation so historical files cannot be overwritten. Then repeat Phase0 integrity validation before integration. None of those recovery changes has been executed.\n\nNo UAC prompt, elevated monitoring component, medium run, large dataset access, VM operation, protected hashing, production operation or integration source change occurred. New preparation/report scripts are confined to this evidence directory; prepare.py was never executed.\n'
with (R/'REPORT.md').open('x',encoding='utf-8') as f:f.write(text)
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
files=[p for p in sorted(R.iterdir()) if p.is_file()]
manifest={'status':'BLOCKED','files':[{'name':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]}
payload=(json.dumps(manifest,indent=2)+'\n').encode()
archive=R.parent/'stage6-authoritative-integration-20260921-preservation-incident.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for p in files:z.write(p,p.name)
 z.writestr('manifest.json',payload)
with archive.open('r+b') as f:os.fsync(f.fileno())
A=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 AUTHORITATIVE INTEGRATION PRESERVATION INCIDENT 20260921')
A.mkdir(exist_ok=False)
dest=A/'evidence.zip'
with dest.open('xb') as f:f.write(archive.read_bytes());f.flush();os.fsync(f.fileno())
assert sha(dest)==sha(archive)
with zipfile.ZipFile(dest) as z:
 assert len(z.namelist())==len(set(z.namelist()))==len(files)+1
 assert z.read('manifest.json')==payload
 for row in manifest['files']:assert hashlib.sha256(z.read(row['name'])).hexdigest()==row['sha256']
receipt={'status':'HASH_VERIFIED','acceptance':'BLOCKED','path':str(A),'members':len(files)+1,'sha256':sha(dest),'reportSHA256':sha(R/'REPORT.md'),'prior143MemberArchiveUnchanged':True}
for p in (R/'archive-verification.json',A/'archive-verification.json'):
 with p.open('x') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt))
