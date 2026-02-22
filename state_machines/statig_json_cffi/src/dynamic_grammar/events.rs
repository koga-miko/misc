use serde::{Deserialize, Serialize};

/// 動的グラマ生成ステートマシンのイベント
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", content = "data")]
pub enum DynamicGrammarEvent {
    /// グラマ生成要求
    GenerateDynamicGrammar { grammar_id: String },
    /// セッション状態変更通知
    ChangedSessionStatus { status_id: String },
    /// データ通知（データ取得完了）
    NotifyData { data: String },
    /// グラマ生成完了
    GenerationComplete,
    /// グラマ生成中断完了
    GenerationAborted,
}
