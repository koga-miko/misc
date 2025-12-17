# gRPC C++ Demo - 4つの通信方法

このプロジェクトは、gRPCの4つの通信方法をC++で実装したデモです。

## 4つの通信方法

1. **Unary RPC** - 単純なリクエスト-レスポンス
2. **Server Streaming RPC** - サーバーからのストリーミング
3. **Client Streaming RPC** - クライアントからのストリーミング
4. **Bidirectional Streaming RPC** - 双方向ストリーミング

## ファイル構成

```
.
├── demo.proto          # プロトコル定義ファイル
├── server.cpp          # サーバー実装
├── client.cpp          # クライアント実装
├── CMakeLists.txt      # ビルド設定
└── README.md           # このファイル
```

## 必要な環境

- CMake 3.15以上
- C++17対応のコンパイラ
- gRPC
- Protocol Buffers

### macOSでの依存関係インストール

```bash
# Homebrewを使用
brew install grpc protobuf cmake
```

### Ubuntuでの依存関係インストール

```bash
sudo apt-get update
sudo apt-get install -y cmake build-essential autoconf libtool pkg-config
sudo apt-get install -y libgrpc++-dev libprotobuf-dev protobuf-compiler-grpc
```

## ビルド方法

```bash
# ビルドディレクトリを作成
mkdir build
cd build

# CMakeでビルド設定を生成
cmake ..

# ビルドを実行
cmake --build .
```

## 実行方法

### サーバーの起動

```bash
# buildディレクトリから実行
./server
```

サーバーが起動すると、以下のように表示されます：

```
Server listening on 0.0.0.0:50051
===========================================
Available RPC methods:
1. UnaryCall
2. ServerStreamingCall
3. ClientStreamingCall
4. BidirectionalStreamingCall
===========================================
```

### クライアントの実行

別のターミナルを開いて：

```bash
# buildディレクトリから実行
./client
```

クライアントは自動的に4つの通信方法すべてをテストします。

## 実行例

### サーバー側の出力例

```
Server listening on 0.0.0.0:50051
[Unary] Received: World
[Server Streaming] Count: 5
[Server Streaming] Sending: Message #0
[Server Streaming] Sending: Message #1
...
[Client Streaming] Waiting for client messages...
[Client Streaming] Received: Data_0
[Client Streaming] Received: Data_1
...
[Bidirectional Streaming] Started
[Bidirectional Streaming] Received: Message_0
[Bidirectional Streaming] Sending: Echo #0: Message_0
...
```

### クライアント側の出力例

```
=========================================
gRPC C++ Demo Client
Testing all 4 communication patterns
=========================================

=== Testing Unary RPC ===
Response: Hello, World!

=== Testing Server Streaming RPC ===
Received [0]: Message #0
Received [1]: Message #1
...
Server streaming completed successfully

=== Testing Client Streaming RPC ===
Sending: Data_0
Sending: Data_1
...
Server response: Received 3 messages: Data_0 Data_1 Data_2
Total count: 3

=== Testing Bidirectional Streaming RPC ===
Sending: Message_0
Received: Echo #0: Message_0
...
Bidirectional streaming completed successfully

=========================================
All tests completed!
=========================================
```

## 各通信方法の説明

### 1. Unary RPC
最も基本的な通信方法。クライアントが1つのリクエストを送信し、サーバーが1つのレスポンスを返します。

### 2. Server Streaming RPC
クライアントがリクエストを送信すると、サーバーが複数のレスポンスをストリームで返します。

### 3. Client Streaming RPC
クライアントが複数のリクエストをストリームで送信し、サーバーが1つのレスポンスを返します。

### 4. Bidirectional Streaming RPC
クライアントとサーバーがそれぞれ独立したストリームで送受信を行います。非同期で双方向の通信が可能です。

## トラブルシューティング

### ポート50051が既に使用されている場合

サーバーのポート番号を変更してください：

```cpp
// server.cppの該当行を修正
std::string server_address("0.0.0.0:50052");
```

```cpp
// client.cppの該当行を修正
std::string server_address("localhost:50052");
```

### gRPCが見つからない場合

CMakeにgRPCのインストールパスを指定してください：

```bash
cmake -DCMAKE_PREFIX_PATH=/path/to/grpc ..
```

## 参考：通信をとめる時のお作法

### C++ クライアント側制御

| 操作 | メソッド | 効果 |
|------|---------|------|
| **送信停止** | `WritesDone()` | サーバー側の`Read()`が`false`を返す（半クローズ） |
| **受信停止** | `Read()`ループから抜ける | クライアント側で受信を止めるだけ |
| **完全終了** | `context.TryCancel()` | 両方向を即座に終了（サーバー側でCANCELLEDエラー） |
| **正常終了** | `Finish()` | ステータスコードを取得して終了 |

### C++ サーバー側制御

| 操作 | 方法 | 効果 |
|------|------|------|
| **受信停止** | `Read()`ループから抜ける | クライアントからの受信を停止、送信は継続可能 |
| **送信停止** | `Write()`を呼ばない | クライアントへの送信を停止、受信は継続可能 |
| **クライアントキャンセル検知** | `context->IsCancelled()` | クライアントが`TryCancel()`を呼んだことを検知 |
| **エラー返却** | `return Status(code, msg)` | 特定のエラーコードでRPCを終了 |

### Python クライアント側制御

| 操作 | メソッド | 効果 |
|------|---------|------|
| **送信停止** | generatorを終了 / `StopIteration`を投げる | サーバー側のイテレータが終了（半クローズ） |
| **受信停止** | `for`ループまたはイテレータから抜ける | クライアント側で受信を止めるだけ |
| **完全終了** | `call.cancel()` | 両方向を即座に終了（サーバー側でRpcError） |
| **正常終了** | generatorとイテレータの自然終了 | 正常にストリームを閉じる |
| **タイムアウト設定** | `timeout`パラメータ | 指定時間後に自動終了 |

### Python サーバー側制御

| 操作 | 方法 | 効果 |
|------|------|------|
| **受信停止** | リクエストイテレータから抜ける | クライアントからの受信を停止、送信は継続可能 |
| **送信停止** | `yield`を停止 / `return` | クライアントへの送信を停止、受信は継続可能 |
| **クライアントキャンセル検知** | `context.is_active()` / `context.cancelled()` | クライアントが`cancel()`を呼んだことを検知 |
| **エラー返却** | `context.abort(code, details)` | 特定のエラーコードでRPCを中断 |
| **エラー設定** | `context.set_code()` + `context.set_details()` | エラー情報を設定して`return` |

## 補足説明

### C++とPythonの主な違い

| 項目 | C++ | Python |
|------|-----|--------|
| **送信の停止** | `WritesDone()`を明示的に呼ぶ | generatorの終了で暗黙的 |
| **エラーハンドリング** | `Status`オブジェクトを返す | 例外またはコンテキスト操作 |
| **スレッド管理** | 明示的にスレッド作成 | asyncioまたはスレッド |
| **キャンセル検知** | `IsCancelled()`メソッド | `is_active()` / `cancelled()`メソッド |

### 半クローズ（Half-Close）の実現方法

| 言語 | クライアント側 | サーバー側 |
|------|--------------|-----------|
| **C++** | `WritesDone()`呼び出し後も`Read()`継続可能 | `Read()`終了後も`Write()`継続可能 |
| **Python** | generator終了後もイテレータ継続可能 | イテレータ終了後も`yield`継続可能 |

## ライセンス

このサンプルコードは自由に使用・改変できます。
