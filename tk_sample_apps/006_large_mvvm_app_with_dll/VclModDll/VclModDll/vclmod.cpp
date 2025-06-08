#include "pch.h"
#include "vclmod.h"
#include <stdio.h>
#include <stdlib.h>
#include <windows.h>

static int is_available = 0;  // unavailable
static OnUpdatedAvailableCallbackFunc registered_callback = NULL;

// 5�b��� is_available ��ύX���A�R�[���o�b�N���Ăяo��
DWORD WINAPI delayed_task(LPVOID param) {
    Sleep(5000);  // 5�b�ҋ@
    is_available = 1;

    if (registered_callback) {
        registered_callback(is_available);
    }
    return 0;
}

// ���݂̗��p�\��Ԃ��擾
extern "C" int VclMod_getAvailable(void) {
    return is_available;
}

// �R�[���o�b�N��o�^���A�ʃX���b�h�ōX�V�������J�n
extern "C" void VclMod_registerUpdatedAvailableCallback(OnUpdatedAvailableCallbackFunc callbackFunc) {
    registered_callback = callbackFunc;

    // �ʃX���b�h�ŏ������J�n
    HANDLE thread = CreateThread(NULL, 0, delayed_task, NULL, 0, NULL);
    if (thread) {
        CloseHandle(thread);  // �X���b�h���f�^�b�`
    }
}