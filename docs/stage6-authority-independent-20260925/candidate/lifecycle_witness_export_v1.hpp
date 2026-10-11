#pragma once
#include <bcrypt.h>
#include <iomanip>
#include <stdexcept>
#pragma comment(lib,"bcrypt.lib")
namespace j6w {
// Called AFTER ProcessTrace thread.join(). No export work in any callback.
inline std::wstring runFolder(const char* channel){return std::string(channel)=="detailed"?folder.substr(0,folder.find_last_of(L"\\/")):folder;}
inline bool writeSidecar(const char* channel,const wchar_t* suffix,const std::string& data){
 // Sibling of the immutable acceptance artifact tree; run-bound filename.
 const auto path=runFolder(channel)+L"."+suffix;
 HANDLE f=CreateFileW(path.c_str(),GENERIC_WRITE,FILE_SHARE_READ,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
 if(f==INVALID_HANDLE_VALUE)return false;DWORD n=0;bool ok=WriteFile(f,data.data(),static_cast<DWORD>(data.size()),&n,nullptr)&&n==data.size();
 bool flushed=FlushFileBuffers(f)!=0;bool closed=CloseHandle(f)!=0;return ok&&flushed&&closed;
}
inline bool exportFailure(const char* channel){return writeSidecar(channel,std::string(channel)=="authority"?L"authority-lifecycle-witness-export-failure-v1.json":L"detailed-lifecycle-witness-export-failure-v1.json","{\"diagnosticOnly\":true,\"acceptanceAuthority\":false,\"status\":\"WITNESS_INCOMPLETE\"}");}
inline std::string fileHash(const std::wstring& path){
 HANDLE f=CreateFileW(path.c_str(),GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
 if(f==INVALID_HANDLE_VALUE)throw std::runtime_error("witness binding read");
 BY_HANDLE_FILE_INFORMATION info{};BCRYPT_ALG_HANDLE a=nullptr;BCRYPT_HASH_HANDLE h=nullptr;
 try {
  if(!GetFileInformationByHandle(f,&info)||(info.dwFileAttributes&(FILE_ATTRIBUTE_REPARSE_POINT|FILE_ATTRIBUTE_DIRECTORY)))throw std::runtime_error("witness binding path");
  if(BCryptOpenAlgorithmProvider(&a,BCRYPT_SHA256_ALGORITHM,nullptr,0)<0||BCryptCreateHash(a,&h,nullptr,0,nullptr,0,0)<0)throw std::runtime_error("witness hash init");
  BYTE data[65536];DWORD n=0;for(;;){if(!ReadFile(f,data,sizeof(data),&n,nullptr))throw std::runtime_error("witness hash read");if(!n)break;if(BCryptHashData(h,data,n,0)<0)throw std::runtime_error("witness hash update");}
  BYTE digest[32];if(BCryptFinishHash(h,digest,32,0)<0)throw std::runtime_error("witness hash finish");
  BCryptDestroyHash(h);h=nullptr;BCryptCloseAlgorithmProvider(a,0);a=nullptr;CloseHandle(f);f=INVALID_HANDLE_VALUE;
  std::ostringstream o;for(auto b:digest)o<<std::hex<<std::setw(2)<<std::setfill('0')<<unsigned(b);return o.str();
 }catch(...){if(h)BCryptDestroyHash(h);if(a)BCryptCloseAlgorithmProvider(a,0);if(f!=INVALID_HANDLE_VALUE)CloseHandle(f);throw;}
}
inline bool exportWitness(const char* channel,bool quiesced){
 try {
  wchar_t module[32768];auto n=GetModuleFileNameW(nullptr,module,32768);if(!n||n==32768)throw std::runtime_error("witness module");
  std::wstring executable(module,n);auto dir=executable.substr(0,executable.find_last_of(L"\\/"));
  auto runPath=runFolder(channel);auto run=runPath.substr(runPath.find_last_of(L"\\/")+1);
  LARGE_INTEGER frequency; if(!QueryPerformanceFrequency(&frequency))throw std::runtime_error("witness frequency");
  std::ostringstream o;o<<"{\"schema\":\"stage6-lifecycle-witness-v1\",\"diagnosticOnly\":true,\"acceptanceAuthority\":false,\"run\":"<<J(U(run))
   <<",\"channel\":"<<J(channel)<<",\"session\":"<<J(U(session))<<",\"candidateSHA256\":"<<J(fileHash(dir+L"\\witness-source-v1.json"))
   <<",\"observerSHA256\":"<<J(fileHash(executable))<<",\"frequency\":"<<frequency.QuadPart
   <<",\"quiesced\":"<<(quiesced?"true":"false")<<",\"capacity\":"<<capacity<<",\"attempted\":"<<buffer.attempted
   <<",\"count\":"<<buffer.count<<",\"overflow\":"<<(buffer.overflow?"true":"false")<<",\"records\":"<<recordsJson(buffer)<<"}";
  return writeSidecar(channel,std::string(channel)=="authority"?L"authority-lifecycle-witness-v1.json":L"detailed-lifecycle-witness-v1.json",o.str());
 }catch(...){return false;}
}
}
