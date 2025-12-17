# データ処理フロー

## 概要

大量データの取り込みから処理、保存までの一連のフローを示します。バッチ処理とストリーム処理の両方に対応しています。

## バッチデータ処理フロー

```mermaid
sequenceDiagram
    autonumber
    participant Scheduler as スケジューラー
    participant Worker as ワーカー<br/>サービス
    participant Storage as オブジェクト<br/>ストレージ
    participant Processor as データ処理<br/>エンジン
    participant DB as データベース
    participant Cache as キャッシュ
    participant Monitor as モニタリング

    Scheduler->>Worker: バッチジョブ起動<br/>(定時実行)
    Worker->>Storage: データファイル取得
    Storage-->>Worker: CSVファイル

    Worker->>Processor: 処理開始

    loop データ行ごと
        Processor->>Processor: データ検証
        Processor->>Processor: データ変換

        alt データ有効
            Processor->>DB: データ挿入
            DB-->>Processor: 成功
        else データ無効
            Processor->>Storage: エラーログ保存
        end
    end

    Processor->>Cache: 集計結果をキャッシュ
    Processor-->>Worker: 処理完了レポート
    Worker->>Monitor: 処理結果送信
    Monitor-->>Scheduler: 完了通知
```

## リアルタイムストリーム処理フロー

```mermaid
sequenceDiagram
    autonumber
    participant Client as クライアント
    participant API as API<br/>サーバー
    participant Queue as メッセージ<br/>キュー
    participant Stream as ストリーム<br/>プロセッサ
    participant DB as データベース
    participant Analytics as 分析<br/>エンジン
    participant Notify as 通知<br/>サービス

    Client->>API: データ送信<br/>(イベント)
    API->>API: 簡易バリデーション
    API->>Queue: メッセージ追加
    API-->>Client: 受付完了

    Queue->>Stream: メッセージ取得

    par データ保存
        Stream->>DB: データ永続化
    and リアルタイム分析
        Stream->>Analytics: 分析処理
        Analytics->>Analytics: 異常検知

        alt 異常検知
            Analytics->>Notify: アラート送信
            Notify->>Client: プッシュ通知
        end
    end

    Stream->>Queue: ACK返却
```

## データ変換処理の詳細

```mermaid
sequenceDiagram
    autonumber
    participant Input as 入力データ
    participant Validator as バリデーター
    participant Transformer as トランス<br/>フォーマー
    participant Enricher as エンリッチャー
    participant Output as 出力データ

    Input->>Validator: 生データ

    Validator->>Validator: スキーマ検証
    Validator->>Validator: 必須項目チェック
    Validator->>Validator: データ型チェック

    alt 検証OK
        Validator->>Transformer: 検証済みデータ

        Transformer->>Transformer: フォーマット変換
        Transformer->>Transformer: 正規化
        Transformer->>Transformer: フィルタリング

        Transformer->>Enricher: 変換済みデータ

        Enricher->>Enricher: マスターデータ結合
        Enricher->>Enricher: 計算項目追加
        Enricher->>Enricher: メタデータ付与

        Enricher->>Output: 最終データ
    else 検証NG
        Validator->>Output: エラーデータ<br/>(リジェクト)
    end
```

## 処理パフォーマンス

### バッチ処理

| 項目 | 値 |
|---|---|
| 処理間隔 | 1時間ごと |
| 1回あたりのデータ量 | 最大100万レコード |
| 平均処理時間 | 15分 |
| 並列度 | 8ワーカー |

### ストリーム処理

| 項目 | 値 |
|---|---|
| スループット | 10,000メッセージ/秒 |
| レイテンシ | < 100ms (p99) |
| リトライ回数 | 最大3回 |
| デッドレターキュー | 有効 |

## エラーハンドリング

!!! danger "重要"
    - データ処理エラーは必ずログに記録
    - リトライ可能なエラーは自動リトライ
    - 致命的エラーはアラート送信

!!! tip "ベストプラクティス"
    - バッチサイズを適切に設定してメモリ使用量を最適化
    - 冪等性を保証して重複実行に対応
    - モニタリングで処理状況を可視化

## データフロー概念図

```mermaid
graph LR
    A[データソース] --> B{データ種別}
    B -->|バッチ| C[ファイルストレージ]
    B -->|ストリーム| D[メッセージキュー]
    C --> E[バッチプロセッサ]
    D --> F[ストリームプロセッサ]
    E --> G[データウェアハウス]
    F --> G
    G --> H[分析・可視化]
```
