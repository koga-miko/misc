use serde::{Deserialize, Serialize};
use std::ffi::CString;
use std::os::raw::c_char;

/// C言語側へ状態entry/exitを通知するコールバック関数ポインタ型
///
/// - `kind`: 通知種別 (0=entry, 1=exit)
/// - `json`: NULL終端UTF-8 JSON文字列
pub type StateCallbackFn = Option<unsafe extern "C" fn(kind: i32, json: *const c_char)>;

/// コールバック種別: 状態に入る直前
pub const CALLBACK_KIND_ENTRY: i32 = 0;
/// コールバック種別: 状態を抜ける直前
pub const CALLBACK_KIND_EXIT: i32 = 1;

/// コールバックを呼び出すヘルパー
pub fn invoke_callback(callback: StateCallbackFn, kind: i32, sm: &str, state: &str) {
    if let Some(cb) = callback {
        let kind_str = match kind {
            CALLBACK_KIND_ENTRY => "entry",
            CALLBACK_KIND_EXIT => "exit",
            _ => "unknown",
        };
        let json = format!(
            r#"{{"sm":"{}","state":"{}","kind":"{}"}}"#,
            sm, state, kind_str
        );
        if let Ok(c_json) = CString::new(json) {
            unsafe {
                cb(kind, c_json.as_ptr());
            }
        }
    }
}

/// FFIから受け取るイベントのJSON表現
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "target", content = "event")]
pub enum SystemEvent {
    /// 音声認識ステートマシン向けイベント
    VoiceRecognition(crate::voice_recognition::events::VoiceRecognitionEvent),
    /// 動的グラマ生成ステートマシン向けイベント
    DynamicGrammar(crate::dynamic_grammar::events::DynamicGrammarEvent),
}

/// FFIから返すレスポンスのJSON表現
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemResponse {
    /// 処理成功したか
    pub success: bool,
    /// 音声認識SMの現在状態
    pub voice_recognition_state: String,
    /// 動的グラマ生成SMの現在状態
    pub dynamic_grammar_state: String,
    /// 追加メッセージ（エラー時など）
    #[serde(skip_serializing_if = "Option::is_none")]
    pub message: Option<String>,
}

/// セッション状態（動的グラマSMが参照する）
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum SessionStatus {
    /// PreSessionでもSessionでもない
    Inactive,
    /// PreSession中
    InPreSession,
    /// Session中
    InSession,
}

impl Default for SessionStatus {
    fn default() -> Self {
        SessionStatus::Inactive
    }
}
