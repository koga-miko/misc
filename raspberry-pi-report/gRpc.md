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




## gRPCのバイナリフォーマット
gRPCで使用されるProtocol Buffersのバイナリエンコーディングについて詳しく説明します。
Protocol Buffersの基本エンコーディング
Wireタイプ
Protocol Buffersでは、各フィールドは「フィールド番号」と「Wireタイプ」でエンコードされます。
Wireタイプ値用途Varint0int32, int64, uint32, uint64, sint32, sint64, bool, enum64-bit1fixed64, sfixed64, doubleLength-delimited2string, bytes, embedded messages, repeated fields32-bit5fixed32, sfixed32, float
キーのエンコーディング
各フィールドは**キー（Tag）**で始まります：
キー = (フィールド番号 << 3) | Wireタイプ
例：
```
フィールド番号1、Wireタイプ0（Varint） → 0x08 (1 << 3 | 0 = 8)
フィールド番号2、Wireタイプ2（Length-delimited） → 0x12 (2 << 3 | 2 = 18)

Varintエンコーディング
Varintは可変長整数エンコーディングです。小さい数値ほど少ないバイトで表現されます。
エンコーディングルール

各バイトの最上位ビット（MSB）が継続フラグ
MSB=1: 次のバイトも続く
MSB=0: 最後のバイト
下位7ビットがデータ

例：数値150のエンコード
150 = 10010110 (2進数)

ステップ1: 7ビットずつ分割
  0000001 0010110

ステップ2: リトルエンディアンで並べる
  0010110 0000001

ステップ3: MSBを付ける
  10010110 00000001

結果: 0x96 0x01
数値    バイナリ           エンコード結果
0       00000000          0x00
1       00000001          0x01
127     01111111          0x7F
128     10000000          0x80 0x01
150     10010110          0x96 0x01
300     100101100         0xAC 0x02
実際のメッセージ例
protoファイル定義
protobuf
message Person {
  int32 id = 1;        // フィールド番号1
  string name = 2;     // フィールド番号2
  bool active = 3;     // フィールド番号3
  repeated int32 scores = 4;  // フィールド番号4
}
```

### エンコード例1：基本データ
```
Person {
  id: 150
  name: "Bob"
  active: true
}
```

**バイナリ表現：**
```
08 96 01          # フィールド1: id=150
                  # 08 = (1<<3|0) キー
                  # 96 01 = 150 (Varint)

12 03 42 6F 62    # フィールド2: name="Bob"
                  # 12 = (2<<3|2) キー
                  # 03 = 長さ3
                  # 42 6F 62 = "Bob" (UTF-8)

18 01             # フィールド3: active=true
                  # 18 = (3<<3|0) キー
                  # 01 = true

合計：11バイト

JSON比較：
json{"id":150,"name":"Bob","active":true}
JSONは37バイト（約3.4倍）
エンコード例2：ネストされたメッセージ
protobuf
message Address {
  string city = 1;
  int32 zip = 2;
}

message Person {
  string name = 1;
  Address address = 2;
}

Person {
  name: "Alice"
  address: {
    city: "Tokyo"
    zip: 1000001
  }
}
```

**バイナリ表現：**
```
0A 05 41 6C 69 63 65    # フィールド1: name="Alice"
                         # 0A = (1<<3|2) キー
                         # 05 = 長さ5
                         # 41 6C 69 63 65 = "Alice"

12 0C                    # フィールド2: address (Length-delimited)
                         # 12 = (2<<3|2) キー
                         # 0C = 長さ12 (埋め込みメッセージのサイズ)
  
  # 埋め込みメッセージAddress:
  0A 05 54 6F 6B 79 6F   # city="Tokyo"
                         # 0A = (1<<3|2)
                         # 05 = 長さ5
                         # 54 6F 6B 79 6F = "Tokyo"
  
  10 81 84 3D            # zip=1000001
                         # 10 = (2<<3|0)
                         # 81 84 3D = 1000001 (Varint)
```

### エンコード例3：repeated（配列）
```
Person {
  scores: [85, 90, 78]
}
```

**方式1：個別エンコード**
```
20 55    # scores[0]=85  (0x20 = 4<<3|0)
20 5A    # scores[1]=90
20 4E    # scores[2]=78
```

**方式2：パックドエンコード（効率的）**
```
22 03 55 5A 4E    # packed repeated
                  # 22 = (4<<3|2) Length-delimited
                  # 03 = 長さ3バイト
                  # 55 5A 4E = [85, 90, 78]
```

## gRPCフレームフォーマット

gRPCでは、Protocol Buffersメッセージを以下の形式でラップします：
```
+------------------+------------------+------------------+
| Compressed-Flag  | Message-Length   | Message-Data     |
| (1 byte)         | (4 bytes)        | (N bytes)        |
+------------------+------------------+------------------+
```

### 例：Personメッセージの送信
```
Person { id: 150, name: "Bob", active: true }
のProtobuf = 08 96 01 12 03 42 6F 62 18 01 (11バイト)
```

**gRPCフレーム：**
```
00                    # 圧縮なし
00 00 00 0B           # メッセージ長=11 (ビッグエンディアン)
08 96 01 12 03 42 6F 62 18 01   # Protobufデータ
```

**合計：16バイト**

### ストリーミング時の複数メッセージ
```
[フレーム1: Message 1]
00 00 00 00 0B [11 bytes data]

[フレーム2: Message 2]
00 00 00 00 08 [8 bytes data]

[フレーム3: Message 3]
00 00 00 00 0F [15 bytes data]
```

各メッセージは独立したフレームとして送信されます。

## 特殊なデータ型

### sint32/sint64（ZigZag符号化）

負の数を効率的にエンコードするため、ZigZag符号化を使用：
```
符号付き値  ZigZag値  バイナリ
0          0         0x00
-1         1         0x01
1          2         0x02
-2         3         0x03
2          4         0x04

変換式：
ZigZag(n) = (n << 1) ^ (n >> 31)  // 32bit
ZigZag(n) = (n << 1) ^ (n >> 63)  // 64bit
```

### fixed32/fixed64（固定長）

常に4バイトまたは8バイトを使用（リトルエンディアン）：
```
fixed32: 0x12345678
→ 78 56 34 12

fixed64: 0x0123456789ABCDEF
→ EF CD AB 89 67 45 23 01
大きな数値が多い場合、Varintより効率的です。
実践的なサイズ比較
MCPプロトコル風のJSONメッセージ
JSON形式：
json{
  "jsonrpc": "2.0",
  "method": "notifications/message",
  "params": {
    "level": "info",
    "message": "Connection established"
  }
}
サイズ：約130バイト
Protocol Buffers定義：
protobufmessage McpMessage {
  string jsonrpc = 1;
  string method = 2;
  Params params = 3;
  
  message Params {
    string level = 1;
    string message = 2;
  }
}
```

**バイナリエンコード：**
```
0A 03 32 2E 30                    # jsonrpc="2.0" (5バイト)
12 16 6E 6F 74 69 66 69 63 61 74  # method="notifications/message" (24バイト)
69 6F 6E 73 2F 6D 65 73 73 61 67 65
1A 23                              # params (Length-delimited)
  0A 04 69 6E 66 6F                # level="info" (6バイト)
  12 1B 43 6F 6E 6E 65 63 74 69 6F  # message="Connection established" (29バイト)
  6E 20 65 73 74 61 62 6C 69 73 68
  65 64
合計：約65バイト（JSON比で50%削減）
デコード手順（C++実装イメージ）
cpp// バイナリからProtobufメッセージをデコード
bool DecodeMessage(const uint8_t* data, size_t size) {
    size_t pos = 0;
    
    while (pos < size) {
        // キーを読む
        uint32_t key;
        pos += DecodeVarint(data + pos, &key);
        
        uint32_t field_number = key >> 3;
        uint32_t wire_type = key & 0x07;
        
        switch (wire_type) {
            case 0: {  // Varint
                uint64_t value;
                pos += DecodeVarint(data + pos, &value);
                // field_numberに応じて値を格納
                break;
            }
            case 2: {  // Length-delimited
                uint32_t length;
                pos += DecodeVarint(data + pos, &length);
                // data[pos]からlengthバイト読む
                pos += length;
                break;
            }
            // 他のwire_typeも同様
        }
    }
    return true;
}
```
このバイナリフォーマットにより、gRPCは高速かつ省メモリで通信できます。特に埋め込みシステムでは、この効率性が重要になります。



## gRPCとRESTの通信効率比較：詳細シーケンス
両者の「本当の違い」を理解するため、TCP/IPレイヤーまで含めた詳細なシーケンスを比較します。
シナリオ：5件のメッセージを順次送信
protobuf// 各メッセージ
message Data {
  int32 id = 1;
  string content = 2;
}
gRPC (HTTP/2) の詳細シーケンス
```mermaid
sequenceDiagram
    participant C as Client
    participant TCP as TCP Layer
    participant S as Server
    
    Note over C,S: ===== 接続確立 (1回のみ) =====
    C->>TCP: SYN
    TCP->>S: SYN
    S->>TCP: SYN-ACK
    TCP->>C: SYN-ACK
    C->>TCP: ACK
    TCP->>S: ACK
    Note over C,S: TCP接続確立完了
    
    Note over C,S: ===== TLSハンドシェイク (省略可能) =====
    C->>S: ClientHello
    S->>C: ServerHello + Certificate
    C->>S: ClientKeyExchange
    Note over C,S: TLS確立完了
    
    Note over C,S: ===== HTTP/2接続初期化 (1回のみ) =====
    C->>S: HTTP/2 Connection Preface<br/>"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"
    C->>S: SETTINGS frame<br/>[max_concurrent_streams=100,<br/>initial_window_size=65535]
    S->>C: SETTINGS frame<br/>[server settings]
    C->>S: SETTINGS ACK
    S->>C: SETTINGS ACK
    Note over C,S: HTTP/2接続確立完了
    
    Note over C,S: ===== Stream 1: メッセージ1送信 =====
    C->>S: HEADERS frame (Stream 1)<br/>:method=POST<br/>:path=/DataService/Send<br/>:authority=server.com<br/>content-type=application/grpc<br/>(圧縮済みヘッダー: 約40バイト)
    
    C->>S: DATA frame (Stream 1)<br/>[Compressed=0][Length=15]<br/>[Protobuf: id=1, content="msg1"]<br/>(計20バイト)
    
    S->>C: HEADERS frame (Stream 1)<br/>:status=200<br/>content-type=application/grpc<br/>(約20バイト)
    
    S->>C: DATA frame (Stream 1)<br/>[Response data: 10バイト]
    
    S->>C: HEADERS frame (Stream 1, END_STREAM)<br/>grpc-status=0<br/>grpc-message=""<br/>(約15バイト)
    
    Note over C,S: Stream 1完了。TCP接続は維持
    
    Note over C,S: ===== Stream 3: メッセージ2送信 =====
    Note over C,S: 既存接続を再利用、HEADERSは圧縮済み
    C->>S: HEADERS frame (Stream 3)<br/>(HPACK圧縮により約5バイト!)
    C->>S: DATA frame (Stream 3)<br/>[20バイト]
    S->>C: HEADERS + DATA + TRAILERS<br/>(約45バイト)
    
    Note over C,S: ===== Stream 5,7,9: メッセージ3,4,5 =====
    Note over C,S: 同様に効率的に送信<br/>各メッセージ約70バイト
    
    Note over C,S: ===== 接続維持 =====
    S->>C: PING frame (Keep-alive)
    C->>S: PING ACK
    
    Note over C,S: 合計データ量<br/>初期: 約200バイト (1回のみ)<br/>メッセージ5件: 約350バイト<br/>総計: 約550バイト
```
REST (HTTP/1.1) の詳細シーケンス
```mermaid
sequenceDiagram
    participant C as Client
    participant TCP as TCP Layer
    participant S as Server
    
    Note over C,S: ===== メッセージ1送信 =====
    Note over C,S: 接続1確立
    C->>TCP: SYN
    TCP->>S: SYN
    S->>TCP: SYN-ACK
    TCP->>C: SYN-ACK
    C->>TCP: ACK
    TCP->>S: ACK
    Note over C,S: TCP 3-way handshake完了
    
    Note over C,S: TLSハンドシェイク (4RTT)
    C->>S: ClientHello
    S->>C: ServerHello + Certificate + Done
    C->>S: ClientKeyExchange + ChangeCipherSpec
    S->>C: ChangeCipherSpec + Finished
    Note over C,S: TLS確立完了
    
    C->>S: POST /api/data HTTP/1.1\r\n<br/>Host: server.com\r\n<br/>Content-Type: application/json\r\n<br/>Content-Length: 35\r\n<br/>Connection: keep-alive\r\n<br/>\r\n<br/>{"id":1,"content":"msg1"}<br/>(約180バイト)
    
    S->>C: HTTP/1.1 200 OK\r\n<br/>Content-Type: application/json\r\n<br/>Content-Length: 22\r\n<br/>Connection: keep-alive\r\n<br/>\r\n<br/>{"status":"success"}<br/>(約150バイト)
    
    Note over C,S: Keep-Alive維持
    
    Note over C,S: ===== メッセージ2送信 =====
    Note over C,S: 同じTCP接続を再利用
    C->>S: POST /api/data HTTP/1.1\r\n<br/>Host: server.com\r\n<br/>Content-Type: application/json\r\n<br/>Content-Length: 35\r\n<br/>\r\n<br/>{"id":2,"content":"msg2"}<br/>(約180バイト、ヘッダー圧縮なし!)
    
    S->>C: HTTP/1.1 200 OK\r\n<br/>...<br/>(約150バイト)
    
    Note over C,S: ===== メッセージ3,4,5送信 =====
    Note over C,S: 各メッセージ約330バイト<br/>(毎回同じヘッダーを送信)
    
    Note over C,S: Keep-Aliveタイムアウト (通常60秒)
    Note over C,S: または接続クローズ
    C->>S: FIN
    S->>C: ACK
    S->>C: FIN
    C->>S: ACK
    
    Note over C,S: 合計データ量<br/>初期: 約330バイト (メッセージ1)<br/>メッセージ2-5: 約1320バイト<br/>総計: 約1650バイト
```
REST (HTTP/1.1 Keep-Aliveなし) の場合
```mermaid
sequenceDiagram
    participant C as Client
    participant S as Server
    
    Note over C,S: ===== メッセージ1 =====
    C->>S: TCP SYN (3-way handshake)
    S->>C: SYN-ACK
    C->>S: ACK
    C->>S: TLS Handshake (4 RTT)
    C->>S: POST /api/data HTTP/1.1<br/>Connection: close<br/>...<br/>(約180バイト)
    S->>C: HTTP/1.1 200 OK<br/>...<br/>(約150バイト)
    C->>S: FIN
    S->>C: FIN-ACK
    Note over C,S: 接続クローズ
    
    Note over C,S: ===== メッセージ2 =====
    C->>S: TCP SYN (再度3-way handshake!)
    S->>C: SYN-ACK
    C->>S: ACK
    C->>S: TLS Handshake (再度4 RTT!)
    C->>S: POST /api/data HTTP/1.1<br/>(約180バイト)
    S->>C: HTTP/1.1 200 OK<br/>(約150バイト)
    Note over C,S: 接続クローズ
    
    Note over C,S: ===== メッセージ3,4,5も同様 =====
    Note over C,S: 各メッセージごとに<br/>TCP + TLS確立が必要!
    
    Note over C,S: 合計データ量<br/>5回のTCP確立<br/>5回のTLS確立<br/>総計: 約2500バイト + 遅延大
```

## バイト単位の詳細比較

### gRPC (HTTP/2) - 5メッセージ送信
```
=== 初期化 (1回のみ) ===
TCP 3-way handshake:     20バイト (SYN/ACK制御)
TLS handshake:           ~500バイト (証明書含む)
HTTP/2 Connection:       ~100バイト (SETTINGS等)
---
初期化合計:              ~620バイト

=== メッセージ1 ===
HEADERS (未圧縮):        40バイト
  :method: POST (インデックス化)
  :path: /DataService/Send
  :authority: server.com
  content-type: application/grpc

DATA:                    20バイト
  [0x00][0x00 0x00 0x00 0x0F]  # 5バイトヘッダー
  [id=1, content="msg1"]       # 15バイトProtobuf

Response HEADERS:        20バイト
Response DATA:           15バイト
Response TRAILERS:       15バイト
---
メッセージ1小計:         110バイト

=== メッセージ2-5 (HPACK圧縮効果) ===
HEADERS (HPACK圧縮):     5バイト!
  # 前回と同じヘッダーは索引参照のみ
  # 例: 0x82 = :method POST (静的テーブル参照)

DATA:                    20バイト
Response:                50バイト
---
メッセージ2-5小計:       75バイト × 4 = 300バイト

=== gRPC総計 ===
初期化:                  620バイト (1回のみ)
メッセージ:              410バイト (5件)
---
総計:                    1030バイト
```

### REST (HTTP/1.1 Keep-Alive) - 5メッセージ送信
```
=== 初期化 ===
TCP 3-way handshake:     20バイト
TLS handshake:           ~500バイト
---
初期化合計:              ~520バイト

=== メッセージ1 ===
Request:
POST /api/data HTTP/1.1\r\n              # 24バイト
Host: server.com\r\n                     # 18バイト
Content-Type: application/json\r\n      # 33バイト
Content-Length: 35\r\n                   # 20バイト
Connection: keep-alive\r\n               # 24バイト
User-Agent: ...\r\n                      # 30バイト
Accept: */*\r\n                          # 13バイト
\r\n                                     # 2バイト
{"id":1,"content":"msg1"}                # 35バイト (JSON)
---
Request小計:             199バイト

Response:
HTTP/1.1 200 OK\r\n                      # 17バイト
Content-Type: application/json\r\n      # 33バイト
Content-Length: 22\r\n                   # 20バイト
Connection: keep-alive\r\n               # 24バイト
Date: ...\r\n                            # 37バイト
Server: nginx\r\n                        # 15バイト
\r\n                                     # 2バイト
{"status":"success"}                     # 22バイト
---
Response小計:            170バイト

メッセージ1小計:         369バイト

=== メッセージ2-5 (圧縮なし!) ===
各メッセージ:            369バイト × 4 = 1476バイト
# ヘッダーは毎回同じ内容を送信!

=== REST総計 ===
初期化:                  520バイト
メッセージ:              1845バイト (5件)
---
総計:                    2365バイト
```

### REST (HTTP/1.1 接続都度確立) - 5メッセージ送信
```
=== 各メッセージごと ===
TCP handshake:           20バイト × 5 = 100バイト
TLS handshake:           500バイト × 5 = 2500バイト
HTTP Request/Response:   369バイト × 5 = 1845バイト
TCP teardown:            20バイト × 5 = 100バイト
---
総計:                    4545バイト
```

## レイテンシ（遅延）比較

### gRPC (HTTP/2)
```
初回接続:
  TCP handshake:         1 RTT
  TLS handshake:         2-3 RTT (TLS 1.3の場合)
  HTTP/2 SETTINGS:       1 RTT
  ---
  初回合計:              4-5 RTT

メッセージ送信 (2回目以降):
  データ送信→応答:       1 RTT
  
5メッセージ合計:         9-10 RTT
```

### REST (Keep-Alive)
```
初回接続:
  TCP handshake:         1 RTT
  TLS handshake:         2-3 RTT
  ---
  初回合計:              3-4 RTT

各メッセージ送信:
  リクエスト→レスポンス:  1 RTT × 5
  
5メッセージ合計:         8-9 RTT
```

### REST (接続都度確立)
```
各メッセージごと:
  TCP handshake:         1 RTT
  TLS handshake:         2-3 RTT
  リクエスト→レスポンス:  1 RTT
  ---
  1メッセージ:           4-5 RTT
  
5メッセージ合計:         20-25 RTT (!!)
HTTP/2の多重化効果
gRPC: 並列送信可能
```
```mermaid
sequenceDiagram
    participant C as Client
    participant S as Server
    
    Note over C,S: 同一TCP接続上で複数ストリーム同時送信
    
    par Stream 1
        C->>S: HEADERS(1) + DATA(1)
        S->>C: Response(1)
    and Stream 3
        C->>S: HEADERS(3) + DATA(3)
        S->>C: Response(3)
    and Stream 5
        C->>S: HEADERS(5) + DATA(5)
        S->>C: Response(5)
    end
    
    Note over C,S: 3つのリクエストが同時進行<br/>Head-of-Line Blocking回避
```
REST (HTTP/1.1): 直列処理
```mermaid
sequenceDiagram
    participant C as Client
    participant S as Server
    
    C->>S: Request 1
    Note over C,S: Request 2,3は待機...
    S->>C: Response 1
    
    C->>S: Request 2
    Note over C,S: Request 3は待機...
    S->>C: Response 2
    
    C->>S: Request 3
    S->>C: Response 3
    
    Note over C,S: 順次処理のみ<br/>Head-of-Line Blocking発生
```
実測値の例（100メッセージ送信）
項目gRPC (HTTP/2)REST (Keep-Alive)REST (都度接続)総データ量~15KB~35KB~450KB総RTT数~105~103~400実時間 (50ms RTT)~5.25秒~5.15秒~20秒実時間 (200ms RTT)~21秒~20.6秒~80秒CPU使用率低 (バイナリ)中 (JSON)高 (接続確立)メモリ使用量少 (接続1本)中 (接続1本)多 (接続100本)
結論：なぜgRPCが効率的か

接続の再利用: HTTP/2で1本のTCP接続を維持
ヘッダー圧縮: HPACK により2回目以降のヘッダーが数バイト
バイナリプロトコル: Protocol BuffersでJSONの約50%サイズ
多重化: 複数リクエストを並列処理、待ち時間なし
フロー制御: ウィンドウサイズ管理で効率的なデータ転送




