# gRPCの詳細とREST APIとの比較

## 1. gRPCのバイナリフォーマット

### 1.1 Protocol Buffersの基本構造

```
フィールドエンコーディング:
┌─────────────┬──────────────────┬─────────────┐
│   Key       │   Value          │  次のフィールド │
│ (field+type)│   (データ)        │              │
└─────────────┴──────────────────┴─────────────┘

Key = (field_number << 3) | wire_type
```

### 1.2 Wire Type（データ型）

| Wire Type | 値 | 用途 | 例 |
|-----------|---|------|-----|
| Varint | 0 | int32, int64, bool | `08 96 01` |
| 64-bit | 1 | fixed64, double | 8バイト固定 |
| Length-delimited | 2 | string, bytes, message | `12 03 42 6F 62` |
| 32-bit | 5 | fixed32, float | 4バイト固定 |

### 1.3 実例：ユーザーデータ

```protobuf
message User {
  int32 id = 1;        // フィールド番号1
  string name = 2;     // フィールド番号2
  bool active = 3;     // フィールド番号3
}
```

**データ例:**
```
User {
  id: 150
  name: "Bob"
  active: true
}
```

**バイナリエンコーディング:**
```
┌─────────────────────────────────────────┐
│ 08 96 01                                │  フィールド1: id=150
│ ├─ 08: Key (1<<3|0) = フィールド1, Varint│
│ └─ 96 01: 150 (Varint)                  │
├─────────────────────────────────────────┤
│ 12 03 42 6F 62                          │  フィールド2: name="Bob"
│ ├─ 12: Key (2<<3|2) = フィールド2, String│
│ ├─ 03: 長さ3バイト                       │
│ └─ 42 6F 62: "Bob" (UTF-8)              │
├─────────────────────────────────────────┤
│ 18 01                                   │  フィールド3: active=true
│ ├─ 18: Key (3<<3|0) = フィールド3, Varint│
│ └─ 01: true                             │
└─────────────────────────────────────────┘

合計: 11バイト
```

**JSON比較:**
```json
{"id":150,"name":"Bob","active":true}
```
```
合計: 37バイト（3.4倍）
```

### 1.4 Varint詳細

```
数値 150 のエンコード:

10進数: 150
2進数:  00000000 10010110

ステップ1: 7ビットずつ分割（リトルエンディアン）
  0010110  0000001
  (下位)    (上位)

ステップ2: MSB（継続ビット）追加
  1 0010110  0 0000001
  ↑継続あり  ↑最終バイト

結果: 0x96 0x01

┌──────────┬──────────┐
│ 10010110 │ 00000001 │
│  (0x96)  │  (0x01)  │
└──────────┴──────────┘
```

### 1.5 gRPCフレームフォーマット

```
gRPCメッセージ全体の構造:

┌─────────────────┬────────────────┬─────────────────────┐
│ Compressed Flag │ Message Length │ Protobuf Message    │
│    (1 byte)     │   (4 bytes)    │     (N bytes)       │
└─────────────────┴────────────────┴─────────────────────┘

例: User { id: 150, name: "Bob", active: true }

┌────┬─────────────────┬────────────────────────────┐
│ 00 │ 00 00 00 0B     │ 08 96 01 12 03 42 6F 62 18 01 │
│    │                 │                            │
│非圧縮│ 11バイト(BigE) │ Protobufデータ(11バイト)   │
└────┴─────────────────┴────────────────────────────┘

合計: 16バイト
```

### 1.6 サイズ比較表

| データ | Protobuf | JSON | XML | 削減率 |
|--------|----------|------|-----|--------|
| User(上記) | 11 B | 37 B | 85 B | 70% |
| int32: 1 | 2 B | 8 B | 20 B | 75% |
| string: "Hello" | 7 B | 9 B | 25 B | 22% |
| 複雑なオブジェクト | 82 B | 220 B | 450 B | 63% |

## 2. gRPC通信シーケンス

### 2.1 初回接続とUnary RPC

```mermaid
sequenceDiagram
    participant C as Client
    participant N as Network
    participant S as Server
    
    Note over C,S: ===== 初回接続確立 =====
    
    rect rgb(200, 220, 240)
        Note over C,N: TCP 3-Way Handshake (1 RTT)
        C->>N: SYN
        N->>S: SYN
        S->>N: SYN-ACK
        N->>C: SYN-ACK
        C->>N: ACK
        N->>S: ACK
    end
    
    rect rgb(220, 240, 200)
        Note over C,S: TLS 1.3 Handshake (1 RTT)
        C->>S: ClientHello + KeyShare
        S->>C: ServerHello + Certificate
        C->>S: Finished
    end
    
    rect rgb(240, 220, 200)
        Note over C,S: HTTP/2 Connection (1 RTT)
        C->>S: MAGIC + SETTINGS
        S->>C: SETTINGS
        C->>S: SETTINGS ACK
        S->>C: SETTINGS ACK
    end
    
    Note over C,S: 合計 3 RTT で接続確立
    
    Note over C,S: ===== Unary RPC =====
    
    rect rgb(240, 240, 200)
        Note over C,S: Stream 1 開始
        
        C->>S: HEADERS Frame (Stream 1)
        Note right of C: :method=POST<br/>:path=/UserService/GetUser<br/>content-type=application/grpc<br/>(HPACK圧縮: 40B)
        
        C->>S: DATA Frame (Stream 1)
        Note right of C: [Compressed=0][Length=11]<br/>[Protobuf: id=150]<br/>(合計16B)
        
        Note over S: サーバー処理
        
        S->>C: HEADERS Frame (Stream 1)
        Note left of S: :status=200<br/>content-type=application/grpc<br/>(20B)
        
        S->>C: DATA Frame (Stream 1)
        Note left of S: [Protobuf: User data]<br/>(25B)
        
        S->>C: HEADERS Frame (END_STREAM)
        Note left of S: grpc-status=0<br/>grpc-message=""<br/>(15B)
        
        Note over C,S: Stream 1 完了 (1 RTT)
    end
    
    Note over C,S: 接続維持、次で再利用
```

### 2.2 複数メッセージの多重化

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Server
    
    Note over C,S: ===== HTTP/2多重化（既存接続） =====
    
    par Stream 1: GetUser(id=1)
        C->>S: HEADERS(1) + DATA(1)
        Note over S: 処理中...
        S->>C: HEADERS(1) + DATA(1)
    and Stream 3: GetUser(id=2)
        C->>S: HEADERS(3) + DATA(3)
        Note over S: 処理中...
        S->>C: HEADERS(3) + DATA(3)
    and Stream 5: GetUser(id=3)
        C->>S: HEADERS(5) + DATA(5)
        Note over S: 処理中...
        S->>C: HEADERS(5) + DATA(5)
    end
    
    Note over C,S: 3つのRPCが同時並行<br/>1つのTCP接続上で多重化<br/>合計: 1 RTT（並列実行）
```

### 2.3 Server Streaming RPC

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Server
    
    Note over C,S: ===== Server Streaming RPC =====
    
    C->>S: HEADERS(Stream 1)
    Note right of C: :path=/UserService/ListUsers
    C->>S: DATA(Stream 1)
    Note right of C: [Empty request]
    
    Note over S: ユーザー一覧取得開始
    
    S->>C: HEADERS(Stream 1)
    Note left of S: :status=200
    
    loop サーバーがデータを送信し続ける
        S->>C: DATA(Stream 1)
        Note left of S: [User 1 data]
        Note over C: User 1 処理
        
        S->>C: DATA(Stream 1)
        Note left of S: [User 2 data]
        Note over C: User 2 処理
        
        S->>C: DATA(Stream 1)
        Note left of S: [User 3 data]
        Note over C: User 3 処理
    end
    
    S->>C: HEADERS(END_STREAM)
    Note left of S: grpc-status=0
    
    Note over C,S: リアルタイムストリーミング<br/>1つのストリームで複数メッセージ
```

### 2.4 Bidirectional Streaming RPC

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Server
    
    Note over C,S: ===== 双方向ストリーミング =====
    
    C->>S: HEADERS(Stream 1)
    Note right of C: :path=/ChatService/Chat
    S->>C: HEADERS(Stream 1)
    Note left of S: :status=200
    
    Note over C,S: ストリーム確立、双方向通信開始
    
    par クライアントからサーバーへ
        C->>S: DATA(Stream 1)
        Note right of C: [Message: "Hello"]
        C->>S: DATA(Stream 1)
        Note right of C: [Message: "How are you?"]
        C->>S: DATA(Stream 1)
        Note right of C: [Message: "Goodbye"]
    and サーバーからクライアントへ
        S->>C: DATA(Stream 1)
        Note left of S: [Message: "Hi there!"]
        S->>C: DATA(Stream 1)
        Note left of S: [Message: "I'm fine"]
        S->>C: DATA(Stream 1)
        Note left of S: [Message: "See you"]
    end
    
    C->>S: DATA(END_STREAM)
    S->>C: HEADERS(END_STREAM)
    Note left of S: grpc-status=0
    
    Note over C,S: 完全な双方向通信<br/>順序は非同期
```

## 3. REST API通信シーケンス

### 3.1 初回接続とリクエスト（Keep-Alive）

```mermaid
sequenceDiagram
    participant C as Client
    participant N as Network
    participant S as Server
    
    Note over C,S: ===== 初回接続 =====
    
    rect rgb(200, 220, 240)
        Note over C,N: TCP 3-Way Handshake (1 RTT)
        C->>N: SYN
        N->>S: SYN
        S->>N: SYN-ACK
        N->>C: SYN-ACK
        C->>N: ACK
        N->>S: ACK
    end
    
    rect rgb(220, 240, 200)
        Note over C,S: TLS 1.3 Handshake (1 RTT)
        C->>S: ClientHello + KeyShare
        S->>C: ServerHello + Certificate
        C->>S: Finished
    end
    
    Note over C,S: 合計 2 RTT で接続確立
    
    Note over C,S: ===== 1つ目のリクエスト (1 RTT) =====
    
    C->>S: GET /api/users/150 HTTP/1.1
    Note right of C: Host: server.com<br/>Accept: application/json<br/>Connection: keep-alive<br/>User-Agent: MyApp/1.0<br/>Authorization: Bearer...<br/>(約180B)
    
    Note over S: サーバー処理
    
    S->>C: HTTP/1.1 200 OK
    Note left of S: Content-Type: application/json<br/>Content-Length: 37<br/>Connection: keep-alive<br/>Cache-Control: max-age=3600<br/>{"id":150,"name":"Bob"}<br/>(約220B)
    
    Note over C,S: 接続維持（Keep-Alive）
    
    Note over C,S: ===== 2つ目のリクエスト (1 RTT) =====
    
    C->>S: GET /api/users/151 HTTP/1.1
    Note right of C: 同じヘッダーを毎回送信<br/>圧縮なし<br/>(約180B)
    
    Note over S: 処理
    
    S->>C: HTTP/1.1 200 OK
    Note left of S: {"id":151,"name":"Alice"}<br/>(約220B)
    
    Note over C,S: 各リクエスト: 1 RTT<br/>ヘッダー圧縮なし
```

### 3.2 複数リクエスト（直列処理）

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Server
    
    Note over C,S: ===== HTTP/1.1 の制限: 順次処理 =====
    
    C->>S: GET /api/users/1 HTTP/1.1
    Note right of C: (180B)
    Note over C,S: リクエスト2,3は待機...
    S->>C: HTTP/1.1 200 OK
    Note left of S: User1 (220B)
    Note over C,S: 1 RTT
    
    C->>S: GET /api/users/2 HTTP/1.1
    Note right of C: (180B)
    Note over C,S: リクエスト3は待機...
    S->>C: HTTP/1.1 200 OK
    Note left of S: User2 (220B)
    Note over C,S: 1 RTT
    
    C->>S: GET /api/users/3 HTTP/1.1
    Note right of C: (180B)
    S->>C: HTTP/1.1 200 OK
    Note left of S: User3 (220B)
    Note over C,S: 1 RTT
    
    Note over C,S: 合計: 3 RTT（順次実行）<br/>Head-of-Line Blocking発生<br/>総データ量: 1,200B
```

### 3.3 接続都度確立（最悪パターン）

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Server
    
    Note over C,S: ===== リクエスト1 =====
    
    rect rgb(240, 200, 200)
        C->>S: TCP SYN
        S->>C: SYN-ACK
        C->>S: ACK
        Note over C,S: 1 RTT
    end
    
    rect rgb(240, 220, 200)
        C->>S: TLS Handshake
        S->>C: Certificates
        Note over C,S: 1 RTT
    end
    
    C->>S: GET /api/users/1
    Note right of C: Connection: close
    S->>C: HTTP/1.1 200 OK
    Note left of S: User1
    Note over C,S: 1 RTT
    
    C->>S: FIN
    S->>C: FIN-ACK
    Note over C,S: 接続クローズ
    
    Note over C,S: リクエスト1完了: 3 RTT
    
    Note over C,S: ===== リクエスト2（再接続） =====
    
    rect rgb(240, 200, 200)
        C->>S: TCP SYN（再度!）
        S->>C: SYN-ACK
        C->>S: ACK
    end
    
    rect rgb(240, 220, 200)
        C->>S: TLS Handshake（再度!）
        S->>C: Certificates
    end
    
    C->>S: GET /api/users/2
    S->>C: HTTP/1.1 200 OK
    
    Note over C,S: リクエスト2完了: 3 RTT
    
    Note over C,S: 合計: 6 RTT<br/>非常に非効率
```

### 3.4 RESTful CRUD操作

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Server
    
    Note over C,S: ===== CREATE (POST) =====
    C->>S: POST /api/users HTTP/1.1
    Note right of C: Content-Type: application/json<br/>{"name":"Bob","email":"bob@example.com"}
    S->>C: HTTP/1.1 201 Created
    Note left of S: Location: /api/users/150<br/>{"id":150,"name":"Bob"}
    
    Note over C,S: ===== READ (GET) =====
    C->>S: GET /api/users/150 HTTP/1.1
    Note right of C: Accept: application/json
    S->>C: HTTP/1.1 200 OK
    Note left of S: Cache-Control: max-age=3600<br/>ETag: "abc123"<br/>{"id":150,"name":"Bob"}
    
    Note over C,S: ===== UPDATE (PUT) =====
    C->>S: PUT /api/users/150 HTTP/1.1
    Note right of C: If-Match: "abc123"<br/>{"name":"Bob","email":"new@example.com"}
    S->>C: HTTP/1.1 200 OK
    Note left of S: ETag: "xyz789"<br/>{"id":150,"email":"new@example.com"}
    
    Note over C,S: ===== DELETE (DELETE) =====
    C->>S: DELETE /api/users/150 HTTP/1.1
    S->>C: HTTP/1.1 204 No Content
    
    Note over C,S: 各操作: 1 RTT<br/>合計: 4 RTT
```

## 4. gRPC vs REST 詳細比較

### 4.1 データ量比較

```mermaid
graph LR
    subgraph "gRPC (Protobuf)"
        A1[リクエスト 16B] --> B1[レスポンス 30B]
        style A1 fill:#9f9
        style B1 fill:#9f9
    end
    
    subgraph "REST (JSON)"
        A2[リクエスト 180B] --> B2[レスポンス 220B]
        style A2 fill:#f99
        style B2 fill:#f99
    end
    
    C[削減率] --> D[約85%削減]
    style D fill:#ff9
```

### 4.2 接続確立の違い

```mermaid
gantt
    title 初回接続までの時間 (RTT = 50ms)
    dateFormat X
    axisFormat %L ms
    
    section gRPC
    TCP Handshake :0, 50
    TLS Handshake :50, 100
    HTTP/2 Setup :100, 150
    
    section REST
    TCP Handshake :0, 50
    TLS Handshake :50, 100
```

### 4.3 複数リクエストの効率

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Server
    
    Note over C,S: gRPC: 並列実行（1 RTT）
    
    par Stream 1
        C->>S: Req1
        S->>C: Res1
    and Stream 3
        C->>S: Req2
        S->>C: Res2
    and Stream 5
        C->>S: Req3
        S->>C: Res3
    end
    
    Note over C,S: データ量: 約150B
    
    Note over C,S: ─────────────────────────
    
    Note over C,S: REST: 順次実行（3 RTT）
    
    C->>S: Req1 (180B)
    S->>C: Res1 (220B)
    
    C->>S: Req2 (180B)
    S->>C: Res2 (220B)
    
    C->>S: Req3 (180B)
    S->>C: Res3 (220B)
    
    Note over C,S: データ量: 約1,200B
```

### 4.4 ストリーミングの違い

```mermaid
graph TD
    subgraph "gRPC: ネイティブサポート"
        A1[Client] <-->|双方向Stream| B1[Server]
        B1 -->|Real-time push| C1[即座に受信]
        style A1 fill:#9f9
        style B1 fill:#9f9
        style C1 fill:#9f9
    end
    
    subgraph "REST: 代替手段"
        A2[Client] -->|Polling 5秒ごと| B2[Server]
        B2 -->|Response| A2
        A3[Client] -->|Long Polling| B3[Server]
        B3 -.->|Wait...| B3
        B3 -->|Event発生| A3
        A4[Client] <-->|WebSocket RESTではない| B4[Server]
        style A2 fill:#f99
        style B2 fill:#f99
        style A3 fill:#ff9
        style B3 fill:#ff9
        style A4 fill:#99f
        style B4 fill:#99f
    end
```

## 5. 性能比較サマリー

### 5.1 レイテンシ比較（RTT = 50ms）

```mermaid
gantt
    title 5メッセージ送信の総時間
    dateFormat X
    axisFormat %L ms
    
    section gRPC
    接続確立 (3 RTT) :0, 150
    メッセージ5件 (1 RTT) :150, 200
    
    section REST (Keep-Alive)
    接続確立 (2 RTT) :0, 100
    メッセージ5件 (5 RTT) :100, 350
    
    section REST (都度接続)
    メッセージ1 (3 RTT) :0, 150
    メッセージ2 (3 RTT) :150, 300
    メッセージ3 (3 RTT) :300, 450
    メッセージ4 (3 RTT) :450, 600
    メッセージ5 (3 RTT) :600, 750
```

### 5.2 データ転送量比較

| 項目 | gRPC | REST | 差 |
|------|------|------|-----|
| **初回接続** | 約200B | 約150B | +33% |
| **1リクエスト** | 約50B | 約400B | -87% |
| **5リクエスト** | 約450B | 約2,150B | -79% |
| **ヘッダー圧縮** | HPACK (85%削減) | なし | - |
| **ボディ圧縮** | Protobuf (60%削減) | JSON | - |

### 5.3 機能比較

```mermaid
graph TB
    subgraph "gRPC の強み"
        G1[双方向ストリーミング]
        G2[HTTP/2多重化]
        G3[型安全]
        G4[コード自動生成]
        G5[バイナリ効率]
        style G1 fill:#9f9
        style G2 fill:#9f9
        style G3 fill:#9f9
        style G4 fill:#9f9
        style G5 fill:#9f9
    end
    
    subgraph "REST の強み"
        R1[シンプル]
        R2[デバッグ容易]
        R3[キャッシング]
        R4[ブラウザ対応]
        R5[ツール豊富]
        style R1 fill:#99f
        style R2 fill:#99f
        style R3 fill:#99f
        style R4 fill:#99f
        style R5 fill:#99f
    end
```

## 6. まとめ

### 6.1 選択基準

```mermaid
graph TD
    Start[API設計] --> Q1{高性能必要?}
    
    Q1 -->|Yes| Q2{ストリーミング?}
    Q2 -->|Yes| gRPC1[gRPC]
    Q2 -->|No| Q3{マイクロサービス?}
    Q3 -->|Yes| gRPC2[gRPC]
    Q3 -->|No| Q4{型安全重要?}
    Q4 -->|Yes| gRPC3[gRPC]
    Q4 -->|No| REST1[REST検討]
    
    Q1 -->|No| Q5{公開API?}
    Q5 -->|Yes| REST2[REST]
    Q5 -->|No| Q6{ブラウザ直接?}
    Q6 -->|Yes| REST3[REST]
    Q6 -->|No| Q7{キャッシング重要?}
    Q7 -->|Yes| REST4[REST]
    Q7 -->|No| Both[どちらでも可]
    
    style gRPC1 fill:#9f9
    style gRPC2 fill:#9f9
    style gRPC3 fill:#9f9
    style REST1 fill:#99f
    style REST2 fill:#99f
    style REST3 fill:#99f
    style REST4 fill:#99f
    style Both fill:#ff9
```

### 6.2 パフォーマンス要約

**gRPCが優れる点:**
- ✅ データサイズ: 約80%削減
- ✅ レイテンシ: 複数リクエストで3-5倍高速
- ✅ 並列処理: HTTP/2多重化
- ✅ ストリーミング: ネイティブサポート

**RESTが優れる点:**
- ✅ シンプルさ: curl でテスト可能
- ✅ デバッグ: 人間可読
- ✅ キャッシング: HTTP標準機構
- ✅ エコシステム: ツール・ドキュメント豊富

**推奨:**
- **内部マイクロサービス**: gRPC
- **公開Web API**: REST
- **モバイル⇔バックエンド**: gRPC
- **ブラウザ⇔サーバー**: REST (またはgRPC-Web)