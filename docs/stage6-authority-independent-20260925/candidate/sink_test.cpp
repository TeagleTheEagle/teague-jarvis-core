#include <fstream>
#include "trace_sink.hpp"
int wmain(int n,wchar_t**v){if(n!=6)return 90;std::wstring root=v[1];if(root.rfind(L"D:\\JARVIS-STAGE6-LIVE\\",0)||root.find(L"..")!=root.npos)return 91;
 unsigned count=wcstoul(v[2],0,10),limit=wcstoul(v[3],0,10);int inject=_wtoi(v[4]);unsigned bytes=wcstoul(v[5],0,10);
 TraceSink sink(root,bytes,limit,128,4096,inject);for(unsigned i=0;i<count;++i)sink.add("{\"ordinal\":"+std::to_string(i)+"}");auto result=sink.finish();std::ofstream out(root+L"\\sink-result.json",std::ios::binary);out<<result;out.close();return sink.fault()?1:0;}
