#pragma once
#include <windows.h>
#include <bcrypt.h>
#include <deque>
#include <condition_variable>
#include <mutex>
#include <thread>
#include <atomic>
#include <string>
#include <vector>
#include <sstream>
#include <iomanip>
// One producer queue, one writer. No filesystem operations while holding queue lock.
class TraceSink {
 struct Segment {std::wstring name;unsigned long long bytes=0,records=0;std::string hash;};
 std::wstring root;std::deque<std::string> queue;std::mutex lock;std::condition_variable wake;
 unsigned long long queued=0,accepted=0,totalBytes=0,persisted=0;bool closing=false;
 unsigned long long maxBytes,maxRecords,segmentLimit,queueLimit;int inject;std::thread writer;
 std::vector<Segment> segments;HANDLE file=INVALID_HANDLE_VALUE;
 BCRYPT_ALG_HANDLE algorithm=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;std::vector<BYTE> object;
 std::atomic<unsigned> failure{0};unsigned long long peakQueue=0;double maxWriteSeconds=0;
 static long long q(){LARGE_INTEGER x;QueryPerformanceCounter(&x);return x.QuadPart;}
 bool openSegment(){
  if(inject==3||segments.size()>=16384){failure=3;return false;}
  wchar_t name[64];swprintf_s(name,L"trace-%05u.jsonl",unsigned(segments.size()));
  file=CreateFileW((root+L"\\"+name).c_str(),GENERIC_WRITE,FILE_SHARE_READ,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
  if(file==INVALID_HANDLE_VALUE){failure=4;return false;}
  if(BCryptCreateHash(algorithm,&hash,object.data(),ULONG(object.size()),nullptr,0,0)<0){failure=5;return false;}
  segments.push_back({name,0,0,{}});return true;
 }
 bool closeSegment(){
  if(file==INVALID_HANDLE_VALUE)return true;
  BYTE digest[32];bool ok=FlushFileBuffers(file)!=0;ok=CloseHandle(file)!=0&&ok;file=INVALID_HANDLE_VALUE;
  ok=BCryptFinishHash(hash,digest,32,0)>=0&&ok;BCryptDestroyHash(hash);hash=nullptr;
  if(!ok){failure=6;return false;}std::ostringstream h;for(auto b:digest)h<<std::hex<<std::setw(2)<<std::setfill('0')<<unsigned(b);segments.back().hash=h.str();return true;
 }
 void run(){
  LARGE_INTEGER freq;QueryPerformanceFrequency(&freq);
  for(;;){std::string row;{
    std::unique_lock<std::mutex> guard(lock);wake.wait(guard,[&]{return closing||!queue.empty();});
    if(queue.empty()){if(closing)break;continue;}row=std::move(queue.front());queue.pop_front();queued-=row.size();
   }
   if(failure)continue;
   if(file==INVALID_HANDLE_VALUE&&!openSegment())continue;
   if(segments.back().bytes+row.size()>segmentLimit){if(!closeSegment()||!openSegment())continue;}
   DWORD done=0;auto start=q();bool ok=inject!=1&&inject!=2&&WriteFile(file,row.data(),DWORD(row.size()),&done,nullptr)&&done==row.size();
   auto seconds=double(q()-start)/freq.QuadPart;if(seconds>maxWriteSeconds)maxWriteSeconds=seconds;
   if(!ok){failure=inject==2?112:7;continue;}
   if(BCryptHashData(hash,reinterpret_cast<PUCHAR>(row.data()),ULONG(row.size()),0)<0){failure=8;continue;}
   auto& s=segments.back();s.bytes+=row.size();++s.records;++persisted;
  }
  closeSegment();
 }
public:
 TraceSink(std::wstring path,unsigned long long bytes=137438953472ULL,unsigned long long records=196531200ULL,unsigned long long segment=8388608ULL,unsigned long long memory=67108864ULL,int fault=0):root(path),maxBytes(bytes),maxRecords(records),segmentLimit(segment),queueLimit(memory),inject(fault){
  DWORD size=0,got=0;
  if(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)<0||BCryptGetProperty(algorithm,BCRYPT_OBJECT_LENGTH,reinterpret_cast<PUCHAR>(&size),sizeof(size),&got,0)<0)throw std::runtime_error("SHA256 initialization");
  object.resize(size);writer=std::thread([this]{run();});
 }
 bool add(std::string row){
  row+='\n';std::lock_guard<std::mutex> guard(lock);
  if(failure||closing)return false;
  if(row.size()>8192||row.size()>segmentLimit||accepted>=maxRecords||totalBytes+row.size()>maxBytes||queued+row.size()>queueLimit){failure=9;return false;}
  ++accepted;totalBytes+=row.size();queued+=row.size();if(queued>peakQueue)peakQueue=queued;queue.push_back(std::move(row));wake.notify_one();return true;
 }
 std::string finish(){
  {std::lock_guard<std::mutex> guard(lock);closing=true;}wake.notify_one();writer.join();
  if(persisted!=accepted)failure=10;
  std::ostringstream s;s<<"{\"format\":\"segmented-jsonl-v1\",\"fault\":"<<failure<<",\"accepted\":"<<accepted<<",\"persisted\":"<<persisted<<",\"bytes\":"<<totalBytes<<",\"peakQueueBytes\":"<<peakQueue<<",\"maximumWriteSeconds\":"<<maxWriteSeconds<<",\"recordBudget\":"<<maxRecords<<",\"storageBudgetBytes\":"<<maxBytes<<",\"segments\":[";
  bool first=true;for(auto& x:segments){if(!first)s<<',';first=false;s<<"{\"name\":\""<<std::string(x.name.begin(),x.name.end())<<"\",\"bytes\":"<<x.bytes<<",\"records\":"<<x.records<<",\"sha256\":\""<<x.hash<<"\"}";}s<<"]}";
  BCryptCloseAlgorithmProvider(algorithm,0);algorithm=nullptr;return s.str();
 }
 unsigned fault()const{return failure.load();}
 ~TraceSink(){if(writer.joinable()){{std::lock_guard<std::mutex> guard(lock);closing=true;}wake.notify_one();writer.join();}if(hash)BCryptDestroyHash(hash);if(file!=INVALID_HANDLE_VALUE)CloseHandle(file);if(algorithm)BCryptCloseAlgorithmProvider(algorithm,0);}
};
