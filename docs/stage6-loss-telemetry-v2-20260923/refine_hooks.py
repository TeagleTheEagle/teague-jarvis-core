from pathlib import Path
C=Path(__file__).parent/'candidate'
def fix(n,a,b):
 p=C/n;s=p.read_text();assert a in s,(n,a);p.write_text(s.replace(a,b))
fix('authority_trace_v3.cpp','{j6d::Span diagnosticSerialization(j6d::Serialization);','{')
fix('authority_trace_v3.cpp','std::ostringstream o;o<<"{\\\"source','std::ostringstream o;{j6d::Span diagnosticSerialization(j6d::Serialization);o<<"{\\\"source')
fix('authority_trace_v3.cpp',' if(!j6t::measure(j6t::Admission',' }if(!j6t::measure(j6t::Admission')
fix('startup_trace.cpp','j6d::Span diagnosticSerialization(j6d::Serialization);std::ostringstream out;','std::ostringstream out;')
fix('startup_trace.cpp','std::ostringstream o;o<<"{\\\"provider','std::ostringstream o;{j6d::Span diagnosticSerialization(j6d::Serialization);o<<"{\\\"provider')
fix('startup_trace.cpp','if(!j6t::measure(j6t::Admission','}if(!j6t::measure(j6t::Admission')
fix('durable_sink.hpp','j6d::Span diagnosticSerialization(j6d::Serialization);auto serial=q();std::string row=','auto serial=q();std::string row;{j6d::Span diagnosticSerialization(j6d::Serialization);row=')
fix('durable_sink.hpp','serializeSeconds+=seconds(serial);','}serializeSeconds+=seconds(serial);')
# Counter snapshots deliberately never acquire the writer lock from sampler/callback.
# Marking StopTrace must happen BEFORE the OS call so expected stopped-session samples are distinguishable.
fix('trace_telemetry.hpp','auto b=now();auto r=f();phase(name,b,now(),','auto b=now();j6d::diagnostic.phase(name,b);auto r=f();phase(name,b,now(),')
