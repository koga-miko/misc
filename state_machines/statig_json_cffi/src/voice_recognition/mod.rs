pub mod events;

use crate::types::{invoke_callback, StateCallbackFn, CALLBACK_KIND_ENTRY, CALLBACK_KIND_EXIT};
use events::VoiceRecognitionEvent;
use statig::blocking::*;
use std::fmt;

type Outcome = statig::Outcome<State>;

const SM_NAME: &str = "VoiceRecognition";

/// 音声認識ステートマシンの本体
pub struct VoiceRecognitionMachine {
    /// セッション状態変更を外部に通知するためのコールバック用フラグ
    pub session_status_changed: Option<crate::types::SessionStatus>,
    /// C言語側への状態entry/exitコールバック
    pub callback: StateCallbackFn,
}

impl Default for VoiceRecognitionMachine {
    fn default() -> Self {
        Self {
            session_status_changed: None,
            callback: None,
        }
    }
}

impl fmt::Debug for VoiceRecognitionMachine {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "VoiceRecognitionMachine")
    }
}

#[state_machine(
    initial = "State::initializing()",
    event_identifier = "event",
    state(derive(Debug, Clone, PartialEq, Eq))
)]
impl VoiceRecognitionMachine {
    // ===========================
    // コールバック通知ヘルパー
    // ===========================

    fn notify(&self, kind: i32, state: &str) {
        invoke_callback(self.callback, kind, SM_NAME, state);
    }

    // ===========================
    // メインレベルの状態
    // ===========================

    /// 初期化中
    #[state(entry_action = "enter_initializing", exit_action = "exit_initializing")]
    fn initializing(&mut self, event: &VoiceRecognitionEvent) -> Outcome {
        match event {
            VoiceRecognitionEvent::InitializeComplete => {
                Transition(State::ready())
            }
            VoiceRecognitionEvent::InitializeFailed => {
                Transition(State::wait_language_set())
            }
            _ => Handled,
        }
    }

    #[action]
    fn enter_initializing(&self) {
        self.notify(CALLBACK_KIND_ENTRY, "Initializing");
    }

    #[action]
    fn exit_initializing(&self) {
        self.notify(CALLBACK_KIND_EXIT, "Initializing");
    }

    /// 初期化失敗中のため次の言語設定を待つ状態
    #[state(entry_action = "enter_wait_language_set", exit_action = "exit_wait_language_set")]
    fn wait_language_set(&mut self, event: &VoiceRecognitionEvent) -> Outcome {
        match event {
            VoiceRecognitionEvent::LanguageChanged => {
                Transition(State::initializing())
            }
            _ => Handled,
        }
    }

    #[action]
    fn enter_wait_language_set(&self) {
        self.notify(CALLBACK_KIND_ENTRY, "WaitLanguageSet");
    }

    #[action]
    fn exit_wait_language_set(&self) {
        self.notify(CALLBACK_KIND_EXIT, "WaitLanguageSet");
    }

    /// PTTかWuWで音声認識を受け付けられる状態
    #[state(entry_action = "enter_ready", exit_action = "exit_ready")]
    fn ready(&mut self, event: &VoiceRecognitionEvent) -> Outcome {
        match event {
            VoiceRecognitionEvent::Ptt | VoiceRecognitionEvent::WuWDetected => {
                self.session_status_changed = Some(crate::types::SessionStatus::InPreSession);
                Transition(State::pre_session())
            }
            VoiceRecognitionEvent::LanguageChanged => {
                Transition(State::initializing())
            }
            _ => Handled,
        }
    }

    #[action]
    fn enter_ready(&self) {
        self.notify(CALLBACK_KIND_ENTRY, "Ready");
    }

    #[action]
    fn exit_ready(&self) {
        self.notify(CALLBACK_KIND_EXIT, "Ready");
    }

    /// 音声認識開始できるかどうか問い合わせて応答を待っている状態
    #[state(entry_action = "enter_pre_session", exit_action = "exit_pre_session")]
    fn pre_session(&mut self, event: &VoiceRecognitionEvent) -> Outcome {
        match event {
            VoiceRecognitionEvent::PreSessionResponse {
                approved,
                context_data: _,
            } => {
                if *approved {
                    self.session_status_changed = Some(crate::types::SessionStatus::InSession);
                    Transition(State::prepare())
                } else {
                    self.session_status_changed = Some(crate::types::SessionStatus::Inactive);
                    Transition(State::ready())
                }
            }
            _ => Handled,
        }
    }

    #[action]
    fn enter_pre_session(&self) {
        self.notify(CALLBACK_KIND_ENTRY, "PreSession");
    }

    #[action]
    fn exit_pre_session(&self) {
        self.notify(CALLBACK_KIND_EXIT, "PreSession");
    }

    // ===========================
    // Session superstate
    // ===========================

    /// Session superstate: 音声認識のセッション状態
    /// Abort/SilentAbortをここで共通処理する
    #[superstate(entry_action = "enter_session", exit_action = "exit_session")]
    fn session(&mut self, event: &VoiceRecognitionEvent) -> Outcome {
        match event {
            VoiceRecognitionEvent::Abort => {
                Transition(State::aborting())
            }
            VoiceRecognitionEvent::SilentAbort => {
                self.session_status_changed = Some(crate::types::SessionStatus::Inactive);
                Transition(State::ready())
            }
            _ => Handled,
        }
    }

    #[action]
    fn enter_session(&self) {
        self.notify(CALLBACK_KIND_ENTRY, "Session");
    }

    #[action]
    fn exit_session(&self) {
        self.notify(CALLBACK_KIND_EXIT, "Session");
    }

    // ===========================
    // Session内のサブ状態
    // ===========================

    /// JSONから最初のコンテキストのデータを読み出して認識語彙を準備
    #[state(superstate = "session", entry_action = "enter_prepare", exit_action = "exit_prepare")]
    fn prepare(&mut self, event: &VoiceRecognitionEvent) -> Outcome {
        match event {
            VoiceRecognitionEvent::PrepareCompleteWithBargeIn => {
                Transition(State::guidance_and_listening())
            }
            VoiceRecognitionEvent::PrepareCompleteWithoutBargeIn => {
                Transition(State::guidance())
            }
            _ => Super,
        }
    }

    #[action]
    fn enter_prepare(&self) {
        self.notify(CALLBACK_KIND_ENTRY, "Prepare");
    }

    #[action]
    fn exit_prepare(&self) {
        self.notify(CALLBACK_KIND_EXIT, "Prepare");
    }

    /// バージイン設定が無効の場合のガイダンス再生
    #[state(superstate = "session", entry_action = "enter_guidance", exit_action = "exit_guidance")]
    fn guidance(&mut self, event: &VoiceRecognitionEvent) -> Outcome {
        match event {
            VoiceRecognitionEvent::GuidanceComplete => {
                Transition(State::listening())
            }
            _ => Super,
        }
    }

    #[action]
    fn enter_guidance(&self) {
        self.notify(CALLBACK_KIND_ENTRY, "Guidance");
    }

    #[action]
    fn exit_guidance(&self) {
        self.notify(CALLBACK_KIND_EXIT, "Guidance");
    }

    /// バージイン設定が有効の場合のガイダンス再生（同時に音声認識開始）
    #[state(superstate = "session", entry_action = "enter_guidance_and_listening", exit_action = "exit_guidance_and_listening")]
    fn guidance_and_listening(&mut self, event: &VoiceRecognitionEvent) -> Outcome {
        match event {
            VoiceRecognitionEvent::SpeechDetected => {
                Transition(State::speaking())
            }
            VoiceRecognitionEvent::GuidanceComplete => {
                Transition(State::listening())
            }
            VoiceRecognitionEvent::RecognitionResult { .. }
            | VoiceRecognitionEvent::UtteranceTimeout => {
                Transition(State::condition_checking())
            }
            _ => Super,
        }
    }

    #[action]
    fn enter_guidance_and_listening(&self) {
        self.notify(CALLBACK_KIND_ENTRY, "GuidanceAndListening");
    }

    #[action]
    fn exit_guidance_and_listening(&self) {
        self.notify(CALLBACK_KIND_EXIT, "GuidanceAndListening");
    }

    /// 音声認識中（発話待ち）
    #[state(superstate = "session", entry_action = "enter_listening", exit_action = "exit_listening")]
    fn listening(&mut self, event: &VoiceRecognitionEvent) -> Outcome {
        match event {
            VoiceRecognitionEvent::SpeechDetected => {
                Transition(State::speaking())
            }
            VoiceRecognitionEvent::SpeechTimeout => {
                Transition(State::condition_checking())
            }
            _ => Super,
        }
    }

    #[action]
    fn enter_listening(&self) {
        self.notify(CALLBACK_KIND_ENTRY, "Listening");
    }

    #[action]
    fn exit_listening(&self) {
        self.notify(CALLBACK_KIND_EXIT, "Listening");
    }

    /// 発話検知後の音声認識中
    #[state(superstate = "session", entry_action = "enter_speaking", exit_action = "exit_speaking")]
    fn speaking(&mut self, event: &VoiceRecognitionEvent) -> Outcome {
        match event {
            VoiceRecognitionEvent::RecognitionResult { .. }
            | VoiceRecognitionEvent::UtteranceTimeout => {
                Transition(State::condition_checking())
            }
            _ => Super,
        }
    }

    #[action]
    fn enter_speaking(&self) {
        self.notify(CALLBACK_KIND_ENTRY, "Speaking");
    }

    #[action]
    fn exit_speaking(&self) {
        self.notify(CALLBACK_KIND_EXIT, "Speaking");
    }

    /// 認識結果を判定して次の遷移先を決定
    #[state(superstate = "session", entry_action = "enter_condition_checking", exit_action = "exit_condition_checking")]
    fn condition_checking(&mut self, event: &VoiceRecognitionEvent) -> Outcome {
        match event {
            VoiceRecognitionEvent::ContinueWithGuidance => {
                Transition(State::followup_guidance())
            }
            VoiceRecognitionEvent::ContinueWithTask => {
                Transition(State::task_exec_and_continue())
            }
            VoiceRecognitionEvent::TaskAndEnd => {
                Transition(State::task_exec_and_end())
            }
            VoiceRecognitionEvent::ErrorEnd => {
                Transition(State::error_and_end())
            }
            _ => Super,
        }
    }

    #[action]
    fn enter_condition_checking(&self) {
        self.notify(CALLBACK_KIND_ENTRY, "ConditionChecking");
    }

    #[action]
    fn exit_condition_checking(&self) {
        self.notify(CALLBACK_KIND_EXIT, "ConditionChecking");
    }

    /// 対話継続前のフォローアップガイダンス再生
    #[state(superstate = "session", entry_action = "enter_followup_guidance", exit_action = "exit_followup_guidance")]
    fn followup_guidance(&mut self, event: &VoiceRecognitionEvent) -> Outcome {
        match event {
            VoiceRecognitionEvent::FollowupGuidanceComplete => {
                Transition(State::prepare())
            }
            _ => Super,
        }
    }

    #[action]
    fn enter_followup_guidance(&self) {
        self.notify(CALLBACK_KIND_ENTRY, "FollowupGuidance");
    }

    #[action]
    fn exit_followup_guidance(&self) {
        self.notify(CALLBACK_KIND_EXIT, "FollowupGuidance");
    }

    /// タスク実行して対話継続
    #[state(superstate = "session", entry_action = "enter_task_exec_and_continue", exit_action = "exit_task_exec_and_continue")]
    fn task_exec_and_continue(&mut self, event: &VoiceRecognitionEvent) -> Outcome {
        match event {
            VoiceRecognitionEvent::TaskExecContinueComplete => {
                Transition(State::prepare())
            }
            _ => Super,
        }
    }

    #[action]
    fn enter_task_exec_and_continue(&self) {
        self.notify(CALLBACK_KIND_ENTRY, "TaskExecAndContinue");
    }

    #[action]
    fn exit_task_exec_and_continue(&self) {
        self.notify(CALLBACK_KIND_EXIT, "TaskExecAndContinue");
    }

    /// タスク実行して終了
    #[state(superstate = "session", entry_action = "enter_task_exec_and_end", exit_action = "exit_task_exec_and_end")]
    fn task_exec_and_end(&mut self, event: &VoiceRecognitionEvent) -> Outcome {
        match event {
            VoiceRecognitionEvent::TaskExecEndComplete => {
                self.session_status_changed = Some(crate::types::SessionStatus::Inactive);
                Transition(State::ready())
            }
            _ => Super,
        }
    }

    #[action]
    fn enter_task_exec_and_end(&self) {
        self.notify(CALLBACK_KIND_ENTRY, "TaskExecAndEnd");
    }

    #[action]
    fn exit_task_exec_and_end(&self) {
        self.notify(CALLBACK_KIND_EXIT, "TaskExecAndEnd");
    }

    /// エラーガイダンスを流して終了
    #[state(superstate = "session", entry_action = "enter_error_and_end", exit_action = "exit_error_and_end")]
    fn error_and_end(&mut self, event: &VoiceRecognitionEvent) -> Outcome {
        match event {
            VoiceRecognitionEvent::ErrorGuidanceComplete => {
                self.session_status_changed = Some(crate::types::SessionStatus::Inactive);
                Transition(State::ready())
            }
            _ => Super,
        }
    }

    #[action]
    fn enter_error_and_end(&self) {
        self.notify(CALLBACK_KIND_ENTRY, "ErrorAndEnd");
    }

    #[action]
    fn exit_error_and_end(&self) {
        self.notify(CALLBACK_KIND_EXIT, "ErrorAndEnd");
    }

    /// 中断ガイダンスを流して終了
    #[state(superstate = "session", entry_action = "enter_aborting", exit_action = "exit_aborting")]
    fn aborting(&mut self, event: &VoiceRecognitionEvent) -> Outcome {
        match event {
            VoiceRecognitionEvent::AbortGuidanceComplete => {
                self.session_status_changed = Some(crate::types::SessionStatus::Inactive);
                Transition(State::ready())
            }
            _ => Super,
        }
    }

    #[action]
    fn enter_aborting(&self) {
        self.notify(CALLBACK_KIND_ENTRY, "Aborting");
    }

    #[action]
    fn exit_aborting(&self) {
        self.notify(CALLBACK_KIND_EXIT, "Aborting");
    }
}

/// 状態名を文字列として取得
pub fn state_name(state: &State) -> &'static str {
    match state {
        State::Initializing {} => "Initializing",
        State::WaitLanguageSet {} => "WaitLanguageSet",
        State::Ready {} => "Ready",
        State::PreSession {} => "PreSession",
        State::Prepare {} => "Prepare",
        State::Guidance {} => "Guidance",
        State::GuidanceAndListening {} => "GuidanceAndListening",
        State::Listening {} => "Listening",
        State::Speaking {} => "Speaking",
        State::ConditionChecking {} => "ConditionChecking",
        State::FollowupGuidance {} => "FollowupGuidance",
        State::TaskExecAndContinue {} => "TaskExecAndContinue",
        State::TaskExecAndEnd {} => "TaskExecAndEnd",
        State::ErrorAndEnd {} => "ErrorAndEnd",
        State::Aborting {} => "Aborting",
    }
}

/// 状態がSession内かどうかを判定
pub fn is_in_session(state: &State) -> bool {
    matches!(
        state,
        State::Prepare {}
            | State::Guidance {}
            | State::GuidanceAndListening {}
            | State::Listening {}
            | State::Speaking {}
            | State::ConditionChecking {}
            | State::FollowupGuidance {}
            | State::TaskExecAndContinue {}
            | State::TaskExecAndEnd {}
            | State::ErrorAndEnd {}
            | State::Aborting {}
    )
}

/// 状態がPreSessionかどうかを判定
pub fn is_in_pre_session(state: &State) -> bool {
    matches!(state, State::PreSession {})
}
