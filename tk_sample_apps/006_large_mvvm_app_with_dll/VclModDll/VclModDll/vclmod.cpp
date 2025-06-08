#include "pch.h"
#include "vclmod.h"
#include <stdio.h>
#include <stdlib.h>
#include <windows.h>

static int is_available = 0;  // unavailable
static OnUpdatedAvailableCallbackFunc registered_callback = NULL;

// 5秒後に is_available を変更し、コールバックを呼び出す
DWORD WINAPI delayed_task(LPVOID param) {
    Sleep(5000);  // 5秒待機
    is_available = 1;

    if (registered_callback) {
        registered_callback(is_available);
    }
    return 0;
}

// 現在の利用可能状態を取得
extern "C" int VclMod_getAvailable(void) {
    return is_available;
}

// コールバックを登録し、別スレッドで更新処理を開始
extern "C" void VclMod_registerUpdatedAvailableCallback(OnUpdatedAvailableCallbackFunc callbackFunc) {
    registered_callback = callbackFunc;

    // 別スレッドで処理を開始
    HANDLE thread = CreateThread(NULL, 0, delayed_task, NULL, 0, NULL);
    if (thread) {
        CloseHandle(thread);  // スレッドをデタッチ
    }
}