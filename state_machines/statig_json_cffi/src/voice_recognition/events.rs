use serde::{Deserialize, Serialize};

/// 音声認識ステートマシンのイベント
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", content = "data")]
pub enum VoiceRecognitionEvent {
    // === メインレベルイベント ===
    /// 初期化完了
    InitializeComplete,
    /// 初期化失敗
    InitializeFailed,
    /// PTT（Push-to-Talk）ボタン押下
    Ptt,
    /// Wake-up Word検出
    WuWDetected,
    /// 言語変更
    LanguageChanged,
    /// PreSession問い合わせへの応答（コンテキストデータ付き）
    PreSessionResponse {
        approved: bool,
        context_data: Option<String>,
    },

    // === Sessionレベルイベント ===
    /// 中断
    Abort,
    /// サイレント中断
    SilentAbort,
    /// アイテム選択
    ItemSelected { context_id: String },
    /// 戻る
    Back { context_id: String },

    // === Session内部遷移用イベント ===
    /// Prepare完了（バージイン設定あり）
    PrepareCompleteWithBargeIn,
    /// Prepare完了（バージイン設定なし）
    PrepareCompleteWithoutBargeIn,
    /// ガイダンス再生完了
    GuidanceComplete,
    /// 発話検知
    SpeechDetected,
    /// 発話検知なし（タイムアウト）
    SpeechTimeout,
    /// 認識結果通知
    RecognitionResult { result: String },
    /// 発話タイムアウト
    UtteranceTimeout,
    /// ConditionChecking結果: 対話継続（ガイダンスあり）
    ContinueWithGuidance,
    /// ConditionChecking結果: 対話継続（タスク実行）
    ContinueWithTask,
    /// ConditionChecking結果: タスク実行して終了
    TaskAndEnd,
    /// ConditionChecking結果: エラー終了
    ErrorEnd,
    /// FollowupGuidance完了
    FollowupGuidanceComplete,
    /// タスク実行完了（継続）
    TaskExecContinueComplete,
    /// タスク実行完了（終了）
    TaskExecEndComplete,
    /// エラーガイダンス完了
    ErrorGuidanceComplete,
    /// 中断ガイダンス完了
    AbortGuidanceComplete,
}
