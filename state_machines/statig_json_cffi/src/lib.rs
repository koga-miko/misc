pub mod dynamic_grammar;
pub mod manager;
pub mod types;
pub mod voice_recognition;

use manager::VoiceSystemManager;
use std::ffi::{CStr, CString};
use std::os::raw::c_char;
use std::panic;
use std::ptr;

/// FFI用のハンドル型
pub struct VoiceSystemHandle {
    manager: VoiceSystemManager,
    /// 最後のレスポンスJSON（C側で参照するため保持）
    last_response: CString,
}

/// 音声認識システムを生成する
///
/// # Safety
/// - 戻り値のポインタは `destroy_voice_system` で解放すること
/// - `callback` は状態のentry/exitタイミングでJSON文字列と共に呼ばれる
///   - kind: 0=entry（状態に入る直前）, 1=exit（状態を抜ける直前）
///   - json: NULL終端UTF-8 JSON文字列（呼び出し中のみ有効）
///   - NULLを渡すとコールバックなし
#[unsafe(no_mangle)]
pub extern "C" fn create_voice_system(
    callback: types::StateCallbackFn,
) -> *mut VoiceSystemHandle {
    let result = panic::catch_unwind(|| {
        let handle = Box::new(VoiceSystemHandle {
            manager: VoiceSystemManager::new(callback),
            last_response: CString::new("").unwrap(),
        });
        Box::into_raw(handle)
    });
    result.unwrap_or(ptr::null_mut())
}

/// 音声認識システムを破棄する
///
/// # Safety
/// `handle` は `create_voice_system` で生成されたポインタであること
#[unsafe(no_mangle)]
pub unsafe extern "C" fn destroy_voice_system(handle: *mut VoiceSystemHandle) {
    if !handle.is_null() {
        unsafe {
            drop(Box::from_raw(handle));
        }
    }
}

/// JSONイベントを処理して結果をJSON文字列で返す
///
/// # Safety
/// - `handle` は有効なポインタであること
/// - `json_ptr` は有効なNULL終端UTF-8文字列へのポインタであること
/// - 戻り値は次の `handle_event` または `destroy_voice_system` 呼び出しまで有効
#[unsafe(no_mangle)]
pub unsafe extern "C" fn handle_event(
    handle: *mut VoiceSystemHandle,
    json_ptr: *const c_char,
) -> *const c_char {
    if handle.is_null() || json_ptr.is_null() {
        return ptr::null();
    }

    let result = panic::catch_unwind(|| {
        let handle = unsafe { &mut *handle };
        let json_str = unsafe { CStr::from_ptr(json_ptr) };
        let json = match json_str.to_str() {
            Ok(s) => s,
            Err(_) => {
                let err = serde_json::to_string(&types::SystemResponse {
                    success: false,
                    voice_recognition_state: String::new(),
                    dynamic_grammar_state: String::new(),
                    message: Some("Invalid UTF-8 input".to_string()),
                })
                .unwrap_or_default();
                handle.last_response = CString::new(err).unwrap_or_default();
                return handle.last_response.as_ptr();
            }
        };

        let response = handle.manager.handle_event_json(json);
        let response_json =
            serde_json::to_string(&response).unwrap_or_else(|_| "{}".to_string());
        handle.last_response = CString::new(response_json).unwrap_or_default();
        handle.last_response.as_ptr()
    });

    result.unwrap_or(ptr::null())
}

/// 現在の状態をJSON文字列で取得する
///
/// # Safety
/// - `handle` は有効なポインタであること
/// - 戻り値は次の `get_current_state` または `destroy_voice_system` 呼び出しまで有効
#[unsafe(no_mangle)]
pub unsafe extern "C" fn get_current_state(
    handle: *mut VoiceSystemHandle,
) -> *const c_char {
    if handle.is_null() {
        return ptr::null();
    }

    let result = panic::catch_unwind(|| {
        let handle = unsafe { &mut *handle };
        let state_json = handle.manager.get_current_state_json();
        handle.last_response = CString::new(state_json).unwrap_or_default();
        handle.last_response.as_ptr()
    });

    result.unwrap_or(ptr::null())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_create_and_destroy() {
        let handle = create_voice_system(None);
        assert!(!handle.is_null());
        unsafe {
            destroy_voice_system(handle);
        }
    }

    #[test]
    fn test_initial_state() {
        let handle = create_voice_system(None);
        assert!(!handle.is_null());

        let state_ptr = unsafe { get_current_state(handle) };
        assert!(!state_ptr.is_null());

        let state_str = unsafe { CStr::from_ptr(state_ptr) }.to_str().unwrap();
        let response: types::SystemResponse = serde_json::from_str(state_str).unwrap();

        assert!(response.success);
        assert_eq!(response.voice_recognition_state, "Initializing");
        assert_eq!(response.dynamic_grammar_state, "Idle");

        unsafe {
            destroy_voice_system(handle);
        }
    }

    #[test]
    fn test_vr_state_transitions() {
        let handle = create_voice_system(None);

        // Initializing → Ready
        let json = r#"{"target":"VoiceRecognition","event":{"type":"InitializeComplete"}}"#;
        let json_c = CString::new(json).unwrap();
        let resp_ptr = unsafe { handle_event(handle, json_c.as_ptr()) };
        let resp: types::SystemResponse =
            serde_json::from_str(unsafe { CStr::from_ptr(resp_ptr) }.to_str().unwrap())
                .unwrap();
        assert!(resp.success);
        assert_eq!(resp.voice_recognition_state, "Ready");

        // Ready → PreSession (via Ptt)
        let json = r#"{"target":"VoiceRecognition","event":{"type":"Ptt"}}"#;
        let json_c = CString::new(json).unwrap();
        let resp_ptr = unsafe { handle_event(handle, json_c.as_ptr()) };
        let resp: types::SystemResponse =
            serde_json::from_str(unsafe { CStr::from_ptr(resp_ptr) }.to_str().unwrap())
                .unwrap();
        assert_eq!(resp.voice_recognition_state, "PreSession");

        // PreSession → Prepare (approved)
        let json = r#"{"target":"VoiceRecognition","event":{"type":"PreSessionResponse","data":{"approved":true,"context_data":"test"}}}"#;
        let json_c = CString::new(json).unwrap();
        let resp_ptr = unsafe { handle_event(handle, json_c.as_ptr()) };
        let resp: types::SystemResponse =
            serde_json::from_str(unsafe { CStr::from_ptr(resp_ptr) }.to_str().unwrap())
                .unwrap();
        assert_eq!(resp.voice_recognition_state, "Prepare");

        // Prepare → Guidance (without barge-in)
        let json =
            r#"{"target":"VoiceRecognition","event":{"type":"PrepareCompleteWithoutBargeIn"}}"#;
        let json_c = CString::new(json).unwrap();
        let resp_ptr = unsafe { handle_event(handle, json_c.as_ptr()) };
        let resp: types::SystemResponse =
            serde_json::from_str(unsafe { CStr::from_ptr(resp_ptr) }.to_str().unwrap())
                .unwrap();
        assert_eq!(resp.voice_recognition_state, "Guidance");

        // Guidance → Listening
        let json = r#"{"target":"VoiceRecognition","event":{"type":"GuidanceComplete"}}"#;
        let json_c = CString::new(json).unwrap();
        let resp_ptr = unsafe { handle_event(handle, json_c.as_ptr()) };
        let resp: types::SystemResponse =
            serde_json::from_str(unsafe { CStr::from_ptr(resp_ptr) }.to_str().unwrap())
                .unwrap();
        assert_eq!(resp.voice_recognition_state, "Listening");

        // Listening → Speaking
        let json = r#"{"target":"VoiceRecognition","event":{"type":"SpeechDetected"}}"#;
        let json_c = CString::new(json).unwrap();
        let resp_ptr = unsafe { handle_event(handle, json_c.as_ptr()) };
        let resp: types::SystemResponse =
            serde_json::from_str(unsafe { CStr::from_ptr(resp_ptr) }.to_str().unwrap())
                .unwrap();
        assert_eq!(resp.voice_recognition_state, "Speaking");

        // Speaking → ConditionChecking
        let json = r#"{"target":"VoiceRecognition","event":{"type":"RecognitionResult","data":{"result":"hello"}}}"#;
        let json_c = CString::new(json).unwrap();
        let resp_ptr = unsafe { handle_event(handle, json_c.as_ptr()) };
        let resp: types::SystemResponse =
            serde_json::from_str(unsafe { CStr::from_ptr(resp_ptr) }.to_str().unwrap())
                .unwrap();
        assert_eq!(resp.voice_recognition_state, "ConditionChecking");

        // ConditionChecking → TaskExecAndEnd
        let json = r#"{"target":"VoiceRecognition","event":{"type":"TaskAndEnd"}}"#;
        let json_c = CString::new(json).unwrap();
        let resp_ptr = unsafe { handle_event(handle, json_c.as_ptr()) };
        let resp: types::SystemResponse =
            serde_json::from_str(unsafe { CStr::from_ptr(resp_ptr) }.to_str().unwrap())
                .unwrap();
        assert_eq!(resp.voice_recognition_state, "TaskExecAndEnd");

        // TaskExecAndEnd → Ready
        let json =
            r#"{"target":"VoiceRecognition","event":{"type":"TaskExecEndComplete"}}"#;
        let json_c = CString::new(json).unwrap();
        let resp_ptr = unsafe { handle_event(handle, json_c.as_ptr()) };
        let resp: types::SystemResponse =
            serde_json::from_str(unsafe { CStr::from_ptr(resp_ptr) }.to_str().unwrap())
                .unwrap();
        assert_eq!(resp.voice_recognition_state, "Ready");

        unsafe {
            destroy_voice_system(handle);
        }
    }

    #[test]
    fn test_abort_from_session() {
        let handle = create_voice_system(None);

        let events = [
            (r#"{"target":"VoiceRecognition","event":{"type":"InitializeComplete"}}"#, "Ready"),
            (r#"{"target":"VoiceRecognition","event":{"type":"Ptt"}}"#, "PreSession"),
            (r#"{"target":"VoiceRecognition","event":{"type":"PreSessionResponse","data":{"approved":true,"context_data":null}}}"#, "Prepare"),
            (r#"{"target":"VoiceRecognition","event":{"type":"PrepareCompleteWithoutBargeIn"}}"#, "Guidance"),
            (r#"{"target":"VoiceRecognition","event":{"type":"GuidanceComplete"}}"#, "Listening"),
            (r#"{"target":"VoiceRecognition","event":{"type":"Abort"}}"#, "Aborting"),
            (r#"{"target":"VoiceRecognition","event":{"type":"AbortGuidanceComplete"}}"#, "Ready"),
        ];

        for (json, expected_state) in &events {
            let json_c = CString::new(*json).unwrap();
            let resp_ptr = unsafe { handle_event(handle, json_c.as_ptr()) };
            let resp: types::SystemResponse =
                serde_json::from_str(unsafe { CStr::from_ptr(resp_ptr) }.to_str().unwrap())
                    .unwrap();
            assert!(resp.success);
            assert_eq!(
                resp.voice_recognition_state, *expected_state,
                "Failed at event: {}",
                json
            );
        }

        unsafe {
            destroy_voice_system(handle);
        }
    }

    #[test]
    fn test_dynamic_grammar_transitions() {
        let handle = create_voice_system(None);

        // Idle → DataGetting
        let json = r#"{"target":"DynamicGrammar","event":{"type":"GenerateDynamicGrammar","data":{"grammar_id":"g1"}}}"#;
        let json_c = CString::new(json).unwrap();
        let resp_ptr = unsafe { handle_event(handle, json_c.as_ptr()) };
        let resp: types::SystemResponse =
            serde_json::from_str(unsafe { CStr::from_ptr(resp_ptr) }.to_str().unwrap())
                .unwrap();
        assert_eq!(resp.dynamic_grammar_state, "DataGetting");

        // DataGetting → Generating (session not active)
        let json =
            r#"{"target":"DynamicGrammar","event":{"type":"NotifyData","data":{"data":"some_data"}}}"#;
        let json_c = CString::new(json).unwrap();
        let resp_ptr = unsafe { handle_event(handle, json_c.as_ptr()) };
        let resp: types::SystemResponse =
            serde_json::from_str(unsafe { CStr::from_ptr(resp_ptr) }.to_str().unwrap())
                .unwrap();
        assert_eq!(resp.dynamic_grammar_state, "Generating");

        // Generating → Idle (complete, no queue)
        let json = r#"{"target":"DynamicGrammar","event":{"type":"GenerationComplete"}}"#;
        let json_c = CString::new(json).unwrap();
        let resp_ptr = unsafe { handle_event(handle, json_c.as_ptr()) };
        let resp: types::SystemResponse =
            serde_json::from_str(unsafe { CStr::from_ptr(resp_ptr) }.to_str().unwrap())
                .unwrap();
        assert_eq!(resp.dynamic_grammar_state, "Idle");

        unsafe {
            destroy_voice_system(handle);
        }
    }

    #[test]
    fn test_session_status_coordination() {
        let handle = create_voice_system(None);

        // Initialize VR to Ready
        let json = r#"{"target":"VoiceRecognition","event":{"type":"InitializeComplete"}}"#;
        let json_c = CString::new(json).unwrap();
        unsafe { handle_event(handle, json_c.as_ptr()) };

        // Start grammar generation
        let json = r#"{"target":"DynamicGrammar","event":{"type":"GenerateDynamicGrammar","data":{"grammar_id":"g1"}}}"#;
        let json_c = CString::new(json).unwrap();
        unsafe { handle_event(handle, json_c.as_ptr()) };

        // Get data → Generating (no session yet)
        let json =
            r#"{"target":"DynamicGrammar","event":{"type":"NotifyData","data":{"data":"d"}}}"#;
        let json_c = CString::new(json).unwrap();
        let resp_ptr = unsafe { handle_event(handle, json_c.as_ptr()) };
        let resp: types::SystemResponse =
            serde_json::from_str(unsafe { CStr::from_ptr(resp_ptr) }.to_str().unwrap())
                .unwrap();
        assert_eq!(resp.dynamic_grammar_state, "Generating");

        // Start VR session (PTT) → should notify DG SM of session start
        let json = r#"{"target":"VoiceRecognition","event":{"type":"Ptt"}}"#;
        let json_c = CString::new(json).unwrap();
        let resp_ptr = unsafe { handle_event(handle, json_c.as_ptr()) };
        let resp: types::SystemResponse =
            serde_json::from_str(unsafe { CStr::from_ptr(resp_ptr) }.to_str().unwrap())
                .unwrap();
        assert_eq!(resp.voice_recognition_state, "PreSession");
        // DG should move to Pending because session became active during Generating
        assert_eq!(resp.dynamic_grammar_state, "Pending");

        unsafe {
            destroy_voice_system(handle);
        }
    }

    #[test]
    fn test_invalid_json() {
        let handle = create_voice_system(None);

        let json = r#"{"invalid": true}"#;
        let json_c = CString::new(json).unwrap();
        let resp_ptr = unsafe { handle_event(handle, json_c.as_ptr()) };
        let resp: types::SystemResponse =
            serde_json::from_str(unsafe { CStr::from_ptr(resp_ptr) }.to_str().unwrap())
                .unwrap();
        assert!(!resp.success);
        assert!(resp.message.is_some());

        unsafe {
            destroy_voice_system(handle);
        }
    }
}
