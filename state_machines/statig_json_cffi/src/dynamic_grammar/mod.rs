pub mod events;

use crate::types::{invoke_callback, StateCallbackFn, CALLBACK_KIND_ENTRY, CALLBACK_KIND_EXIT};
use events::DynamicGrammarEvent;
use statig::blocking::*;
use std::collections::VecDeque;
use std::fmt;

type Outcome = statig::Outcome<State>;

const SM_NAME: &str = "DynamicGrammar";

/// 動的グラマ生成ステートマシンの本体
pub struct DynamicGrammarMachine {
    /// 生成要求キュー
    pub queue: VecDeque<String>,
    /// 現在のセッション状態（音声認識SMから通知される）
    pub session_active: bool,
    /// C言語側への状態entry/exitコールバック
    pub callback: StateCallbackFn,
}

impl Default for DynamicGrammarMachine {
    fn default() -> Self {
        Self {
            queue: VecDeque::new(),
            session_active: false,
            callback: None,
        }
    }
}

impl fmt::Debug for DynamicGrammarMachine {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "DynamicGrammarMachine")
    }
}

#[state_machine(
    initial = "State::idle()",
    event_identifier = "event",
    state(derive(Debug, Clone, PartialEq, Eq))
)]
impl DynamicGrammarMachine {
    // ===========================
    // コールバック通知ヘルパー
    // ===========================

    fn notify(&self, kind: i32, state: &str) {
        invoke_callback(self.callback, kind, SM_NAME, state);
    }

    // ===========================
    // 状態
    // ===========================

    /// Idle: グラマ生成が動いていない状態
    #[state(entry_action = "enter_idle", exit_action = "exit_idle")]
    fn idle(&mut self, event: &DynamicGrammarEvent) -> Outcome {
        match event {
            DynamicGrammarEvent::GenerateDynamicGrammar { .. } => {
                Transition(State::data_getting())
            }
            DynamicGrammarEvent::ChangedSessionStatus { status_id } => {
                self.session_active =
                    status_id == "InPreSession" || status_id == "InSession";
                Handled
            }
            _ => Handled,
        }
    }

    #[action]
    fn enter_idle(&self) {
        self.notify(CALLBACK_KIND_ENTRY, "Idle");
    }

    #[action]
    fn exit_idle(&self) {
        self.notify(CALLBACK_KIND_EXIT, "Idle");
    }

    /// DataGetting: 動的グラマを作るためのデータを取得中
    #[state(entry_action = "enter_data_getting", exit_action = "exit_data_getting")]
    fn data_getting(&mut self, event: &DynamicGrammarEvent) -> Outcome {
        match event {
            DynamicGrammarEvent::NotifyData { .. } => {
                if self.session_active {
                    Transition(State::pending())
                } else {
                    Transition(State::generating())
                }
            }
            DynamicGrammarEvent::ChangedSessionStatus { status_id } => {
                self.session_active =
                    status_id == "InPreSession" || status_id == "InSession";
                Handled
            }
            DynamicGrammarEvent::GenerateDynamicGrammar { grammar_id } => {
                self.queue.push_back(grammar_id.clone());
                Handled
            }
            _ => Handled,
        }
    }

    #[action]
    fn enter_data_getting(&self) {
        self.notify(CALLBACK_KIND_ENTRY, "DataGetting");
    }

    #[action]
    fn exit_data_getting(&self) {
        self.notify(CALLBACK_KIND_EXIT, "DataGetting");
    }

    /// Generating: グラマ生成動作中
    #[state(entry_action = "enter_generating", exit_action = "exit_generating")]
    fn generating(&mut self, event: &DynamicGrammarEvent) -> Outcome {
        match event {
            DynamicGrammarEvent::GenerateDynamicGrammar { grammar_id } => {
                self.queue.push_back(grammar_id.clone());
                Handled
            }
            DynamicGrammarEvent::GenerationComplete => {
                if let Some(_next) = self.queue.pop_front() {
                    Transition(State::data_getting())
                } else {
                    Transition(State::idle())
                }
            }
            DynamicGrammarEvent::ChangedSessionStatus { status_id } => {
                let new_active =
                    status_id == "InPreSession" || status_id == "InSession";
                if new_active && !self.session_active {
                    self.session_active = true;
                    Transition(State::pending())
                } else {
                    self.session_active = new_active;
                    Handled
                }
            }
            DynamicGrammarEvent::GenerationAborted => {
                Transition(State::pending())
            }
            _ => Handled,
        }
    }

    #[action]
    fn enter_generating(&self) {
        self.notify(CALLBACK_KIND_ENTRY, "Generating");
    }

    #[action]
    fn exit_generating(&self) {
        self.notify(CALLBACK_KIND_EXIT, "Generating");
    }

    /// Pending: グラマ生成保留中（セッションが終了するまで待機）
    #[state(entry_action = "enter_pending", exit_action = "exit_pending")]
    fn pending(&mut self, event: &DynamicGrammarEvent) -> Outcome {
        match event {
            DynamicGrammarEvent::ChangedSessionStatus { status_id } => {
                let new_active =
                    status_id == "InPreSession" || status_id == "InSession";
                self.session_active = new_active;
                if !new_active {
                    Transition(State::data_getting())
                } else {
                    Handled
                }
            }
            DynamicGrammarEvent::GenerateDynamicGrammar { grammar_id } => {
                self.queue.push_back(grammar_id.clone());
                Handled
            }
            _ => Handled,
        }
    }

    #[action]
    fn enter_pending(&self) {
        self.notify(CALLBACK_KIND_ENTRY, "Pending");
    }

    #[action]
    fn exit_pending(&self) {
        self.notify(CALLBACK_KIND_EXIT, "Pending");
    }
}

/// 状態名を文字列として取得
pub fn state_name(state: &State) -> &'static str {
    match state {
        State::Idle {} => "Idle",
        State::DataGetting {} => "DataGetting",
        State::Generating {} => "Generating",
        State::Pending {} => "Pending",
    }
}
