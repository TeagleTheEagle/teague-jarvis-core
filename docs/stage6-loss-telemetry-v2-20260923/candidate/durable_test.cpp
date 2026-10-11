#define WIN32_LEAN_AND_MEAN
#include "durable_sink.hpp"
#include <iostream>
int wmain(int argc,wchar_t**argv){
 if(argc!=4)return 90;
 try{int fault=_wtoi(argv[2]);int count=_wtoi(argv[3]);if(count<1||count>20000)return 91;
  auto start=std::chrono::steady_clock::now();DurableSink sink(argv[1],"durable",65536,fault);
  for(int i=0;i<count;i++){std::string raw="{\"value\":"+std::to_string(i)+",\"text\":\""+std::string(200,'x')+"\"}";if(!sink.add(raw))break;}
  double producer=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();auto result=sink.finish();std::cout<<"{\"producerSeconds\":"<<producer<<",\"result\":"<<result<<"}"<<std::endl;return sink.fault()?2:0;
 }catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 3;}
}
