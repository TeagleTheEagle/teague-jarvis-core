#ifdef REFERENCE
#include "D:/JARVIS-STAGE6-LIVE/7f204e14c90a497a8476be0e9927e074/code/trace_telemetry.hpp"
#else
#include "trace_telemetry.hpp"
#endif
#include <iostream>
int main(){LARGE_INTEGER hz;QueryPerformanceFrequency(&hz);
#ifndef REFERENCE
 j6d::diagnostic.bind(L"offline-overhead",L"Synthetic","detail",hz.QuadPart,"{}");
#endif
 std::mutex guard;auto begin=j6t::now();unsigned count=500000;
 // Wrapper mix approximates preserved metadata/selection frequencies, no provider/ETW calls.
 for(unsigned i=0;i<count;i++){j6t::CallbackScope c;{j6t::Lock l(guard);}if(i%2==0){j6t::Scope metadata(j6t::Metadata);}if(i%8==0){c.selected=true;j6t::Scope admission(j6t::Admission);}}
 std::cout<<"{\"count\":"<<count<<",\"seconds\":"<<double(j6t::now()-begin)/hz.QuadPart<<"}";
}
