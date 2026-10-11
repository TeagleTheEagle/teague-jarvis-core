#define WIN32_LEAN_AND_MEAN
#include <windows.h>
/* Diagnostic only: no CRT entry, disk access, child process or console output.
   Anonymous mapping handle is explicitly inherited from the collector.
   Slots: magic, earliest entry QPC, work begin, work end, pre-exit, result,
   mode, PID. No user/token/SID contents are exported. */
__declspec(noreturn) void ProbeEntry(void) {
    LARGE_INTEGER first, now;
    QueryPerformanceCounter(&first);
    WCHAR *p=GetCommandLineW();
    if (*p==L'"') {p++;while(*p && *p!=L'"')p++;if(*p)p++;}
    else {while(*p && *p!=L' ')p++;}
    while(*p==L' ')p++;
    unsigned mode=(unsigned)(*p-L'0');
    if(mode>2 || p[1]!=L' ')ExitProcess(101);
    p+=2;while(*p==L' ')p++;
    ULONG_PTR number=0;unsigned digits=0;
    while(*p && *p!=L' ') {
        unsigned v=(*p>=L'0'&&*p<=L'9')?(unsigned)(*p-L'0'):
          (*p>=L'a'&&*p<=L'f')?(unsigned)(*p-L'a'+10):99;
        if(v>15 || ++digits>16)ExitProcess(102);
        number=(number<<4)|v;p++;
    }
    if(!digits || !number || *p)ExitProcess(103);
    HANDLE map=(HANDLE)number;
    volatile LONG64 *s=(volatile LONG64*)MapViewOfFile(map,FILE_MAP_WRITE,0,0,4096);
    if(!s)ExitProcess(104);
    s[1]=first.QuadPart;s[6]=mode;s[7]=GetCurrentProcessId();
    QueryPerformanceCounter(&now);s[2]=now.QuadPart;
    DWORD error=0;ULONG value=1;
#ifdef J6_TOKEN_CONTROL
    if(mode!=2)error=105;
    else {
        HANDLE token=0;DWORD length=0;
        void *buffer=HeapAlloc(GetProcessHeap(),0,512);
        if(!buffer)error=106;
        else {
            if(!OpenProcessToken(GetCurrentProcess(),TOKEN_QUERY,&token))error=107;
            else {
                if(!GetTokenInformation(token,TokenUser,buffer,512,&length))error=108;
                CloseHandle(token);
            }
            HeapFree(GetProcessHeap(),0,buffer);
        }
    }
#else
    if(mode>1)error=109;
    if(mode==1) {
        volatile ULONG accumulator=1;
        for(unsigned i=0;i<10000;i++)accumulator=accumulator*1664525u+1013904223u;
        value=accumulator;
    }
#endif
    QueryPerformanceCounter(&now);s[3]=now.QuadPart;
    s[5]=error?-(LONG64)error:(LONG64)value;
    QueryPerformanceCounter(&now);s[4]=now.QuadPart;
    InterlockedExchange64(s,0x4a365052);
    UnmapViewOfFile((void*)s);CloseHandle(map);
    ExitProcess(error);
}
