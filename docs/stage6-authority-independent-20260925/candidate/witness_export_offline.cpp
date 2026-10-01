#define NOMINMAX
#include <windows.h>
#include <string>
#include <sstream>
#include <iostream>
#include "lifecycle_witness_v1.hpp"
static std::wstring folder,session=L"J6-OFFLINE-NOT-A-SESSION";
static std::string U(const std::wstring& w){if(w.empty())return "";int n=WideCharToMultiByte(CP_UTF8,0,w.data(),static_cast<int>(w.size()),nullptr,0,nullptr,nullptr);std::string s(n,0);WideCharToMultiByte(CP_UTF8,0,w.data(),static_cast<int>(w.size()),s.data(),n,nullptr,nullptr);return s;}
static std::string J(const std::string& s){std::string o="\"";for(unsigned char c:s){if(c=='"'||c=='\\'){o+='\\';o+=c;}else if(c<32){o+='?';}else o+=c;}return o+'"';}
static bool Write(const wchar_t* name,const std::string& s){std::wstring p=folder+L"\\"+name;HANDLE f=CreateFileW(p.c_str(),GENERIC_WRITE,FILE_SHARE_READ,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);if(f==INVALID_HANDLE_VALUE)return false;DWORD n=0;BOOL ok=WriteFile(f,s.data(),static_cast<DWORD>(s.size()),&n,nullptr);BOOL flush=FlushFileBuffers(f);CloseHandle(f);return ok&&flush&&n==s.size();}

#include "lifecycle_witness_export_v1.hpp"
int wmain(int argc,wchar_t**argv){if(argc!=3)return 2;folder=argv[1];const char*channel=std::wstring(argv[2])==L"detailed"?"detailed":"authority";{j6w::Scope w(1,100,101);w.field(20,j6w::PID,true);w.parent(true);w.result(j6w::ADMITTED);}bool first=j6w::exportWitness(channel,true);bool duplicate=j6w::exportWitness(channel,true);folder+=L"\\missing\\run\\detail";bool missing=j6w::exportWitness(channel,true);std::cout<<"first="<<first<<" duplicate="<<duplicate<<" missing="<<missing<<"\n";return first&&!duplicate&&!missing?0:1;}
