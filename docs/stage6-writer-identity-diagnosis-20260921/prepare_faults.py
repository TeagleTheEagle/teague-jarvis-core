import pathlib,json
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'freeze.json').read_text())['newCode'])
p=C/'AuthoritativeEvents.cs';s=p.read_text()
with (R/'AuthoritativeEvents.before-fault-tests.cs').open('x') as f:f.write(s)
needle='long q=Stopwatch.GetTimestamp();stream.Write(item.bytes,0,item.bytes.Length);'
assert needle in s
s=s.replace(needle,'if(inject==5 && persisted>=3)throw new IOException("INJECTED_PARTIAL_BATCH");if(inject==6){stream.Write(item.bytes,0,item.bytes.Length/2);throw new IOException("INJECTED_PARTIAL_APPEND");}'+needle)
p.write_text(s)
for n in ['WriterFaults.cs','focused.ps1']:
 with (C/n).open('xb') as f:f.write((R/n).read_bytes())
with (R/'fault-preparation-transitional-failure.json').open('x') as f:json.dump({'failure':'Inline Python quoting SyntaxError before any file modification; focused script not created or run','correction':'Use a reviewable standalone preparation script','originalOutputPreserved':'tool transcript'},f)
