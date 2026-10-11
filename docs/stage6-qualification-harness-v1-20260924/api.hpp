#pragma once
#include <windows.h>
#include <cstdint>
struct Outcome {unsigned long long hash=0,queries=0,captures=0,acquires=0,records=0,attempted=0,overflow=0,handoffErrors=0,allocations=0;unsigned faults=0,discarded=0,disposition=0,valid=0;bool timing=true;};
struct Arm {const char*name;void(*prepare)(unsigned,unsigned,unsigned);void(*dispatch)(unsigned);Outcome(*finish)();unsigned(*scopeSize)();};
extern "C" Arm arm_A();extern "C" Arm arm_B();extern "C" Arm arm_C();
extern unsigned long long allocationCount;
