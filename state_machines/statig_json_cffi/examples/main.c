/**
 * 音声認識ステートマシン C言語呼び出しサンプル
 *
 * ビルド方法 (MinGW):
 *   cargo build
 *   gcc -o examples/main.exe examples/main.c \
 *       -Iinclude -Ltarget/debug -lstatig_json_cffi
 *
 * 実行方法:
 *   PATH=$PATH:target/debug ./examples/main.exe
 */

#include <stdio.h>
#include <string.h>
#include "statig_json_cffi.h"

/* 状態entry/exitコールバック */
static void state_callback(int kind, const char *json)
{
    const char *kind_str = (kind == 0) ? "ENTRY" : "EXIT";
    printf("    [CB:%s] %s\n", kind_str, json);
}

/* イベントを送信して結果を表示するヘルパー */
static void send_event(VoiceSystemHandle *handle, const char *description, const char *json)
{
    printf("  [EVENT] %-40s -> ", description);
    const char *response = handle_event(handle, json);
    if (response == NULL) {
        printf("ERROR: NULL response\n");
        return;
    }
    printf("%s\n", response);
}

/* 現在の状態を表示するヘルパー */
static void print_state(VoiceSystemHandle *handle)
{
    const char *state = get_current_state(handle);
    if (state != NULL) {
        printf("  [STATE] %s\n", state);
    }
}

int main(void)
{
    printf("=== 音声認識ステートマシン C言語呼び出しサンプル ===\n\n");

    /* 1. システム生成（コールバック付き） */
    printf("--- システム生成 ---\n");
    VoiceSystemHandle *handle = create_voice_system(state_callback);
    if (handle == NULL) {
        printf("ERROR: create_voice_system failed\n");
        return 1;
    }
    printf("  システム生成成功\n");
    print_state(handle);
    printf("\n");

    /* 2. 初期化完了 → Ready */
    printf("--- シナリオ1: 基本的な音声認識フロー ---\n");
    send_event(handle, "InitializeComplete",
        "{\"target\":\"VoiceRecognition\",\"event\":{\"type\":\"InitializeComplete\"}}");

    /* 3. PTT → PreSession */
    send_event(handle, "Ptt",
        "{\"target\":\"VoiceRecognition\",\"event\":{\"type\":\"Ptt\"}}");

    /* 4. PreSession承認 → Prepare */
    send_event(handle, "PreSessionResponse(approved)",
        "{\"target\":\"VoiceRecognition\",\"event\":{\"type\":\"PreSessionResponse\","
        "\"data\":{\"approved\":true,\"context_data\":\"navigation_context\"}}}");

    /* 5. Prepare完了(バージインなし) → Guidance */
    send_event(handle, "PrepareCompleteWithoutBargeIn",
        "{\"target\":\"VoiceRecognition\",\"event\":{\"type\":\"PrepareCompleteWithoutBargeIn\"}}");

    /* 6. ガイダンス完了 → Listening */
    send_event(handle, "GuidanceComplete",
        "{\"target\":\"VoiceRecognition\",\"event\":{\"type\":\"GuidanceComplete\"}}");

    /* 7. 発話検知 → Speaking */
    send_event(handle, "SpeechDetected",
        "{\"target\":\"VoiceRecognition\",\"event\":{\"type\":\"SpeechDetected\"}}");

    /* 8. 認識結果 → ConditionChecking */
    send_event(handle, "RecognitionResult",
        "{\"target\":\"VoiceRecognition\",\"event\":{\"type\":\"RecognitionResult\","
        "\"data\":{\"result\":\"navigate to Tokyo\"}}}");

    /* 9. タスク実行して終了 → TaskExecAndEnd */
    send_event(handle, "TaskAndEnd",
        "{\"target\":\"VoiceRecognition\",\"event\":{\"type\":\"TaskAndEnd\"}}");

    /* 10. タスク完了 → Ready */
    send_event(handle, "TaskExecEndComplete",
        "{\"target\":\"VoiceRecognition\",\"event\":{\"type\":\"TaskExecEndComplete\"}}");
    printf("\n");

    /* 11. コールバックなしでのシステム生成も可能 */
    printf("--- コールバックなしでの生成テスト ---\n");
    VoiceSystemHandle *handle_no_cb = create_voice_system(NULL);
    if (handle_no_cb != NULL) {
        printf("  コールバックなし: OK\n");
        print_state(handle_no_cb);
        destroy_voice_system(handle_no_cb);
    }
    printf("\n");

    /* 12. 動的グラマ生成フロー */
    printf("--- シナリオ3: 動的グラマ生成 ---\n");
    send_event(handle, "GenerateDynamicGrammar(g1)",
        "{\"target\":\"DynamicGrammar\",\"event\":{\"type\":\"GenerateDynamicGrammar\","
        "\"data\":{\"grammar_id\":\"contact_list\"}}}");

    send_event(handle, "NotifyData",
        "{\"target\":\"DynamicGrammar\",\"event\":{\"type\":\"NotifyData\","
        "\"data\":{\"data\":\"John,Jane,Bob\"}}}");

    send_event(handle, "GenerationComplete",
        "{\"target\":\"DynamicGrammar\",\"event\":{\"type\":\"GenerationComplete\"}}");
    printf("\n");

    /* 13. エラーハンドリング */
    printf("--- シナリオ6: 不正なJSON ---\n");
    send_event(handle, "Invalid JSON",
        "this is not json");

    send_event(handle, "Unknown target",
        "{\"target\":\"Unknown\",\"event\":{\"type\":\"Ptt\"}}");
    printf("\n");

    /* 14. 最終状態確認 */
    printf("--- 最終状態 ---\n");
    print_state(handle);
    printf("\n");

    /* 15. システム破棄 */
    printf("--- システム破棄 ---\n");
    destroy_voice_system(handle);
    printf("  システム破棄完了\n");

    return 0;
}
