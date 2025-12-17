# ユーザー認証フロー

## 概要

OAuth2.0を使用したユーザー認証フローを示します。クライアントアプリケーションが認証サーバーと連携してユーザー認証を行います。

## シーケンス図

### 認証フロー全体

```mermaid
sequenceDiagram
    autonumber
    actor User as ユーザー
    participant Client as クライアント<br/>アプリ
    participant Gateway as API<br/>ゲートウェイ
    participant Auth as 認証<br/>サービス
    participant DB as データベース

    User->>Client: ログイン要求
    Client->>Gateway: 認証リクエスト<br/>(email, password)

    Gateway->>Auth: 認証処理依頼
    Auth->>DB: ユーザー情報取得
    DB-->>Auth: ユーザー情報

    Auth->>Auth: パスワード検証

    alt 認証成功
        Auth->>Auth: アクセストークン生成
        Auth->>DB: トークン保存
        Auth-->>Gateway: トークン返却
        Gateway-->>Client: 認証成功レスポンス<br/>(access_token, refresh_token)
        Client->>Client: トークン保存
        Client-->>User: ログイン成功
    else 認証失敗
        Auth-->>Gateway: エラーレスポンス
        Gateway-->>Client: 認証失敗
        Client-->>User: エラーメッセージ表示
    end
```

## フロー詳細

### 1. ログイン要求
ユーザーがクライアントアプリケーションでログインフォームに情報を入力します。

### 2-3. 認証リクエスト
クライアントはAPIゲートウェイ経由で認証サービスにリクエストを送信します。

```json
{
  "email": "user@example.com",
  "password": "********"
}
```

### 4-5. ユーザー情報の検証
認証サービスはデータベースからユーザー情報を取得し、パスワードをハッシュ比較で検証します。

### 6-9. トークン生成と返却
認証成功時、JWTトークンを生成してクライアントに返却します。

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "dGhpcyBpcyByZWZyZXNo...",
  "expires_in": 3600
}
```

## トークンリフレッシュフロー

```mermaid
sequenceDiagram
    autonumber
    participant Client as クライアント<br/>アプリ
    participant Gateway as API<br/>ゲートウェイ
    participant Auth as 認証<br/>サービス
    participant DB as データベース

    Client->>Gateway: APIリクエスト<br/>(expired token)
    Gateway-->>Client: 401 Unauthorized

    Client->>Gateway: トークンリフレッシュ要求<br/>(refresh_token)
    Gateway->>Auth: リフレッシュ処理
    Auth->>DB: トークン検証
    DB-->>Auth: トークン有効

    Auth->>Auth: 新トークン生成
    Auth->>DB: 新トークン保存
    Auth-->>Gateway: 新トークン返却
    Gateway-->>Client: 新トークン

    Client->>Gateway: APIリクエスト<br/>(new token)
    Gateway-->>Client: 成功レスポンス
```

## セキュリティ考慮事項

!!! warning "セキュリティ"
    - パスワードは必ずハッシュ化して保存
    - トークンの有効期限を適切に設定
    - HTTPS通信を必須とする
    - リフレッシュトークンは1回限りの使用とする

!!! info "補足"
    - アクセストークンの有効期限: 1時間
    - リフレッシュトークンの有効期限: 30日
    - 同時ログインセッション数: 最大5セッション
