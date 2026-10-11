#include <fstream>
#include <iostream>
#include <chrono>
#include "trace_sink.hpp"
// Standalone sacrificial capacity test. No ETW, process inspection or identity claims.
int wmain(int argc,wchar_t**argv){
 if(argc!=8)return 90;
 std::wstring root=argv[1];if(root.rfind(L"D:\\JARVIS-STAGE6-LIVE\\instance-stream-",0)||root.find(L"..")!=root.npos)return 91;
 unsigned count=wcstoul(argv[2],0,10),rate=wcstoul(argv[3],0,10),fault=wcstoul(argv[4],0,10);
 auto memory=_wcstoui64(argv[5],0,10),limit=_wcstoui64(argv[6],0,10),byteCap=_wcstoui64(argv[7],0,10);
 if(count>1000000||rate>1000000||memory>67108864||limit>1000000||byteCap>1073741824)return 92;
 TraceSink sink(root,byteCap,limit,8388608,memory,fault);
 std::vector<std::string> view;view.reserve(20000);unsigned long long viewTruncated=0,admitted=0;
 LARGE_INTEGER freq,begin,end;QueryPerformanceFrequency(&freq);QueryPerformanceCounter(&begin);
 std::string payload="{\"kind\":\"CAPACITY_ONLY\",\"padding\":\""+std::string(600,'x')+"\"}";
 for(unsigned i=0;i<count;i++){
  if(rate&&i%1000==0){double target=double(i)/rate;for(;;){LARGE_INTEGER now;QueryPerformanceCounter(&now);if(double(now.QuadPart-begin.QuadPart)/freq.QuadPart>=target)break;Sleep(1);}}
  if(!sink.add(payload))break;
  ++admitted;if(view.size()<20000)view.push_back(payload);else ++viewTruncated;
 }
 QueryPerformanceCounter(&end);double producerSeconds=double(end.QuadPart-begin.QuadPart)/freq.QuadPart;
 auto manifest=sink.finish();LARGE_INTEGER closed;QueryPerformanceCounter(&closed);
 std::ofstream out(root+L"\\manifest.json",std::ios::binary);out<<manifest;out.close();
 std::ofstream stats(root+L"\\bench.json",std::ios::binary);
 stats<<"{\"capacityOnly\":true,\"requested\":"<<count<<",\"admitted\":"<<admitted<<",\"producerSeconds\":"<<producerSeconds<<",\"closedSeconds\":"<<double(closed.QuadPart-begin.QuadPart)/freq.QuadPart<<",\"recordsPerSecond\":"<<admitted/producerSeconds<<",\"viewRows\":"<<view.size()<<",\"viewTruncated\":"<<viewTruncated<<",\"viewAuthoritative\":false,\"fault\":"<<sink.fault()<<"}";stats.close();
 return sink.fault()?1:0;
}
