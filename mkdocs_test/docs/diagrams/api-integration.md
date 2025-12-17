# API連携フロー

## 概要

外部サービスとのAPI連携における標準的なフローを示します。認証、リトライ、エラーハンドリングを含みます。

## 外部API呼び出しフロー

```mermaid
sequenceDiagram
    autonumber
    actor User as ユーザー
    participant Frontend as フロント<br/>エンド
    participant Backend as バック<br/>エンド
    participant Cache as キャッシュ
    participant Gateway as API<br/>ゲートウェイ
    participant External as 外部API

    User->>Frontend: 機能実行要求
    Frontend->>Backend: APIリクエスト

    Backend->>Cache: キャッシュ確認

    alt キャッシュヒット
        Cache-->>Backend: キャッシュデータ
        Backend-->>Frontend: レスポンス
        Frontend-->>User: 結果表示
    else キャッシュミス
        Cache-->>Backend: キャッシュなし

        Backend->>Gateway: 外部API呼び出し準備
        Gateway->>Gateway: APIキー取得
        Gateway->>Gateway: リクエスト構築

        Gateway->>External: HTTP Request

        alt 成功 (200 OK)
            External-->>Gateway: 成功レスポンス
            Gateway->>Gateway: レスポンス検証
            Gateway-->>Backend: データ返却
            Backend->>Cache: キャッシュ保存
            Backend-->>Frontend: レスポンス
            Frontend-->>User: 結果表示

        else エラー (4xx/5xx)
            External-->>Gateway: エラーレスポンス
            Gateway->>Gateway: エラー判定

            alt リトライ可能 (5xx)
                loop 最大3回
                    Gateway->>External: リトライ
                    External-->>Gateway: レスポンス
                end
            else リトライ不可 (4xx)
                Gateway-->>Backend: エラー返却
                Backend-->>Frontend: エラーレスポンス
                Frontend-->>User: エラーメッセージ
            end
        end
    end
```

## Webhook受信フロー

```mermaid
sequenceDiagram
    autonumber
    participant External as 外部サービス
    participant Firewall as ファイア<br/>ウォール
    participant Webhook as Webhook<br/>エンドポイント
    participant Validator as 署名検証
    participant Queue as メッセージ<br/>キュー
    participant Worker as ワーカー
    participant DB as データベース
    participant Notify as 通知<br/>サービス

    External->>Firewall: Webhook POST
    Firewall->>Firewall: IPホワイトリスト確認

    alt 許可IPから
        Firewall->>Webhook: リクエスト転送

        Webhook->>Validator: 署名検証依頼
        Validator->>Validator: HMAC署名確認

        alt 署名有効
            Validator-->>Webhook: 検証OK
            Webhook->>Queue: イベント登録
            Webhook-->>External: 200 OK (即座に応答)

            Queue->>Worker: イベント処理
            Worker->>Worker: ビジネスロジック実行
            Worker->>DB: データ更新
            Worker->>Notify: 完了通知

        else 署名無効
            Validator-->>Webhook: 検証NG
            Webhook-->>External: 401 Unauthorized
        end

    else 不正IPから
        Firewall-->>External: 403 Forbidden
    end
```

## サービス間連携フロー

```mermaid
sequenceDiagram
    autonumber
    participant ServiceA as サービスA
    participant Registry as サービス<br/>レジストリ
    participant LB as ロード<br/>バランサー
    participant ServiceB as サービスB<br/>(インスタンス1)
    participant ServiceB2 as サービスB<br/>(インスタンス2)
    participant Monitor as モニタリング

    ServiceA->>Registry: サービスB検索
    Registry-->>ServiceA: エンドポイント情報

    ServiceA->>LB: リクエスト送信

    LB->>LB: ヘルスチェック確認
    LB->>LB: ラウンドロビン選択

    alt インスタンス1が健全
        LB->>ServiceB: リクエスト転送
        ServiceB->>ServiceB: 処理実行
        ServiceB-->>LB: レスポンス
        LB-->>ServiceA: レスポンス返却

    else インスタンス1が異常
        LB->>ServiceB2: フェイルオーバー
        ServiceB2->>ServiceB2: 処理実行
        ServiceB2-->>LB: レスポンス
        LB-->>ServiceA: レスポンス返却
    end

    ServiceA->>Monitor: メトリクス送信
    ServiceB->>Monitor: メトリクス送信
```

## API認証フロー (OAuth 2.0 Client Credentials)

```mermaid
sequenceDiagram
    autonumber
    participant Service as 自システム<br/>サービス
    participant Cache as トークン<br/>キャッシュ
    participant AuthServer as 認証<br/>サーバー
    participant API as 外部API

    Service->>Cache: トークン確認

    alt トークン有効
        Cache-->>Service: 有効なトークン
    else トークン期限切れ
        Cache-->>Service: トークンなし

        Service->>AuthServer: トークン要求<br/>(client_id, client_secret)
        AuthServer->>AuthServer: クライアント認証
        AuthServer-->>Service: access_token
        Service->>Cache: トークン保存<br/>(TTL設定)
    end

    Service->>API: APIリクエスト<br/>(Authorization: Bearer token)

    alt トークン有効
        API->>API: トークン検証
        API->>API: 処理実行
        API-->>Service: 成功レスポンス

    else トークン無効
        API-->>Service: 401 Unauthorized
        Service->>Cache: トークン削除
        Note over Service: 最初から再試行
    end
```

## API仕様

### エンドポイント例

```http
GET /api/v1/users/{userId}/profile
Authorization: Bearer {access_token}
Accept: application/json
```

### レスポンス例

```json
{
  "status": "success",
  "data": {
    "userId": "12345",
    "name": "山田太郎",
    "email": "yamada@example.com",
    "createdAt": "2024-01-01T00:00:00Z"
  },
  "metadata": {
    "requestId": "req_abc123",
    "timestamp": "2024-12-17T10:30:00Z"
  }
}
```

## SLA・パフォーマンス指標

| 指標 | 目標値 |
|---|---|
| レスポンスタイム | < 200ms (p95) |
| 可用性 | 99.9% |
| エラー率 | < 0.1% |
| リトライ成功率 | > 95% |

## エラーハンドリング戦略

!!! warning "リトライ戦略"
    - **5xx エラー**: 指数バックオフでリトライ (1秒、2秒、4秒)
    - **429 (Rate Limit)**: Retry-Afterヘッダーに従う
    - **4xx エラー (429以外)**: リトライしない

!!! info "タイムアウト設定"
    - 接続タイムアウト: 5秒
    - 読み取りタイムアウト: 30秒
    - 全体タイムアウト: 60秒

!!! tip "ベストプラクティス"
    - サーキットブレーカーパターンの実装
    - レート制限の遵守
    - 適切なキャッシュ戦略
    - 詳細なログとモニタリング

## 連携先一覧

| サービス名 | 用途 | プロトコル | 認証方式 |
|---|---|---|---|
| 決済サービス | 決済処理 | HTTPS/REST | OAuth 2.0 |
| メール配信 | メール送信 | HTTPS/REST | APIキー |
| SMS送信 | SMS通知 | HTTPS/REST | Basic認証 |
| 地図サービス | 位置情報 | HTTPS/REST | APIキー |
