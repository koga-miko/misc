#ifndef VCLMOD_H
#define VCLMOD_H

#ifdef _WIN32
#define EXPORT extern "C" __declspec(dllexport)
#else
#define EXPORT
#endif

#include <windows.h>

// コールバック関数の型定義
typedef void (*OnUpdatedAvailableCallbackFunc)(int is_available);

// 関数の定義
EXPORT int VclMod_getAvailable(void);
EXPORT void VclMod_registerUpdatedAvailableCallback(OnUpdatedAvailableCallbackFunc callbackFunc);

#endif
