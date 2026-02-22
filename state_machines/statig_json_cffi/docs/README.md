# statig_json_cffi - 音声認識ステートマシン ライブラリ

Rustの[statig](https://crates.io/crates/statig)クレートで実装した階層型ステートマシンを、JSON入出力のC FFIとして公開するライブラリ。

---

## 目次

- [アーキテクチャ概要](#アーキテクチャ概要)
- [ディレクトリ構成](#ディレクトリ構成)
- [ステートマシン構成](#ステートマシン構成)
  - [音声認識SM（VoiceRecognition）](#音声認識smvoicerecognition)
  - [動的グラマ生成SM（DynamicGrammar）](#動的グラマ生成smdynamicgrammar)
  - [SM間協調](#sm間協調)
- [FFI API](#ffi-api)
  - [関数一覧](#関数一覧)
  - [コールバック](#コールバック)
  - [JSON入出力フォーマット](#json入出力フォーマット)
- [ビルドと実行](#ビルドと実行)
- [テスト](#テスト)

---

## アーキテクチャ概要

```
┌──────────────────────────────────────────────────────┐
│  C言語アプリケーション                                 │
│    - JSON文字列でイベント送信                           │
│    - JSON文字列でレスポンス受信                         │
│    - コールバックで状態entry/exit通知を受信              │
└────────────┬─────────────────────┬────────────────────┘
             │ FFI (C ABI)         │ コールバック
             ▼                     ▲
┌──────────────────────────────────────────────────────┐
│  lib.rs  (FFI層)                                      │
│    create_voice_system / destroy_voice_system          │
│    handle_event / get_current_state                    │
└────────────┬─────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────┐
│  manager.rs  (VoiceSystemManager)                     │
│    - JSONパースとルーティング                           │
│    - 2つのSMの協調管理                                 │
│    - セッション状態変更の連動                           │
├──────────────────────┬───────────────────────────────┤
│  音声認識SM (statig)  │  動的グラマ生成SM (statig)     │
│  15状態 + superstate  │  4状態                        │
└──────────────────────┴───────────────────────────────┘
```

---

## ディレクトリ構成

```
statig_json_cffi/
├── Cargo.toml                  # プロジェクト設定
├── cbindgen.toml               # cbindgen設定（参考用）
├── src/
│   ├── lib.rs                  # FFIエントリポイント（extern "C"関数群）
│   ├── manager.rs              # SM協調マネージャ
│   ├── types.rs                # 共有型定義（イベント/レスポンス/コールバック）
│   ├── voice_recognition/
│   │   ├── mod.rs              # 音声認識ステートマシン（15状態）
│   │   └── events.rs           # 音声認識イベント定義（27バリアント）
│   └── dynamic_grammar/
│       ├── mod.rs              # 動的グラマ生成ステートマシン（4状態）
│       └── events.rs           # 動的グラマイベント定義（5バリアント）
├── include/
│   └── statig_json_cffi.h      # Cヘッダファイル
├── examples/
│   └── main.c                  # C言語呼び出しサンプル
├── tests/
│   └── integration_test.rs     # 統合テスト（90テスト）
└── docs/
    ├── README.md               # 本ドキュメント
    └── state_diagrams.md       # Mermaid状態遷移図
```

### 各ファイルの役割

| ファイル | 行数目安 | 役割 |
|---------|---------|------|
| `src/lib.rs` | ~370行 | FFI関数 + ユニットテスト7件。panic安全なextern "C"関数をC側に公開 |
| `src/manager.rs` | ~100行 | `VoiceSystemManager`: JSONルーティング、SM間セッション状態連動 |
| `src/types.rs` | ~75行 | `SystemEvent`, `SystemResponse`, `SessionStatus`, `StateCallbackFn`, `invoke_callback` |
| `src/voice_recognition/mod.rs` | ~490行 | statigマクロによる15状態SM + Session superstate + entry/exit action |
| `src/voice_recognition/events.rs` | ~65行 | serde tagged enumによる27種のイベント定義 |
| `src/dynamic_grammar/mod.rs` | ~200行 | statigマクロによる4状態SM + キュー管理 + entry/exit action |
| `src/dynamic_grammar/events.rs` | ~17行 | serde tagged enumによる5種のイベント定義 |
| `tests/integration_test.rs` | ~1300行 | 90件の統合テスト（全状態・全イベント・全遷移パス網羅） |

---

## ステートマシン構成

### 音声認識SM（VoiceRecognition）

15の状態 + Session superstateを持つ階層型ステートマシン。

```
Initializing ←→ WaitLanguageSet
     │
     ▼
   Ready ←──────────────────────────────────────┐
     │                                           │
     ▼                                           │
 PreSession ─rejected──────────────────────────→┤
     │approved                                   │
     ▼                                           │
 ┌─Session superstate────────────────────────┐   │
 │  Prepare → Guidance → Listening           │   │
 │  Prepare → GuidanceAndListening           │   │
 │          → Listening / Speaking            │   │
 │  Speaking → ConditionChecking             │   │
 │  ConditionChecking → FollowupGuidance ──→ Prepare │
 │  ConditionChecking → TaskExecAndContinue→ Prepare │
 │  ConditionChecking → TaskExecAndEnd ─────────→┤
 │  ConditionChecking → ErrorAndEnd ────────────→┤
 │                                           │   │
 │  (どの状態からも)                          │   │
 │    Abort → Aborting ─────────────────────────→┤
 │    SilentAbort ──────────────────────────────→┘
 └───────────────────────────────────────────┘
```

#### 状態一覧

| # | 状態名 | superstate | 説明 |
|---|--------|-----------|------|
| 1 | Initializing | - | システム初期化中 |
| 2 | WaitLanguageSet | - | 初期化失敗→言語設定待ち |
| 3 | Ready | - | 音声認識受付待ち（PTT/WuW待機） |
| 4 | PreSession | - | セッション開始可否問い合わせ中 |
| 5 | Prepare | Session | 認識語彙の準備 |
| 6 | Guidance | Session | ガイダンス再生（バージインなし） |
| 7 | GuidanceAndListening | Session | ガイダンス再生＋音声認識同時実行 |
| 8 | Listening | Session | 発話待ち |
| 9 | Speaking | Session | 発話中の音声認識 |
| 10 | ConditionChecking | Session | 認識結果の評価・次アクション決定 |
| 11 | FollowupGuidance | Session | 対話継続前ガイダンス再生 |
| 12 | TaskExecAndContinue | Session | タスク実行→対話継続 |
| 13 | TaskExecAndEnd | Session | タスク実行→終了 |
| 14 | ErrorAndEnd | Session | エラーガイダンス→終了 |
| 15 | Aborting | Session | 中断ガイダンス→終了 |

#### イベント一覧（27種）

| カテゴリ | イベント | data | 説明 |
|---------|---------|------|------|
| メインレベル | `InitializeComplete` | - | 初期化成功 |
| | `InitializeFailed` | - | 初期化失敗 |
| | `Ptt` | - | Push-to-Talk押下 |
| | `WuWDetected` | - | Wake-up Word検出 |
| | `LanguageChanged` | - | 言語変更 |
| | `PreSessionResponse` | `{approved, context_data}` | PreSession応答 |
| Session共通 | `Abort` | - | 中断 |
| | `SilentAbort` | - | サイレント中断 |
| | `ItemSelected` | `{context_id}` | アイテム選択 |
| | `Back` | `{context_id}` | 戻る |
| Session内部 | `PrepareCompleteWithBargeIn` | - | Prepare完了（バージインあり） |
| | `PrepareCompleteWithoutBargeIn` | - | Prepare完了（バージインなし） |
| | `GuidanceComplete` | - | ガイダンス再生完了 |
| | `SpeechDetected` | - | 発話検知 |
| | `SpeechTimeout` | - | 発話待ちタイムアウト |
| | `RecognitionResult` | `{result}` | 認識結果 |
| | `UtteranceTimeout` | - | 発話タイムアウト |
| | `ContinueWithGuidance` | - | 対話継続（ガイダンスあり） |
| | `ContinueWithTask` | - | 対話継続（タスク実行） |
| | `TaskAndEnd` | - | タスク実行して終了 |
| | `ErrorEnd` | - | エラー終了 |
| | `FollowupGuidanceComplete` | - | フォローアップガイダンス完了 |
| | `TaskExecContinueComplete` | - | タスク実行完了（継続） |
| | `TaskExecEndComplete` | - | タスク実行完了（終了） |
| | `ErrorGuidanceComplete` | - | エラーガイダンス完了 |
| | `AbortGuidanceComplete` | - | 中断ガイダンス完了 |

---

### 動的グラマ生成SM（DynamicGrammar）

音声認識SMと並行して動作する4状態のステートマシン。

```
Idle → DataGetting → Generating → Idle（キュー空）
                   ↘             → DataGetting（キューあり）
                    Pending ←── Generating（セッション開始時に中断）
                       └──→ DataGetting（セッション終了時に復帰）
```

#### 状態一覧

| # | 状態名 | 説明 |
|---|--------|------|
| 1 | Idle | 待機中。生成要求でDataGettingへ |
| 2 | DataGetting | データ取得中。セッション状態に応じてGeneratingかPendingへ |
| 3 | Generating | グラマ生成中。新規要求はキューに蓄積。セッション開始で中断→Pending |
| 4 | Pending | 生成保留中。セッション終了でDataGettingへ復帰 |

#### イベント一覧（5種）

| イベント | data | 説明 |
|---------|------|------|
| `GenerateDynamicGrammar` | `{grammar_id}` | グラマ生成要求 |
| `ChangedSessionStatus` | `{status_id}` | セッション状態変更通知 |
| `NotifyData` | `{data}` | データ取得完了 |
| `GenerationComplete` | - | 生成完了 |
| `GenerationAborted` | - | 生成中断完了 |

---

### SM間協調

`VoiceSystemManager`が2つのSMを協調管理する。

1. VRイベント処理時、VR SMの`session_status_changed`フラグを監視
2. フラグがセットされていれば、DG SMへ`ChangedSessionStatus`イベントを自動送信
3. セッション状態は3値: `Inactive`, `InPreSession`, `InSession`

通知が発生するVR状態遷移:
- Ready → PreSession: `InPreSession`
- PreSession → Prepare (approved): `InSession`
- PreSession → Ready (rejected): `Inactive`
- TaskExecAndEnd → Ready: `Inactive`
- ErrorAndEnd → Ready: `Inactive`
- Aborting → Ready: `Inactive`
- Session → Ready (SilentAbort): `Inactive`

---

## FFI API

### 関数一覧

```c
#include "statig_json_cffi.h"

// コールバック型
typedef void (*state_callback_t)(int kind, const char *json);

// システム生成（callbackはNULL可）
VoiceSystemHandle *create_voice_system(state_callback_t callback);

// システム破棄（NULLセーフ）
void destroy_voice_system(VoiceSystemHandle *handle);

// JSONイベント処理 → JSON結果返却
const char *handle_event(VoiceSystemHandle *handle, const char *json_ptr);

// 現在の状態をJSON取得
const char *get_current_state(VoiceSystemHandle *handle);
```

### コールバック

状態のentry/exitタイミングでC側にコールバック通知される。

```c
void my_callback(int kind, const char *json) {
    // kind: 0 = entry（状態に入る直前）, 1 = exit（状態を抜ける直前）
    // json: {"sm":"VoiceRecognition","state":"Listening","kind":"entry"}
    printf("[%s] %s\n", kind == 0 ? "ENTRY" : "EXIT", json);
}

VoiceSystemHandle *handle = create_voice_system(my_callback);
```

コールバックJSONのフィールド:

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `sm` | string | ステートマシン名 (`"VoiceRecognition"` or `"DynamicGrammar"`) |
| `state` | string | 状態名 (`"Listening"`, `"Idle"` 等) |
| `kind` | string | `"entry"` or `"exit"` |

Session superstateのentry/exitもコールバックされる（`"state":"Session"`）。

コールバック不要の場合は`NULL`を渡す:
```c
VoiceSystemHandle *handle = create_voice_system(NULL);
```

### JSON入出力フォーマット

#### 入力（イベント送信）

基本形式:
```json
{"target": "<SM名>", "event": {"type": "<イベント名>"}}
```

データ付き:
```json
{"target": "<SM名>", "event": {"type": "<イベント名>", "data": {<データ>}}}
```

具体例:
```json
{"target":"VoiceRecognition","event":{"type":"Ptt"}}

{"target":"VoiceRecognition","event":{"type":"PreSessionResponse","data":{"approved":true,"context_data":"ctx1"}}}

{"target":"VoiceRecognition","event":{"type":"RecognitionResult","data":{"result":"navigate to Tokyo"}}}

{"target":"DynamicGrammar","event":{"type":"GenerateDynamicGrammar","data":{"grammar_id":"g1"}}}

{"target":"DynamicGrammar","event":{"type":"NotifyData","data":{"data":"John,Jane,Bob"}}}
```

#### 出力（レスポンス）

```json
{
    "success": true,
    "voice_recognition_state": "Listening",
    "dynamic_grammar_state": "Idle"
}
```

エラー時:
```json
{
    "success": false,
    "voice_recognition_state": "Ready",
    "dynamic_grammar_state": "Idle",
    "message": "JSON parse error: ..."
}
```

---

## ビルドと実行

### 前提条件

- Rust 2024 edition (1.85+)
- GCC (MinGW等、Cサンプルビルド用)

### Rustライブラリのビルド

```bash
cargo build          # debug
cargo build --release  # release
```

成果物:
- `target/debug/statig_json_cffi.dll` (Windows)
- `target/debug/libstatig_json_cffi.rlib` (Rustテスト用)

### Cサンプルのビルドと実行

```bash
# ビルド
gcc -o examples/main.exe examples/main.c \
    -Iinclude -Ltarget/debug -lstatig_json_cffi

# 実行（DLLパスを通す）
PATH=$PATH:target/debug ./examples/main.exe
```

---

## テスト

### テスト構成

| 種別 | ファイル | テスト数 | 内容 |
|------|---------|---------|------|
| ユニット | `src/lib.rs` | 7件 | FFI関数の基本動作、状態遷移、エッジケース |
| 統合 | `tests/integration_test.rs` | 90件 | 全状態・全イベント・全遷移パス網羅 |
| **合計** | | **97件** | |

### テスト実行

```bash
cargo test                    # 全テスト実行
cargo test -- --nocapture     # 出力表示付き
cargo test vr_               # 音声認識SM関連のみ
cargo test dg_               # 動的グラマSM関連のみ
cargo test coordination_     # SM間協調テストのみ
cargo test ffi_              # FFIテストのみ
```

### 統合テストのカテゴリ

| プレフィックス | テスト数 | 対象 |
|--------------|---------|------|
| `vr_` | 42件 | 音声認識SM: 全15状態からの全遷移パス |
| `dg_` | 16件 | 動的グラマSM: 全4状態からの全遷移パス + キュー管理 |
| `coordination_` | 7件 | SM間セッション状態連動 |
| `ffi_` | 7件 | FFI層: NULL安全性、JSON形式、エラーハンドリング |
| その他 | 18件 | 複合シナリオ（フルダイアログループ等） |
