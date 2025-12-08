# Protocol Buffers について

## gRPCのバイナリフォーマット

gRPCで使用されるProtocol Buffersのバイナリエンコーディングについて詳しく説明します。

### Protocol Buffersの基本エンコーディング

**Wireタイプ**
Protocol Buffersでは、各フィールドは「フィールド番号」と「Wireタイプ」でエンコードされます。

**Wireタイプ値用途**
- Varint: int32, int64, uint32, uint64, sint32, sint64, bool, enum64-bit1fixed64, sfixed64, double
- Length-delimited: string, bytes, embedded messages, repeated fields32-bit5fixed32, sfixed32, float

**キーのエンコーディング**
各フィールドは**キー（Tag）**で始まります：
- キー = (フィールド番号 << 3) | Wireタイプ

例：
```
フィールド番号1、Wireタイプ0（Varint） → 0x08 (1 << 3 | 0 = 8)
フィールド番号2、Wireタイプ2（Length-delimited） → 0x12 (2 << 3 | 2 = 18)

Varintエンコーディング：
Varintは可変長整数エンコーディングです。小さい数値ほど少ないバイトで表現されます。

エンコーディングルール：
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
```

### エンコード例2：ネストされたメッセージ
```
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
