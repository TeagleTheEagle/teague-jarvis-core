"""One-time bounded successor transform; refuses an already-integrated input."""
from pathlib import Path
ROOT = Path(__file__).parent
C = ROOT / 'candidate'
for name, channel in [('authority_trace_v3.cpp', 'authority'), ('startup_trace.cpp', 'detailed')]:
    p = C / name
    s = p.read_text()
    assert 'lifecycle_witness_v1.hpp' not in s
    s = s.replace('#include "trace_telemetry.hpp"', '#include "trace_telemetry.hpp"\n#include "lifecycle_witness_v1.hpp"', 1)
    start = s.index('static void WINAPI Event(') if channel == 'authority' else s.index('static void LifecycleEvent(')
    end = s.index('static void Sample()', start) if channel == 'authority' else s.index('\nstatic const GUID FileProvider', start)
    old = s[start:end]
    gate = 'if(!IsEqualGUID(e->EventHeader.ProviderId,Provider))return;unsigned id=e->EventHeader.EventDescriptor.Id;if(id!=1&&id!=2)return;'
    # Reuse the existing outer CallbackScope::begin for both channels.
    prefix = ('static void WINAPI Event(EVENT_RECORD* e){j6t::CallbackScope timing;timing.eventQpc=e->EventHeader.TimeStamp.QuadPart;'
              if channel == 'authority' else 'static void LifecycleEvent(EVENT_RECORD* e,LONGLONG callbackQpc){')
    arrival = 'timing.begin' if channel == 'authority' else 'callbackQpc'
    body = old[old.index(gate) + len(gate):]
    body = body.replace('j6t::Lock l(guard);', 'witness.field(pid,j6w::PID,hasPid);witness.field(created,j6w::CREATION,hasTime);\n j6t::Lock l(guard);', 1)
    body = body.replace('Number(e,L"ParentProcessID")', 'read(L"ParentProcessID",j6w::PARENT)')
    body = body.replace('Number(e,L"ParentProcessSequenceNumber")', 'read(L"ParentProcessSequenceNumber",j6w::PARENT_SEQUENCE)')
    body = body.replace('Number(e,L"ProcessSequenceNumber")', 'read(L"ProcessSequenceNumber",j6w::SEQUENCE)')
    body = body.replace('if(!ParentKnown(parent,created,read(L"ParentProcessSequenceNumber",j6w::PARENT_SEQUENCE))){++discarded;return;}',
                        'if(!witness.parent(ParentKnown(parent,created,read(L"ParentProcessSequenceNumber",j6w::PARENT_SEQUENCE)))){witness.result(j6w::UNKNOWN_PARENT,j6w::PARENT_NOT_KNOWN);++discarded;return;}')
    body = body.replace('if(!hasPid||!hasTime||!created||rows.size()>=8192){++faults;return;}',
        'if(!hasPid||!hasTime||!created||rows.size()>=8192){witness.result((!hasPid||!hasTime)?j6w::DECODE_FAILURE:!created?j6w::INVALID_IDENTITY:j6w::OTHER_EXPLICIT_REJECTION,(!hasPid||!hasTime)?j6w::FIELD_DECODE_FAILED:!created?j6w::ZERO_CREATION:j6w::ROW_CAPACITY);++faults;return;}')
    body = body.replace('if(rows.count(key)){++faults;return;}', 'if(rows.count(key)){witness.result(j6w::DUPLICATE_EVENT,j6w::DUPLICATE_START);++faults;return;}')
    body = body.replace('rows.emplace(key,std::move(r));', 'rows.emplace(key,std::move(r));witness.result(j6w::ADMITTED);')
    body = body.replace('if(it==rows.end()){++discarded;return;}', 'if(!witness.instance(it!=rows.end())){witness.result(j6w::UNKNOWN_INSTANCE,j6w::INSTANCE_NOT_KNOWN);++discarded;return;}')
    body = body.replace('if(r.stop){++faults;return;}', 'if(r.stop){witness.result(j6w::DUPLICATE_EVENT,j6w::DUPLICATE_STOP);++faults;return;}')
    stop_tail = 'timing.selected=true;Capture(r,false);}' if channel == 'authority' else 'r.stopSchema=Schemas(e);}'
    body = body.replace(stop_tail, stop_tail[:-1] + 'witness.result(j6w::ADMITTED);}')
    body = body.replace('}catch(...){++faults;}}', '}catch(...){witness.result(j6w::OTHER_EXPLICIT_REJECTION,j6w::EXCEPTION);++faults;}}')
    new = prefix + '\n ' + gate + '\n j6w::Scope witness(id,e->EventHeader.TimeStamp.QuadPart,' + arrival + ');\n auto read=[&](const wchar_t* n,j6w::Field f){bool ok=false;auto v=Number(e,n,&ok);return witness.field(v,f,ok);};try{' + body
    s = s[:start] + new + s[end:]
    if channel == 'detailed':
        s = s.replace('LifecycleEvent(e);', 'LifecycleEvent(e,timing.begin);', 1)
    s = s.replace('int wmain(', '#include "lifecycle_witness_export_v1.hpp"\nint wmain(', 1)
    # No change to existing acceptance fields/exit code. Export failure is an
    # explicit diagnostic-incomplete sidecar, or missing sidecar if disk fails.
    anchor = 'thread.join();j6d::diagnostic.stop();CloseTrace(consumer);Sample();CloseHandle(root);'
    assert s.count(anchor) == 1
    extra = '\n if(!j6w::exportWitness("'+channel+'",stop==0&&consumed==0)){j6w::exportFailure("'+channel+'");}\n'
    s = s.replace(anchor, anchor+extra)
    p.write_text(s, encoding='utf-8')
    print(name, 'integrated')
