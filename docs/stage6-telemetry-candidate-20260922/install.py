import json,hashlib,difflib
from pathlib import Path
R=Path(__file__).parent;pre=json.loads((R/'candidate.json').read_text());C=Path(pre['code'])
p=C/'durable_sink.hpp';old=p.read_text();s=old
def replace(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
replace('State state=ACTIVE;', 'State state=ACTIVE;\n  U enqueued=0,dequeued=0,completed=0,flushBegin=0,flushEnd=0,hashBegin=0,hashEnd=0,waitBegin=0,waitEnd=0;')
replace('struct Item{U seq;std::string raw;};','struct Item{U seq;std::string raw;U admitted;};\n struct Snapshot{U tick,kind,id,rawBytes,input,inflight,bytes,sealed,pending,pendingBytes;};\n static constexpr U telemetryCap=65536;std::vector<Snapshot> telemetry;\n U clockFrequency=0,backpressureStarted=0,backpressureCompleted=0,backpressureInterrupted=0,blockedTicks=0;\n U dequeuedCount=0,completedCount=0,dequeueLagTicks=0,maxDequeueLagTicks=0,completionLagTicks=0,maxCompletionLagTicks=0;')
replace('void fault(int id)', '''void snapshot(U kind,U id=0,U raw=0){
  if(telemetry.size()>=telemetryCap||(inject==18&&telemetry.size()>=4)){fail(15);return;}
  telemetry.push_back({U(q()),kind,id,raw,U(input.size()),inflightItems,queueBytes,U(sealed.size()),pending,pendingBytes});
 }
 std::string telemetryJson(){
  std::ostringstream o;o<<"{\\"schema\\":\\"stage6-writer-telemetry-v1\\",\\"frequency\\":"<<clockFrequency<<",\\"capacity\\":"<<telemetryCap<<",\\"snapshotBytes\\":"<<sizeof(Snapshot)<<",\\"allocatedBytes\\":"<<telemetryCap*sizeof(Snapshot)<<",\\"overflow\\":"<<(failure==15?"true":"false")
   <<",\\"backpressure\\":{\\"started\\":"<<backpressureStarted<<",\\"completed\\":"<<backpressureCompleted<<",\\"interrupted\\":"<<backpressureInterrupted<<",\\"ticks\\":"<<blockedTicks<<"}"
   <<",\\"lag\\":{\\"dequeued\\":"<<dequeuedCount<<",\\"completed\\":"<<completedCount<<",\\"dequeueTicks\\":"<<dequeueLagTicks<<",\\"maxDequeueTicks\\":"<<maxDequeueLagTicks<<",\\"completionTicks\\":"<<completionLagTicks<<",\\"maxCompletionTicks\\":"<<maxCompletionLagTicks<<"}"
   <<",\\"windows\\":{\\"firstWrite\\":"<<firstWrite<<",\\"lastWrite\\":"<<lastWrite<<",\\"firstFinal\\":"<<firstFinal<<",\\"lastFinal\\":"<<lastFinal<<"},\\"snapshots\\":[";
  bool first=true;for(const auto&x:telemetry){if(!first)o<<",";first=false;o<<"["<<x.tick<<","<<x.kind<<","<<x.id<<","<<x.rawBytes<<","<<x.input<<","<<x.inflight<<","<<x.bytes<<","<<x.sealed<<","<<x.pending<<","<<x.pendingBytes<<"]";}return o.str()+"]}";
 }
 void fault(int id)''')
replace('cv.wait(l,[&]{return failure||pending<pendingLimit;});backpressureSeconds+=seconds(b);if(failure)throw std::runtime_error("failed before transfer");', '''bool blocked=!failure&&pending>=pendingLimit;
  if(blocked){backpressureStarted++;s->waitBegin=U(q());snapshot(8,s->number);if(inject==19)fail(19);}
  cv.wait(l,[&]{return failure||pending<pendingLimit;});backpressureSeconds+=seconds(b);
  if(blocked){s->waitEnd=U(q());blockedTicks+=s->waitEnd-s->waitBegin;if(failure){backpressureInterrupted++;snapshot(10,s->number);}else{backpressureCompleted++;snapshot(9,s->number);}}
  if(failure)throw std::runtime_error("failed before transfer");''')
replace('sealed.push_back(std::move(s));cv.notify_all();','s->enqueued=U(q());U id=s->number;sealed.push_back(std::move(s));snapshot(4,id);cv.notify_all();')
replace('item=std::move(input.front());input.pop_front();','item=std::move(input.front());input.pop_front();snapshot(2,item.seq,item.raw.size());U lag=telemetry.back().tick-item.admitted;dequeuedCount++;dequeueLagTicks+=lag;maxDequeueLagTicks=std::max(maxDequeueLagTicks,lag);')
replace('queueBytes-=item.raw.size();inflightItems--;','queueBytes-=item.raw.size();inflightItems--;snapshot(3,item.seq,item.raw.size());U lag=telemetry.back().tick-item.admitted;completedCount++;completionLagTicks+=lag;maxCompletionLagTicks=std::max(maxCompletionLagTicks,lag);')
replace('s=std::move(sealed.front());sealed.pop_front();','s=std::move(sealed.front());sealed.pop_front();s->dequeued=U(q());snapshot(5,s->number);')
replace('fault(7);auto t=q();if(!FlushFileBuffers(s->handle))','fault(7);auto t=q();s->flushBegin=U(t);if(!FlushFileBuffers(s->handle))')
replace('auto dt=seconds(t);flushSeconds+=dt;','s->flushEnd=U(q());auto dt=double(s->flushEnd-s->flushBegin)/clockFrequency;flushSeconds+=dt;')
replace('DWORD n=0;t=q();','DWORD n=0;t=q();s->hashBegin=U(t);')
replace('hashSeconds+=seconds(t);','s->hashEnd=U(q());hashSeconds+=double(s->hashEnd-s->hashBegin)/clockFrequency;')
replace('pending--;pendingBytes-=s->bytes;done.push_back(std::move(s));','pending--;pendingBytes-=s->bytes;s->completed=U(q());U id=s->number;done.push_back(std::move(s));snapshot(6,id);')
replace('o<<"]}";}return o.str()+"]";}', 'o<<"],\\"timing\\":{\\"enqueued\\":"<<s->enqueued<<",\\"dequeued\\":"<<s->dequeued<<",\\"completed\\":"<<s->completed<<",\\"flushBegin\\":"<<s->flushBegin<<",\\"flushEnd\\":"<<s->flushEnd<<",\\"hashBegin\\":"<<s->hashBegin<<",\\"hashEnd\\":"<<s->hashEnd<<",\\"waitBegin\\":"<<s->waitBegin<<",\\"waitEnd\\":"<<s->waitEnd<<"}}";}return o.str()+"]";}')
replace('born=q();\n  finalizer=', 'born=q();LARGE_INTEGER freq{};if(!QueryPerformanceFrequency(&freq)||freq.QuadPart<=0)throw std::runtime_error("telemetry clock");clockFrequency=U(freq.QuadPart);telemetry.reserve(telemetryCap);snapshot(0);\n  finalizer=')
replace('input.push_back({accepted,std::move(raw)});cv.notify_all();','U size=raw.size();input.push_back({accepted,std::move(raw),U(q())});snapshot(1,accepted,size);input.back().admitted=telemetry.back().tick;cv.notify_all();')
replace('writer.join();finalizer.join();\n  try{', 'writer.join();finalizer.join();\n  std::string telemetryRef;\n  try{{std::lock_guard<std::mutex>l(gate);snapshot(7);}\n   ')
replace('fault(12);std::string manifest=', '''fault(12);fault(16);auto ts=telemetryJson();durableFile(prefix+"-telemetry.json",ts);Hash th;th.add(ts.data(),ts.size());auto telemetryHash=th.end();
   fault(17);telemetryRef="{\\"schema\\":\\"stage6-writer-telemetry-v1\\",\\"name\\":\\""+prefix+"-telemetry.json\\",\\"sha256\\":\\""+telemetryHash+"\\"}";
   std::string manifest=''')
replace('std::to_string(bytes)+",\\"segments\\":"+metadata()', 'std::to_string(bytes)+",\\"telemetry\\":"+telemetryRef+",\\"segments\\":"+metadata()')
replace('<<",\\"elapsedSeconds\\":"<<seconds(born)', '<<",\\"telemetry\\":"<<(telemetryRef.empty()?"null":telemetryRef)<<",\\"elapsedSeconds\\":"<<seconds(born)')
assert s!=old
p.write_text(s,encoding='utf8')
(R/'durable_sink.hpp.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile=pre['old']+'/durable_sink.hpp',tofile=str(p))),encoding='utf8')
(R/'implementation-hashes.json').write_text(json.dumps(dict(before=hashlib.sha256(old.encode()).hexdigest(),after=hashlib.sha256(p.read_bytes()).hexdigest(),file=str(p)),indent=2))
print(str(p))
