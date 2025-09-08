#ifndef VCLMOD_H
#define VCLMOD_H

#ifdef _WIN32
#define EXPORT extern "C" __declspec(dllexport)
#else
#define EXPORT
#endif

#include <windows.h>

// �R�[���o�b�N�֐��̌^��`
typedef void (*OnUpdatedAvailableCallbackFunc)(int is_available);

// �֐��̒�`
EXPORT int VclMod_getAvailable(void);
EXPORT void VclMod_registerUpdatedAvailableCallback(OnUpdatedAvailableCallbackFunc callbackFunc);

#endif
