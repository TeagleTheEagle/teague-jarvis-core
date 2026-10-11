import pathlib,uuid,json,hashlib,shutil
R=pathlib.Path(__file__).parent
old=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\f469b94b665e4808af1c5bb6aa46b207\code')
root=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE')/('instance-stream-'+uuid.uuid4().hex);root.mkdir();code=root/'code';code.mkdir()
s=(old/'trace_sink.hpp').read_text()
before=hashlib.sha256((old/'trace_sink.hpp').read_bytes()).hexdigest()
def replace(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
replace('bytes=0,records=0;std::string hash;', 'bytes=0,records=0,first=0,last=0;std::string hash;')
replace('queued=0,accepted=0,totalBytes=0,persisted=0;', 'queued=0,accepted=0,totalBytes=0,persisted=0,attempted=0;')
replace('auto begin=q();LARGE_INTEGER freq;', 'auto begin=q();if(inject==4)Sleep(500);LARGE_INTEGER freq;')
replace('ok=BCryptFinishHash(hash,digest,32,0)>=0&&ok;', 'ok=inject!=5&&BCryptFinishHash(hash,digest,32,0)>=0&&ok;')
replace('auto& s=segments.back();s.bytes+=row.size();++s.records;segmentBuffer+=row;', 'auto& s=segments.back();auto seq=acceptedSequence(row);if(!s.records)s.first=seq;s.last=seq;s.bytes+=row.size();++s.records;segmentBuffer+=row;')
replace('public:\n TraceSink', 'static unsigned long long acceptedSequence(const std::string& row){return std::stoull(row.substr(7));}\npublic:\n TraceSink')
replace("row+='\\n';std::lock_guard<std::mutex> guard(lock);", 'std::lock_guard<std::mutex> guard(lock);++attempted;\n  if(row.size()<2||row.front()!=\'{\'||row.back()!=\'}\'){failure=11;return false;}\n  row="{\\\"seq\\\":"+std::to_string(accepted+1)+","+row.substr(1)+"\\n";')
replace('<<",\\\"records\\\":"<<x.records<<",\\\"sha256\\\":\\\""', '<<",\\\"records\\\":"<<x.records<<",\\\"firstSequence\\\":"<<x.first<<",\\\"lastSequence\\\":"<<x.last<<",\\\"sha256\\\":\\\""')
replace('<<failure<<",\\\"accepted\\\":"', '<<failure<<",\\\"attempted\\\":"<<attempted<<",\\\"accepted\\\":"')
replace('segmented-jsonl-v1','sequenced-prototype-v1')
(code/'trace_sink.hpp').write_text(s)
shutil.copy2(R/'stream_bench.cpp',code/'stream_bench.cpp')
shutil.copy2(old/'J6Probe.exe',code/'J6Probe.exe')
plan=dict(root=str(root),code=str(code),originalSink=str(old/'trace_sink.hpp'),originalSinkSHA256=before,prototypeSinkSHA256=hashlib.sha256((code/'trace_sink.hpp').read_bytes()).hexdigest(),probeSHA256=hashlib.sha256((code/'J6Probe.exe').read_bytes()).hexdigest(),productionChanges=False)
(R/'plan.json').write_text(json.dumps(plan,indent=2));print(json.dumps(plan))
