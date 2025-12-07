# タイトル
## サブタイトル1
通信パターン
gRPCは4つの通信パターンをサポートしています：

Unary RPC - 単純なリクエスト/レスポンス
Server streaming - クライアントが1つのリクエストを送り、サーバーからストリームでレスポンスを受け取る
Client streaming - クライアントがストリームでリクエストを送り、サーバーが1つのレスポンスを返す
Bidirectional streaming - 双方向でストリームを送受信


```mermaid
sequenceDiagram
    participant C as Client
    participant S as Server
    
    Note over C,S: 1. 導通確認
    C->>S: HTTP/2 HEADERS: :method=POST: :path=/HealthService/Check
    S->>C: HTTP/2 HEADERS :status=200
    S->>C: HTTP/2 DATA [health status]
    S->>C: HTTP/2 HEADERS (trailers): grpc-status=0
    
    Note over C,S: 2. オープン (チャネル開設)
    C->>S: HTTP/2 HEADERS: :path=/ChannelService/Open
    C->>S: HTTP/2 DATA [target info]
    S->>C: HTTP/2 HEADERS :status=200
    S->>C: HTTP/2 DATA [channel_id]
    S->>C: HTTP/2 HEADERS: grpc-status=0
    
    Note over C,S: 3. サブスク登録 (Server Streaming開始)
    C->>S: HTTP/2 HEADERS: :path=/ChannelService/Read
    C->>S: HTTP/2 DATA [channel_id, callback_info]
    S->>C: HTTP/2 HEADERS :status=200
    Note over S: ストリーム確立: サーバー側でコールバック準備
    
    Note over C,S: 4. コールバック複数 (非同期イベント)
    S->>C: HTTP/2 DATA [json_message_1]
    Note over C: コールバック1実行
    S->>C: HTTP/2 DATA [json_message_2]
    Note over C: コールバック2実行
    S->>C: HTTP/2 DATA [json_message_3]
    Note over C: コールバック3実行
    Note over C,S: ストリームは継続中
    
    Note over C,S: 5. クローズ (チャネル閉鎖)
    C->>S: HTTP/2 HEADERS: :path=/ChannelService/Close
    C->>S: HTTP/2 DATA [channel_id]
    S->>C: HTTP/2 HEADERS :status=200
    S->>C: HTTP/2 DATA [close result]
    S->>C: HTTP/2 HEADERS: grpc-status=0
    Note over S: Readストリーム終了
    S->>C: HTTP/2 HEADERS (Read終了): grpc-status=0
    
    Note over C,S: 6. 切断
    C->>S: HTTP/2 GOAWAY
    Note over C,S: TCP接続クローズ
```

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Server
    
    Note over C,S: 1. 導通確認
    C->>S: GET /health HTTP/1.1<br/>Host: example.com
    S->>C: HTTP/1.1 200 OK<br/>Content-Type: application/json<br/><br/>{"status":"ok"}
    Note over C,S: 接続クローズまたはKeep-Alive
    
    Note over C,S: 2. オープン (セッション作成)
    C->>S: POST /channels HTTP/1.1<br/>Content-Type: application/json<br/><br/>{"target":"device1"}
    S->>C: HTTP/1.1 201 Created<br/>Content-Type: application/json<br/><br/>{"channel_id":"ch_123"}
    
    Note over C,S: 3. サブスク登録 (コールバックURL登録)
    C->>S: POST /channels/ch_123/subscribe HTTP/1.1<br/>Content-Type: application/json<br/><br/>{"callback_url":"http://client/callback"}
    S->>C: HTTP/1.1 200 OK<br/>{"subscription_id":"sub_456"}
    Note over S: Webhook情報を保存
    
    Note over C,S: 4. コールバック複数 (Webhook呼び出し)
    Note over S: イベント1発生
    S->>C: POST /callback HTTP/1.1<br/>Content-Type: application/json<br/><br/>{"event":"message_1"}
    C->>S: HTTP/1.1 200 OK
    Note over C: コールバック1実行
    
    Note over S: イベント2発生
    S->>C: POST /callback HTTP/1.1<br/>Content-Type: application/json<br/><br/>{"event":"message_2"}
    C->>S: HTTP/1.1 200 OK
    Note over C: コールバック2実行
    
    Note over S: イベント3発生
    S->>C: POST /callback HTTP/1.1<br/>Content-Type: application/json<br/><br/>{"event":"message_3"}
    C->>S: HTTP/1.1 200 OK
    Note over C: コールバック3実行
    
    Note over C,S: 5. クローズ (セッション削除)
    C->>S: DELETE /channels/ch_123/subscribe/sub_456 HTTP/1.1
    S->>C: HTTP/1.1 204 No Content
    Note over S: サブスクリプション削除
    
    C->>S: DELETE /channels/ch_123 HTTP/1.1
    S->>C: HTTP/1.1 204 No Content
    Note over S: チャネル削除
    
    Note over C,S: 6. 切断
    Note over C,S: HTTP接続クローズ<br/>(Keep-Aliveの場合はタイムアウト)
```
