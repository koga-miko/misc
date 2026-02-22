//! 全ての状態・イベント・遷移を網羅する統合テスト
//!
//! テスト構成:
//!   - 音声認識SM: メインレベル遷移 / Session内全パス / superstate共通処理
//!   - 動的グラマSM: 全状態・全イベント
//!   - SM間協調: セッション状態変更の連動
//!   - FFI: JSON入出力の全パターン

use statig_json_cffi::manager::VoiceSystemManager;
use statig_json_cffi::types::SystemResponse;
use std::ffi::{CStr, CString};

// ============================================================
// ヘルパー関数
// ============================================================

/// VoiceSystemManagerにJSONイベントを送信し、レスポンスを返す
fn send(mgr: &mut VoiceSystemManager, json: &str) -> SystemResponse {
    mgr.handle_event_json(json)
}

/// VRイベント用のJSONを生成する（dataなし）
fn vr(event_type: &str) -> String {
    format!(
        r#"{{"target":"VoiceRecognition","event":{{"type":"{}"}}}}"#,
        event_type
    )
}

/// VRイベント用のJSONを生成する（data付き）
fn vr_with_data(event_type: &str, data_json: &str) -> String {
    format!(
        r#"{{"target":"VoiceRecognition","event":{{"type":"{}","data":{}}}}}"#,
        event_type, data_json
    )
}

/// DGイベント用のJSONを生成する（dataなし）
fn dg(event_type: &str) -> String {
    format!(
        r#"{{"target":"DynamicGrammar","event":{{"type":"{}"}}}}"#,
        event_type
    )
}

/// DGイベント用のJSONを生成する（data付き）
fn dg_with_data(event_type: &str, data_json: &str) -> String {
    format!(
        r#"{{"target":"DynamicGrammar","event":{{"type":"{}","data":{}}}}}"#,
        event_type, data_json
    )
}

/// Initializing → Ready の共通手順
fn go_to_ready(mgr: &mut VoiceSystemManager) {
    let r = send(mgr, &vr("InitializeComplete"));
    assert_eq!(r.voice_recognition_state, "Ready");
}

/// Ready → PreSession → Prepare の共通手順
fn go_to_prepare(mgr: &mut VoiceSystemManager) {
    go_to_ready(mgr);
    let r = send(mgr, &vr("Ptt"));
    assert_eq!(r.voice_recognition_state, "PreSession");
    let r = send(
        mgr,
        &vr_with_data(
            "PreSessionResponse",
            r#"{"approved":true,"context_data":"ctx"}"#,
        ),
    );
    assert_eq!(r.voice_recognition_state, "Prepare");
}

/// Prepare → Guidance → Listening の共通手順（バージインなし）
fn go_to_listening_no_bargein(mgr: &mut VoiceSystemManager) {
    go_to_prepare(mgr);
    let r = send(mgr, &vr("PrepareCompleteWithoutBargeIn"));
    assert_eq!(r.voice_recognition_state, "Guidance");
    let r = send(mgr, &vr("GuidanceComplete"));
    assert_eq!(r.voice_recognition_state, "Listening");
}

/// Prepare → GuidanceAndListening の共通手順（バージインあり）
fn go_to_guidance_and_listening(mgr: &mut VoiceSystemManager) {
    go_to_prepare(mgr);
    let r = send(mgr, &vr("PrepareCompleteWithBargeIn"));
    assert_eq!(r.voice_recognition_state, "GuidanceAndListening");
}

/// → ConditionChecking の共通手順
fn go_to_condition_checking(mgr: &mut VoiceSystemManager) {
    go_to_listening_no_bargein(mgr);
    let r = send(mgr, &vr("SpeechDetected"));
    assert_eq!(r.voice_recognition_state, "Speaking");
    let r = send(
        mgr,
        &vr_with_data("RecognitionResult", r#"{"result":"test"}"#),
    );
    assert_eq!(r.voice_recognition_state, "ConditionChecking");
}

// ============================================================
// 音声認識SM: メインレベル状態遷移テスト
// ============================================================

#[test]
fn vr_initializing_to_ready() {
    let mut mgr = VoiceSystemManager::new(None);
    let r = send(&mut mgr, &vr("InitializeComplete"));
    assert!(r.success);
    assert_eq!(r.voice_recognition_state, "Ready");
}

#[test]
fn vr_initializing_to_wait_language_set() {
    let mut mgr = VoiceSystemManager::new(None);
    let r = send(&mut mgr, &vr("InitializeFailed"));
    assert_eq!(r.voice_recognition_state, "WaitLanguageSet");
}

#[test]
fn vr_wait_language_set_to_initializing() {
    let mut mgr = VoiceSystemManager::new(None);
    send(&mut mgr, &vr("InitializeFailed"));
    let r = send(&mut mgr, &vr("LanguageChanged"));
    assert_eq!(r.voice_recognition_state, "Initializing");
}

#[test]
fn vr_wait_language_set_ignores_irrelevant_events() {
    let mut mgr = VoiceSystemManager::new(None);
    send(&mut mgr, &vr("InitializeFailed"));
    // Pttは無視される
    let r = send(&mut mgr, &vr("Ptt"));
    assert_eq!(r.voice_recognition_state, "WaitLanguageSet");
    // WuWDetectedも無視される
    let r = send(&mut mgr, &vr("WuWDetected"));
    assert_eq!(r.voice_recognition_state, "WaitLanguageSet");
}

#[test]
fn vr_ready_to_pre_session_via_ptt() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_ready(&mut mgr);
    let r = send(&mut mgr, &vr("Ptt"));
    assert_eq!(r.voice_recognition_state, "PreSession");
}

#[test]
fn vr_ready_to_pre_session_via_wuw() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_ready(&mut mgr);
    let r = send(&mut mgr, &vr("WuWDetected"));
    assert_eq!(r.voice_recognition_state, "PreSession");
}

#[test]
fn vr_ready_to_initializing_via_language_changed() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_ready(&mut mgr);
    let r = send(&mut mgr, &vr("LanguageChanged"));
    assert_eq!(r.voice_recognition_state, "Initializing");
}

#[test]
fn vr_ready_ignores_irrelevant_events() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_ready(&mut mgr);
    let r = send(&mut mgr, &vr("InitializeComplete"));
    assert_eq!(r.voice_recognition_state, "Ready");
    let r = send(&mut mgr, &vr("Abort"));
    assert_eq!(r.voice_recognition_state, "Ready");
}

#[test]
fn vr_pre_session_approved() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_ready(&mut mgr);
    send(&mut mgr, &vr("Ptt"));
    let r = send(
        &mut mgr,
        &vr_with_data(
            "PreSessionResponse",
            r#"{"approved":true,"context_data":"ctx"}"#,
        ),
    );
    assert_eq!(r.voice_recognition_state, "Prepare");
}

#[test]
fn vr_pre_session_rejected() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_ready(&mut mgr);
    send(&mut mgr, &vr("Ptt"));
    let r = send(
        &mut mgr,
        &vr_with_data(
            "PreSessionResponse",
            r#"{"approved":false,"context_data":null}"#,
        ),
    );
    assert_eq!(r.voice_recognition_state, "Ready");
}

#[test]
fn vr_pre_session_ignores_irrelevant_events() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_ready(&mut mgr);
    send(&mut mgr, &vr("Ptt"));
    let r = send(&mut mgr, &vr("Ptt"));
    assert_eq!(r.voice_recognition_state, "PreSession");
    let r = send(&mut mgr, &vr("GuidanceComplete"));
    assert_eq!(r.voice_recognition_state, "PreSession");
}

// ============================================================
// 音声認識SM: Session内サブ状態遷移テスト
// ============================================================

// --- Prepare ---

#[test]
fn vr_prepare_to_guidance_without_bargein() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_prepare(&mut mgr);
    let r = send(&mut mgr, &vr("PrepareCompleteWithoutBargeIn"));
    assert_eq!(r.voice_recognition_state, "Guidance");
}

#[test]
fn vr_prepare_to_guidance_and_listening_with_bargein() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_prepare(&mut mgr);
    let r = send(&mut mgr, &vr("PrepareCompleteWithBargeIn"));
    assert_eq!(r.voice_recognition_state, "GuidanceAndListening");
}

// --- Guidance ---

#[test]
fn vr_guidance_to_listening() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_prepare(&mut mgr);
    send(&mut mgr, &vr("PrepareCompleteWithoutBargeIn"));
    let r = send(&mut mgr, &vr("GuidanceComplete"));
    assert_eq!(r.voice_recognition_state, "Listening");
}

#[test]
fn vr_guidance_abort() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_prepare(&mut mgr);
    send(&mut mgr, &vr("PrepareCompleteWithoutBargeIn"));
    let r = send(&mut mgr, &vr("Abort"));
    assert_eq!(r.voice_recognition_state, "Aborting");
}

#[test]
fn vr_guidance_silent_abort() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_prepare(&mut mgr);
    send(&mut mgr, &vr("PrepareCompleteWithoutBargeIn"));
    let r = send(&mut mgr, &vr("SilentAbort"));
    assert_eq!(r.voice_recognition_state, "Ready");
}

// --- GuidanceAndListening ---

#[test]
fn vr_guidance_and_listening_speech_detected() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_guidance_and_listening(&mut mgr);
    let r = send(&mut mgr, &vr("SpeechDetected"));
    assert_eq!(r.voice_recognition_state, "Speaking");
}

#[test]
fn vr_guidance_and_listening_guidance_complete_no_speech() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_guidance_and_listening(&mut mgr);
    let r = send(&mut mgr, &vr("GuidanceComplete"));
    assert_eq!(r.voice_recognition_state, "Listening");
}

#[test]
fn vr_guidance_and_listening_recognition_result() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_guidance_and_listening(&mut mgr);
    let r = send(
        &mut mgr,
        &vr_with_data("RecognitionResult", r#"{"result":"yes"}"#),
    );
    assert_eq!(r.voice_recognition_state, "ConditionChecking");
}

#[test]
fn vr_guidance_and_listening_utterance_timeout() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_guidance_and_listening(&mut mgr);
    let r = send(&mut mgr, &vr("UtteranceTimeout"));
    assert_eq!(r.voice_recognition_state, "ConditionChecking");
}

#[test]
fn vr_guidance_and_listening_abort() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_guidance_and_listening(&mut mgr);
    let r = send(&mut mgr, &vr("Abort"));
    assert_eq!(r.voice_recognition_state, "Aborting");
}

#[test]
fn vr_guidance_and_listening_silent_abort() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_guidance_and_listening(&mut mgr);
    let r = send(&mut mgr, &vr("SilentAbort"));
    assert_eq!(r.voice_recognition_state, "Ready");
}

// --- Listening ---

#[test]
fn vr_listening_speech_detected() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_listening_no_bargein(&mut mgr);
    let r = send(&mut mgr, &vr("SpeechDetected"));
    assert_eq!(r.voice_recognition_state, "Speaking");
}

#[test]
fn vr_listening_speech_timeout() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_listening_no_bargein(&mut mgr);
    let r = send(&mut mgr, &vr("SpeechTimeout"));
    assert_eq!(r.voice_recognition_state, "ConditionChecking");
}

#[test]
fn vr_listening_abort() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_listening_no_bargein(&mut mgr);
    let r = send(&mut mgr, &vr("Abort"));
    assert_eq!(r.voice_recognition_state, "Aborting");
}

#[test]
fn vr_listening_silent_abort() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_listening_no_bargein(&mut mgr);
    let r = send(&mut mgr, &vr("SilentAbort"));
    assert_eq!(r.voice_recognition_state, "Ready");
}

// --- Speaking ---

#[test]
fn vr_speaking_recognition_result() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_listening_no_bargein(&mut mgr);
    send(&mut mgr, &vr("SpeechDetected"));
    let r = send(
        &mut mgr,
        &vr_with_data("RecognitionResult", r#"{"result":"hello"}"#),
    );
    assert_eq!(r.voice_recognition_state, "ConditionChecking");
}

#[test]
fn vr_speaking_utterance_timeout() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_listening_no_bargein(&mut mgr);
    send(&mut mgr, &vr("SpeechDetected"));
    let r = send(&mut mgr, &vr("UtteranceTimeout"));
    assert_eq!(r.voice_recognition_state, "ConditionChecking");
}

#[test]
fn vr_speaking_abort() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_listening_no_bargein(&mut mgr);
    send(&mut mgr, &vr("SpeechDetected"));
    let r = send(&mut mgr, &vr("Abort"));
    assert_eq!(r.voice_recognition_state, "Aborting");
}

#[test]
fn vr_speaking_silent_abort() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_listening_no_bargein(&mut mgr);
    send(&mut mgr, &vr("SpeechDetected"));
    let r = send(&mut mgr, &vr("SilentAbort"));
    assert_eq!(r.voice_recognition_state, "Ready");
}

// --- ConditionChecking ---

#[test]
fn vr_condition_checking_continue_with_guidance() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_condition_checking(&mut mgr);
    let r = send(&mut mgr, &vr("ContinueWithGuidance"));
    assert_eq!(r.voice_recognition_state, "FollowupGuidance");
}

#[test]
fn vr_condition_checking_continue_with_task() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_condition_checking(&mut mgr);
    let r = send(&mut mgr, &vr("ContinueWithTask"));
    assert_eq!(r.voice_recognition_state, "TaskExecAndContinue");
}

#[test]
fn vr_condition_checking_task_and_end() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_condition_checking(&mut mgr);
    let r = send(&mut mgr, &vr("TaskAndEnd"));
    assert_eq!(r.voice_recognition_state, "TaskExecAndEnd");
}

#[test]
fn vr_condition_checking_error_end() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_condition_checking(&mut mgr);
    let r = send(&mut mgr, &vr("ErrorEnd"));
    assert_eq!(r.voice_recognition_state, "ErrorAndEnd");
}

#[test]
fn vr_condition_checking_abort() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_condition_checking(&mut mgr);
    let r = send(&mut mgr, &vr("Abort"));
    assert_eq!(r.voice_recognition_state, "Aborting");
}

// --- FollowupGuidance ---

#[test]
fn vr_followup_guidance_complete_to_prepare() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_condition_checking(&mut mgr);
    send(&mut mgr, &vr("ContinueWithGuidance"));
    let r = send(&mut mgr, &vr("FollowupGuidanceComplete"));
    assert_eq!(r.voice_recognition_state, "Prepare");
}

#[test]
fn vr_followup_guidance_abort() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_condition_checking(&mut mgr);
    send(&mut mgr, &vr("ContinueWithGuidance"));
    let r = send(&mut mgr, &vr("Abort"));
    assert_eq!(r.voice_recognition_state, "Aborting");
}

// --- TaskExecAndContinue ---

#[test]
fn vr_task_exec_continue_complete_to_prepare() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_condition_checking(&mut mgr);
    send(&mut mgr, &vr("ContinueWithTask"));
    let r = send(&mut mgr, &vr("TaskExecContinueComplete"));
    assert_eq!(r.voice_recognition_state, "Prepare");
}

#[test]
fn vr_task_exec_continue_abort() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_condition_checking(&mut mgr);
    send(&mut mgr, &vr("ContinueWithTask"));
    let r = send(&mut mgr, &vr("Abort"));
    assert_eq!(r.voice_recognition_state, "Aborting");
}

// --- TaskExecAndEnd ---

#[test]
fn vr_task_exec_end_complete_to_ready() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_condition_checking(&mut mgr);
    send(&mut mgr, &vr("TaskAndEnd"));
    let r = send(&mut mgr, &vr("TaskExecEndComplete"));
    assert_eq!(r.voice_recognition_state, "Ready");
}

#[test]
fn vr_task_exec_end_abort() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_condition_checking(&mut mgr);
    send(&mut mgr, &vr("TaskAndEnd"));
    let r = send(&mut mgr, &vr("Abort"));
    assert_eq!(r.voice_recognition_state, "Aborting");
}

// --- ErrorAndEnd ---

#[test]
fn vr_error_and_end_complete_to_ready() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_condition_checking(&mut mgr);
    send(&mut mgr, &vr("ErrorEnd"));
    let r = send(&mut mgr, &vr("ErrorGuidanceComplete"));
    assert_eq!(r.voice_recognition_state, "Ready");
}

#[test]
fn vr_error_and_end_abort() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_condition_checking(&mut mgr);
    send(&mut mgr, &vr("ErrorEnd"));
    let r = send(&mut mgr, &vr("Abort"));
    assert_eq!(r.voice_recognition_state, "Aborting");
}

// --- Aborting ---

#[test]
fn vr_aborting_complete_to_ready() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_listening_no_bargein(&mut mgr);
    send(&mut mgr, &vr("Abort"));
    let r = send(&mut mgr, &vr("AbortGuidanceComplete"));
    assert_eq!(r.voice_recognition_state, "Ready");
}

#[test]
fn vr_aborting_ignores_irrelevant_events() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_listening_no_bargein(&mut mgr);
    send(&mut mgr, &vr("Abort"));
    // SpeechDetected は無視される
    let r = send(&mut mgr, &vr("SpeechDetected"));
    assert_eq!(r.voice_recognition_state, "Aborting");
    // GuidanceComplete も無視される
    let r = send(&mut mgr, &vr("GuidanceComplete"));
    assert_eq!(r.voice_recognition_state, "Aborting");
}

// ============================================================
// 音声認識SM: Session superstate共通処理テスト
// Abort/SilentAbort が全Session内状態から動作することを確認
// ============================================================

#[test]
fn vr_abort_from_prepare() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_prepare(&mut mgr);
    let r = send(&mut mgr, &vr("Abort"));
    assert_eq!(r.voice_recognition_state, "Aborting");
}

#[test]
fn vr_silent_abort_from_prepare() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_prepare(&mut mgr);
    let r = send(&mut mgr, &vr("SilentAbort"));
    assert_eq!(r.voice_recognition_state, "Ready");
}

#[test]
fn vr_abort_from_condition_checking() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_condition_checking(&mut mgr);
    let r = send(&mut mgr, &vr("Abort"));
    assert_eq!(r.voice_recognition_state, "Aborting");
}

#[test]
fn vr_silent_abort_from_condition_checking() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_condition_checking(&mut mgr);
    let r = send(&mut mgr, &vr("SilentAbort"));
    assert_eq!(r.voice_recognition_state, "Ready");
}

// ============================================================
// 音声認識SM: 複合シナリオ（対話ループ）
// ============================================================

#[test]
fn vr_full_dialog_loop_with_followup_guidance() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_condition_checking(&mut mgr);

    // ConditionChecking → FollowupGuidance → Prepare（ループ1回目）
    send(&mut mgr, &vr("ContinueWithGuidance"));
    let r = send(&mut mgr, &vr("FollowupGuidanceComplete"));
    assert_eq!(r.voice_recognition_state, "Prepare");

    // Prepare → GuidanceAndListening → Speaking → ConditionChecking
    send(&mut mgr, &vr("PrepareCompleteWithBargeIn"));
    send(&mut mgr, &vr("SpeechDetected"));
    let r = send(
        &mut mgr,
        &vr_with_data("RecognitionResult", r#"{"result":"ok"}"#),
    );
    assert_eq!(r.voice_recognition_state, "ConditionChecking");

    // ConditionChecking → TaskExecAndEnd → Ready
    send(&mut mgr, &vr("TaskAndEnd"));
    let r = send(&mut mgr, &vr("TaskExecEndComplete"));
    assert_eq!(r.voice_recognition_state, "Ready");
}

#[test]
fn vr_full_dialog_loop_with_task_continue() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_condition_checking(&mut mgr);

    // ConditionChecking → TaskExecAndContinue → Prepare（ループ）
    send(&mut mgr, &vr("ContinueWithTask"));
    let r = send(&mut mgr, &vr("TaskExecContinueComplete"));
    assert_eq!(r.voice_recognition_state, "Prepare");

    // Prepare → Guidance → Listening → SpeechTimeout → ConditionChecking
    send(&mut mgr, &vr("PrepareCompleteWithoutBargeIn"));
    send(&mut mgr, &vr("GuidanceComplete"));
    let r = send(&mut mgr, &vr("SpeechTimeout"));
    assert_eq!(r.voice_recognition_state, "ConditionChecking");

    // ConditionChecking → ErrorAndEnd → Ready
    send(&mut mgr, &vr("ErrorEnd"));
    let r = send(&mut mgr, &vr("ErrorGuidanceComplete"));
    assert_eq!(r.voice_recognition_state, "Ready");
}

#[test]
fn vr_init_failure_retry_cycle() {
    let mut mgr = VoiceSystemManager::new(None);

    // 初期化失敗 → WaitLanguageSet → LanguageChanged → Initializing
    send(&mut mgr, &vr("InitializeFailed"));
    let r = send(&mut mgr, &vr("LanguageChanged"));
    assert_eq!(r.voice_recognition_state, "Initializing");

    // 再度失敗
    let r = send(&mut mgr, &vr("InitializeFailed"));
    assert_eq!(r.voice_recognition_state, "WaitLanguageSet");

    // 再度言語変更 → 初期化 → 今度は成功
    send(&mut mgr, &vr("LanguageChanged"));
    let r = send(&mut mgr, &vr("InitializeComplete"));
    assert_eq!(r.voice_recognition_state, "Ready");
}

// ============================================================
// 音声認識SM: ItemSelected / Back イベント（Session superstateで処理）
// ============================================================

#[test]
fn vr_item_selected_in_session_handled() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_listening_no_bargein(&mut mgr);
    // ItemSelectedはSession superstateでHandledとして処理される
    let r = send(
        &mut mgr,
        &vr_with_data("ItemSelected", r#"{"context_id":"ctx1"}"#),
    );
    assert!(r.success);
    assert_eq!(r.voice_recognition_state, "Listening");
}

#[test]
fn vr_back_in_session_handled() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_listening_no_bargein(&mut mgr);
    let r = send(
        &mut mgr,
        &vr_with_data("Back", r#"{"context_id":"ctx1"}"#),
    );
    assert!(r.success);
    assert_eq!(r.voice_recognition_state, "Listening");
}

// ============================================================
// 動的グラマSM: 全状態・全イベントテスト
// ============================================================

// --- Idle ---

#[test]
fn dg_idle_generate_to_data_getting() {
    let mut mgr = VoiceSystemManager::new(None);
    let r = send(
        &mut mgr,
        &dg_with_data("GenerateDynamicGrammar", r#"{"grammar_id":"g1"}"#),
    );
    assert_eq!(r.dynamic_grammar_state, "DataGetting");
}

#[test]
fn dg_idle_changed_session_status_stays_idle() {
    let mut mgr = VoiceSystemManager::new(None);
    let r = send(
        &mut mgr,
        &dg_with_data("ChangedSessionStatus", r#"{"status_id":"InSession"}"#),
    );
    assert_eq!(r.dynamic_grammar_state, "Idle");
}

#[test]
fn dg_idle_ignores_notify_data() {
    let mut mgr = VoiceSystemManager::new(None);
    let r = send(
        &mut mgr,
        &dg_with_data("NotifyData", r#"{"data":"test"}"#),
    );
    assert_eq!(r.dynamic_grammar_state, "Idle");
}

#[test]
fn dg_idle_ignores_generation_complete() {
    let mut mgr = VoiceSystemManager::new(None);
    let r = send(&mut mgr, &dg("GenerationComplete"));
    assert_eq!(r.dynamic_grammar_state, "Idle");
}

// --- DataGetting ---

#[test]
fn dg_data_getting_notify_data_to_generating_when_session_inactive() {
    let mut mgr = VoiceSystemManager::new(None);
    send(
        &mut mgr,
        &dg_with_data("GenerateDynamicGrammar", r#"{"grammar_id":"g1"}"#),
    );
    let r = send(
        &mut mgr,
        &dg_with_data("NotifyData", r#"{"data":"test"}"#),
    );
    assert_eq!(r.dynamic_grammar_state, "Generating");
}

#[test]
fn dg_data_getting_notify_data_to_pending_when_session_active() {
    let mut mgr = VoiceSystemManager::new(None);
    send(
        &mut mgr,
        &dg_with_data("GenerateDynamicGrammar", r#"{"grammar_id":"g1"}"#),
    );
    // セッション開始を通知
    send(
        &mut mgr,
        &dg_with_data("ChangedSessionStatus", r#"{"status_id":"InSession"}"#),
    );
    let r = send(
        &mut mgr,
        &dg_with_data("NotifyData", r#"{"data":"test"}"#),
    );
    assert_eq!(r.dynamic_grammar_state, "Pending");
}

#[test]
fn dg_data_getting_queues_new_request() {
    let mut mgr = VoiceSystemManager::new(None);
    send(
        &mut mgr,
        &dg_with_data("GenerateDynamicGrammar", r#"{"grammar_id":"g1"}"#),
    );
    // DataGetting中に追加要求
    let r = send(
        &mut mgr,
        &dg_with_data("GenerateDynamicGrammar", r#"{"grammar_id":"g2"}"#),
    );
    assert_eq!(r.dynamic_grammar_state, "DataGetting");

    // データ取得完了 → Generating
    send(
        &mut mgr,
        &dg_with_data("NotifyData", r#"{"data":"test"}"#),
    );
    // 生成完了 → キューにg2があるのでDataGettingへ
    let r = send(&mut mgr, &dg("GenerationComplete"));
    assert_eq!(r.dynamic_grammar_state, "DataGetting");
}

#[test]
fn dg_data_getting_session_status_change_stays() {
    let mut mgr = VoiceSystemManager::new(None);
    send(
        &mut mgr,
        &dg_with_data("GenerateDynamicGrammar", r#"{"grammar_id":"g1"}"#),
    );
    let r = send(
        &mut mgr,
        &dg_with_data("ChangedSessionStatus", r#"{"status_id":"InPreSession"}"#),
    );
    // DataGettingにとどまる（状態はNotifyDataで判断）
    assert_eq!(r.dynamic_grammar_state, "DataGetting");
}

// --- Generating ---

#[test]
fn dg_generating_complete_to_idle_when_queue_empty() {
    let mut mgr = VoiceSystemManager::new(None);
    send(
        &mut mgr,
        &dg_with_data("GenerateDynamicGrammar", r#"{"grammar_id":"g1"}"#),
    );
    send(
        &mut mgr,
        &dg_with_data("NotifyData", r#"{"data":"test"}"#),
    );
    let r = send(&mut mgr, &dg("GenerationComplete"));
    assert_eq!(r.dynamic_grammar_state, "Idle");
}

#[test]
fn dg_generating_complete_to_data_getting_when_queue_has_items() {
    let mut mgr = VoiceSystemManager::new(None);
    send(
        &mut mgr,
        &dg_with_data("GenerateDynamicGrammar", r#"{"grammar_id":"g1"}"#),
    );
    send(
        &mut mgr,
        &dg_with_data("NotifyData", r#"{"data":"test"}"#),
    );
    // Generating中に新規要求をキューイング
    send(
        &mut mgr,
        &dg_with_data("GenerateDynamicGrammar", r#"{"grammar_id":"g2"}"#),
    );
    let r = send(&mut mgr, &dg("GenerationComplete"));
    assert_eq!(r.dynamic_grammar_state, "DataGetting");
}

#[test]
fn dg_generating_session_start_to_pending() {
    let mut mgr = VoiceSystemManager::new(None);
    send(
        &mut mgr,
        &dg_with_data("GenerateDynamicGrammar", r#"{"grammar_id":"g1"}"#),
    );
    send(
        &mut mgr,
        &dg_with_data("NotifyData", r#"{"data":"test"}"#),
    );
    // Generating中にセッション開始 → Pending
    let r = send(
        &mut mgr,
        &dg_with_data("ChangedSessionStatus", r#"{"status_id":"InSession"}"#),
    );
    assert_eq!(r.dynamic_grammar_state, "Pending");
}

#[test]
fn dg_generating_session_inactive_stays() {
    let mut mgr = VoiceSystemManager::new(None);
    send(
        &mut mgr,
        &dg_with_data("GenerateDynamicGrammar", r#"{"grammar_id":"g1"}"#),
    );
    send(
        &mut mgr,
        &dg_with_data("NotifyData", r#"{"data":"test"}"#),
    );
    // Generating中にInactive通知 → 変化なし
    let r = send(
        &mut mgr,
        &dg_with_data("ChangedSessionStatus", r#"{"status_id":"Inactive"}"#),
    );
    assert_eq!(r.dynamic_grammar_state, "Generating");
}

#[test]
fn dg_generating_aborted_to_pending() {
    let mut mgr = VoiceSystemManager::new(None);
    send(
        &mut mgr,
        &dg_with_data("GenerateDynamicGrammar", r#"{"grammar_id":"g1"}"#),
    );
    send(
        &mut mgr,
        &dg_with_data("NotifyData", r#"{"data":"test"}"#),
    );
    let r = send(&mut mgr, &dg("GenerationAborted"));
    assert_eq!(r.dynamic_grammar_state, "Pending");
}

#[test]
fn dg_generating_queues_multiple_requests() {
    let mut mgr = VoiceSystemManager::new(None);
    send(
        &mut mgr,
        &dg_with_data("GenerateDynamicGrammar", r#"{"grammar_id":"g1"}"#),
    );
    send(
        &mut mgr,
        &dg_with_data("NotifyData", r#"{"data":"test"}"#),
    );
    // 複数の追加要求をキューイング
    send(
        &mut mgr,
        &dg_with_data("GenerateDynamicGrammar", r#"{"grammar_id":"g2"}"#),
    );
    send(
        &mut mgr,
        &dg_with_data("GenerateDynamicGrammar", r#"{"grammar_id":"g3"}"#),
    );
    // 1回目の完了 → キューにg2,g3があるのでDataGettingへ
    let r = send(&mut mgr, &dg("GenerationComplete"));
    assert_eq!(r.dynamic_grammar_state, "DataGetting");
}

// --- Pending ---

#[test]
fn dg_pending_session_end_to_data_getting() {
    let mut mgr = VoiceSystemManager::new(None);
    send(
        &mut mgr,
        &dg_with_data("GenerateDynamicGrammar", r#"{"grammar_id":"g1"}"#),
    );
    // セッションアクティブ状態で NotifyData → Pending
    send(
        &mut mgr,
        &dg_with_data("ChangedSessionStatus", r#"{"status_id":"InSession"}"#),
    );
    send(
        &mut mgr,
        &dg_with_data("NotifyData", r#"{"data":"test"}"#),
    );
    // セッション終了 → DataGetting
    let r = send(
        &mut mgr,
        &dg_with_data("ChangedSessionStatus", r#"{"status_id":"Inactive"}"#),
    );
    assert_eq!(r.dynamic_grammar_state, "DataGetting");
}

#[test]
fn dg_pending_session_still_active_stays() {
    let mut mgr = VoiceSystemManager::new(None);
    send(
        &mut mgr,
        &dg_with_data("GenerateDynamicGrammar", r#"{"grammar_id":"g1"}"#),
    );
    send(
        &mut mgr,
        &dg_with_data("ChangedSessionStatus", r#"{"status_id":"InSession"}"#),
    );
    send(
        &mut mgr,
        &dg_with_data("NotifyData", r#"{"data":"test"}"#),
    );
    // PreSession → まだアクティブなのでPendingのまま
    let r = send(
        &mut mgr,
        &dg_with_data("ChangedSessionStatus", r#"{"status_id":"InPreSession"}"#),
    );
    assert_eq!(r.dynamic_grammar_state, "Pending");
}

#[test]
fn dg_pending_queues_new_request() {
    let mut mgr = VoiceSystemManager::new(None);
    send(
        &mut mgr,
        &dg_with_data("GenerateDynamicGrammar", r#"{"grammar_id":"g1"}"#),
    );
    send(
        &mut mgr,
        &dg_with_data("ChangedSessionStatus", r#"{"status_id":"InSession"}"#),
    );
    send(
        &mut mgr,
        &dg_with_data("NotifyData", r#"{"data":"test"}"#),
    );
    // Pending中に追加要求
    let r = send(
        &mut mgr,
        &dg_with_data("GenerateDynamicGrammar", r#"{"grammar_id":"g2"}"#),
    );
    assert_eq!(r.dynamic_grammar_state, "Pending");
}

#[test]
fn dg_pending_ignores_generation_complete() {
    let mut mgr = VoiceSystemManager::new(None);
    send(
        &mut mgr,
        &dg_with_data("GenerateDynamicGrammar", r#"{"grammar_id":"g1"}"#),
    );
    send(
        &mut mgr,
        &dg_with_data("ChangedSessionStatus", r#"{"status_id":"InSession"}"#),
    );
    send(
        &mut mgr,
        &dg_with_data("NotifyData", r#"{"data":"test"}"#),
    );
    let r = send(&mut mgr, &dg("GenerationComplete"));
    assert_eq!(r.dynamic_grammar_state, "Pending");
}

// ============================================================
// SM間協調テスト
// ============================================================

#[test]
fn coordination_vr_ptt_notifies_dg_pre_session() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_ready(&mut mgr);

    // DGをIdle → DataGetting → Generating
    send(
        &mut mgr,
        &dg_with_data("GenerateDynamicGrammar", r#"{"grammar_id":"g1"}"#),
    );
    send(
        &mut mgr,
        &dg_with_data("NotifyData", r#"{"data":"d"}"#),
    );

    // VRでPTT → DGにInPreSessionが通知される → Generating中なのでPendingへ
    let r = send(&mut mgr, &vr("Ptt"));
    assert_eq!(r.voice_recognition_state, "PreSession");
    assert_eq!(r.dynamic_grammar_state, "Pending");
}

#[test]
fn coordination_vr_wuw_notifies_dg_pre_session() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_ready(&mut mgr);

    send(
        &mut mgr,
        &dg_with_data("GenerateDynamicGrammar", r#"{"grammar_id":"g1"}"#),
    );
    send(
        &mut mgr,
        &dg_with_data("NotifyData", r#"{"data":"d"}"#),
    );

    let r = send(&mut mgr, &vr("WuWDetected"));
    assert_eq!(r.voice_recognition_state, "PreSession");
    assert_eq!(r.dynamic_grammar_state, "Pending");
}

#[test]
fn coordination_vr_session_approved_notifies_dg_in_session() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_ready(&mut mgr);
    send(&mut mgr, &vr("Ptt"));

    // DGをDataGettingへ
    send(
        &mut mgr,
        &dg_with_data("GenerateDynamicGrammar", r#"{"grammar_id":"g1"}"#),
    );

    // PreSession → Prepare で InSession 通知
    let r = send(
        &mut mgr,
        &vr_with_data(
            "PreSessionResponse",
            r#"{"approved":true,"context_data":"c"}"#,
        ),
    );
    assert_eq!(r.voice_recognition_state, "Prepare");
    // DGのDataGettingにはChangedSessionStatus(InSession)が来るが、
    // DataGettingはNotifyDataまで遷移しないのでDataGettingのまま
    assert_eq!(r.dynamic_grammar_state, "DataGetting");
}

#[test]
fn coordination_vr_session_rejected_notifies_dg_inactive() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_ready(&mut mgr);
    send(&mut mgr, &vr("Ptt"));

    let r = send(
        &mut mgr,
        &vr_with_data(
            "PreSessionResponse",
            r#"{"approved":false,"context_data":null}"#,
        ),
    );
    assert_eq!(r.voice_recognition_state, "Ready");
}

#[test]
fn coordination_vr_session_end_notifies_dg_pending_to_data_getting() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_ready(&mut mgr);

    // DGをGeneratingにする
    send(
        &mut mgr,
        &dg_with_data("GenerateDynamicGrammar", r#"{"grammar_id":"g1"}"#),
    );
    send(
        &mut mgr,
        &dg_with_data("NotifyData", r#"{"data":"d"}"#),
    );

    // VR PTT → DG Pending
    send(&mut mgr, &vr("Ptt"));
    assert_eq!(
        mgr.handle_event_json(&vr("InitializeComplete"))
            .dynamic_grammar_state,
        "Pending"
    );

    // VR: PreSession → Prepare → ... → TaskExecAndEnd → Ready
    // PreSessionResponseでInSession通知、DGはPendingのまま
    send(
        &mut mgr,
        &vr_with_data(
            "PreSessionResponse",
            r#"{"approved":true,"context_data":"c"}"#,
        ),
    );
    send(&mut mgr, &vr("PrepareCompleteWithoutBargeIn"));
    send(&mut mgr, &vr("GuidanceComplete"));
    send(&mut mgr, &vr("SpeechDetected"));
    send(
        &mut mgr,
        &vr_with_data("RecognitionResult", r#"{"result":"ok"}"#),
    );
    send(&mut mgr, &vr("TaskAndEnd"));

    // TaskExecEndComplete → Ready → Inactive通知 → DGはPending → DataGetting
    let r = send(&mut mgr, &vr("TaskExecEndComplete"));
    assert_eq!(r.voice_recognition_state, "Ready");
    assert_eq!(r.dynamic_grammar_state, "DataGetting");
}

#[test]
fn coordination_vr_silent_abort_notifies_dg() {
    let mut mgr = VoiceSystemManager::new(None);
    go_to_ready(&mut mgr);

    // DGをGeneratingにする
    send(
        &mut mgr,
        &dg_with_data("GenerateDynamicGrammar", r#"{"grammar_id":"g1"}"#),
    );
    send(
        &mut mgr,
        &dg_with_data("NotifyData", r#"{"data":"d"}"#),
    );

    // VR PTT → DG Pending
    send(&mut mgr, &vr("Ptt"));
    send(
        &mut mgr,
        &vr_with_data(
            "PreSessionResponse",
            r#"{"approved":true,"context_data":"c"}"#,
        ),
    );

    // SilentAbort → Inactive通知 → DG Pending → DataGetting
    let r = send(&mut mgr, &vr("SilentAbort"));
    assert_eq!(r.voice_recognition_state, "Ready");
    assert_eq!(r.dynamic_grammar_state, "DataGetting");
}

#[test]
fn coordination_vr_error_end_notifies_dg() {
    let mut mgr = VoiceSystemManager::new(None);

    // DGをGeneratingにする
    send(
        &mut mgr,
        &dg_with_data("GenerateDynamicGrammar", r#"{"grammar_id":"g1"}"#),
    );
    send(
        &mut mgr,
        &dg_with_data("NotifyData", r#"{"data":"d"}"#),
    );

    // VRをSessionに入れる → DG Pending
    go_to_condition_checking(&mut mgr);

    // ErrorEnd → ErrorGuidanceComplete → Ready → DG DataGetting
    send(&mut mgr, &vr("ErrorEnd"));
    let r = send(&mut mgr, &vr("ErrorGuidanceComplete"));
    assert_eq!(r.voice_recognition_state, "Ready");
    assert_eq!(r.dynamic_grammar_state, "DataGetting");
}

#[test]
fn coordination_vr_abort_end_notifies_dg() {
    let mut mgr = VoiceSystemManager::new(None);

    // DGをGeneratingにする
    send(
        &mut mgr,
        &dg_with_data("GenerateDynamicGrammar", r#"{"grammar_id":"g1"}"#),
    );
    send(
        &mut mgr,
        &dg_with_data("NotifyData", r#"{"data":"d"}"#),
    );

    // VRをListeningに入れる → DG Pending
    go_to_listening_no_bargein(&mut mgr);

    // Abort → AbortGuidanceComplete → Ready → DG DataGetting
    send(&mut mgr, &vr("Abort"));
    let r = send(&mut mgr, &vr("AbortGuidanceComplete"));
    assert_eq!(r.voice_recognition_state, "Ready");
    assert_eq!(r.dynamic_grammar_state, "DataGetting");
}

// ============================================================
// FFI: JSON入出力テスト
// ============================================================

#[test]
fn ffi_handle_event_null_handle() {
    let json_c = CString::new("{}").unwrap();
    let result = unsafe { statig_json_cffi::handle_event(std::ptr::null_mut(), json_c.as_ptr()) };
    assert!(result.is_null());
}

#[test]
fn ffi_handle_event_null_json() {
    let handle = statig_json_cffi::create_voice_system(None);
    let result = unsafe { statig_json_cffi::handle_event(handle, std::ptr::null()) };
    assert!(result.is_null());
    unsafe {
        statig_json_cffi::destroy_voice_system(handle);
    }
}

#[test]
fn ffi_get_current_state_null_handle() {
    let result = unsafe { statig_json_cffi::get_current_state(std::ptr::null_mut()) };
    assert!(result.is_null());
}

#[test]
fn ffi_destroy_null_handle() {
    // NULLハンドルのdestroyはno-opであること（クラッシュしない）
    unsafe {
        statig_json_cffi::destroy_voice_system(std::ptr::null_mut());
    }
}

#[test]
fn ffi_invalid_json_returns_error() {
    let handle = statig_json_cffi::create_voice_system(None);
    let json_c = CString::new("not json").unwrap();
    let result = unsafe { statig_json_cffi::handle_event(handle, json_c.as_ptr()) };
    assert!(!result.is_null());
    let resp_str = unsafe { CStr::from_ptr(result) }.to_str().unwrap();
    let resp: SystemResponse = serde_json::from_str(resp_str).unwrap();
    assert!(!resp.success);
    assert!(resp.message.unwrap().contains("JSON parse error"));
    unsafe {
        statig_json_cffi::destroy_voice_system(handle);
    }
}

#[test]
fn ffi_unknown_target_returns_error() {
    let handle = statig_json_cffi::create_voice_system(None);
    let json_c = CString::new(r#"{"target":"Unknown","event":{"type":"Ptt"}}"#).unwrap();
    let result = unsafe { statig_json_cffi::handle_event(handle, json_c.as_ptr()) };
    assert!(!result.is_null());
    let resp_str = unsafe { CStr::from_ptr(result) }.to_str().unwrap();
    let resp: SystemResponse = serde_json::from_str(resp_str).unwrap();
    assert!(!resp.success);
    unsafe {
        statig_json_cffi::destroy_voice_system(handle);
    }
}

#[test]
fn ffi_all_vr_event_json_formats_parse_correctly() {
    // 全VRイベントのJSONが正しくパースされることを確認
    let handle = statig_json_cffi::create_voice_system(None);

    let events = [
        r#"{"target":"VoiceRecognition","event":{"type":"InitializeComplete"}}"#,
        r#"{"target":"VoiceRecognition","event":{"type":"InitializeFailed"}}"#,
        r#"{"target":"VoiceRecognition","event":{"type":"Ptt"}}"#,
        r#"{"target":"VoiceRecognition","event":{"type":"WuWDetected"}}"#,
        r#"{"target":"VoiceRecognition","event":{"type":"LanguageChanged"}}"#,
        r#"{"target":"VoiceRecognition","event":{"type":"PreSessionResponse","data":{"approved":true,"context_data":"c"}}}"#,
        r#"{"target":"VoiceRecognition","event":{"type":"PreSessionResponse","data":{"approved":false,"context_data":null}}}"#,
        r#"{"target":"VoiceRecognition","event":{"type":"Abort"}}"#,
        r#"{"target":"VoiceRecognition","event":{"type":"SilentAbort"}}"#,
        r#"{"target":"VoiceRecognition","event":{"type":"ItemSelected","data":{"context_id":"id1"}}}"#,
        r#"{"target":"VoiceRecognition","event":{"type":"Back","data":{"context_id":"id1"}}}"#,
        r#"{"target":"VoiceRecognition","event":{"type":"PrepareCompleteWithBargeIn"}}"#,
        r#"{"target":"VoiceRecognition","event":{"type":"PrepareCompleteWithoutBargeIn"}}"#,
        r#"{"target":"VoiceRecognition","event":{"type":"GuidanceComplete"}}"#,
        r#"{"target":"VoiceRecognition","event":{"type":"SpeechDetected"}}"#,
        r#"{"target":"VoiceRecognition","event":{"type":"SpeechTimeout"}}"#,
        r#"{"target":"VoiceRecognition","event":{"type":"RecognitionResult","data":{"result":"hello"}}}"#,
        r#"{"target":"VoiceRecognition","event":{"type":"UtteranceTimeout"}}"#,
        r#"{"target":"VoiceRecognition","event":{"type":"ContinueWithGuidance"}}"#,
        r#"{"target":"VoiceRecognition","event":{"type":"ContinueWithTask"}}"#,
        r#"{"target":"VoiceRecognition","event":{"type":"TaskAndEnd"}}"#,
        r#"{"target":"VoiceRecognition","event":{"type":"ErrorEnd"}}"#,
        r#"{"target":"VoiceRecognition","event":{"type":"FollowupGuidanceComplete"}}"#,
        r#"{"target":"VoiceRecognition","event":{"type":"TaskExecContinueComplete"}}"#,
        r#"{"target":"VoiceRecognition","event":{"type":"TaskExecEndComplete"}}"#,
        r#"{"target":"VoiceRecognition","event":{"type":"ErrorGuidanceComplete"}}"#,
        r#"{"target":"VoiceRecognition","event":{"type":"AbortGuidanceComplete"}}"#,
    ];

    for event_json in &events {
        let json_c = CString::new(*event_json).unwrap();
        let result = unsafe { statig_json_cffi::handle_event(handle, json_c.as_ptr()) };
        assert!(!result.is_null(), "NULL response for: {}", event_json);
        let resp_str = unsafe { CStr::from_ptr(result) }.to_str().unwrap();
        let resp: SystemResponse = serde_json::from_str(resp_str)
            .unwrap_or_else(|e| panic!("Failed to parse response for {}: {}", event_json, e));
        assert!(
            resp.success,
            "Event failed: {} -> {:?}",
            event_json, resp.message
        );
    }

    unsafe {
        statig_json_cffi::destroy_voice_system(handle);
    }
}

#[test]
fn ffi_all_dg_event_json_formats_parse_correctly() {
    // 全DGイベントのJSONが正しくパースされることを確認
    let handle = statig_json_cffi::create_voice_system(None);

    let events = [
        r#"{"target":"DynamicGrammar","event":{"type":"GenerateDynamicGrammar","data":{"grammar_id":"g1"}}}"#,
        r#"{"target":"DynamicGrammar","event":{"type":"ChangedSessionStatus","data":{"status_id":"Inactive"}}}"#,
        r#"{"target":"DynamicGrammar","event":{"type":"ChangedSessionStatus","data":{"status_id":"InPreSession"}}}"#,
        r#"{"target":"DynamicGrammar","event":{"type":"ChangedSessionStatus","data":{"status_id":"InSession"}}}"#,
        r#"{"target":"DynamicGrammar","event":{"type":"NotifyData","data":{"data":"test_data"}}}"#,
        r#"{"target":"DynamicGrammar","event":{"type":"GenerationComplete"}}"#,
        r#"{"target":"DynamicGrammar","event":{"type":"GenerationAborted"}}"#,
    ];

    for event_json in &events {
        let json_c = CString::new(*event_json).unwrap();
        let result = unsafe { statig_json_cffi::handle_event(handle, json_c.as_ptr()) };
        assert!(!result.is_null(), "NULL response for: {}", event_json);
        let resp_str = unsafe { CStr::from_ptr(result) }.to_str().unwrap();
        let resp: SystemResponse = serde_json::from_str(resp_str)
            .unwrap_or_else(|e| panic!("Failed to parse response for {}: {}", event_json, e));
        assert!(
            resp.success,
            "Event failed: {} -> {:?}",
            event_json, resp.message
        );
    }

    unsafe {
        statig_json_cffi::destroy_voice_system(handle);
    }
}

#[test]
fn ffi_response_json_format() {
    let handle = statig_json_cffi::create_voice_system(None);

    let state_ptr = unsafe { statig_json_cffi::get_current_state(handle) };
    let state_str = unsafe { CStr::from_ptr(state_ptr) }.to_str().unwrap();
    let resp: serde_json::Value = serde_json::from_str(state_str).unwrap();

    // レスポンスJSONの全フィールドが存在すること
    assert!(resp.get("success").unwrap().is_boolean());
    assert!(resp.get("voice_recognition_state").unwrap().is_string());
    assert!(resp.get("dynamic_grammar_state").unwrap().is_string());
    // message は null (省略) であること
    assert!(resp.get("message").is_none());

    unsafe {
        statig_json_cffi::destroy_voice_system(handle);
    }
}

// ============================================================
// 動的グラマSM: 複合シナリオ
// ============================================================

#[test]
fn dg_full_lifecycle_with_queue_and_session_interrupt() {
    let mut mgr = VoiceSystemManager::new(None);

    // 1. Idle → DataGetting → Generating
    send(
        &mut mgr,
        &dg_with_data("GenerateDynamicGrammar", r#"{"grammar_id":"g1"}"#),
    );
    send(
        &mut mgr,
        &dg_with_data("NotifyData", r#"{"data":"d1"}"#),
    );
    assert_eq!(
        mgr.get_current_state_json(),
        serde_json::to_string(&SystemResponse {
            success: true,
            voice_recognition_state: "Initializing".to_string(),
            dynamic_grammar_state: "Generating".to_string(),
            message: None,
        })
        .unwrap()
    );

    // 2. Generating中に追加要求2件
    send(
        &mut mgr,
        &dg_with_data("GenerateDynamicGrammar", r#"{"grammar_id":"g2"}"#),
    );
    send(
        &mut mgr,
        &dg_with_data("GenerateDynamicGrammar", r#"{"grammar_id":"g3"}"#),
    );

    // 3. セッション開始 → Pending
    let r = send(
        &mut mgr,
        &dg_with_data("ChangedSessionStatus", r#"{"status_id":"InSession"}"#),
    );
    assert_eq!(r.dynamic_grammar_state, "Pending");

    // 4. Pending中に追加要求
    send(
        &mut mgr,
        &dg_with_data("GenerateDynamicGrammar", r#"{"grammar_id":"g4"}"#),
    );

    // 5. セッション終了 → DataGetting
    let r = send(
        &mut mgr,
        &dg_with_data("ChangedSessionStatus", r#"{"status_id":"Inactive"}"#),
    );
    assert_eq!(r.dynamic_grammar_state, "DataGetting");

    // 6. 中断された要求を再開: DataGetting → Generating
    //    キューは[g2,g3,g4]
    send(
        &mut mgr,
        &dg_with_data("NotifyData", r#"{"data":"d_resume"}"#),
    );
    // 完了 → g2をpop → キュー[g3,g4] → DataGetting
    let r = send(&mut mgr, &dg("GenerationComplete"));
    assert_eq!(r.dynamic_grammar_state, "DataGetting");

    // 7. g2の処理: DataGetting → Generating
    send(
        &mut mgr,
        &dg_with_data("NotifyData", r#"{"data":"d2"}"#),
    );
    // 完了 → g3をpop → キュー[g4] → DataGetting
    let r = send(&mut mgr, &dg("GenerationComplete"));
    assert_eq!(r.dynamic_grammar_state, "DataGetting");

    // 8. g3の処理: DataGetting → Generating
    send(
        &mut mgr,
        &dg_with_data("NotifyData", r#"{"data":"d3"}"#),
    );
    // 完了 → g4をpop → キュー空 → DataGetting
    let r = send(&mut mgr, &dg("GenerationComplete"));
    assert_eq!(r.dynamic_grammar_state, "DataGetting");

    // 9. g4の処理: DataGetting → Generating
    send(
        &mut mgr,
        &dg_with_data("NotifyData", r#"{"data":"d4"}"#),
    );
    // 完了 → キュー空 → Idle
    let r = send(&mut mgr, &dg("GenerationComplete"));
    assert_eq!(r.dynamic_grammar_state, "Idle");
}
