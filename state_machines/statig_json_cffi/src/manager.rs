use crate::dynamic_grammar;
use crate::dynamic_grammar::events::DynamicGrammarEvent;
use crate::types::{SessionStatus, StateCallbackFn, SystemEvent, SystemResponse};
use crate::voice_recognition;
use crate::voice_recognition::events::VoiceRecognitionEvent;
use statig::blocking::IntoStateMachineExt;

/// 2つのステートマシンを協調管理するマネージャ
pub struct VoiceSystemManager {
    vr_sm: statig::blocking::StateMachine<voice_recognition::VoiceRecognitionMachine>,
    dg_sm: statig::blocking::StateMachine<dynamic_grammar::DynamicGrammarMachine>,
}

impl VoiceSystemManager {
    pub fn new(callback: StateCallbackFn) -> Self {
        let mut vr = voice_recognition::VoiceRecognitionMachine::default();
        vr.callback = callback;
        let mut dg = dynamic_grammar::DynamicGrammarMachine::default();
        dg.callback = callback;
        Self {
            vr_sm: vr.state_machine(),
            dg_sm: dg.state_machine(),
        }
    }

    /// JSONイベント文字列を受け取り、適切なSMへルーティングして処理する
    pub fn handle_event_json(&mut self, json: &str) -> SystemResponse {
        let event: SystemEvent = match serde_json::from_str(json) {
            Ok(e) => e,
            Err(e) => {
                return SystemResponse {
                    success: false,
                    voice_recognition_state: self.vr_state_name().to_string(),
                    dynamic_grammar_state: self.dg_state_name().to_string(),
                    message: Some(format!("JSON parse error: {}", e)),
                };
            }
        };

        match event {
            SystemEvent::VoiceRecognition(vr_event) => {
                self.handle_vr_event(&vr_event);
            }
            SystemEvent::DynamicGrammar(dg_event) => {
                self.dg_sm.handle(&dg_event);
            }
        }

        SystemResponse {
            success: true,
            voice_recognition_state: self.vr_state_name().to_string(),
            dynamic_grammar_state: self.dg_state_name().to_string(),
            message: None,
        }
    }

    /// 音声認識イベントを処理し、セッション状態変更があれば動的グラマSMに通知する
    fn handle_vr_event(&mut self, event: &VoiceRecognitionEvent) {
        // イベント前にフラグをリセット
        // Safety: session_status_changedの変更はSMの状態遷移ロジックに影響しない
        unsafe {
            self.vr_sm.inner_mut().session_status_changed = None;
        }

        self.vr_sm.handle(event);

        // セッション状態変更があれば動的グラマSMに通知
        // Deref経由で読み取り（immutable）
        let status = self.vr_sm.session_status_changed;
        if let Some(status) = status {
            let status_id = match status {
                SessionStatus::Inactive => "Inactive",
                SessionStatus::InPreSession => "InPreSession",
                SessionStatus::InSession => "InSession",
            };
            self.dg_sm.handle(&DynamicGrammarEvent::ChangedSessionStatus {
                status_id: status_id.to_string(),
            });
        }
    }

    /// 現在の状態をJSON文字列として取得
    pub fn get_current_state_json(&self) -> String {
        let response = SystemResponse {
            success: true,
            voice_recognition_state: self.vr_state_name().to_string(),
            dynamic_grammar_state: self.dg_state_name().to_string(),
            message: None,
        };
        serde_json::to_string(&response).unwrap_or_else(|_| "{}".to_string())
    }

    fn vr_state_name(&self) -> &'static str {
        voice_recognition::state_name(self.vr_sm.state())
    }

    fn dg_state_name(&self) -> &'static str {
        dynamic_grammar::state_name(self.dg_sm.state())
    }
}
